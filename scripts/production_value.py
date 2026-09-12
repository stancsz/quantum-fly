"""Receipt construction and verification for the v1 production-value slice."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_METRICS = (
    "n",
    "cumulative_pnl",
    "mean_turnover",
    "activity_rate",
    "unique_position_count",
    "max_drawdown",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return bool(np.isfinite(value))
    if isinstance(value, list):
        return all(_finite(item) for item in value)
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    return False


def _metric_path(value: dict, path: str) -> dict:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"missing metric path: {path}")
        current = current[part]
    if not isinstance(current, dict):
        raise ValueError(f"metric path is not an object: {path}")
    return current


def _episode_rows(comparisons: list[dict], candidate: str, baseline: str, metric_view: str) -> list[dict]:
    rows: list[dict] = []
    for cost_result in comparisons:
        cost = float(cost_result["costs"])
        for fold_index, fold in enumerate(cost_result["folds"]):
            fold_meta = fold.get("fold", {})
            fold_id = int(fold_meta.get("close_start_index", fold_index))
            for seed_receipt in fold["seed_receipts"]:
                seed = int(seed_receipt["seed"])
                structures = seed_receipt["structures"]
                candidate_metrics = _metric_path(structures[candidate], metric_view)
                baseline_metrics = _metric_path(structures[baseline], metric_view)
                case_id = f"cost={cost:g}|fold={fold_id}|seed={seed}"
                rows.append({
                    "case_id": case_id,
                    "cost": cost,
                    "fold": fold_id,
                    "seed": seed,
                    "candidate": {"name": candidate, "metrics": candidate_metrics},
                    "baseline": {"name": baseline, "metrics": baseline_metrics},
                })
    return rows


def _bootstrap_lower_bound(values: list[float], confidence: float, replicates: int, block_size: int, seed: int) -> float:
    if not values:
        return float("nan")
    array = np.asarray(values, dtype=float)
    if len(array) == 1:
        return float(array[0])
    block_size = max(1, min(int(block_size), len(array)))
    starts = np.arange(len(array) - block_size + 1)
    rng = np.random.default_rng(seed)
    samples = np.empty(int(replicates), dtype=float)
    blocks_needed = int(np.ceil(len(array) / block_size))
    for index in range(len(samples)):
        selected = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate([array[start : start + block_size] for start in selected])[: len(array)]
        samples[index] = float(sample.mean())
    return float(np.quantile(samples, (1.0 - confidence) / 2.0))


def summarize_comparison(rows: list[dict], thresholds: dict) -> dict:
    deltas = [float(row["candidate"]["metrics"]["cumulative_pnl"]) - float(row["baseline"]["metrics"]["cumulative_pnl"]) for row in rows]
    by_fold: dict[int, list[float]] = defaultdict(list)
    for row, delta in zip(rows, deltas):
        by_fold[int(row["fold"])].append(delta)
    fold_means = {str(fold): float(np.mean(values)) for fold, values in sorted(by_fold.items())}
    positive_folds = sum(value > 0.0 for value in fold_means.values())
    positive_units = sum(value > 0.0 for value in deltas)
    candidate_turnover = float(np.mean([row["candidate"]["metrics"]["mean_turnover"] for row in rows]))
    baseline_turnover = float(np.mean([row["baseline"]["metrics"]["mean_turnover"] for row in rows]))
    turnover_ratio = float(candidate_turnover / baseline_turnover) if baseline_turnover > 0 else float("inf")
    candidate_activity_rates = [float(row["candidate"]["metrics"]["activity_rate"]) for row in rows]
    candidate_unique_positions = [int(row["candidate"]["metrics"]["unique_position_count"]) for row in rows]
    drawdown_deterioration = float(max(
        [max(0.0, float(row["baseline"]["metrics"]["max_drawdown"]) - float(row["candidate"]["metrics"]["max_drawdown"])) for row in rows] or [0.0]
    ))
    lower_bound = _bootstrap_lower_bound(
        deltas,
        float(thresholds["bootstrap_confidence"]),
        int(thresholds["bootstrap_replicates"]),
        int(thresholds["bootstrap_block_size"]),
        int(thresholds["bootstrap_seed"]),
    )
    checks = {
        "minimum_positive_folds": positive_folds >= int(thresholds["minimum_positive_folds"]),
        "minimum_positive_units": positive_units >= int(thresholds["minimum_positive_units"]),
        "bootstrap_lower_bound": lower_bound > float(thresholds["bootstrap_lower_bound_gt"]),
        "max_drawdown_deterioration": drawdown_deterioration <= float(thresholds["max_drawdown_deterioration"]),
        "turnover_ratio": turnover_ratio <= float(thresholds["max_turnover_ratio"]),
        "candidate_activity_rate": min(candidate_activity_rates, default=0.0) >= float(thresholds["minimum_candidate_activity_rate"]),
        "candidate_unique_positions": min(candidate_unique_positions, default=0) >= int(thresholds["minimum_candidate_unique_position_count"]),
    }
    return {
        "unit_count": len(rows),
        "fold_count": len(by_fold),
        "delta_definition": "candidate cumulative_pnl minus baseline cumulative_pnl per fold-seed episode",
        "deltas": deltas,
        "fold_mean_deltas": fold_means,
        "positive_folds": positive_folds,
        "positive_units": positive_units,
        "bootstrap": {"confidence": float(thresholds["bootstrap_confidence"]), "block_size": int(thresholds["bootstrap_block_size"]), "replicates": int(thresholds["bootstrap_replicates"]), "seed": int(thresholds["bootstrap_seed"]), "lower_bound": lower_bound},
        "drawdown_deterioration": drawdown_deterioration,
        "turnover": {"candidate_mean": candidate_turnover, "best_control_mean": baseline_turnover, "ratio": turnover_ratio},
        "activity": {
            "candidate_mean_rate": float(np.mean(candidate_activity_rates)) if candidate_activity_rates else 0.0,
            "candidate_min_rate": min(candidate_activity_rates, default=0.0),
            "candidate_min_unique_positions": min(candidate_unique_positions, default=0),
            "turnover_activity_threshold": 1e-6,
        },
        "checks": checks,
        "research_gate": "GO" if all(checks.values()) else "NO-GO",
    }


def build_receipt(config: dict, config_path: Path, data_provenance: dict, code_provenance: dict, comparisons: list[dict]) -> dict:
    candidate = str(config["candidate"])
    baseline = str(config["baseline"])
    metric_view = str(config["metric_view"])
    episodes = _episode_rows(comparisons, candidate, baseline, metric_view)
    base_cost = float(config["base_cost"])
    base_rows = [row for row in episodes if np.isclose(row["cost"], base_cost)]
    paired = summarize_comparison(base_rows, config["thresholds"])
    cost_summaries = {}
    for multiplier in config["cost_multipliers"]:
        cost = base_cost * float(multiplier)
        rows = [row for row in episodes if np.isclose(row["cost"], cost)]
        cost_summaries[str(multiplier)] = {"cost": cost, **summarize_comparison(rows, config["thresholds"])}
    sensitivity_stable = len({summary["research_gate"] for summary in cost_summaries.values()}) <= 1
    decision = "GO" if paired["research_gate"] == "GO" and sensitivity_stable else "NO-GO"
    return {
        "schema": "quantum-fly-production-value-receipt.v1",
        "protocol": config["protocol"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "provenance": {"config": {"path": str(config_path), "sha256": sha256_file(config_path)}, "data": data_provenance, "code": code_provenance},
        "candidate": {"name": candidate, "metric_view": metric_view, "episodes": [row for row in episodes if row["candidate"]["name"] == candidate]},
        "baseline": {"name": baseline, "metric_view": metric_view, "episodes": [row for row in episodes if row["baseline"]["name"] == baseline]},
        "episodes": episodes,
        "costs": {"base": base_cost, "tested": [float(base_cost) * float(multiplier) for multiplier in config["cost_multipliers"]]},
        "paired_comparison": paired,
        "cost_sensitivity": {"stable": sensitivity_stable, "summaries": cost_summaries},
        "decision": {"research_gate": decision, "shadow_operational_gate": "NOT-IMPLEMENTED", "forward_paper_value": "NOT-IMPLEMENTED", "overall": decision},
        "limitations": list(config.get("limitations", [])),
    }


def verify_receipt(receipt: dict) -> dict:
    errors: list[str] = []
    if receipt.get("schema") != "quantum-fly-production-value-receipt.v1":
        errors.append("schema missing or unsupported")
    for key in ("protocol", "config", "provenance", "candidate", "baseline", "episodes", "costs", "paired_comparison", "limitations", "decision"):
        if key not in receipt:
            errors.append(f"missing required field: {key}")
    if not _finite(receipt):
        errors.append("non-finite numeric value")
    provenance = receipt.get("provenance", {})
    if not isinstance(receipt.get("config"), dict) or not receipt.get("config"):
        errors.append("config is missing or incomplete")
    elif not receipt["config"].get("schema") or not receipt["config"].get("protocol"):
        errors.append("config schema/protocol missing")
    for key in ("config", "data", "code"):
        if not isinstance(provenance.get(key), dict) or not provenance[key]:
            errors.append(f"missing provenance: {key}")
    if isinstance(provenance.get("config"), dict) and not provenance["config"].get("sha256"):
        errors.append("config provenance hash missing")
    if isinstance(provenance.get("data"), dict) and not provenance["data"].get("sha256"):
        errors.append("data provenance hash missing")
    if isinstance(provenance.get("code"), dict) and not provenance["code"].get("files"):
        errors.append("code provenance files missing")
    episodes = receipt.get("episodes", [])
    candidate = receipt.get("candidate", {})
    baseline = receipt.get("baseline", {})
    candidate_name = candidate.get("name")
    baseline_name = baseline.get("name")
    if not candidate_name or not baseline_name or candidate_name == baseline_name:
        errors.append("candidate and baseline must be distinct and named")
    case_ids = [episode.get("case_id") for episode in episodes if isinstance(episode, dict)]
    if len(case_ids) != len(set(case_ids)):
        errors.append("duplicate case")
    candidate_episodes = candidate.get("episodes", []) if isinstance(candidate, dict) else []
    baseline_episodes = baseline.get("episodes", []) if isinstance(baseline, dict) else []
    if len(episodes) == 0 or len(candidate_episodes) != len(episodes) or len(baseline_episodes) != len(episodes):
        errors.append("candidate/baseline episode count mismatch")
    if len(episodes) and {
        item.get("case_id") for item in candidate_episodes if isinstance(item, dict)
    } != set(case_ids):
        errors.append("candidate episode identity/count mismatch")
    if len(episodes) and {
        item.get("case_id") for item in baseline_episodes if isinstance(item, dict)
    } != set(case_ids):
        errors.append("baseline episode identity/count mismatch")
    if isinstance(receipt.get("costs"), dict):
        tested_costs = receipt["costs"].get("tested", [])
        parsed_costs = []
        try:
            parsed_costs = [float(cost) for cost in tested_costs]
        except (TypeError, ValueError):
            errors.append("cost contains an unknown or non-numeric value")
        if not tested_costs or any(not np.isfinite(cost) or cost <= 0 for cost in parsed_costs):
            errors.append("missing or invalid tested costs")
        try:
            episode_costs = {float(episode.get("cost")) for episode in episodes if isinstance(episode, dict) and episode.get("cost") is not None}
            if set(parsed_costs) != episode_costs:
                errors.append("cost count or coverage mismatch")
        except (TypeError, ValueError):
            errors.append("episode cost contains an unknown or non-numeric value")
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            errors.append("episode is not an object")
            continue
        for side in ("candidate", "baseline"):
            metrics = episode.get(side, {}).get("metrics", {})
            for metric in REQUIRED_METRICS:
                if metric not in metrics:
                    errors.append(f"episode {index} missing {side} metric: {metric}")
        if episode.get("candidate", {}).get("name") != candidate_name or episode.get("baseline", {}).get("name") != baseline_name:
            errors.append(f"episode {index} candidate/baseline identity mismatch")
    paired = receipt.get("paired_comparison")
    if not isinstance(paired, dict) or not paired.get("checks"):
        errors.append("paired comparison is incomplete")
    elif isinstance(receipt.get("costs"), dict):
        try:
            base_cost = float(receipt["costs"].get("base"))
            base_count = sum(1 for episode in episodes if isinstance(episode, dict) and np.isclose(float(episode.get("cost", float("nan"))), base_cost))
            if paired.get("unit_count") != base_count:
                errors.append("paired comparison unit count mismatch")
        except (TypeError, ValueError):
            errors.append("paired comparison base cost is unknown")
        if paired.get("research_gate") != ("GO" if all(paired["checks"].values()) else "NO-GO"):
            errors.append("paired comparison decision does not match its checks")
    decision = receipt.get("decision", {})
    if decision.get("research_gate") not in ("GO", "NO-GO") or decision.get("overall") not in ("GO", "NO-GO"):
        errors.append("decision is missing explicit GO/NO-GO")
    elif isinstance(paired, dict):
        stable = receipt.get("cost_sensitivity", {}).get("stable")
        expected = "GO" if paired.get("research_gate") == "GO" and stable is True else "NO-GO"
        if decision.get("research_gate") != expected or decision.get("overall") != expected:
            errors.append("overall decision does not match research gate and cost sensitivity")
    return {"valid": not errors, "errors": errors, "decision": decision.get("overall", "NO-GO"), "research_gate": decision.get("research_gate", "NO-GO")}
