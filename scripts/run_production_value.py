"""Run the preregistered historical research-value gate and write a receipt."""

from pathlib import Path
import argparse
import csv
import hashlib
from urllib.parse import parse_qs, urlparse
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantum_fly.backtest import run_walk_forward_comparison
from quantum_fly.connectome import load_bounded_connectome
from quantum_fly.market import CacheProvenanceError, load_history
from scripts.production_value import build_receipt, sha256_file


def _legacy_header_history(cache: Path, url: str) -> tuple[np.ndarray, dict]:
    """Validate the existing FRED cache while accepting DATE aliases."""
    metadata_path = cache.with_name(cache.name + ".meta.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    raw = cache.read_bytes()
    if metadata.get("url") != url:
        raise ValueError("replay cache URL does not match protocol data_url")
    query = parse_qs(urlparse(url).query)
    expected_range = {"start": (query.get("cosd") or [None])[0], "end": (query.get("coed") or [None])[0]}
    if metadata.get("requested_date_range") != expected_range:
        raise ValueError("replay cache date range does not match protocol data_url")
    digest = hashlib.sha256(raw).hexdigest()
    if metadata.get("sha256") != digest:
        raise ValueError("replay cache sidecar SHA256 does not match bytes")
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    date_column = "DATE" if rows and "DATE" in rows[0] else "observation_date" if rows and "observation_date" in rows[0] else None
    if date_column is None or not rows or "SP500" not in rows[0]:
        raise ValueError("replay cache must contain DATE or observation_date and SP500")
    closes = np.asarray([float(row["SP500"]) for row in rows if row.get("SP500") not in ("", ".")], dtype=float)
    if len(closes) < 30 or not np.all(np.isfinite(closes)):
        raise ValueError("replay cache does not provide enough finite closes")
    dates = [row.get(date_column, "") for row in rows if row.get("SP500") not in ("", ".")]
    return closes, {
        **metadata,
        "cache_path": str(cache),
        "metadata_path": str(metadata_path),
        "rows_raw": len(rows),
        "rows_valid_close": len(closes),
        "first_date": dates[0],
        "last_date": dates[-1],
        "date_column": date_column,
        "legacy_header_compatibility": date_column == "observation_date",
        "symbol": "S&P 500 index proxy for stock/ETF research smoke test",
    }


def load_replay_history(cache: Path, url: str) -> tuple[np.ndarray, dict]:
    try:
        return load_history(cache, url)
    except CacheProvenanceError as exc:
        if "missing required columns DATE and SP500" not in str(exc):
            raise
        return _legacy_header_history(cache, url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "--protocol", dest="config", default="configs/production_value_v1.json")
    parser.add_argument("--mode", choices=("replay",), default="replay")
    parser.add_argument("--output", default="outputs/production-value-v1.json")
    parser.add_argument("--max-nodes", type=int, default=4096)
    parser.add_argument("--max-source-edges", type=int, default=10_000_000)
    args = parser.parse_args()
    config_path = (ROOT / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    data_path = (ROOT / config["data_path"]).resolve()
    closes, market = load_replay_history(data_path, config["data_url"])
    raw = ROOT / "data" / "malecns-v1.0" / "raw"
    selection = load_bounded_connectome(raw, args.max_nodes, args.max_source_edges)
    comparisons = []
    for multiplier in config["cost_multipliers"]:
        cost = float(config["base_cost"]) * float(multiplier)
        comparison = run_walk_forward_comparison(
            selection,
            closes,
            train_size=int(config["train_size"]),
            validation_size=int(config["validation_size"]),
            test_size=int(config["test_size"]),
            step_size=int(config["step_size"]),
            costs=cost,
            seeds=tuple(int(seed) for seed in config["seeds"]),
        )
        comparisons.append(comparison)
    code_paths = [ROOT / "quantum_fly" / "backtest.py", ROOT / "scripts" / "production_value.py", config_path]
    receipt = build_receipt(
        config,
        config_path,
        {**market, "path": str(data_path), "sha256": sha256_file(data_path)},
        {"files": {str(path.relative_to(ROOT)): sha256_file(path) for path in code_paths}},
        comparisons,
    )
    receipt["provenance"]["connectome"] = {
        "selection_rule": selection.selection_rule,
        "selected_segments": selection.selected_rows,
        "source_weight_rows_scanned": selection.source_edges,
        "retained_edges": selection.retained_edges,
        "id_integrity": selection.id_integrity,
    }
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "decision": receipt["decision"], "paired_comparison": receipt["paired_comparison"], "cost_sensitivity": receipt["cost_sensitivity"]}, indent=2))


if __name__ == "__main__":
    main()
