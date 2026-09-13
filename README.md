# 🪰 We Gave a Fruit Fly Brain Four Qubits and Sent It to Wall Street.

## Then we built it a mecha and made it fight the most boring baseline.

![A connectome-powered mecha fruit fly raises an energy shield against a quantum market experiment](assets/quantum-fly-mecha-shield-hero-v4.png)

**A real fruit-fly connectome. An optional 4-qubit scoring path. One brutally ordinary portfolio control.**

```text
FRUIT-FLY CONNECTOME → 4-QUBIT SCORE → PORTFOLIO SIGNAL
                                            ⚔
                                    NO-GRAPH CONTROL
```

> **Weird brain. Boring controls. No magical returns.**

[Run the experiment](#see-it-in-30-seconds) · [See the evidence](docs/VERIFICATION_2026-09-12.md) · [简体中文](README.zh-CN.md)

This is a reproducible attempt to find out whether biological network structure leaves any useful signal after causal splits, transaction costs, perturbations, and simpler controls have tried to kill it.

> [!IMPORTANT]
> Research prototype only. No live trading, investment advice, profitability claim, biological-fidelity claim, or quantum-advantage claim.

[![MIT License](https://img.shields.io/badge/license-MIT-2ea44f)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)](pyproject.toml) [![Research prototype](https://img.shields.io/badge/status-research%20prototype-6f42c1)](docs/RESEARCH_BOUNDARY.md)

## Verified bounded run

The current evidence snapshot records **45+ local tests**, **4,096 selected MaleCNS segments**, and **160,053 retained sparse edges**. A preregistered historical comparison passed its bounded research gate, but that result is not forward performance or investment evidence. See the [criterion-level verification record](docs/VERIFICATION_2026-09-12.md) for commands, denominators, limitations, and separate GO/NO-GO decisions.

## See it in 30 seconds

This synthetic demo needs no external research data:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m scripts.demo
```

It prints the same four-value input through a tiny sparse recurrent fixture and a no-graph control. The output is a code-path demonstration, not MaleCNS or market evidence.

## Why this project is worth exploring

Most portfolio models begin with a familiar architecture and optimize performance. Quantum Fly begins with robustness and falsifiability.

It uses the fruit fly connectome as a sparse structural prior, then asks whether that structure adds anything beyond simpler alternatives. Every interesting result must compete with classical baselines, no-graph variants, randomized topology, matched-degree controls, multiple seeds, causal time splits, and transaction costs.

The phrase **quantum stability** is a project hypothesis, not an established scientific capability. Here it means the measured sensitivity of a portfolio decision to market perturbations, model-parameter noise, and sampling variation under a declared evaluation protocol.

## What works today

The repository contains a reproducible Python research skeleton that runs offline after its inputs are prepared, with:

- bounded MaleCNS connectome scans and subgraph experiments
- finite market-feature encoding and sparse recurrent graph state
- transparent classical baselines and a no-graph ablation
- causal historical evaluation and walk-forward tooling
- an optional 4-qubit PennyLane scoring path
- single-Fly, three-member, and coordinator structure comparisons
- persistent, typed local Fly messages and research receipts
- request-correlated LeanRouter smoke probes with explicit failure reporting

The default fixtures are synthetic. The current real-data path uses a bounded subset of the official MaleCNS release plus cached FRED 2024 S&P 500 index inputs. A successful run is evidence for that bounded experiment only.

## Reproduce the official-data path

Requirements: Python 3.10 or newer and roughly 1.1 GB for the three bounded MaleCNS input tables. The optional PennyLane path requires Python 3.11 or newer. The first preparation step downloads official data; the first research run also downloads its declared FRED market input. Later validated runs can operate from those caches.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test,quantum]"
python -m scripts.prepare_malecns --download
python -m scripts.quickstart --check
python -m scripts.quickstart
python -m pytest -q
```

Read [data preparation](docs/DATA_PREPARATION.md) before downloading. The run writes a machine-readable receipt to `outputs/local-research-run.json`. Generated receipts are intentionally ignored by Git, so copy the exact receipt somewhere durable when sharing a result. If PennyLane is not installed, the receipt marks quantum outputs unavailable and still records the classical and connectome results.

Other useful entry points:

```powershell
# Ask the local receipt-backed research interface what evidence is missing
python -m scripts.fly_chat "What is the current assessment, and what evidence is missing?"

# Compare single Fly, three-member mean, coordinator state, and no-graph controls
python -m scripts.run_structure_comparison --max-nodes 4096 --max-source-edges 10000000 --seeds 0 1 2

# Run the bounded multi-Fly message and state loop with explicit inputs
python -m scripts.run_fly_loop `
  --features 0.1 -0.2 0.3 -0.05 `
  --as-of 2024-01-02T00:00:00Z
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

Start with a degree-matched random graph or no-graph control. Include the command, configuration, random seeds, data provenance, runtime, resource use, and failed runs, then open a research-result issue or propose a small pull request. The best contribution may be the experiment that proves an exciting idea does not work. See [CONTRIBUTING.md](CONTRIBUTING.md).

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
- [Marketing and launch review](docs/MARKETING_REVIEW.md): audience, proof funnel, launch experiments, and measurement rules

## Data and attribution

The project uses the official [Janelia MaleCNS v1.0 download](https://male-cns.janelia.org/download/). The upstream page identifies the data as CC BY. Raw data stays under the gitignored `data/malecns-v1.0/raw/` directory. See [DATA_RECEIPT.md](docs/DATA_RECEIPT.md) for expected files and validation details.

Quantum Fly is early, strange, and deliberately testable. **Fork the question, not the conclusion.**
