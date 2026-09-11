"""A small restartable multi-Fly communication loop.

This is an offline research runtime, not a broker or a general-purpose agent
framework.  Members share an immutable graph but keep independent dynamic
state and readouts.  Only bounded typed signals cross the member/coordinator
boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from .agent import FlyCoordinator
from .backtest import Agent, risk_clamp
from .graph import SparseGraph


@dataclass(frozen=True)
class MemberSpec:
    name: str
    feature_index: int


class CommunicatingFlyLoop:
    """Run bounded typed member messages and persist state after each step."""

    def __init__(
        self,
        graph: SparseGraph,
        state_path: Path,
        coordinator: FlyCoordinator,
        members: Iterable[MemberSpec] = (
            MemberSpec("trend-fly", 0),
            MemberSpec("mean-reversion-fly", 1),
            MemberSpec("risk-fly", 2),
        ),
        max_history: int = 128,
    ):
        self.graph = graph
        self.state_path = state_path
        self.coordinator = coordinator
        self.max_history = max_history
        self.members = tuple(members)
        if not self.members:
            raise ValueError("at least one Fly member is required")
        if len(self.members) > 16:
            raise ValueError("member count exceeds bounded local runtime limit")
        if any(m.feature_index < 0 for m in self.members):
            raise ValueError("feature_index must be non-negative")
        self.agents = {spec.name: Agent.create(graph, spec.feature_index) for spec in self.members}
        self.history: list[dict] = []
        self.step_index = 0
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or data.get("graph_nodes") != self.graph.n_nodes:
            raise ValueError("persisted Fly state is incompatible with this graph")
        saved = data.get("members", {})
        expected = {spec.name for spec in self.members}
        if set(saved) != expected:
            raise ValueError("persisted Fly members do not match configured members")
        for spec in self.members:
            agent = self.agents[spec.name]
            record = saved[spec.name]
            agent.state = np.asarray(record["state"], dtype=float)
            agent.readout = np.asarray(record["readout"], dtype=float)
            if agent.state.shape != (self.graph.n_nodes,) or agent.readout.shape != (4,):
                raise ValueError("persisted Fly state has an invalid shape")
        self.step_index = int(data.get("step_index", 0))
        self.history = list(data.get("history", []))[-self.max_history :]

    def _persist(self) -> None:
        data = {
            "version": 1,
            "graph_nodes": self.graph.n_nodes,
            "step_index": self.step_index,
            "members": {
                spec.name: {
                    "feature_index": spec.feature_index,
                    "state": self.agents[spec.name].state.tolist(),
                    "readout": self.agents[spec.name].readout.tolist(),
                }
                for spec in self.members
            },
            "history": self.history[-self.max_history :],
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(self.state_path)

    def step(self, features: np.ndarray, as_of_time: str | None = None) -> dict:
        """Process one aligned feature vector and persist the resulting state."""
        values = np.asarray(features, dtype=float)
        if values.ndim != 1 or len(values) < 3 or not np.isfinite(values).all():
            raise ValueError("features must be a finite one-dimensional vector with at least 3 values")
        if any(spec.feature_index >= len(values) for spec in self.members):
            raise ValueError("member feature_index is outside the input vector")

        self.step_index += 1
        member_messages: list[dict] = []
        signals: list[float] = []
        for spec in self.members:
            agent = self.agents[spec.name]
            signal = risk_clamp(agent.decide(values))
            signals.append(signal)
            message = self.coordinator.envelope(
                "status",
                spec.name,
                "coordinator:local",
                {
                    "state": "observed",
                    "signal": signal,
                    "feature_index": spec.feature_index,
                    "step": self.step_index,
                    "as_of_time": as_of_time,
                },
            )
            self.coordinator.append(message)
            member_messages.append(message)

        aggregate = risk_clamp(float(np.mean(signals)))
        result = self.coordinator.envelope(
            "task_result",
            "coordinator:local",
            "human:local",
            {
                "state": "result",
                "step": self.step_index,
                "observed": {"member_signals": signals, "aggregate_signal": aggregate},
                "interpretation": "bounded local coordinator mean over independent Fly signals",
                "hypothesis": "multi-member aggregation may or may not improve held-out quality",
                "limitations": ["offline research loop", "no trading action", "no biological fidelity claim"],
                "as_of_time": as_of_time,
            },
            member_messages[-1]["message_id"],
            ["quantum_fly/fixture.py"],
        )
        self.coordinator.append(result)
        self.history.append({"step": self.step_index, "signals": signals, "aggregate_signal": aggregate, "as_of_time": as_of_time})
        self._persist()
        return result

    def relay_peer_signal(
        self,
        sender: str,
        recipient: str,
        signal: float,
        evidence_refs: Iterable[str] = (),
    ) -> dict:
        """Send one bounded, typed signal directly from one configured Fly to another.

        The API intentionally exposes no arbitrary payload, command, URL fetch,
        credential, or permission field. Evidence references are labels only,
        and execution remains owned by the coordinator/executor boundary.
        """
        names = {spec.name for spec in self.members}
        if sender not in names or recipient not in names or sender == recipient:
            raise ValueError("peer signal requires two distinct configured members")
        if not np.isfinite(signal):
            raise ValueError("peer signal must be finite")
        refs = tuple(evidence_refs)
        if len(refs) > 4 or any(not isinstance(ref, str) or len(ref) > 256 for ref in refs):
            raise ValueError("peer evidence refs must contain at most four short strings")
        message = self.coordinator.envelope(
            "status",
            sender,
            recipient,
            {"state": "peer_signal", "signal": risk_clamp(float(signal)), "step": self.step_index},
            evidence_refs=list(refs),
        )
        self.coordinator.append(message)
        return message

    def receive_human_question(self, text: str, recipient: str = "trend-fly") -> dict:
        """Persist a bounded human question addressed to one configured Fly."""
        names = {spec.name for spec in self.members}
        if recipient not in names:
            raise ValueError("question recipient is not a configured Fly")
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("human question must be a non-empty string of at most 2000 characters")
        message = self.coordinator.envelope(
            "question",
            "human:local",
            recipient,
            {"text": text.strip(), "scope": "research-only"},
        )
        self.coordinator.append(message)
        return message
