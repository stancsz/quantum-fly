import json

from scripts.production_value import build_receipt, verify_receipt


def _comparison(cost: float, candidate_pnl: float = 1.0, activity_rate: float = 0.2, unique_positions: int = 3):
    folds = []
    for fold_index in range(4):
        seed_receipts = []
        for seed in range(3):
            metrics = {
                "n": 10,
                "cumulative_pnl": candidate_pnl,
                "mean_turnover": 0.1,
                "activity_rate": activity_rate,
                "unique_position_count": unique_positions,
                "max_drawdown": -0.01,
            }
            baseline_metrics = {**metrics, "cumulative_pnl": 0.0}
            structures = {
                "three_coordinator": {"exposure_matching": {"test": metrics}},
                "no_graph_mean": {"exposure_matching": {"test": baseline_metrics}},
            }
            seed_receipts.append({"seed": seed, "structures": structures})
        folds.append({"fold": {"close_start_index": fold_index}, "seed_receipts": seed_receipts})
    return {"costs": cost, "folds": folds}


def _config():
    return {
        "schema": "quantum-fly-production-value-config.v1",
        "protocol": "test protocol",
        "candidate": "three_coordinator",
        "baseline": "no_graph_mean",
        "metric_view": "exposure_matching.test",
        "base_cost": 0.001,
        "cost_multipliers": [0.5, 1.0, 2.0],
        "thresholds": {
            "minimum_positive_folds": 3,
            "minimum_positive_units": 8,
            "bootstrap_confidence": 0.95,
            "bootstrap_lower_bound_gt": 0.0,
            "max_drawdown_deterioration": 0.005,
            "max_turnover_ratio": 1.2,
            "minimum_candidate_activity_rate": 0.01,
            "minimum_candidate_unique_position_count": 2,
            "bootstrap_replicates": 50,
            "bootstrap_block_size": 2,
            "bootstrap_seed": 7,
        },
        "limitations": ["test only"],
    }


def test_harness_builds_a_complete_research_receipt(tmp_path):
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    comparisons = [_comparison(config["base_cost"] * multiplier) for multiplier in config["cost_multipliers"]]
    receipt = build_receipt(
        config,
        config_path,
        {"path": "fixture.csv", "sha256": "data-hash"},
        {"files": {"fixture.py": "code-hash"}},
        comparisons,
    )
    result = verify_receipt(receipt)
    assert result["valid"] is True
    assert result["decision"] == "GO"
    assert len(receipt["episodes"]) == 36
    assert receipt["decision"]["shadow_operational_gate"] == "NOT-IMPLEMENTED"


def test_harness_rejects_duplicate_case_and_missing_baseline(tmp_path):
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    receipt = build_receipt(
        config,
        config_path,
        {"path": "fixture.csv", "sha256": "data-hash"},
        {"files": {"fixture.py": "code-hash"}},
        [_comparison(config["base_cost"] * multiplier) for multiplier in config["cost_multipliers"]],
    )
    receipt["episodes"][1]["case_id"] = receipt["episodes"][0]["case_id"]
    receipt["baseline"]["name"] = ""
    result = verify_receipt(receipt)
    assert result["valid"] is False
    assert any("duplicate case" in error for error in result["errors"])
    assert any("candidate and baseline" in error for error in result["errors"])


def test_harness_marks_negative_replay_no_go_without_hiding_observation(tmp_path):
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    comparisons = [_comparison(config["base_cost"] * multiplier, candidate_pnl=-1.0) for multiplier in config["cost_multipliers"]]
    receipt = build_receipt(
        config,
        config_path,
        {"path": "fixture.csv", "sha256": "data-hash"},
        {"files": {"fixture.py": "code-hash"}},
        comparisons,
    )
    assert verify_receipt(receipt)["valid"] is True
    assert receipt["decision"]["overall"] == "NO-GO"
    assert receipt["paired_comparison"]["research_gate"] == "NO-GO"


def test_harness_rejects_unknown_cost_without_crashing(tmp_path):
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    receipt = build_receipt(
        config,
        config_path,
        {"path": "fixture.csv", "sha256": "data-hash"},
        {"files": {"fixture.py": "code-hash"}},
        [_comparison(config["base_cost"] * multiplier) for multiplier in config["cost_multipliers"]],
    )
    receipt["costs"]["tested"][0] = "unknown"
    result = verify_receipt(receipt)
    assert result["valid"] is False
    assert any("unknown" in error for error in result["errors"])


def test_harness_rejects_near_constant_candidate_as_degenerate(tmp_path):
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    receipt = build_receipt(
        config,
        config_path,
        {"path": "fixture.csv", "sha256": "data-hash"},
        {"files": {"fixture.py": "code-hash"}},
        [_comparison(config["base_cost"] * multiplier, activity_rate=0.0, unique_positions=1) for multiplier in config["cost_multipliers"]],
    )
    assert verify_receipt(receipt)["valid"] is True
    assert receipt["decision"]["overall"] == "NO-GO"
    assert receipt["paired_comparison"]["checks"]["candidate_activity_rate"] is False
    assert receipt["paired_comparison"]["checks"]["candidate_unique_positions"] is False
