"""Stream-validate the complete downloaded MaleCNS weight table."""

from pathlib import Path
import argparse
import json

from quantum_fly.connectome import scan_full_connectome


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=str(ROOT / "data" / "malecns-v1.0" / "raw"))
    parser.add_argument("--output", default="outputs/full-connectome-scan.json")
    args = parser.parse_args()
    receipt = scan_full_connectome(Path(args.raw_dir))
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()

