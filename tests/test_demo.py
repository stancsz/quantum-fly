from scripts.demo import build_demo


def test_demo_is_finite_and_explicitly_synthetic():
    result = build_demo()
    assert result["scope"] == "synthetic fixture demonstration"
    assert result["l1_difference"] > 0
    assert len(result["connectome_inspired_output"]) == 4
    assert any("not investment value" in item for item in result["limitations"])
