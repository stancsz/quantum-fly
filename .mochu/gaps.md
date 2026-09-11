# Gap register

Scoring formula: impact × confidence / effort. Scores are for selecting one independently verifiable iteration, not a promise of product readiness.

| id | dimension | gap | evidence: what was observed | impact | effort | confidence | score |
|---|---|---|---|---:|---:|---:|---:|
| multi_asset_evidence | features | Evaluation remains a single S&P 500 proxy rather than multi-asset evidence. | `outputs/walk-forward-comparison.json` explicitly records one index proxy. | 4 | 5 | 5 | 4.0 |
| long-term-reliability | reliability-errors | Long-term operational reliability is not established. | One bounded LeanRouter success coexists with timeout and provider failure receipts; no sustained-run, restart, uptime, or bounded failure-rate evidence. | 5 | 5 | 5 | 5.0 |
| model-quality-cost | performance | Model quality and cost advantages are not established. | Current receipts record latency and usage fields for bounded calls, but no repeated baseline quality or cost comparison exists. | 5 | 4 | 5 | 6.25 |
| tool-execution-coverage | features | Universal tool execution is not established. | Only one allowlisted read-only Janelia executor is verified; no universal or permissioned tool-class coverage exists. | 4 | 5 | 4 | 3.2 |
| whole-brain-materialization | performance | Whole-brain materialization is not established. | Full file streaming validation exists, but executable graph construction remains bounded to 4,096 selected segments. | 4 | 5 | 5 | 4.0 |
| quantum-advantage | features | Quantum advantage is not established. | Analytic and finite-shot PennyLane outputs are paired with classical outputs, with no advantage claim or preregistered superiority evidence. | 4 | 5 | 5 | 4.0 |
| investment-efficacy | features | Profitability and investment efficacy are not established. | Evaluation is a bounded S&P 500 proxy with mixed results, not approved multi-asset out-of-sample evidence. | 5 | 5 | 5 | 5.0 |
| production-readiness | trust | Production readiness is not established. | No complete deployment, rollback, security, support, uptime, quality, or cost gate is green. | 5 | 5 | 5 | 5.0 |

## Closed in iter-1

- `docs-quickstart`: `python .mochu/verifiers/docs-quickstart/verify_quickstart.py` executes `python -m scripts.quickstart`, checks the real bounded research receipt, and passes in the prepared local environment. The entry point reports missing data/dependency prerequisites instead of failing opaquely; clean-machine download and installation remain unclaimed.
- `research-scope`: `python .mochu/verifiers/research-scope/verify_boundary.py` checks the canonical boundary document and executes the structured human assessment CLI. It passes with explicit research-only limits and no investment or production claims.
- `reliability-receipts`: `python .mochu/verifiers/corpus-health/verify_registry.py` executes every other registered verifier and reports 2/2 green; the corpus therefore exercises the substantive receipt and boundary checks instead of only counting rows.
- `model-quality-cost-surface` M1: `python .mochu/verifiers/model-quality-cost-surface/verify_surface.py` executed three real default-model calls, all with exact expected output, latency, usage/cost fields, served model, request IDs, and resource snapshots. This is a measurement surface only; the R6 advantage claim remains open pending M2.
- `model-quality-cost-baseline` M2: `outputs/model-quality-cost-baseline.json` records candidate 3/3 success and advertised `gpt-6-astra` baseline 2/3 success with one HTTP 503. The matched comparison is invalid until the baseline is reliably available or a new baseline class is authorized.

## Parked / human judgment

- None yet. Investment efficacy and production-readiness claims remain out of scope until a Steward defines a separate goal.
