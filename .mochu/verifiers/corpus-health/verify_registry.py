"""Execute every registered verifier except this registry-health verifier."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / ".mochu" / "verifiers" / "REGISTRY.md"


def entries() -> list[tuple[str, str]]:
    result = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) >= 4 and cells[0].lower() != "id" and cells[0]:
            result.append((cells[0], cells[3]))
    return result


def main() -> int:
    registered = entries()
    runnable = [(vid, command) for vid, command in registered if vid != "corpus-health"]
    if len(runnable) < 2:
        print("registry health requires at least two independent registered verifiers", file=sys.stderr)
        return 1
    for verifier_id, command in runnable:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        if completed.returncode != 0:
            print(f"[RED] {verifier_id}\n{completed.stdout[-1000:]}\n{completed.stderr[-1000:]}", file=sys.stderr)
            return 1
        print(f"[GREEN] {verifier_id}")
    print(f"registry health: {len(runnable)}/{len(runnable)} registered verifiers green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
