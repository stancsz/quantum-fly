"""Stranger-friendly entry point for the bounded Quantum Fly research run."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "malecns-v1.0" / "raw"
MANIFEST_PATH = ROOT / "configs" / "malecns-v1.0-manifest.json"
REQUIRED_RAW_FILES = (
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
    "body-neurotransmitters-male-cns-v1.0.feather",
)


def missing_prerequisites(
    raw_dir: Path = RAW_DIR,
    manifest_path: Path = MANIFEST_PATH,
) -> list[str]:
    missing: list[str] = []
    try:
        importlib.import_module("numpy")
        importlib.import_module("pyarrow")
    except ImportError as exc:
        missing.append(f"Python dependency: {exc.name}")
        return missing
    try:
        from quantum_fly.data_manifest import ManifestValidationError, validate_malecns

        validate_malecns(raw_dir, manifest_path)
    except ManifestValidationError as exc:
        missing.append(str(exc))
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
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR, help="MaleCNS raw-data directory to validate")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="MaleCNS manifest to validate")
    args = parser.parse_args()
    missing = missing_prerequisites(args.data_dir, args.manifest)
    if missing:
        print("Quickstart prerequisites are missing:")
        for item in missing:
            print(f"- {item}")
        print("See docs/DATA_RECEIPT.md and configs/malecns-v1.0-manifest.json for the official data source and validation contract.")
        return 2
    if args.check:
        print("Quickstart prerequisites: OK")
        return 0

    from scripts.run_local_research import main as run_research

    run_research()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
