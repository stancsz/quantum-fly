"""Run a fast, dependency-light Quantum Fly synthetic demonstration."""

from __future__ import annotations

import json

import numpy as np

from quantum_fly.classical import classical_baseline, graph_score
from quantum_fly.fixture import synthetic_graph


def build_demo() -> dict:
    graph = synthetic_graph()
    features = np.asarray([0.02, -0.01, 0.03, 0.015], dtype=float)
    connectome_inspired = graph_score(graph, features, steps=2)
    no_graph = classical_baseline(features)
    return {
        "scope": "synthetic fixture demonstration",
        "question": "Does sparse recurrent structure change the same four-value input?",
        "input": features.tolist(),
        "connectome_inspired_output": connectome_inspired.tolist(),
        "no_graph_output": no_graph.tolist(),
        "l1_difference": float(np.abs(connectome_inspired - no_graph).sum()),
        "next_step": "Run the official-data quickstart and registered controls before making a research claim.",
        "limitations": [
            "synthetic graph, not MaleCNS evidence",
            "demonstrates code behavior, not investment value",
            "does not establish quantum advantage or biological fidelity",
        ],
    }


def main() -> int:
    print(json.dumps(build_demo(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
