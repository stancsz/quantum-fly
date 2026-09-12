"""Verify a matched candidate/baseline quality and cost comparison receipt."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
def main() -> int:
    with tempfile.TemporaryDirectory(prefix="quantum-fly-baseline-") as temp:
        receipt = Path(temp) / "model-quality-cost-baseline.json"
        env = {**os.environ, "QUANTUM_FLY_MODEL_BASELINE_RECEIPT": str(receipt)}
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.run_model_quality_cost_baseline"], cwd=ROOT, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240,
        )
        if completed.returncode != 0:
            print(completed.stdout[-1500:], file=sys.stderr)
            print(completed.stderr[-1500:], file=sys.stderr)
            return completed.returncode or 1
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    if payload.get("comparison", {}).get("status") != "complete":
        print("matched baseline comparison is incomplete", file=sys.stderr)
        return 1
    for arm in ("candidate", "baseline"):
        calls = payload.get("arms", {}).get(arm, [])
        if len(calls) != 3 or not all(call.get("status") == "ok" for call in calls):
            print(f"{arm} arm does not have three successful calls", file=sys.stderr)
            return 1
        if not all("quality" in call and "latency_seconds" in call and "usage" in call for call in calls):
            print(f"{arm} arm is missing matched metrics", file=sys.stderr)
            return 1
    for metric in ("quality_rate", "latency_mean_seconds", "cost_mean"):
        if metric not in payload["comparison"].get("candidate", {}) or metric not in payload["comparison"].get("baseline", {}):
            print(f"comparison metric missing: {metric}", file=sys.stderr)
            return 1
    if not payload["comparison"].get("uncertainty"):
        print("uncertainty summary missing", file=sys.stderr)
        return 1
    if not any("no advantage" in item.lower() for item in payload.get("limitations", [])):
        print("no-advantage limitation missing", file=sys.stderr)
        return 1
    print("matched model quality/cost baseline comparison: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
