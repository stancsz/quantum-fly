"""Deterministic synthetic fixture, never a biological or market dataset."""

import numpy as np
from .graph import SparseGraph


def synthetic_graph() -> SparseGraph:
    """Return a tiny hand-built graph for integration tests only."""
    return SparseGraph(
        n_nodes=4,
        pre=np.array([0, 1, 2, 3, 0], dtype=int),
        post=np.array([1, 2, 3, 0, 2], dtype=int),
        weight=np.array([0.8, -0.4, 0.6, -0.3, 0.2], dtype=float),
    )


def synthetic_features() -> np.ndarray:
    """Return deterministic bounded inputs for offline integration only."""
    return np.array([0.2, -0.4, 0.6, -0.1], dtype=float)
