"""Bounded loader for the downloaded official MaleCNS Feather tables."""

from dataclasses import dataclass
from pathlib import Path
import ctypes
import time
import numpy as np
import pyarrow.dataset as ds
import pyarrow.feather as feather

from .graph import SparseGraph


MAX_CONNECTOME_NODES = 100_000
MAX_SOURCE_EDGES = 50_000_000


def _bounded_int(value, *, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not minimum <= int(value) <= maximum:
        raise ValueError(f"{label} must be an integer between {minimum} and {maximum}")
    return int(value)


def _coerce_edge_ids(values, *, label: str, allow_negative: bool = False) -> np.ndarray:
    raw = np.asarray(values)
    try:
        finite = np.isfinite(raw).all()
        integral = np.equal(raw, np.rint(raw)).all()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain numeric IDs") from exc
    if not finite or not integral:
        raise ValueError(f"{label} contains non-finite or non-integral IDs")
    lower_bound = np.iinfo(np.int64).min if allow_negative else 0
    if np.any(raw < lower_bound) or np.any(raw > np.iinfo(np.int64).max):
        raise ValueError(f"{label} contains out-of-range IDs")
    return raw.astype(np.int64, copy=False)


def _process_working_set_bytes() -> int | None:
    """Read the current Windows process working set without a dependency."""
    if not hasattr(ctypes, "windll"):
        return None

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = ctypes.c_void_p
    get_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    get_memory_info.restype = ctypes.c_int
    ok = get_memory_info(get_current_process(), ctypes.byref(counters), counters.cb)
    return int(counters.working_set_size) if ok else None


@dataclass(frozen=True)
class ConnectomeSelection:
    graph: SparseGraph
    body_ids: np.ndarray
    neurotransmitter_signs: np.ndarray
    annotated_rows: int
    selected_rows: int
    source_edges: int
    retained_edges: int
    selection_rule: str

    @property
    def id_integrity(self) -> dict:
        """Return cheap, explicit integrity facts for a bounded selection."""
        ids = np.asarray(self.body_ids)
        return {
            "selected_ids_sorted_unique": bool(len(ids) == len(np.unique(ids)) and np.all(ids[:-1] < ids[1:])),
            "selected_id_count": int(len(ids)),
            "graph_node_count_matches_selected_ids": bool(self.graph.n_nodes == len(ids)),
            "retained_edge_indices_in_graph": bool(
                np.all(self.graph.pre >= 0)
                and np.all(self.graph.post >= 0)
                and np.all(self.graph.pre < self.graph.n_nodes)
                and np.all(self.graph.post < self.graph.n_nodes)
            ),
        }


def load_bounded_connectome(
    raw_dir: Path, max_nodes: int = 4096, max_source_edges: int = 10_000_000
) -> ConnectomeSelection:
    """Load a deterministic annotated-segment subgraph without dense allocation.

    The current run selects the lowest sorted annotated body IDs. This is a
    segment-level research fixture, not a whole-brain neuron graph.
    """
    max_nodes = _bounded_int(max_nodes, label="max_nodes", minimum=2, maximum=MAX_CONNECTOME_NODES)
    max_source_edges = _bounded_int(max_source_edges, label="max_source_edges", minimum=1, maximum=MAX_SOURCE_EDGES)
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        raise ValueError("raw_dir must be an existing directory")
    try:
        annotation_path = next(raw_dir.glob("body-annotations*.feather"))
        weight_path = next(raw_dir.glob("connectome-weights*.feather"))
        nt_path = next(raw_dir.glob("body-neurotransmitters*.feather"))
    except StopIteration as exc:
        raise ValueError("raw_dir is missing one or more required Feather tables") from exc

    annotations = feather.read_table(annotation_path, columns=["bodyId"])
    all_ids = np.unique(annotations["bodyId"].to_numpy(zero_copy_only=False))
    try:
        finite_ids = np.isfinite(all_ids).all()
        integral_ids = np.equal(all_ids, np.rint(all_ids)).all()
    except (TypeError, ValueError) as exc:
        raise ValueError("body annotations must contain numeric body IDs") from exc
    if all_ids.ndim != 1 or not len(all_ids) or not finite_ids:
        raise ValueError("body annotations contain non-finite or empty body IDs")
    if not integral_ids:
        raise ValueError("body annotations contain non-integral body IDs")
    if np.any(all_ids < 0) or np.any(all_ids > np.iinfo(np.int64).max):
        raise ValueError("body annotations contain out-of-range body IDs")
    all_ids = all_ids.astype(np.int64, copy=False)
    body_ids = np.sort(all_ids)[:max_nodes]
    nt = feather.read_table(nt_path, columns=["body", "consensus_nt"])
    nt_signs = np.zeros(len(body_ids), dtype=np.float32)
    sign_by_name = {"acetylcholine": 1.0, "glutamate": -1.0, "gaba": -1.0}
    for body, label in zip(nt["body"].to_numpy(zero_copy_only=False), nt["consensus_nt"].to_pylist()):
        i = int(np.searchsorted(body_ids, body))
        if i < len(body_ids) and body_ids[i] == body and label:
            nt_signs[i] = sign_by_name.get(str(label).strip().lower(), 0.0)

    pre_parts: list[np.ndarray] = []
    post_parts: list[np.ndarray] = []
    weight_parts: list[np.ndarray] = []
    source_edges = 0
    scanner = ds.dataset(weight_path, format="feather").scanner(
        columns=["body_pre", "body_post", "weight"], batch_size=250_000
    )
    for batch in scanner.to_batches():
        data = batch.to_pydict()
        pre = _coerce_edge_ids(data["body_pre"], label="body_pre")
        post = _coerce_edge_ids(data["body_post"], label="body_post")
        raw_weights = np.asarray(data["weight"], dtype=np.float32)
        if not np.isfinite(raw_weights).all():
            raise ValueError("connectome weights contain non-finite values")
        remaining = max_source_edges - source_edges
        if len(pre) > remaining:
            pre = pre[:remaining]
            post = post[:remaining]
            raw_weights = raw_weights[:remaining]
        keep = np.isin(pre, body_ids) & np.isin(post, body_ids)
        source_edges += len(pre)
        if keep.any():
            pre_parts.append(np.searchsorted(body_ids, pre[keep]).astype(np.int32))
            post_parts.append(np.searchsorted(body_ids, post[keep]).astype(np.int32))
            raw_weight = raw_weights[keep]
            signs = nt_signs[pre_parts[-1]]
            post_parts[-1] = post_parts[-1]
            # Unknown transmitter mapping keeps the published positive contact
            # count. Known assumptions flip inhibitory edges for the experiment.
            factors = np.where(signs == 0, 1.0, np.sign(signs))
            weight_parts.append(factors * raw_weight)
        if source_edges >= max_source_edges:
            break

    if not pre_parts:
        raise RuntimeError("selected annotated subgraph has no retained edges")
    pre = np.concatenate(pre_parts)
    post = np.concatenate(post_parts)
    weight = np.concatenate(weight_parts)
    scale = max(float(np.max(np.abs(weight))), 1.0)
    graph = SparseGraph(len(body_ids), pre, post, weight / scale)
    return ConnectomeSelection(
        graph=graph,
        body_ids=body_ids,
        neurotransmitter_signs=nt_signs,
        annotated_rows=len(all_ids),
        selected_rows=len(body_ids),
        source_edges=source_edges,
        retained_edges=len(pre),
        selection_rule=f"sorted unique annotated bodyId, first {max_nodes}",
    )


def scan_full_connectome(raw_dir: Path) -> dict:
    """Stream the complete downloaded graph and emit a bounded receipt.

    This validates the full Feather weight table without retaining all edges,
    so it is evidence about source integrity and scan feasibility, not a claim
    that a full executable graph fits the local memory budget.
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        raise ValueError("raw_dir must be an existing directory")
    try:
        weight_path = next(raw_dir.glob("connectome-weights*.feather"))
    except StopIteration as exc:
        raise ValueError("raw_dir is missing the connectome weights Feather table") from exc
    started = time.perf_counter()
    import tracemalloc

    tracemalloc.start()
    rows = 0
    batches = 0
    invalid_endpoint_rows = 0
    min_body = None
    max_body = None
    peak_working_set = _process_working_set_bytes()
    scanner = ds.dataset(weight_path, format="feather").scanner(
        columns=["body_pre", "body_post", "weight"], batch_size=1_000_000
    )
    try:
        for batch in scanner.to_batches():
            batches += 1
            # Convert one bounded batch at a time. ``to_pydict`` would create
            # a large Python object graph for every batch and obscure the
            # memory boundary we are measuring.
            pre = _coerce_edge_ids(batch.column(0).to_numpy(zero_copy_only=False), label="body_pre", allow_negative=True)
            post = _coerce_edge_ids(batch.column(1).to_numpy(zero_copy_only=False), label="body_post", allow_negative=True)
            weight = batch.column(2).to_numpy(zero_copy_only=False).astype(np.float64, copy=False)
            rows += len(pre)
            invalid_endpoint_rows += int(np.count_nonzero((pre < 0) | (post < 0)))
            if not np.isfinite(weight).all():
                raise ValueError("connectome weights contain non-finite values")
            if len(pre):
                batch_min = int(min(pre.min(), post.min()))
                batch_max = int(max(pre.max(), post.max()))
                min_body = batch_min if min_body is None else min(min_body, batch_min)
                max_body = batch_max if max_body is None else max(max_body, batch_max)
            if len(weight) != len(pre):
                raise RuntimeError("weight batch columns have inconsistent lengths")
            current_ws = _process_working_set_bytes()
            if current_ws is not None and (peak_working_set is None or current_ws > peak_working_set):
                peak_working_set = current_ws
    except Exception:
        tracemalloc.stop()
        raise
    _, python_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "completed": True,
        "file_bytes": weight_path.stat().st_size,
        "rows_scanned": rows,
        "batches": batches,
        "invalid_endpoint_rows": invalid_endpoint_rows,
        "body_id_min": min_body,
        "body_id_max": max_body,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "python_tracemalloc_peak_bytes": python_peak,
        "process_working_set_peak_bytes": peak_working_set,
        "mode": "streaming validation only; no full graph materialization",
    }
