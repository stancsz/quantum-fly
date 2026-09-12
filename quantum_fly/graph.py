"""Explicit sparse graph boundary.

The graph is a structural fixture, not a biological connectome and not a
complete executable neural model.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SparseGraph:
    """Directed weighted graph in a small, explicit edge-list form."""

    n_nodes: int
    pre: np.ndarray
    post: np.ndarray
    weight: np.ndarray

    def __post_init__(self) -> None:
        if isinstance(self.n_nodes, bool) or not isinstance(self.n_nodes, (int, np.integer)) or self.n_nodes < 1:
            raise ValueError("n_nodes must be positive")
        arrays = (self.pre, self.post, self.weight)
        if not (len(self.pre) == len(self.post) == len(self.weight)):
            raise ValueError("edge arrays must have equal length")
        if np.any(self.pre < 0) or np.any(self.post < 0):
            raise ValueError("edge indices must be non-negative")
        if np.any(self.pre >= self.n_nodes) or np.any(self.post >= self.n_nodes):
            raise ValueError("edge index outside graph")
        if any(np.asarray(a).ndim != 1 for a in arrays):
            raise ValueError("edge arrays must be one-dimensional")
        if not np.isfinite(np.asarray(self.weight, dtype=float)).all():
            raise ValueError("edge weights must be finite")

    def step(self, state: np.ndarray, gain: float = 1.0) -> np.ndarray:
        """Apply one linear sparse message-passing step."""
        state = np.asarray(state, dtype=float)
        if state.shape != (self.n_nodes,):
            raise ValueError("state shape must equal (n_nodes,)")
        if not np.isfinite(state).all() or not np.isfinite(gain):
            raise ValueError("state and gain must be finite")
        result = np.zeros_like(state)
        np.add.at(result, self.post, gain * self.weight * state[self.pre])
        return np.tanh(result)

    def readout(self, state: np.ndarray, indices: np.ndarray) -> np.ndarray:
        """Return selected nodes as an explicit output boundary."""
        state = np.asarray(state, dtype=float)
        indices = np.asarray(indices, dtype=int)
        if state.shape != (self.n_nodes,):
            raise ValueError("state shape must equal (n_nodes,)")
        if not np.isfinite(state).all():
            raise ValueError("state must be finite")
        if np.any(indices < 0) or np.any(indices >= self.n_nodes):
            raise ValueError("readout index outside graph")
        return state[indices].copy()
