"""Run one bounded, persistent local Fly loop step over supplied features."""

from pathlib import Path
import argparse
import json

import numpy as np

from quantum_fly.agent import FlyCoordinator
from quantum_fly.fixture import synthetic_graph
from quantum_fly.loop import CommunicatingFlyLoop


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", nargs="+", type=float, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--state", default="outputs/fly-loop-state.json")
    parser.add_argument("--trace", default="outputs/fly-loop.jsonl")
    args = parser.parse_args()
    coordinator = FlyCoordinator(Path(args.trace))
    loop = CommunicatingFlyLoop(synthetic_graph(), Path(args.state), coordinator)
    result = loop.step(np.asarray(args.features, dtype=float), args.as_of)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

