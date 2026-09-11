"""Classical baseline and graph-inspired scorer."""

import numpy as np
from .encoding import encode_features, portfolio_signal
from .graph import SparseGraph


def classical_baseline(features: np.ndarray) -> np.ndarray:
    """A transparent centered feature baseline."""
    return portfolio_signal(np.asarray(features, dtype=float))


def graph_score(graph: SparseGraph, features: np.ndarray, steps: int = 2) -> np.ndarray:
    """Run a tiny deterministic graph scorer over an explicit state boundary."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    state = encode_features(features, graph.n_nodes)
    for _ in range(steps):
        state = graph.step(state)
    return portfolio_signal(graph.readout(state, np.arange(len(features))))
