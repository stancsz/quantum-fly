"""Verify the public research-boundary document and a real assessment path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BOUNDARY = ROOT / "docs" / "RESEARCH_BOUNDARY.md"
REQUIRED = (
    "reproducible research prototype",
    "operationally reliable software",
    "investment advice",
    "production readiness",
    "quantum advantage",
)


def main() -> int:
    if not BOUNDARY.exists():
        print(f"missing canonical boundary document: {BOUNDARY}", file=sys.stderr)
        return 1
    text = BOUNDARY.read_text(encoding="utf-8").lower()
    missing = [phrase for phrase in REQUIRED if phrase not in text]
    if missing:
        print(f"boundary document missing claims: {missing}", file=sys.stderr)
        return 1
    trace = ROOT / ".mochu" / "wip" / "boundary-verifier-trace.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "scripts.fly_chat", "当前评估是什么，缺少什么证据？", "--trace", str(trace)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0 or "limitations" not in result.stdout.lower():
        print(result.stdout[-1500:], file=sys.stderr)
        print(result.stderr[-1500:], file=sys.stderr)
        return result.returncode or 1
    print("research boundary and structured assessment path: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
