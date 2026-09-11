"""Verify a bounded repeated live model quality/cost measurement receipt."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RECEIPT = ROOT / "outputs" / "model-quality-cost-eval.json"


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.run_model_quality_cost_eval", "--attempts", "3"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if completed.returncode != 0:
        print(completed.stdout[-1500:], file=sys.stderr)
        print(completed.stderr[-1500:], file=sys.stderr)
        return completed.returncode or 1
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    attempts = receipt.get("attempts", [])
    if len(attempts) != 3:
        print("expected exactly three attempts", file=sys.stderr)
        return 1
    if not all(item.get("status") == "ok" for item in attempts):
        print("not all bounded model attempts succeeded", file=sys.stderr)
        return 1
    if not all(item.get("quality", {}).get("exact_expected") is True for item in attempts):
        print("fixed expected-answer quality check failed", file=sys.stderr)
        return 1
    if not all(item.get("latency_seconds", 0) > 0 for item in attempts):
        print("latency telemetry missing", file=sys.stderr)
        return 1
    if not all("usage" in item and "cost" in item["usage"] for item in attempts):
        print("usage/cost telemetry missing", file=sys.stderr)
        return 1
    if not receipt.get("limitations") or "advantage" not in " ".join(receipt["limitations"]).lower():
        print("measurement limitations missing", file=sys.stderr)
        return 1
    print("bounded model quality/cost measurement surface: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
