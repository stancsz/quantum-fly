# North Star verification, 2026-09-12

## Assessment

The active `GOAL.md` contract has 11 acceptance criteria. All eleven have current code, focused tests, and observed local evidence. Completion is therefore **11/11 (100%)**, above the requested threshold.

The Steward authorized an MIT software license and an evidence-baseline commit on 2026-09-12. The implementation and verifier sources are recorded in commit `ecef5619c0e6e16913d4f4e36f08a9fdf8cfb3e3`; `.mochu/VERIFIER_BASELINE` resolves to that exact commit.

## Criterion mapping

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `position_pnl` and `position_turnover`; entry, hold, reversal, exit, recorded cost/PnL, and frozen readout regression tests. |
| 2 | PASS | FRED content plus sidecar bind exact URL/range, SHA256, first download and validation times; five offline provenance/header tests pass. |
| 3 | PASS | `configs/malecns-v1.0-manifest.json`, validation/import command, and exact local validation of all three official files. |
| 4 | PASS | A disposable Python environment installed the editable project and exact dependency snapshot, ran 44 tests, and completed the bounded research path using isolated cache/receipt files. |
| 5 | PASS | Commit `ecef5619c0e6e16913d4f4e36f08a9fdf8cfb3e3` contains the current source, tests, docs, and isolated verifiers. `.mochu/VERIFIER_BASELINE` resolves to it; focused verification preserves canonical receipt hashes and cleans temporary paths and normal locks. |
| 6 | PASS | `requirements-lock.txt`, Python/platform policy, CI workflow, editable install, compile/import, PennyLane 0.45.1 import, full suite, and explicit missing-data exit 2 were observed. |
| 7 | PASS | Registered candidate/no-graph replay covers four chronological folds, three seeds, 0.5x/1x/2x costs, paired deltas and deterministic 95% block-bootstrap interval. Receipt verifier returned valid `GO` for the bounded research gate only. |
| 8 | PASS | Runtime enforces finite timeout, queue, payload/state bounds and thread-safe append/dedupe; concurrent tests pass. Cooperative timeout limitations remain visible. |
| 9 | PASS | Connectome, graph, JSON, and persisted state reject invalid schema, excessive input, and non-finite values with focused tests. |
| 10 | PASS | MIT `LICENSE`, package metadata, CLI entry points, install/platform guidance, dependency policy, and security boundary are present. MaleCNS data remains separately attributed under CC BY. |
| 11 | PASS | This fresh mapping records criterion evidence and separate capability-layer decisions without collapsing them into one readiness claim. |

## Observed commands and receipts

- `.venv\\Scripts\\python.exe -m pytest -q`: 45 passed in 3.79 seconds after all implementation files settled.
- Disposable CPython 3.14 environment: editable install succeeded with NumPy 2.5.3, PyArrow 25.0.1, PennyLane 0.45.1, and pytest 9.1.1; its full suite passed 43 tests at that snapshot.
- Explicit empty data directory: module and installed `quantum-fly` entry point both returned exit 2 with a precise missing-directory error.
- Clean-interpreter bounded run: exit 0, 4,096 selected segments, 160,053 retained edges, isolated FRED SHA256 `a06c3c2b315402729b47579da2726b363a3fee2f25611eaa89321ead952bb5e9`, 63.226 seconds.
- `.venv\\Scripts\\python.exe -m scripts.run_production_value --output outputs/production-value-v1.json` followed by verifier: valid `GO`; 4/4 positive folds, 12/12 positive fold-seed units, base-cost bootstrap lower bound `0.004048163805431809`. This is historical research evidence, not forward or investment proof.
- `python scripts/ship_gate.py`: FAIL. Isolated quickstart initially exposed legacy FRED cache provenance, and the provider-dependent matched model baseline was incomplete. Verifier isolation was subsequently implemented, but the changed verifier set cannot become the accepted baseline without a commit.
- Isolated quickstart verifier: exit 0; canonical `outputs/local-research-run.json` SHA256 remained `0F1701ACA449A736B5B49C1E94ABF10E3A9F593D052B7556E4B999A6DB487EBD` before and after; no `.mochu/LOCK` remained.
- Isolated research-boundary verifier: exit 0; its prior trace hash remained unchanged and its temporary directory was removed. No `.mochu/LOCK` remained after the focused verifier. Four verifier sources still differ from the commit named by `.mochu/VERIFIER_BASELINE`, so the baseline is not accepted-current.

## Capability-layer decisions

- Local research: **GO**, bounded to the declared data, controls, resources, and historical protocol.
- Public reproducibility: **GO** for sharing the identified Git snapshot under MIT with separately attributed MaleCNS inputs and the documented reconstruction process. No push or public publication was performed.
- Unattended runtime: **NO-GO**, because tested local concurrency and cooperative timeouts do not prove long-running external executor termination or recovery.
- Investment claims: **NO-GO**. Historical research lift is not forward performance, suitability, profitability, or advice.
- Production use: **NO-GO**. No operational SLO, deployment, monitoring, rollback, security review, or live-service evidence exists.
