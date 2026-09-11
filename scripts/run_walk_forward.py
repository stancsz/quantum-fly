"""Run seeded rolling structure comparisons over an official FRED history."""

from pathlib import Path
import argparse
import json

from quantum_fly.backtest import run_walk_forward_comparison
from quantum_fly.connectome import load_bounded_connectome
from quantum_fly.market import load_history


ROOT = Path(__file__).resolve().parents[1]
LONG_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2022-01-01&coed=2025-12-31"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-nodes", type=int, default=4096)
    parser.add_argument("--max-source-edges", type=int, default=10_000_000)
    parser.add_argument("--train-size", type=int, default=252)
    parser.add_argument("--validation-size", type=int, default=126)
    parser.add_argument("--test-size", type=int, default=126)
    parser.add_argument("--step-size", type=int, default=126)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--output", default="outputs/walk-forward-comparison.json")
    args = parser.parse_args()
    raw = ROOT / "data" / "malecns-v1.0" / "raw"
    cache = ROOT / "data" / "market" / "sp500-2022-2025.csv"
    closes, market = load_history(cache, LONG_URL)
    selection = load_bounded_connectome(raw, args.max_nodes, args.max_source_edges)
    result = run_walk_forward_comparison(
        selection,
        closes,
        train_size=args.train_size,
        validation_size=args.validation_size,
        test_size=args.test_size,
        step_size=args.step_size,
        seeds=tuple(args.seeds),
    )
    result["market"] = market
    result["connectome"] = {
        "selection_rule": selection.selection_rule,
        "selected_segments": selection.selected_rows,
        "source_weight_rows_scanned": selection.source_edges,
        "retained_edges": selection.retained_edges,
        "id_integrity": selection.id_integrity,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

