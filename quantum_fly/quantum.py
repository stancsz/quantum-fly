"""Optional PennyLane scorer.

This module is intentionally replaceable. PennyLane is not required for the
classical fixture or its tests.
"""

import numpy as np


def quantum_score(features: np.ndarray, layers: int = 1, shots: int | None = None) -> np.ndarray:
    """Return analytic Z expectations for a four-qubit shallow circuit.

    The initial design is four qubits and one or two layers on CPU
    ``default.qubit``. This is a research component, not evidence of quantum
    advantage. Finite shots are accepted for future perturbation tests.
    """
    if len(features) != 4:
        raise ValueError("the initial quantum fixture requires exactly 4 features")
    if layers not in (1, 2):
        raise ValueError("layers must be 1 or 2")
    if shots is not None and shots < 1:
        raise ValueError("shots must be positive")
    try:
        import pennylane as qml
    except ImportError as exc:
        raise RuntimeError("optional dependency missing: install PennyLane") from exc

    values = np.asarray(features, dtype=float)
    dev = qml.device("default.qubit", wires=4)

    @qml.qnode(dev, shots=shots)
    def circuit():
        for i, value in enumerate(values):
            qml.RY(float(np.clip(value, -1.0, 1.0)), wires=i)
        for _ in range(layers):
            for i in range(3):
                qml.CNOT(wires=[i, i + 1])
                qml.RZ(0.15, wires=i + 1)
        return [qml.expval(qml.PauliZ(i)) for i in range(4)]

    return np.asarray(circuit(), dtype=float)
