"""Verify a production-value receipt without changing its decision."""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.production_value import verify_receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", nargs="?", default="outputs/production-value-v1.json")
    parser.add_argument("--require-go", action="store_true")
    args = parser.parse_args()
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    result = verify_receipt(receipt)
    print(json.dumps(result, indent=2))
    if not result["valid"] or (args.require_go and result["decision"] != "GO"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
