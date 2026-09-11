"""Record a bounded, read-only LeanRouter compatibility probe."""

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import time
import urllib.error
import urllib.request

from quantum_fly.connectome import _process_working_set_bytes


def probe(url: str, model: str, timeout: float, request_id: str) -> dict:
    body = {"model": model, "messages": [{"role": "user", "content": "Reply with exactly READY"}], "max_tokens": 8, "temperature": 0}
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Request-ID": request_id},
        method="POST",
    )
    started = time.perf_counter()
    result = {"request_id": request_id, "model": model, "request": body}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result.update({"status": response.status, "response": response.read().decode("utf-8", "replace")[:2000]})
    except urllib.error.HTTPError as exc:
        result.update({"status": exc.code, "error_type": "HTTPError", "error": exc.read().decode("utf-8", "replace")[:2000]})
    except Exception as exc:
        result.update({"status": "error", "error_type": type(exc).__name__, "error": str(exc)[:500]})
    result["latency_seconds"] = round(time.perf_counter() - started, 3)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output", default="outputs/leanrouter-goal-probe.json")
    args = parser.parse_args()
    started = time.perf_counter()
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "models_url": args.base_url + "/v1/models",
        "chat_url": args.base_url + "/v1/chat/completions",
        "timeout_seconds": args.timeout,
        "python_pid": os.getpid(),
        "process_working_set_before_bytes": _process_working_set_bytes(),
        "probes": [],
    }
    for model in ("gpt-6-astra", "minimax/minimax-m3", "openrouter/minimax/minimax-m3"):
        result["probes"].append(probe(result["chat_url"], model, args.timeout, "quantum-fly-goal-" + model.replace("/", "-")))
    result["wall_seconds"] = round(time.perf_counter() - started, 3)
    result["process_working_set_after_bytes"] = _process_working_set_bytes()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
