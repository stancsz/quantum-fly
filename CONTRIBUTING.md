# Contributing to Quantum Fly

Quantum Fly welcomes small, falsifiable experiments and fixes that make results easier to reproduce. A useful contribution can confirm a hypothesis, reject it, or expose a boundary that was previously unclear.

## Start with the fast path

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test,quantum]"
python -m scripts.demo
python -m pytest -q
```

Official-data experiments also require the MaleCNS files and manifest validation documented in [DATA_PREPARATION.md](docs/DATA_PREPARATION.md).

## What makes a strong contribution

- Change one research variable when practical.
- Keep chronological splits and transaction costs explicit.
- Compare against a transparent classical or no-graph control.
- Record configuration, seeds, input provenance, runtime, and failed runs.
- Preserve negative and inconclusive results.
- State what the evidence does not establish.

Do not include private strategies, credentials, brokerage details, proprietary datasets, or generated raw-data files. No contribution should claim investment suitability, stable profitability, quantum advantage, biological fidelity, or production readiness without a separately defined and verified evidence contract.

Use the issue templates for bugs, experiment results, and proposals. Keep pull requests narrow, explain the acceptance evidence, and run the relevant tests before submitting.

By contributing code, you agree that it may be distributed under the repository's [MIT License](LICENSE). MaleCNS and other external data retain their own licenses and attribution requirements.
