"""Execute the documented bounded research quickstart and validate its receipt."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RECEIPT = ROOT / "outputs" / "local-research-run.json"


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.quickstart"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        print(completed.stdout[-2000:])
        print(completed.stderr[-2000:], file=sys.stderr)
        return completed.returncode or 1
    if not RECEIPT.exists():
        print(f"missing receipt: {RECEIPT}", file=sys.stderr)
        return 1
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    connectome = receipt.get("connectome", {})
    resources = receipt.get("resources", {})
    limitations = receipt.get("limitations", [])
    required = {
        "created_utc": receipt.get("created_utc"),
        "selected_segments": connectome.get("selected_segments"),
        "retained_edges": connectome.get("retained_edges"),
        "id_integrity": connectome.get("id_integrity"),
        "backtest": receipt.get("backtest"),
        "wall_seconds": resources.get("wall_seconds"),
        "limitations": limitations,
    }
    if not required["created_utc"] or required["selected_segments"] <= 0 or required["retained_edges"] < 0:
        print(json.dumps(required, indent=2), file=sys.stderr)
        return 1
    if not required["id_integrity"] or not required["backtest"] or not required["limitations"]:
        print(json.dumps(required, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "receipt": str(RECEIPT), "summary": required}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
