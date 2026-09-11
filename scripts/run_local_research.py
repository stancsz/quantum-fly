"""Run the bounded official-connectome research smoke test."""

from datetime import datetime, timezone
from pathlib import Path
import json
import time
import tracemalloc
import numpy as np

from quantum_fly.classical import classical_baseline, graph_score
from quantum_fly.backtest import run_backtest
from quantum_fly.connectome import load_bounded_connectome
from quantum_fly.market import load_history, load_or_download, causal_features
from quantum_fly.quantum import quantum_score


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    started = time.perf_counter()
    tracemalloc.start()
    raw = ROOT / "data" / "malecns-v1.0" / "raw"
    market_cache = ROOT / "data" / "market" / "sp500-2024.csv"
    market_features, market_provenance = load_or_download(market_cache)
    closes, history_provenance = load_history(market_cache)
    selection = load_bounded_connectome(raw, max_nodes=4096, max_source_edges=10_000_000)
    neural = graph_score(selection.graph, market_features, steps=2)
    zero_graph_input = graph_score(selection.graph, np.zeros(4), steps=2)
    perturbed_graph_input = graph_score(selection.graph, market_features + np.array([0.05, 0, 0, 0]), steps=2)
    baseline = classical_baseline(market_features)
    quantum_status = "ok"
    quantum_comparison = {}
    quantum_started = time.perf_counter()
    try:
        quantum = quantum_score(neural)
        quantum_seconds = time.perf_counter() - quantum_started
        finite_shot = quantum_score(neural, shots=1000)
        classical_coordinator_started = time.perf_counter()
        classical_coordinator = classical_baseline(neural)
        classical_coordinator_seconds = time.perf_counter() - classical_coordinator_started
        heldout_features = causal_features(closes, int(len(closes) * 0.8))
        heldout_neural = graph_score(selection.graph, heldout_features, steps=2)
        heldout_started = time.perf_counter()
        heldout_quantum = quantum_score(heldout_neural)
        heldout_quantum_seconds = time.perf_counter() - heldout_started
        heldout_classical_started = time.perf_counter()
        heldout_classical = classical_baseline(heldout_neural)
        heldout_classical_seconds = time.perf_counter() - heldout_classical_started
        quantum_comparison = {
            "input_boundary": "same four-value connectome signal for each paired coordinator",
            "analytic": {
                "quantum": quantum.tolist(),
                "classical": classical_coordinator.tolist(),
                "l1_distance": float(np.abs(quantum - classical_coordinator).sum()),
                "quantum_seconds": quantum_seconds,
                "classical_seconds": classical_coordinator_seconds,
            },
            "finite_shot": {"shots": 1000, "quantum": finite_shot.tolist()},
            "heldout": {
                "as_of_close_index": int(len(closes) * 0.8),
                "same_input_boundary": True,
                "quantum": heldout_quantum.tolist(),
                "classical": heldout_classical.tolist(),
                "l1_distance": float(np.abs(heldout_quantum - heldout_classical).sum()),
                "quantum_seconds": heldout_quantum_seconds,
                "classical_seconds": heldout_classical_seconds,
            },
        }
    except RuntimeError as exc:
        quantum = None
        quantum_status = {"state": "unavailable", "error": str(exc)}
    backtest = run_backtest(selection, closes, costs=0.001)
    if quantum is None:
        heldout_quantum = None
    current, peak = tracemalloc.get_traced_memory()
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "market": {"features": market_features.tolist(), **market_provenance, "history": history_provenance},
        "connectome": {
            "selection_rule": selection.selection_rule,
            "annotation_unique_body_ids": selection.annotated_rows,
            "selected_segments": selection.selected_rows,
            "source_weight_rows_scanned": selection.source_edges,
            "retained_edges": selection.retained_edges,
            "id_integrity": selection.id_integrity,
            "neurotransmitter_sign_counts": {
                "excitatory_assumption_positive": int((selection.neurotransmitter_signs > 0).sum()),
                "inhibitory_assumption_negative": int((selection.neurotransmitter_signs < 0).sum()),
                "unknown_or_unmapped_neutral": int((selection.neurotransmitter_signs == 0).sum()),
            },
            "weight_semantics": "normalized anatomy-derived contact counts; transmitter signs are model assumptions",
        },
        "outputs": {
            "classical_baseline": baseline.tolist(),
            "connectome_signal": neural.tolist(),
            "connectome_zero_input": zero_graph_input.tolist(),
            "connectome_perturbed_input": perturbed_graph_input.tolist(),
            "graph_input_sensitivity_l1": float(np.abs(neural - perturbed_graph_input).sum()),
            "graph_nonzero_edge_fraction": float(np.count_nonzero(selection.graph.weight) / len(selection.graph.weight)),
            "pennylane_4_qubit_analytic": quantum.tolist() if quantum is not None else quantum_status,
            "heldout_pennylane_4_qubit_analytic": heldout_quantum.tolist() if heldout_quantum is not None else quantum_status,
            "quantum_classical_comparison": quantum_comparison if quantum is not None else quantum_status,
        },
        "backtest": backtest,
        "resources": {
            "wall_seconds": round(time.perf_counter() - started, 3),
            "python_tracemalloc_peak_bytes": peak,
            "python_tracemalloc_current_bytes": current,
        },
        "limitations": [
            "bounded annotated segment subgraph, not whole-brain coverage",
            "S&P 500 index is a smoke-test market proxy, not investment validation",
            "transmitter sign mapping and graph dynamics are explicit assumptions",
            "untrained baseline pipeline, no quantum advantage or profitability claim",
        ],
    }
    if quantum is None:
        result["limitations"].append("PennyLane analytic/held-out outputs are unavailable when the optional quantum extra is not installed")
    out = ROOT / "outputs" / "local-research-run.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
