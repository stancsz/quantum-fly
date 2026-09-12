import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import numpy as np

from quantum_fly.agent import MAX_PAYLOAD_BYTES, DurableTaskRuntime, FlyCoordinator, QueueFullError
from quantum_fly.fixture import synthetic_graph
from quantum_fly.loop import CommunicatingFlyLoop


def test_message_correlation_and_durable_trace(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    result = coordinator.handle("当前评估是什么？")
    assert result["type"] == "task_result"
    assert result["correlation_id"]
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["correlation_id"] == json.loads(lines[0])["message_id"]
    payload = result["payload"]
    assert payload["observed"]["as_of_time"] is not None or "as_of_time" in payload["observed"]
    assert result["as_of_time"] == payload["observed"]["as_of_time"]
    assert payload["interpretation"]
    assert payload["hypothesis"]
    assert payload["limitations"]


def test_assessment_without_local_receipt_is_structured(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    result = FlyCoordinator(tmp_path / "trace.jsonl").handle("What is the current assessment?")
    payload = result["payload"]
    assert payload["state"] == "failed"
    assert payload["observed"] == {"receipt_available": False, "as_of_time": None}
    assert payload["missing_evidence"] == ["outputs/local-research-run.json"]
    assert payload["limitations"]
    assert "quickstart" in payload["proposed_next_action"]


def test_allowlisted_research_preserves_evidence(tmp_path):
    result = FlyCoordinator(tmp_path / "trace.jsonl").handle("请研究官方 connectome source")
    assert result["type"] in {"task_result", "error"}
    if result["type"] == "task_result":
        assert result["evidence_refs"]


def test_router_failure_is_explicit(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl", "http://127.0.0.1:1/unavailable")
    result = coordinator.router_advice("reply READY", timeout=0.2)
    assert result["status"] == "unavailable"
    assert result["model"] == "minimax/minimax-m3"
    assert result["request_id"].startswith("req-")
    assert result["latency_seconds"] >= 0
    assert "process_working_set_before_bytes" in result["resource"]


def test_duplicate_and_cancel_are_typed(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    message = coordinator.envelope("status", "a", "b", {})
    coordinator.append(message)
    assert coordinator.append(message)["duplicate"] is True
    cancelled = coordinator.cancel(message["message_id"])
    assert cancelled["payload"]["state"] == "cancelled"


def test_durable_queue_replays_and_enforces_its_bound(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    runtime = DurableTaskRuntime(coordinator.trace_path, coordinator.append, max_queue_size=1)
    request = coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": 1}})
    runtime.enqueue(request)
    assert runtime.replay_pending() == [request["message_id"]]
    restarted = DurableTaskRuntime(coordinator.trace_path, coordinator.append, max_queue_size=1)
    assert restarted.replay_pending() == [request["message_id"]]
    with pytest.raises(QueueFullError):
        restarted.enqueue(coordinator.envelope("research_request", "fly:b", "executor:allowlisted-http", {"budget": {"max_seconds": 1}}))


def test_specific_task_run_does_not_consume_an_older_replay(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    runtime = DurableTaskRuntime(coordinator.trace_path, coordinator.append)
    older = coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": 1}})
    current = coordinator.envelope("research_request", "fly:b", "executor:allowlisted-http", {"budget": {"max_seconds": 1}})
    runtime.enqueue(older)
    runtime.enqueue(current)
    result = runtime.run_task(current["message_id"], lambda _request, _context: {"value": "current"}, coordinator.envelope)
    assert result["payload"]["observed"] == {"value": "current"}
    assert runtime.replay_pending() == [older["message_id"]]


def test_runtime_records_timeout_for_an_inflight_cooperative_executor(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    runtime = DurableTaskRuntime(coordinator.trace_path, coordinator.append)
    request = coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": 0.03}})
    runtime.enqueue(request)

    def slow_executor(_request, context):
        while True:
            time.sleep(0.005)
            context.raise_if_stopped()

    result = runtime.run_next(slow_executor, coordinator.envelope)
    assert result is not None
    assert result["type"] == "error"
    assert result["payload"]["state"] == "timed_out"


def test_pending_runtime_cancel_is_persisted_and_not_executed(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    runtime = DurableTaskRuntime(coordinator.trace_path, coordinator.append)
    request = coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": 1}})
    runtime.enqueue(request)
    result = runtime.cancel(request["message_id"], coordinator.envelope)
    assert result["payload"]["state"] == "cancelled"
    assert runtime.run_next(lambda *_: {"unexpected": True}, coordinator.envelope) is None


@pytest.mark.parametrize("max_seconds", [0, -1, 301, float("nan"), float("inf"), True, "slow"])
def test_runtime_rejects_unbounded_or_nonfinite_task_budgets(tmp_path, max_seconds):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    with pytest.raises(ValueError):
        coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": max_seconds}})


def test_protocol_payload_and_queue_constructor_are_bounded(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    with pytest.raises(ValueError):
        coordinator.envelope("status", "a", "b", {"blob": "x" * MAX_PAYLOAD_BYTES})
    with pytest.raises(ValueError):
        DurableTaskRuntime(coordinator.trace_path, coordinator.append, max_queue_size=0)
    with pytest.raises(ValueError):
        DurableTaskRuntime(coordinator.trace_path, coordinator.append, max_queue_size=1025)


def test_concurrent_runtime_workers_write_a_replayable_trace(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "trace.jsonl")
    runtime = DurableTaskRuntime(coordinator.trace_path, coordinator.append, max_queue_size=4)
    requests = [
        coordinator.envelope("research_request", "fly:a", "executor:allowlisted-http", {"budget": {"max_seconds": 1}})
        for _ in range(4)
    ]
    for request in requests:
        runtime.enqueue(request)

    def execute(request, _context):
        time.sleep(0.01)
        return {"task_id": request["message_id"]}

    with ThreadPoolExecutor(max_workers=4) as workers:
        results = [future.result() for future in as_completed([workers.submit(runtime.run_next, execute, coordinator.envelope) for _ in requests])]
    assert {result["payload"]["observed"]["task_id"] for result in results} == {request["message_id"] for request in requests}
    assert runtime.replay_pending() == []
    lines = [json.loads(line) for line in coordinator.trace_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 12
    assert all(isinstance(line["message_id"], str) for line in lines)


def test_persisted_nonfinite_fly_state_is_rejected(tmp_path):
    trace = tmp_path / "messages.jsonl"
    state = tmp_path / "fly-state.json"
    coordinator = FlyCoordinator(trace)
    loop = CommunicatingFlyLoop(synthetic_graph(), state, coordinator)
    loop.step(np.array([0.2, -0.4, 0.6, -0.1]))
    state.write_text(state.read_text(encoding="utf-8").replace("0.0", "NaN", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="strict JSON"):
        CommunicatingFlyLoop(synthetic_graph(), state, FlyCoordinator(trace))


def test_communicating_loop_persists_independent_members_and_restarts(tmp_path):
    trace = tmp_path / "messages.jsonl"
    state = tmp_path / "fly-state.json"
    coordinator = FlyCoordinator(trace)
    loop = CommunicatingFlyLoop(synthetic_graph(), state, coordinator)
    first = loop.step(np.array([0.2, -0.4, 0.6, -0.1]), "2024-01-02T00:00:00Z")
    assert first["payload"]["observed"]["member_signals"]
    assert first["payload"]["interpretation"]
    assert first["evidence_refs"] == ["quantum_fly/fixture.py"]
    assert len(json.loads(state.read_text(encoding="utf-8")).get("history")) == 1
    before = loop.agents["trend-fly"].state.copy()
    restarted = CommunicatingFlyLoop(synthetic_graph(), state, FlyCoordinator(trace))
    assert restarted.step_index == 1
    np.testing.assert_allclose(restarted.agents["trend-fly"].state, before)
    second = restarted.step(np.array([0.1, -0.2, 0.3, -0.05]), "2024-01-03T00:00:00Z")
    assert second["payload"]["step"] == 2
    lines = trace.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8  # three member reports and one result per step
    assert {json.loads(line)["sender"] for line in lines[:4]} >= {"trend-fly", "mean-reversion-fly", "risk-fly", "coordinator:local"}


def test_fly_to_fly_relay_is_bounded_and_cannot_carry_commands(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "messages.jsonl")
    loop = CommunicatingFlyLoop(synthetic_graph(), tmp_path / "state.json", coordinator)
    message = loop.relay_peer_signal("trend-fly", "risk-fly", 0.75, ["fixture:evidence"])
    assert message["recipient"] == "risk-fly"
    assert message["payload"] == {"state": "peer_signal", "signal": 0.5, "step": 0}
    assert message["evidence_refs"] == ["fixture:evidence"]
    with pytest.raises(ValueError):
        loop.relay_peer_signal("trend-fly", "risk-fly", 0.1, ["x" * 257])
    with pytest.raises(ValueError):
        loop.relay_peer_signal("trend-fly", "risk-fly", 0.1, ["command:delete-all"] * 5)


def test_human_to_fly_question_is_scoped_and_persisted(tmp_path):
    coordinator = FlyCoordinator(tmp_path / "messages.jsonl")
    loop = CommunicatingFlyLoop(synthetic_graph(), tmp_path / "state.json", coordinator)
    message = loop.receive_human_question("当前信号缺少什么证据？", "trend-fly")
    assert message["sender"] == "human:local"
    assert message["recipient"] == "trend-fly"
    assert message["payload"]["scope"] == "research-only"
    with pytest.raises(ValueError):
        loop.receive_human_question("x" * 2001, "trend-fly")
