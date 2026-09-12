# Quantum Fly production-value protocol v1

This protocol is the first bounded attempt to test whether the project creates useful investment-research lift. It is deliberately a historical replay and paper-decision experiment. It does not place orders, connect to a brokerage, or establish profitability.

## Three gates

1. **Research lift.** On the same chronological data, folds, seeds, and explicit transaction costs, compare the registered candidate (`three_coordinator`) with a transparent no-graph classical control (`no_graph_mean`). The receipt reports paired episode deltas, turnover, drawdown, and a deterministic block-bootstrap interval. The v1 implementation can decide only this gate.
2. **Shadow operational.** A future gate would run the frozen candidate and baseline in parallel on newly arriving data, record timestamps, missing-input behavior, latency, decision availability, and human override without sending orders. It is not implemented here.
3. **Forward paper value.** A future gate would preregister a later time window, preserve the frozen code/config, record paper decisions and realized outcomes with complete cost and slippage accounting, and compare against the same control. It is not implemented here.

## Registered research decision

The base-cost gate requires all of the following:

- at least 3 of 4 chronological folds have a positive paired candidate-minus-baseline cumulative PnL delta;
- at least 8 of 12 fold-seed episodes are positive;
- the lower bound of a 95% deterministic block bootstrap interval is greater than zero;
- the candidate's maximum drawdown deterioration is no more than 0.5 percentage points;
- candidate mean turnover is no more than 1.2 times the best registered control;
- every candidate episode must change position in at least 1% of scored periods and contain at least two distinct target positions, preventing a near-constant position from being counted as research lift;
- the conclusion does not reverse at 0.5x, 1x, and 2x the registered transaction cost.

The exact values are in `configs/production_value_v1.json` and are read into every receipt before execution. A failed check is a valid observed **NO-GO**, not a reason to tune the threshold after seeing results.

## Receipt integrity

`outputs/production-value-v1.json` is a self-contained evidence receipt. It must identify the schema, protocol, config hash, data hash and dates, code hashes, candidate and baseline names, every fold-seed-cost episode, finite metrics, costs, turnover, drawdown, paired comparison, limitations, and explicit decisions. The verifier rejects missing baseline or provenance, non-finite values, duplicate cases, cost/count mismatches, and incomplete metrics. An ignored output, dashboard screenshot, or model-generated summary is not a portable proof.

## Boundaries

Even a research GO would mean only that the preregistered historical replay met its research criteria. It would not mean profitable trading, production readiness, quantum advantage, biological fidelity, or cross-market generalization. The supplied S&P 500 series is an index proxy, not an execution feed. Shadow operational and forward paper-value gates remain open until separately implemented and observed.

Run the slice with:

```powershell
py -3 -X utf8 -m scripts.run_production_value --protocol configs/production_value_v1.json --mode replay --output outputs/production-value-v1.json
py -3 -X utf8 -m scripts.verify_production_value outputs/production-value-v1.json
```
