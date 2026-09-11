"""Run a local bounded Fly conversation."""

from pathlib import Path
import argparse
import json
import sys

from quantum_fly.agent import FlyCoordinator


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="当前评估是什么，缺少什么证据，下一步建议做什么？")
    parser.add_argument("--trace", default="outputs/fly-conversation.jsonl")
    args = parser.parse_args()
    result = FlyCoordinator(Path(args.trace)).handle(args.prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
