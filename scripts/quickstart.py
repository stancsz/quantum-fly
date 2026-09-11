"""Stranger-friendly entry point for the bounded Quantum Fly research run."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "malecns-v1.0" / "raw"
REQUIRED_RAW_FILES = (
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
    "body-neurotransmitters-male-cns-v1.0.feather",
)


def missing_prerequisites() -> list[str]:
    missing = [
        name
        for name in REQUIRED_RAW_FILES
        if not (RAW_DIR / name).exists()
    ]
    try:
        importlib.import_module("numpy")
        importlib.import_module("pyarrow")
    except ImportError as exc:
        missing.append(f"Python dependency: {exc.name}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bounded, receipt-producing Quantum Fly research smoke test."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check local prerequisites without running the research job",
    )
    args = parser.parse_args()
    missing = missing_prerequisites()
    if missing:
        print("Quickstart prerequisites are missing:")
        for item in missing:
            print(f"- {item}")
        print("See docs/DATA_RECEIPT.md for the official data source and expected files.")
        return 2
    if args.check:
        print("Quickstart prerequisites: OK")
        return 0

    from scripts.run_local_research import main as run_research

    run_research()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
