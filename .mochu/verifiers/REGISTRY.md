# Verifier registry

| id | dimension | claim, one sentence | single run command | iter-N |
|---|---|---|---|---|
| docs-quickstart | docs | The documented bounded research quickstart executes and produces a substantive receipt. | `python .mochu/verifiers/docs-quickstart/verify_quickstart.py` | iter-1 |
| research-scope | trust | The canonical boundary document and structured assessment path preserve research-only limitations. | `python .mochu/verifiers/research-scope/verify_boundary.py` | iter-2 |
| corpus-health | reliability-errors | The registered verifier commands execute successfully as a corpus. | `python .mochu/verifiers/corpus-health/verify_registry.py` | iter-3 |
| model-quality-cost-surface | performance | A bounded repeated live model measurement records quality, latency, usage, cost, errors, and limitations. | `python .mochu/verifiers/model-quality-cost-surface/verify_surface.py` | iter-4 |
| model-quality-cost-baseline | performance | Matched candidate and independent baseline calls produce quality, latency, cost, and uncertainty metrics. | `python .mochu/verifiers/model-quality-cost-baseline/verify_baseline.py` | iter-5 |
