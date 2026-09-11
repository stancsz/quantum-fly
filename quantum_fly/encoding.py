"""Market-feature encoding and output normalization."""

import numpy as np


def encode_features(features: np.ndarray, n_nodes: int) -> np.ndarray:
    """Map a finite feature vector to the first graph nodes, with zero padding."""
    features = np.asarray(features, dtype=float)
    if features.ndim != 1 or len(features) > n_nodes:
        raise ValueError("features must be a vector no longer than n_nodes")
    if not np.all(np.isfinite(features)):
        raise ValueError("features must be finite")
    state = np.zeros(n_nodes, dtype=float)
    state[: len(features)] = np.clip(features, -1.0, 1.0)
    return state


def portfolio_signal(readout: np.ndarray) -> np.ndarray:
    """Turn readout values into a zero-sum, unit-L1 research signal."""
    values = np.asarray(readout, dtype=float)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("readout must be a finite vector")
    centered = values - values.mean()
    scale = np.abs(centered).sum()
    return centered / scale if scale else np.zeros_like(centered)
