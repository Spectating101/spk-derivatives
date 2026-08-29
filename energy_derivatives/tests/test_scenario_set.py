import json

import pytest

from spk_derivatives.scenario_set import (
    ScenarioSetError,
    build_joint_scenarios,
    build_market_price_scenarios,
    load_scenario_set,
    validate_scenario_set,
    write_scenario_set,
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


def test_scenario_manifest_round_trip_verifies_identity(tmp_path):
    manifest = build_market_price_scenarios(
        [-20.0, 15.0, 90.0],
        price_unit="USD/MWh",
        source="market fixture",
        observed_at_utc="2026-08-29T01:00:00Z",
        model_id="spike-replay",
        model_parameters={"regime": "test"},
        source_hash="a" * 64,
        seed=17,
    )
    path = tmp_path / "scenario-set.json"

    assert write_scenario_set(manifest, path) == path
    loaded = load_scenario_set(path)

    assert loaded == manifest
    assert validate_scenario_set(path) is True
    assert loaded.scenario_set_id == manifest.scenario_set_id


def test_scenario_manifest_rejects_tampered_values(tmp_path):
    manifest = build_market_price_scenarios(
        [10.0, 20.0, 30.0],
        price_unit="USD/MWh",
        source="fixture",
        observed_at_utc="2026-08-29T01:00:00Z",
        model_id="historical-replay",
    )
    payload = manifest.to_dict()
    payload["market_prices"][1] = 999.0
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ScenarioSetError, match="does not match scenario content"):
        load_scenario_set(path)


def test_scenario_manifest_rejects_count_mismatch():
    manifest = build_market_price_scenarios(
        [10.0, 20.0],
        price_unit="USD/MWh",
        source="fixture",
        observed_at_utc="2026-08-29T01:00:00Z",
        model_id="historical-replay",
    ).to_dict()
    manifest["scenario_count"] = 3

    with pytest.raises(ScenarioSetError, match="scenario_count"):
        load_scenario_set(manifest)
