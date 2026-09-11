"""Small causal paper backtest over the bounded connectome selection."""

from dataclasses import dataclass
import time
import tracemalloc
import numpy as np

from .connectome import ConnectomeSelection
from .encoding import portfolio_signal
from .graph import SparseGraph
from .market import causal_features


@dataclass
class Agent:
    graph: SparseGraph
    feature_index: int
    readout: np.ndarray
    state: np.ndarray

    @classmethod
    def create(cls, graph: SparseGraph, feature_index: int) -> "Agent":
        seed_readout = np.array([0.25, -0.15, 0.1, 0.05], dtype=float)
        seed_readout = np.roll(seed_readout, feature_index)
        return cls(graph, feature_index, seed_readout, np.zeros(graph.n_nodes))

    def decide(self, features: np.ndarray, use_graph: bool = True) -> float:
        encoded = np.zeros(self.graph.n_nodes)
        encoded[self.feature_index] = features[self.feature_index]
        self.state = self.graph.step(self.state + encoded) if use_graph else encoded
        raw = (
            np.array([self.state.mean(), self.state.std(), self.state.max(), self.state.min()])
            if use_graph
            else encoded[:4]
        )
        return float(np.dot(self.readout, raw))

    def update(self, reward: float, signal: float, learning_rate: float = 0.02) -> None:
        self.readout += learning_rate * reward * signal * np.array([1.0, 0.5, -0.5, 0.25])
        self.readout = np.clip(self.readout, -1.0, 1.0)


def risk_clamp(value: float, limit: float = 0.5) -> float:
    return float(np.clip(value, -limit, limit))


def run_backtest(selection: ConnectomeSelection, closes: np.ndarray, costs: float = 0.001) -> dict:
    train_end = int(len(closes) * 0.6)
    validation_end = int(len(closes) * 0.8)
    agents = [Agent.create(selection.graph, i) for i in range(3)]
    no_learning = [Agent.create(selection.graph, i) for i in range(3)]
    records: list[dict] = []
    for t in range(20, len(closes) - 1):
        features = causal_features(closes, t)
        signals = np.array([risk_clamp(a.decide(features)) for a in agents])
        nolearn = np.array([risk_clamp(a.decide(features, use_graph=False)) for a in no_learning])
        classical = risk_clamp(float(signals.mean()))
        queen_state = selection.graph.step(np.pad(signals, (0, selection.graph.n_nodes - 3)))
        queen = risk_clamp(float(queen_state.mean()))
        next_return = float(closes[t + 1] / closes[t] - 1.0)
        # Credit is computed only after t+1 is observed. It is never used to
        # update an agent once the training cutoff has passed.
        reward = next_return * signals - costs * np.abs(signals)
        if t < train_end:
            for agent, reward_i, signal_i in zip(agents, reward, signals):
                agent.update(float(reward_i), float(signal_i))
        records.append({"t": t, "features": features.tolist(), "signals": signals.tolist(), "classical": classical, "queen": queen, "nolearn": float(nolearn.mean()), "next_return": next_return, "rewards": reward.tolist(), "engineering_credit": reward.tolist(), "credit_observed_at": t + 1, "readout_updated": bool(t < train_end)})

    def metric(key: str, start: int, end: int) -> dict:
        part = records[start:end]
        values = np.array([x[key] for x in part], dtype=float)
        returns = np.array([x["next_return"] for x in part], dtype=float)
        pnl = values * returns - costs * np.abs(values)
        return {"n": len(part), "mean_pnl": float(pnl.mean()), "cumulative_pnl": float(pnl.sum()), "mean_abs_signal": float(np.abs(values).mean())}

    test_start = validation_end - 20
    return {
        "split": {"train_end_close_index": train_end, "validation_end_close_index": validation_end, "test_record_start": test_start},
        "costs": costs,
        "learning": {
            "credit_rule": "next_return * signal - costs * abs(signal)",
            "credit_observation_lag": 1,
            "readout_updates_before_close_index": train_end,
            "validation_and_test_readout_frozen": True,
            "credit_is_engineering_rule": True,
        },
        "metrics": {name: {"validation": metric(name, train_end - 20, test_start), "test": metric(name, test_start, len(records))} for name in ("classical", "queen", "nolearn")},
        "records": records,
    }


def compare_agent_structures(
    selection: ConnectomeSelection,
    closes: np.ndarray,
    costs: float = 0.001,
    seeds: tuple[int, ...] = (0, 1, 2),
    split_indices: tuple[int, int] | None = None,
) -> dict:
    """Compare bounded local structures under the same causal history.

    This is an experiment receipt, not a promotion decision. Each seed uses
    the same time split and cost rule. The coordinator has independent state,
    while ``three_mean`` receives the same member signals and only averages.
    """
    if len(closes) < 60:
        raise ValueError("comparison requires at least 60 chronological closes")
    if selection.graph.n_nodes < 3:
        raise ValueError("comparison requires a graph with at least three nodes")
    if not seeds:
        raise ValueError("at least one seed is required")
    if split_indices is None:
        train_end = int(len(closes) * 0.6)
        validation_end = int(len(closes) * 0.8)
    else:
        train_end, validation_end = split_indices
        if not (20 < train_end < validation_end < len(closes) - 1):
            raise ValueError("split indices must leave a 20-close warmup and a non-empty test")
    structures = ("single_fly", "three_mean", "three_coordinator", "no_graph_mean")
    started = time.perf_counter()
    tracemalloc.start()
    seed_receipts: list[dict] = []

    def make_agent(graph: SparseGraph, feature_index: int, rng: np.random.Generator) -> Agent:
        agent = Agent.create(graph, feature_index)
        agent.readout = agent.readout + rng.normal(0.0, 0.01, size=agent.readout.shape)
        return agent

    def metric(records: list[dict], start: int, end: int, signal_scale: float = 1.0) -> dict:
        part = [record for record in records if start <= record["t"] < end]
        values = np.asarray([record["signal"] for record in part], dtype=float) * signal_scale
        values = np.clip(values, -0.5, 0.5)
        returns = np.asarray([record["next_return"] for record in part], dtype=float)
        pnl = values * returns - costs * np.abs(values)
        cumulative = np.cumsum(pnl) if len(pnl) else np.zeros(0)
        drawdown = cumulative - np.maximum.accumulate(cumulative) if len(cumulative) else np.zeros(0)
        previous = np.concatenate(([0.0], values[:-1])) if len(values) else np.zeros(0)
        return {
            "n": int(len(part)),
            "mean_pnl": float(pnl.mean()) if len(pnl) else 0.0,
            "cumulative_pnl": float(pnl.sum()) if len(pnl) else 0.0,
            "mean_abs_signal": float(np.abs(values).mean()) if len(values) else 0.0,
            "mean_turnover": float(np.abs(values - previous).mean()) if len(values) else 0.0,
            "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
        }

    for seed in seeds:
        rng = np.random.default_rng(seed)
        single = make_agent(selection.graph, 0, rng)
        members = [make_agent(selection.graph, index, rng) for index in range(3)]
        no_graph = [make_agent(selection.graph, index, rng) for index in range(3)]
        coordinator_state = np.zeros(selection.graph.n_nodes, dtype=float)
        records = {name: [] for name in structures}
        member_history: list[list[float]] = []
        for t in range(20, len(closes) - 1):
            features = causal_features(closes, t)
            single_signal = risk_clamp(single.decide(features))
            member_signals = np.asarray([risk_clamp(agent.decide(features)) for agent in members])
            no_graph_signals = np.asarray([risk_clamp(agent.decide(features, use_graph=False)) for agent in no_graph])
            mean_signal = risk_clamp(float(member_signals.mean()))
            no_graph_signal = risk_clamp(float(no_graph_signals.mean()))
            coordinator_input = np.pad(member_signals, (0, selection.graph.n_nodes - len(member_signals)))
            coordinator_state = selection.graph.step(coordinator_state + coordinator_input)
            coordinator_signal = risk_clamp(float(coordinator_state.mean()))
            next_return = float(closes[t + 1] / closes[t] - 1.0)
            values = {
                "single_fly": single_signal,
                "three_mean": mean_signal,
                "three_coordinator": coordinator_signal,
                "no_graph_mean": no_graph_signal,
            }
            for name, signal in values.items():
                records[name].append({"t": t, "signal": signal, "next_return": next_return})
            member_history.append(member_signals.tolist())
            if t < train_end:
                for agent, signal in zip(members, member_signals):
                    agent.update(next_return * signal - costs * abs(signal), float(signal))
                single.update(next_return * single_signal - costs * abs(single_signal), single_signal)
                for agent, signal in zip(no_graph, no_graph_signals):
                    agent.update(next_return * signal - costs * abs(signal), float(signal))

        member_matrix = np.asarray(member_history, dtype=float)
        if member_matrix.shape[0] > 1 and member_matrix.shape[1] > 1:
            correlation = np.corrcoef(member_matrix.T)
            disagreement = float(np.mean(np.std(member_matrix, axis=1)))
        else:
            correlation = np.eye(3)
            disagreement = 0.0
        train_exposures = {
            name: float(np.mean(np.abs([record["signal"] for record in records[name] if record["t"] < train_end])))
            for name in structures
        }
        target_exposure = float(np.median(list(train_exposures.values())))
        structure_receipts = {}
        for name in structures:
            train_exposure = train_exposures[name]
            scale = target_exposure / train_exposure if train_exposure else 1.0
            structure_receipts[name] = {
                "agent_count": 1 if name == "single_fly" else 3,
                "graph_enabled": name != "no_graph_mean",
                "aggregation": "single" if name == "single_fly" else ("coordinator_state" if name == "three_coordinator" else "mean"),
                "validation": metric(records[name], train_end, validation_end),
                "test": metric(records[name], validation_end, len(closes)),
                "exposure_matching": {
                    "train_mean_abs_signal": train_exposure,
                    "target_train_mean_abs_signal": target_exposure,
                    "scale_derived_from_train_only": True,
                    "validation": metric(records[name], train_end, validation_end, scale),
                    "test": metric(records[name], validation_end, len(closes), scale),
                },
            }
        seed_receipts.append({
            "seed": seed,
            "structures": structure_receipts,
            "member_signal_correlation": correlation.tolist(),
            "member_signal_disagreement": disagreement,
        })
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "protocol": "causal structure comparison v1",
        "structures": list(structures),
        "seeds": list(seeds),
        "split": {"train_end_close_index": train_end, "validation_end_close_index": validation_end},
        "costs": costs,
        "seed_receipts": seed_receipts,
        "resources": {"wall_seconds": round(time.perf_counter() - started, 3), "python_tracemalloc_peak_bytes": peak},
        "limitations": [
            "one chronological market history supplied by caller",
            "S&P 500 index proxy is not investment validation",
            "structure comparison is not a promotion gate or profitability claim",
            "no_graph_mean is an edge/dynamics ablation, not a parameter-matched universal baseline",
        ],
    }


def run_walk_forward_comparison(
    selection: ConnectomeSelection,
    closes: np.ndarray,
    train_size: int = 252,
    validation_size: int = 126,
    test_size: int = 126,
    step_size: int = 126,
    costs: float = 0.001,
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict:
    """Run the same structure comparison over rolling chronological folds."""
    if min(train_size, validation_size, test_size, step_size) < 1:
        raise ValueError("walk-forward sizes must be positive")
    folds: list[dict] = []
    start = 0
    while start + train_size + validation_size + test_size <= len(closes):
        # Keep a causal warmup before each fold's first scored decision.
        window_start = max(0, start - 20)
        window_end = start + train_size + validation_size + test_size
        window = np.asarray(closes[window_start:window_end], dtype=float)
        train_index = (start - window_start) + train_size
        validation_index = train_index + validation_size
        comparison = compare_agent_structures(
            selection,
            window,
            costs=costs,
            seeds=seeds,
            split_indices=(train_index, validation_index),
        )
        comparison["fold"] = {
            "close_start_index": start,
            "close_end_index": window_end,
            "warmup_closes": start - window_start,
            "train_size": train_size,
            "validation_size": validation_size,
            "test_size": test_size,
        }
        folds.append(comparison)
        start += step_size
    if not folds:
        raise ValueError("history is too short for one walk-forward fold")
    return {
        "protocol": "causal walk-forward structure comparison v1",
        "fold_count": len(folds),
        "folds": folds,
        "costs": costs,
        "seeds": list(seeds),
        "limitations": [
            "all folds use the supplied market series and bounded connectome selection",
            "folds are chronological windows, not independent asset classes",
            "results are research evidence, not trading advice or a promotion gate",
        ],
    }
