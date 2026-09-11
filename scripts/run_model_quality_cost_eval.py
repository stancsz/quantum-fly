"""Run a bounded repeated live model measurement without claiming superiority."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import time
import urllib.error
import urllib.request
import uuid

from quantum_fly.connectome import _process_working_set_bytes


def one_call(url: str, model: str, timeout: float, expected: str) -> dict:
    request_id = f"quantum-fly-quality-{uuid.uuid4().hex}"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly READY and nothing else."}],
        "max_tokens": 64,
        "temperature": 0,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Request-ID": request_id},
        method="POST",
    )
    result = {
        "request_id": request_id,
        "model": model,
        "request": body,
        "resource": {"process_working_set_before_bytes": _process_working_set_bytes()},
    }
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            payload = json.loads(raw)
            content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content"))
            result.update(
                {
                    "status": "ok",
                    "http_status": response.status,
                    "served_model": payload.get("model"),
                    "response": payload,
                    "quality": {"expected": expected, "observed": content, "exact_expected": content == expected},
                    "usage": payload.get("usage", {}),
                }
            )
    except urllib.error.HTTPError as exc:
        result.update({"status": "error", "http_status": exc.code, "error_type": "HTTPError", "error": exc.read().decode("utf-8", "replace")[:2000]})
    except Exception as exc:
        result.update({"status": "error", "error_type": type(exc).__name__, "error": str(exc)[:500]})
    result["latency_seconds"] = round(time.perf_counter() - started, 3)
    result["resource"]["process_working_set_after_bytes"] = _process_working_set_bytes()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4011/v1/chat/completions")
    parser.add_argument("--model", default="minimax/minimax-m3")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output", default="outputs/model-quality-cost-eval.json")
    args = parser.parse_args()
    if args.attempts < 1 or args.attempts > 5:
        parser.error("--attempts must be between 1 and 5")
    started = time.perf_counter()
    attempts = [one_call(args.base_url, args.model, args.timeout, "READY") for _ in range(args.attempts)]
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.base_url,
        "model": args.model,
        "attempt_count": args.attempts,
        "timeout_seconds": args.timeout,
        "attempts": attempts,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "bounded fixed-prompt smoke measurement, not a model-quality benchmark",
            "no independent baseline or uncertainty estimate, so no quality or cost advantage claim",
            "provider availability and routing can vary outside this receipt",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "statuses": [item.get("status") for item in attempts], "wall_seconds": result["wall_seconds"]}, indent=2))
    return 0 if all(item.get("status") == "ok" for item in attempts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
