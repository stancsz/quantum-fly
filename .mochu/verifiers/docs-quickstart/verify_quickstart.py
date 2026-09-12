"""Execute the documented bounded research quickstart and validate its receipt."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
def main() -> int:
    with tempfile.TemporaryDirectory(prefix="quantum-fly-quickstart-") as temp:
        temp_path = Path(temp)
        receipt = temp_path / "local-research-run.json"
        env = {**os.environ, "QUANTUM_FLY_MARKET_CACHE": str(temp_path / "sp500-2024.csv"), "QUANTUM_FLY_LOCAL_RECEIPT": str(receipt)}
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.quickstart"], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=180,
        )
        if completed.returncode != 0:
            print(completed.stdout[-2000:])
            print(completed.stderr[-2000:], file=sys.stderr)
            return completed.returncode or 1
        if not receipt.exists():
            print(f"missing isolated receipt: {receipt}", file=sys.stderr)
            return 1
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    connectome = payload.get("connectome", {})
    resources = payload.get("resources", {})
    limitations = payload.get("limitations", [])
    required = {
        "created_utc": payload.get("created_utc"),
        "selected_segments": connectome.get("selected_segments"),
        "retained_edges": connectome.get("retained_edges"),
        "id_integrity": connectome.get("id_integrity"),
        "backtest": bool(payload.get("backtest")),
        "wall_seconds": resources.get("wall_seconds"),
        "limitations": limitations,
    }
    if not required["created_utc"] or required["selected_segments"] <= 0 or required["retained_edges"] < 0:
        print(json.dumps(required, indent=2), file=sys.stderr)
        return 1
    if not required["id_integrity"] or not required["backtest"] or not required["limitations"]:
        print(json.dumps(required, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "receipt_mode": "isolated-temporary", "summary": required}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
