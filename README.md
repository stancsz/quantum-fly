# Quantum Fly

### Can a fruit fly brain map help us build more robust portfolio experiments?

[简体中文](README.zh-CN.md) · [Research hypotheses](docs/HYPOTHESES.md) · [Experiment plan](docs/EXPERIMENT_PLAN.md) · [Current goal](GOAL.md)

Quantum Fly is a research prototype designed for open, reproducible experimentation. It combines three unusual ingredients:

- the published male fruit fly connectome as structural inspiration
- causal, offline portfolio experiments with explicit classical baselines
- small quantum simulations used as testable scoring and stability components

The aim is not to make a magical trading bot. It is to ask a sharper question: **when markets, parameters, and samples change, which decisions survive the perturbation?**

If that question interests you, fork the project, replace one component, run the same controls, and share what breaks. Negative results are welcome.

> [!IMPORTANT]
> This is an experimental research prototype, not investment advice. It does not claim quantum advantage, biological fidelity, profitability, whole-brain execution, or production readiness.

## Why this project is worth exploring

Most portfolio models begin with a familiar architecture and optimize performance. Quantum Fly begins with robustness and falsifiability.

It uses the fruit fly connectome as a sparse structural prior, then asks whether that structure adds anything beyond simpler alternatives. Every interesting result must compete with classical baselines, no-graph variants, randomized topology, matched-degree controls, multiple seeds, causal time splits, and transaction costs.

The phrase **quantum stability** is a project hypothesis, not an established scientific capability. Here it means the measured sensitivity of a portfolio decision to market perturbations, model-parameter noise, and sampling variation under a declared evaluation protocol.

## What works today

The repository contains a reproducible, offline Python research skeleton with:

- bounded MaleCNS connectome scans and subgraph experiments
- finite market-feature encoding and sparse recurrent graph state
- transparent classical baselines and a no-graph ablation
- causal historical evaluation and walk-forward tooling
- an optional 4-qubit PennyLane scoring path
- single-Fly, three-member, and coordinator structure comparisons
- persistent, typed local Fly messages and research receipts
- request-correlated LeanRouter smoke probes with explicit failure reporting

The default fixtures are synthetic. The current real-data path uses a bounded subset of the official MaleCNS release plus cached FRED 2024 S&P 500 index inputs. A successful run is evidence for that bounded experiment only.

## Quick start

Requirements: Python 3.10 or newer, plus the official MaleCNS files described in [the data receipt](docs/DATA_RECEIPT.md).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test,quantum]"
python -m scripts.quickstart --check
python -m scripts.quickstart
python -m pytest
```

The run writes a machine-readable receipt to `outputs/local-research-run.json`. If PennyLane is not installed, the receipt marks quantum outputs unavailable and still records the classical and connectome results.

Other useful entry points:

```powershell
# Ask the local receipt-backed research interface what evidence is missing
python -m scripts.fly_chat "What is the current assessment, and what evidence is missing?"

# Compare single Fly, three-member mean, coordinator state, and no-graph controls
python -m scripts.run_structure_comparison --max-nodes 4096 --max-source-edges 10000000 --seeds 0 1 2

# Run the bounded multi-Fly message and state loop
python -m scripts.run_fly_loop
```

## How it fits together

```text
market features
      |
      v
connectome-inspired sparse state ----> classical controls
      |                                      |
      v                                      |
optional quantum scoring                     |
      |                                      |
      +--------------> portfolio signal <----+
                              |
                              v
                 causal offline evaluation
                 plus costs and perturbations
```

The exact coupling between connectome structure and quantum simulation is a research question. It is not assumed to be useful in advance.

## Fork it and try a falsifiable idea

A useful fork changes one thing and preserves the controls. Good starting experiments include:

1. Replace the connectome topology with a degree-matched random graph.
2. Swap the quantum scorer for a parameter-matched classical model.
3. Test fewer Fly modules against the three-member coordinator.
4. Add another causal market feature without changing the evaluation window.
5. Reproduce a negative result on different hardware or a different seed set.

When you publish a result, include the command, configuration, random seeds, data provenance, runtime, resource use, and failed runs. Open an issue with your receipt or propose a small pull request. The best contribution may be the experiment that proves an exciting idea does not work.

The project software is available under the [MIT License](LICENSE). Before redistributing research results or data, also review [the open collaboration boundary](docs/OPEN_COLLABORATION.md); the MaleCNS data retains its separate CC BY attribution requirements.

## Research rules

- Anatomical connections are not executable neural dynamics. State, weights, updates, inputs, objectives, and readout must be specified separately.
- Backtests must use time-correct splits and report costs, leakage checks, seeds, and failures.
- A local test, smoke call, or research receipt is not proof of operational reliability.
- No result should be presented as investment advice or evidence of stable profitability.
- Simulated quantum components do not establish quantum speedup or advantage.

## Project map

- [GOAL.md](GOAL.md): verified capability, open gaps, acceptance conditions, and hard boundaries
- [Hypotheses](docs/HYPOTHESES.md): claims designed to be tested and rejected
- [Experiment plan](docs/EXPERIMENT_PLAN.md): baselines, ablations, and evaluation protocol
- [Architecture](docs/ARCHITECTURE.md): multi-Fly and coordinator design
- [Agent protocol](docs/AGENT_PROTOCOL.md): bounded communication between components
- [Data receipt](docs/DATA_RECEIPT.md): MaleCNS source, schema, checksums, and scale
- [Research boundary](docs/RESEARCH_BOUNDARY.md): what the evidence does and does not establish
- [Open collaboration](docs/OPEN_COLLABORATION.md): public research and private-work boundaries

## Data and attribution

The project uses the official [Janelia MaleCNS v1.0 download](https://male-cns.janelia.org/download/). The upstream page identifies the data as CC BY. Raw data stays under the gitignored `data/malecns-v1.0/raw/` directory. See [DATA_RECEIPT.md](docs/DATA_RECEIPT.md) for expected files and validation details.

Quantum Fly is early, strange, and deliberately testable. **Fork the question, not the conclusion.**
