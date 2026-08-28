import pytest

from spk_derivatives.scenario_set import (
    ScenarioSetError,
    build_joint_scenarios,
    build_market_price_scenarios,
)


def test_market_scenario_manifest_is_deterministic():
    first = build_market_price_scenarios(
        [-10.0, 20.0, 40.0],
        price_unit="CNY/MWh",
        source="fixture",
        observed_at_utc="2026-08-29T00:00:00Z",
        model_id="historical-replay",
        model_parameters={"window": "3-observations"},
    )
    second = build_market_price_scenarios(
        [-10.0, 20.0, 40.0],
        price_unit="CNY/MWh",
        source="fixture",
        observed_at_utc="2026-08-29T00:00:00Z",
        model_id="historical-replay",
        model_parameters={"window": "3-observations"},
    )
    assert first.scenario_set_id == second.scenario_set_id
    assert first.to_dict()["scenario_count"] == 3


def test_joint_manifest_preserves_paired_quantity_price_scenarios():
    manifest = build_joint_scenarios(
        [10.0, 20.0, 30.0],
        [80.0, 60.0, 40.0],
        quantity_unit="MWh",
        price_unit="USD/MWh",
        source="paired fixture",
        observed_at_utc="2026-08-29T00:00:00Z",
        model_id="empirical-pairs",
    )
    assert manifest.normalized_kind == "joint-volume-price"
    assert manifest.quantities == (10.0, 20.0, 30.0)
    assert manifest.market_prices == (80.0, 60.0, 40.0)


def test_joint_manifest_rejects_unpaired_scenarios():
    with pytest.raises(ScenarioSetError, match="equal length"):
        build_joint_scenarios(
            [10.0, 20.0],
            [80.0, 60.0, 40.0],
            quantity_unit="MWh",
            price_unit="USD/MWh",
            source="fixture",
            observed_at_utc="2026-08-29T00:00:00Z",
            model_id="bad-pairs",
        )
