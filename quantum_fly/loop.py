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


MAX_HISTORY = 1024
MAX_STATE_BYTES = 16 * 1024 * 1024
MAX_STEP_INDEX = 10**12
MAX_MEMBER_NAME_CHARS = 64


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
        if isinstance(max_history, bool) or not isinstance(max_history, int) or not 1 <= max_history <= MAX_HISTORY:
            raise ValueError(f"max_history must be an integer between 1 and {MAX_HISTORY}")
        self.max_history = max_history
        self.members = tuple(members)
        if not self.members:
            raise ValueError("at least one Fly member is required")
        if len(self.members) > 16:
            raise ValueError("member count exceeds bounded local runtime limit")
        if any(not isinstance(m.name, str) or not m.name or len(m.name) > MAX_MEMBER_NAME_CHARS for m in self.members):
            raise ValueError("member names must be bounded non-empty strings")
        if len({m.name for m in self.members}) != len(self.members):
            raise ValueError("member names must be unique")
        if any(isinstance(m.feature_index, bool) or not isinstance(m.feature_index, int) or m.feature_index < 0 for m in self.members):
            raise ValueError("feature_index must be non-negative")
        self.agents = {spec.name: Agent.create(graph, spec.feature_index) for spec in self.members}
        self.history: list[dict] = []
        self.step_index = 0
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        if self.state_path.stat().st_size > MAX_STATE_BYTES:
            raise ValueError(f"persisted Fly state exceeds {MAX_STATE_BYTES} bytes")
        try:
            data = json.loads(
                self.state_path.read_text(encoding="utf-8"),
                parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON constant: {token}")),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("persisted Fly state is not strict JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("persisted Fly state must be an object")
        if data.get("version") != 1 or data.get("graph_nodes") != self.graph.n_nodes:
            raise ValueError("persisted Fly state is incompatible with this graph")
        saved = data.get("members", {})
        expected = {spec.name for spec in self.members}
        if not isinstance(saved, dict) or set(saved) != expected:
            raise ValueError("persisted Fly members do not match configured members")
        for spec in self.members:
            agent = self.agents[spec.name]
            record = saved[spec.name]
            if not isinstance(record, dict) or "state" not in record or "readout" not in record:
                raise ValueError("persisted Fly member record is malformed")
            try:
                agent.state = np.asarray(record["state"], dtype=float)
                agent.readout = np.asarray(record["readout"], dtype=float)
            except (TypeError, ValueError) as exc:
                raise ValueError("persisted Fly member record is not numeric") from exc
            if agent.state.shape != (self.graph.n_nodes,) or agent.readout.shape != (4,) or not np.isfinite(agent.state).all() or not np.isfinite(agent.readout).all():
                raise ValueError("persisted Fly state has an invalid shape")
        raw_step = data.get("step_index", 0)
        if isinstance(raw_step, bool) or not isinstance(raw_step, int) or not 0 <= raw_step <= MAX_STEP_INDEX:
            raise ValueError("persisted Fly step_index is outside its bound")
        raw_history = data.get("history", [])
        if not isinstance(raw_history, list) or len(raw_history) > MAX_HISTORY:
            raise ValueError("persisted Fly history is outside its bound")
        self.step_index = raw_step
        self.history = raw_history[-self.max_history :]

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
        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if len(serialized.encode("utf-8")) > MAX_STATE_BYTES:
            raise ValueError(f"Fly state exceeds {MAX_STATE_BYTES} bytes")
        temp.write_text(serialized + "\n", encoding="utf-8")
        temp.replace(self.state_path)

    def step(self, features: np.ndarray, as_of_time: str | None = None) -> dict:
        """Process one aligned feature vector and persist the resulting state."""
        values = np.asarray(features, dtype=float)
        if values.ndim != 1 or len(values) < 3 or not np.isfinite(values).all():
            raise ValueError("features must be a finite one-dimensional vector with at least 3 values")
        if any(spec.feature_index >= len(values) for spec in self.members):
            raise ValueError("member feature_index is outside the input vector")
        if self.step_index >= MAX_STEP_INDEX:
            raise ValueError("step_index reached its explicit bound")

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
