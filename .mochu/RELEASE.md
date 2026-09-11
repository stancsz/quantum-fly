# Release finish line

- [x] R1 A stranger with the documented data and Python prerequisites can run the bounded research quickstart and receive a valid receipt; verifier: `docs-quickstart`
- [x] R2 The verifier corpus runs all registered checks and fails on missing or malformed receipts; verifier: `corpus-health`, with receipt validators in `docs-quickstart` and `research-scope`
- [x] R3 Public copy distinguishes the reproducible research prototype from operational reliability, investment efficacy, and production readiness; verifier: `research-scope`
- [x] R4 No release claim implies live brokerage, automatic trading, clinical use, quantum advantage, or profitability; verifier: `research-scope`
- [ ] R5 Long-term operational reliability is demonstrated across sustained runs, restart/recovery, bounded failure rates, and observable health evidence; verifier: `operational-reliability`
- [ ] R6 Model quality and cost advantages are demonstrated against predeclared baselines with repeated evaluation, latency, usage, and cost receipts; verifier: `model-quality-cost`
- [ ] R7 Universal tool execution is not claimed until a scoped, permissioned tool suite is demonstrated end to end across supported tool classes, including failures and revocation; verifier: `tool-execution-coverage`
- [ ] R8 Whole-brain materialization is demonstrated only with an executable full-connectome representation, measured resource envelope, and reproducible load/restart evidence; verifier: `whole-brain-materialization`
- [ ] R9 Quantum advantage is demonstrated only by a preregistered comparison against matched classical baselines with independent quality, runtime, and resource evidence; verifier: `quantum-advantage`
- [ ] R10 Profitability and investment efficacy are demonstrated only by an approved, leakage-controlled, multi-period and multi-asset evaluation with costs, risk, uncertainty, and out-of-sample evidence; verifier: `investment-efficacy`
- [ ] R11 Production readiness is demonstrated only after the relevant reliability, security, deployment, rollback, operations, quality, cost, and support gates are independently green; verifier: `production-readiness`

## Current verification

R1-R4 are green in the local verifier corpus; the model-quality WIP M1 measurement surface is green. M2 is currently blocked because the independent baseline produced one HTTP 503, so R5-R11 remain unverified until their claim-specific milestones pass. The bundled ship gate still reports that `.mochu/VERIFIER_BASELINE` cannot be created because this repository has no authorized initial Git commit; this is a repository handoff limitation, not evidence of product readiness.
