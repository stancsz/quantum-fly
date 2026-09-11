import numpy as np
import pytest
from importlib.util import find_spec

from quantum_fly.classical import classical_baseline, graph_score
from quantum_fly.fixture import synthetic_features, synthetic_graph
from quantum_fly.quantum import quantum_score


def test_quantum_score_shape_finite_and_deterministic():
    if find_spec("pennylane") is None:
        pytest.skip("PennyLane is an optional quantum extra")
    features = synthetic_features()
    first = quantum_score(features)
    second = quantum_score(features)
    assert first.shape == (4,)
    assert np.isfinite(first).all()
    np.testing.assert_allclose(first, second)


def test_synthetic_fixture_is_deterministic_and_graph_is_explicit():
    graph = synthetic_graph()
    features = synthetic_features()
    assert graph.n_nodes == 4
    np.testing.assert_allclose(graph_score(graph, features), graph_score(graph, features))


def test_classical_baseline_is_zero_sum_unit_l1():
    signal = classical_baseline(synthetic_features())
    assert np.isclose(signal.sum(), 0.0)
    assert np.isclose(np.abs(signal).sum(), 1.0)


def test_quantum_module_is_optional_and_has_explicit_boundary():
    if find_spec("pennylane") is None:
        with pytest.raises(RuntimeError):
            quantum_score(synthetic_features())
    else:
        result = quantum_score(synthetic_features())
        assert result.shape == (4,)
