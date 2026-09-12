"""Small durable, typed local Fly conversation coordinator.

The runtime is deliberately limited to pre-registered callables.  It is not a
shell, browser, or general agent-execution bridge.
"""

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import json
import math
import os
from pathlib import Path
import threading
import time
import uuid
import urllib.error
import urllib.request

from .connectome import _process_working_set_bytes
from .research import connectome_source_request


DEFAULT_ROUTER_MODEL = os.environ.get("QUANTUM_FLY_ROUTER_MODEL", "minimax/minimax-m3")

# These are deliberately small, explicit local-runtime limits.  They are
# safety/operability bounds, not a claim about the capacity of a deployment.
MIN_TASK_SECONDS = 0.001
MAX_TASK_SECONDS = 300.0
MIN_ROUTER_TIMEOUT_SECONDS = 0.01
MAX_ROUTER_TIMEOUT_SECONDS = 60.0
MAX_QUEUE_SIZE = 1024
MAX_PAYLOAD_BYTES = 64 * 1024
MAX_STATE_CHARS = 64
MAX_MESSAGE_ID_CHARS = 128
MAX_EVIDENCE_REFS = 16
MAX_EVIDENCE_REF_CHARS = 256


def _strict_json_bytes(value, *, label: str) -> bytes:
    """Serialize a protocol value without allowing NaN/Infinity or huge data."""
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be JSON-safe and finite") from exc
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"{label} exceeds {MAX_PAYLOAD_BYTES} bytes")
    return encoded


def _strict_json_loads(text: str):
    return json.loads(text, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON constant: {token}")))


def _bounded_seconds(value, *, label: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum} seconds")
    return result


def _validate_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    state = payload.get("state")
    if state is not None and (not isinstance(state, str) or not state or len(state) > MAX_STATE_CHARS):
        raise ValueError(f"state must be a non-empty string of at most {MAX_STATE_CHARS} characters")
    budget = payload.get("budget")
    if budget is not None:
        if not isinstance(budget, dict):
            raise ValueError("budget must be an object")
        if "max_seconds" in budget:
            _bounded_seconds(budget["max_seconds"], label="max_seconds", minimum=MIN_TASK_SECONDS, maximum=MAX_TASK_SECONDS)
    _strict_json_bytes(payload, label="payload")


def _validate_request(request: dict) -> None:
    if not isinstance(request, dict) or request.get("type") != "research_request":
        raise ValueError("runtime accepts only research_request envelopes")
    if not isinstance(request.get("message_id"), str) or not request["message_id"] or len(request["message_id"]) > MAX_MESSAGE_ID_CHARS:
        raise ValueError("message_id is missing or exceeds its bound")
    _validate_payload(request.get("payload"))
    budget = request["payload"].get("budget", {})
    if not isinstance(budget, dict):
        raise ValueError("budget must be an object")
    _bounded_seconds(budget.get("max_seconds", 15), label="max_seconds", minimum=MIN_TASK_SECONDS, maximum=MAX_TASK_SECONDS)


class QueueFullError(RuntimeError):
    """Raised before a request is persisted when its bounded queue is full."""


class TaskContext:
    """Cooperative cancellation context supplied to a registered executor."""

    def __init__(self, cancel_event: threading.Event, deadline_monotonic: float):
        self._cancel_event = cancel_event
        self._deadline_monotonic = deadline_monotonic

    def raise_if_stopped(self) -> None:
        if self._cancel_event.is_set():
            raise RuntimeError("cancelled")
        if time.monotonic() >= self._deadline_monotonic:
            self._cancel_event.set()
            raise TimeoutError("deadline exceeded")


class DurableTaskRuntime:
    """A small persisted FIFO for allowlisted, cooperative research requests.

    A timed-out thread is never reported as a successful result.  Python cannot
    safely kill a running thread, so cancellation is cooperative and executors
    must call ``TaskContext.raise_if_stopped`` at safe boundaries.
    """

    def __init__(self, trace_path: Path, append, max_queue_size: int = 8):
        if isinstance(max_queue_size, bool) or not isinstance(max_queue_size, int) or not 1 <= max_queue_size <= MAX_QUEUE_SIZE:
            raise ValueError(f"max_queue_size must be an integer between 1 and {MAX_QUEUE_SIZE}")
        self.trace_path = trace_path
        self._append = append
        self.max_queue_size = max_queue_size
        self.tasks: dict[str, dict] = {}
        self.queue: list[str] = []
        self._active: set[str] = set()
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        if not self.trace_path.exists():
            return
        for line in self.trace_path.read_text(encoding="utf-8").splitlines():
            try:
                message = _strict_json_loads(line)
                task_id = message.get("correlation_id")
                state = message.get("payload", {}).get("state")
                if message.get("type") == "research_request":
                    _validate_request(message)
                    task_id = message["message_id"]
                    if task_id in self.tasks:
                        continue
                    if len(self.queue) >= self.max_queue_size:
                        raise QueueFullError("persisted runtime queue exceeds configured bound")
                    self.tasks[task_id] = {"request": message, "state": "accepted"}
                    self.queue.append(task_id)
                elif task_id in self.tasks and state in {"running", "result", "failed", "cancelled", "timed_out"}:
                    self.tasks[task_id]["state"] = state
                    if state in {"result", "failed", "cancelled", "timed_out"} and task_id in self.queue:
                        self.queue.remove(task_id)
            except (ValueError, KeyError, TypeError, AttributeError):
                continue

    def enqueue(self, request: dict) -> dict:
        _validate_request(request)
        task_id = request["message_id"]
        with self._lock:
            if task_id in self.tasks:
                return {"type": "ack", "duplicate": True, "message_id": task_id}
            if len(self.queue) >= self.max_queue_size:
                raise QueueFullError(f"bounded queue full (max={self.max_queue_size})")
            self.tasks[task_id] = {"request": request, "state": "accepted"}
            self.queue.append(task_id)
        self._append(request)
        return request

    def cancel(self, task_id: str, envelope) -> dict:
        with self._lock:
            task = self.tasks.get(task_id)
            if task is None:
                return envelope("error", "coordinator:local", "human:local", {"state": "failed", "error": "unknown task"}, task_id)
            task["cancel_event"].set() if "cancel_event" in task else None
            task["state"] = "cancelled"
            if task_id in self.queue:
                self.queue.remove(task_id)
        result = envelope("task_result", "coordinator:local", "human:local", {"state": "cancelled", "correlation_id": task_id}, task_id)
        self._append(result)
        return result

    def replay_pending(self) -> list[str]:
        """Return accepted requests restored from the durable trace in FIFO order."""
        with self._lock:
            return list(self.queue)

    def run_next(self, executor, envelope) -> dict | None:
        with self._lock:
            while self.queue:
                task_id = self.queue.pop(0)
                task = self.tasks[task_id]
                if task["state"] == "cancelled" or task_id in self._active:
                    continue
                self._active.add(task_id)
                request = task["request"]
                max_seconds = _bounded_seconds(
                    request.get("payload", {}).get("budget", {}).get("max_seconds", 15),
                    label="max_seconds", minimum=MIN_TASK_SECONDS, maximum=MAX_TASK_SECONDS,
                )
                cancel_event = threading.Event()
                task["cancel_event"] = cancel_event
                task["state"] = "running"
                break
            else:
                return None

        self._append(envelope("status", "coordinator:local", "human:local", {"state": "running"}, task_id))
        context = TaskContext(cancel_event, time.monotonic() + max_seconds)
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(executor, request, context)
        try:
            try:
                observed = future.result(timeout=max_seconds)
                context.raise_if_stopped()
            except FutureTimeout:
                cancel_event.set()
                state = "timed_out"
                result = envelope("error", "executor:allowlisted-http", "human:local", {"state": state, "error": "executor exceeded max_seconds"}, task_id)
            except Exception as exc:
                state = "timed_out" if isinstance(exc, TimeoutError) else ("cancelled" if cancel_event.is_set() or str(exc) == "cancelled" else "failed")
                result = envelope("error", "executor:allowlisted-http", "human:local", {"state": state, "error": str(exc)[:240]}, task_id)
            else:
                with self._lock:
                    cancelled = cancel_event.is_set() or task["state"] == "cancelled"
                    state = "cancelled" if cancelled else "result"
                if state == "cancelled":
                    result = envelope("task_result", "coordinator:local", "human:local", {"state": state, "correlation_id": task_id}, task_id)
                else:
                    result = envelope("task_result", "executor:allowlisted-http", "human:local", {"state": state, "observed": observed}, task_id, [observed["url"]] if isinstance(observed, dict) and "url" in observed else [])
            with self._lock:
                task["state"] = state
            self._append(result)
            return result
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
            with self._lock:
                self._active.discard(task_id)

    def run_task(self, task_id: str, executor, envelope) -> dict | None:
        """Run a specific accepted task while preserving other replayable work."""
        with self._lock:
            if task_id not in self.tasks or task_id not in self.queue or task_id in self._active:
                return None
            self.queue.remove(task_id)
            self.queue.insert(0, task_id)
        return self.run_next(executor, envelope)


class FlyCoordinator:
    def __init__(self, trace_path: Path, router_url: str = "http://127.0.0.1:4000/v1/chat/completions"):
        self.trace_path = trace_path
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.router_url = router_url
        self.seen: set[str] = set()
        self._append_lock = threading.RLock()
        if self.trace_path.exists():
            for line in self.trace_path.read_text(encoding="utf-8").splitlines():
                try:
                    message = _strict_json_loads(line)
                    if isinstance(message, dict) and isinstance(message.get("message_id"), str):
                        self.seen.add(message["message_id"])
                except (ValueError, KeyError, TypeError):
                    continue
        self.runtime = DurableTaskRuntime(self.trace_path, self.append)

    def envelope(self, kind: str, sender: str, recipient: str, payload: dict, correlation_id: str | None = None, evidence_refs: list[str] | None = None) -> dict:
        if not all(isinstance(value, str) and value and len(value) <= MAX_STATE_CHARS for value in (kind, sender, recipient)):
            raise ValueError("kind, sender, and recipient must be bounded non-empty strings")
        _validate_payload(payload)
        if correlation_id is not None and (not isinstance(correlation_id, str) or len(correlation_id) > MAX_MESSAGE_ID_CHARS):
            raise ValueError("correlation_id exceeds its bound")
        refs = evidence_refs or []
        if not isinstance(refs, list) or len(refs) > MAX_EVIDENCE_REFS or any(
            not isinstance(ref, str) or not ref or len(ref) > MAX_EVIDENCE_REF_CHARS for ref in refs
        ):
            raise ValueError("evidence_refs exceed their explicit bounds")
        observed = payload.get("observed")
        as_of_time = payload.get("as_of_time")
        if as_of_time is None and isinstance(observed, dict):
            as_of_time = observed.get("as_of_time")
        return {
            "protocol_version": "fly/0.1",
            "type": kind,
            "message_id": f"msg-{uuid.uuid4().hex}",
            "correlation_id": correlation_id,
            "sender": sender,
            "recipient": recipient,
            "event_time": datetime.now(timezone.utc).isoformat(),
            "as_of_time": as_of_time,
            "payload": payload,
            "evidence_refs": refs,
        }

    def append(self, message: dict) -> dict:
        if not isinstance(message, dict) or not isinstance(message.get("message_id"), str) or not message["message_id"] or len(message["message_id"]) > MAX_MESSAGE_ID_CHARS:
            raise ValueError("message_id is missing or exceeds its bound")
        _validate_payload(message.get("payload"))
        _strict_json_bytes(message, label="message")
        with self._append_lock:
            if message["message_id"] in self.seen:
                return {"type": "ack", "duplicate": True, "message_id": message["message_id"]}
            self.seen.add(message["message_id"])
            with self.trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(message, ensure_ascii=False, allow_nan=False) + "\n")
        return message

    def _trace(self, message: dict) -> None:
        self.append(message)

    def router_advice(self, prompt: str, timeout: float = 8.0, model: str | None = None) -> dict:
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PAYLOAD_BYTES:
            raise ValueError("prompt must be a non-empty bounded string")
        timeout = _bounded_seconds(timeout, label="timeout", minimum=MIN_ROUTER_TIMEOUT_SECONDS, maximum=MAX_ROUTER_TIMEOUT_SECONDS)
        selected_model = model or DEFAULT_ROUTER_MODEL
        if not isinstance(selected_model, str) or not selected_model or len(selected_model) > MAX_STATE_CHARS:
            raise ValueError("model must be a bounded non-empty string")
        request_id = f"req-{uuid.uuid4().hex}"
        request_body = {"model": selected_model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 200, "temperature": 0}
        body = json.dumps(request_body).encode()
        request = urllib.request.Request(
            self.router_url,
            data=body,
            headers={"Content-Type": "application/json", "X-Request-ID": request_id},
            method="POST",
        )
        started = time.perf_counter()
        working_set_before = _process_working_set_bytes()
        result = {
            "model": selected_model,
            "request_id": request_id,
            "request": request_body,
            "url": self.router_url,
            "timeout_seconds": timeout,
            "resource": {"process_working_set_before_bytes": working_set_before},
        }
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", "replace")
                try:
                    response_body = json.loads(raw)
                except json.JSONDecodeError:
                    response_body = raw[:4000]
                result.update({"status": "ok", "http_status": response.status, "response": response_body})
        except urllib.error.HTTPError as exc:
            result.update({"status": "unavailable", "http_status": exc.code, "error_type": "HTTPError", "error": exc.read().decode("utf-8", "replace")[:1000]})
        except Exception as exc:
            result.update({"status": "unavailable", "error_type": type(exc).__name__, "error": str(exc)[:240]})
        result["latency_seconds"] = round(time.perf_counter() - started, 3)
        result["resource"]["process_working_set_after_bytes"] = _process_working_set_bytes()
        return result

    def handle(self, text: str) -> dict:
        request = self.envelope("question", "human:local", "coordinator:local", {"text": text})
        self._trace(request)
        lower = text.lower()
        if "research" in lower or "来源" in text or "source" in lower:
            task = self.envelope("research_request", "coordinator:local", "executor:allowlisted-http", {"task": "connectome_source", "budget": {"max_seconds": 15}} , request["message_id"])
            self.runtime.enqueue(task)
            reply = self.runtime.run_task(
                task["message_id"],
                lambda _request, context: self._run_connectome_source(context),
                self.envelope,
            )
            assert reply is not None
            return reply
        trace = Path("outputs/local-research-run.json")
        if trace.exists():
            data = json.loads(trace.read_text(encoding="utf-8"))
            payload = {
                "state": "result",
                "observed": {
                    "test_metrics": data.get("backtest", {}).get("metrics"),
                    "connectome": data.get("connectome"),
                    "as_of_time": data.get("market", {}).get("history", {}).get("last_date"),
                },
                "interpretation": "当前是有边界的离线 smoke/backtest",
                "hypothesis": "在扩大样本与匹配对照前，不能判断多 Fly、连接组结构或量子步骤是否有增量价值",
                "missing_evidence": data.get("limitations", []),
                "limitations": [
                    "receipt is offline research evidence, not investment advice",
                    "market input is a bounded proxy and the connectome is a bounded subgraph",
                    "model advisor output is not used to fill missing evidence",
                ],
                "proposed_next_action": "比较更简单基线与扩大样本前先保持当前边界",
            }
            refs = ["outputs/local-research-run.json"]
        else:
            payload = {"state": "failed", "error": "persisted research trace missing"}
            refs = []
        reply = self.envelope("task_result", "coordinator:local", "human:local", payload, request["message_id"], refs)
        self._trace(reply)
        return reply

    def cancel(self, correlation_id: str) -> dict:
        """Record an explicit cancellation request; no arbitrary process is killed."""
        if correlation_id in self.runtime.tasks:
            return self.runtime.cancel(correlation_id, self.envelope)
        control = self.envelope("feedback_control", "human:local", "coordinator:local", {"action": "cancel"}, correlation_id)
        self._trace(control)
        result = self.envelope("task_result", "coordinator:local", "human:local", {"state": "cancelled", "correlation_id": correlation_id}, correlation_id)
        self._trace(result)
        return result

    @staticmethod
    def _run_connectome_source(context: TaskContext) -> dict:
        context.raise_if_stopped()
        result = connectome_source_request(timeout=10.0)
        context.raise_if_stopped()
        return result
