import numpy as np

from quantum_fly.backtest import Agent, compare_agent_structures, position_pnl, position_turnover, risk_clamp, run_backtest, run_walk_forward_comparison
from quantum_fly.fixture import synthetic_graph
from quantum_fly.market import causal_features
from quantum_fly.connectome import ConnectomeSelection


def test_features_do_not_use_future_close():
    closes = np.arange(40.0) + 100
    before = causal_features(closes, 25)
    changed = closes.copy()
    changed[26:] += 1000
    np.testing.assert_allclose(before, causal_features(changed, 25))


def test_agent_states_are_independent_and_risk_is_clamped():
    a = Agent.create(synthetic_graph(), 0)
    b = Agent.create(synthetic_graph(), 1)
    a.decide(np.array([1.0, 0.0, 0.0, 0.0]))
    assert not np.array_equal(a.state, b.state)
    assert risk_clamp(10.0) == 0.5


def test_transaction_cost_is_position_turnover_with_explicit_transition_semantics():
    assert position_turnover(0.25, 0.0) == 0.25
    assert position_turnover(0.25, 0.25) == 0.0
    assert position_turnover(-0.25, 0.25) == 0.5
    assert position_turnover(0.0, -0.25) == 0.25
    pnl, turnover, transaction_cost = position_pnl(0.25, 0.04, 0.0, 0.01)
    assert np.isclose(turnover, 0.25)
    assert np.isclose(transaction_cost, 0.0025)
    assert np.isclose(pnl, 0.0075)


def test_backtest_records_cost_hold_and_exit_turnover_consistently():
    graph = synthetic_graph()
    selection = ConnectomeSelection(graph, np.arange(4), np.zeros(4), 4, 4, 5, 5, "fixture")
    result = run_backtest(selection, np.linspace(100, 120, 80), costs=0.001)
    records = result["records"]
    assert np.isclose(records[0]["turnover"]["classical"], abs(records[0]["classical"]))
    assert np.isclose(records[0]["transaction_cost"]["classical"], 0.001 * abs(records[0]["classical"]))
    for index in range(1, len(records)):
        previous = records[index - 1]["classical"]
        current = records[index]["classical"]
        assert np.isclose(records[index]["turnover"]["classical"], abs(current - previous))
        assert np.isclose(records[index]["transaction_cost"]["classical"], 0.001 * abs(current - previous))


def test_backtest_has_frozen_style_test_metrics_and_costs():
    graph = synthetic_graph()
    selection = ConnectomeSelection(graph, np.arange(4), np.zeros(4), 4, 4, 5, 5, "fixture")
    assert selection.id_integrity["selected_ids_sorted_unique"]
    assert selection.id_integrity["graph_node_count_matches_selected_ids"]
    result = run_backtest(selection, np.linspace(100, 120, 80), costs=0.001)
    assert result["costs"] == 0.001
    assert result["metrics"]["queen"]["test"]["n"] > 0
    assert np.isfinite(result["metrics"]["classical"]["test"]["mean_pnl"])
    assert result["learning"]["validation_and_test_readout_frozen"] is True
    assert all(record["engineering_credit"] == record["rewards"] for record in result["records"])
    assert all(record["credit_observed_at"] == record["t"] + 1 for record in result["records"])


def test_structure_comparison_is_causal_seeded_and_reports_controls():
    graph = synthetic_graph()
    selection = ConnectomeSelection(graph, np.arange(4), np.zeros(4), 4, 4, 5, 5, "fixture")
    closes = np.linspace(100, 130, 100) + np.sin(np.arange(100))
    result = compare_agent_structures(selection, closes, costs=0.001, seeds=(0, 1))
    assert result["structures"] == ["single_fly", "three_mean", "three_coordinator", "no_graph_mean"]
    assert result["seeds"] == [0, 1]
    assert result["split"]["train_end_close_index"] < result["split"]["validation_end_close_index"]
    assert len(result["seed_receipts"]) == 2
    for receipt in result["seed_receipts"]:
        assert set(receipt["structures"]) == set(result["structures"])
        assert len(receipt["member_signal_correlation"]) == 3
        assert all("max_drawdown" in item["test"] and "mean_turnover" in item["test"] for item in receipt["structures"].values())
        assert all(item["exposure_matching"]["scale_derived_from_train_only"] for item in receipt["structures"].values())
    assert result["resources"]["python_tracemalloc_peak_bytes"] > 0


def test_walk_forward_comparison_uses_multiple_chronological_folds():
    graph = synthetic_graph()
    selection = ConnectomeSelection(graph, np.arange(4), np.zeros(4), 4, 4, 5, 5, "fixture")
    closes = np.linspace(100, 150, 180) + np.sin(np.arange(180))
    result = run_walk_forward_comparison(selection, closes, train_size=60, validation_size=20, test_size=20, step_size=20, seeds=(0, 1))
    assert result["fold_count"] == 5
    assert result["folds"][0]["fold"]["close_start_index"] == 0
    assert result["folds"][1]["fold"]["close_start_index"] == 20
    assert result["folds"][0]["split"]["train_end_close_index"] < result["folds"][0]["split"]["validation_end_close_index"]
