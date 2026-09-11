"""Run matched fixed-task measurements for candidate and independent baseline models."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import math
import time
import urllib.error
import urllib.request
import uuid

from quantum_fly.connectome import _process_working_set_bytes


TASKS = (
    ("ready", "Reply with exactly READY and nothing else.", "READY"),
    ("four", "What is two plus two? Reply with exactly FOUR and nothing else.", "FOUR"),
    ("blue", "Reply with exactly BLUE and nothing else.", "BLUE"),
)


def call(url: str, model: str, task_id: str, prompt: str, expected: str, timeout: float) -> dict:
    request_id = f"quantum-fly-baseline-{uuid.uuid4().hex}"
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 64, "temperature": 0}
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Request-ID": request_id},
        method="POST",
    )
    result = {"task_id": task_id, "request_id": request_id, "model": model, "request": body, "resource": {"before": _process_working_set_bytes()}}
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
            content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content"))
            result.update({
                "status": "ok",
                "http_status": response.status,
                "served_model": payload.get("model"),
                "quality": {"expected": expected, "observed": content, "exact_expected": content == expected},
                "usage": payload.get("usage", {}),
                "response": payload,
            })
    except urllib.error.HTTPError as exc:
        result.update({"status": "error", "http_status": exc.code, "error_type": "HTTPError", "error": exc.read().decode("utf-8", "replace")[:1500]})
    except Exception as exc:
        result.update({"status": "error", "error_type": type(exc).__name__, "error": str(exc)[:500]})
    result["latency_seconds"] = round(time.perf_counter() - started, 3)
    result["resource"]["after"] = _process_working_set_bytes()
    return result


def summary(calls: list[dict]) -> dict:
    successful = [item for item in calls if item.get("status") == "ok"]
    quality = [1.0 if item.get("quality", {}).get("exact_expected") else 0.0 for item in successful]
    latencies = [float(item["latency_seconds"]) for item in successful]
    costs = [float(item.get("usage", {}).get("cost", 0) or 0) for item in successful]

    def mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 6) if values else None

    def ci(values: list[float]) -> list[float] | None:
        if not values:
            return None
        avg = sum(values) / len(values)
        if len(values) == 1:
            margin = 0.0
        else:
            variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
            margin = 1.96 * math.sqrt(variance / len(values))
        return [round(avg - margin, 6), round(avg + margin, 6)]

    return {
        "n_total": len(calls),
        "n_success": len(successful),
        "quality_rate": mean(quality),
        "latency_mean_seconds": mean(latencies),
        "cost_mean": mean(costs),
        "uncertainty": {"quality_rate_approx_95ci": ci(quality), "latency_approx_95ci": ci(latencies), "cost_approx_95ci": ci(costs)},
    }


def main() -> int:
    endpoint = "http://127.0.0.1:4011/v1/chat/completions"
    timeout = 30.0
    models = {"candidate": "minimax/minimax-m3", "baseline": "gpt-6-astra"}
    started = time.perf_counter()
    arms = {
        arm: [call(endpoint, model, task_id, prompt, expected, timeout) for task_id, prompt, expected in TASKS]
        for arm, model in models.items()
    }
    candidate = summary(arms["candidate"])
    baseline = summary(arms["baseline"])
    complete = candidate["n_success"] == len(TASKS) and baseline["n_success"] == len(TASKS)
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "task_count_per_arm": len(TASKS),
        "models": models,
        "arms": arms,
        "comparison": {"status": "complete" if complete else "incomplete_provider_evidence", "candidate": candidate, "baseline": baseline},
        "wall_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "three fixed tasks are a bounded smoke comparison, not a general quality benchmark",
            "no advantage is claimed; incomplete provider arms make quality/cost comparison invalid",
            "approximate intervals are descriptive and do not replace preregistration or independent evaluation",
        ],
    }
    output = Path("outputs/model-quality-cost-baseline.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["comparison"]["status"], "candidate": candidate, "baseline": baseline, "wall_seconds": result["wall_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
