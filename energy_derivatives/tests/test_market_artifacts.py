import copy

import pytest

from spk_derivatives.energy_contracts import EnergyContract
from spk_derivatives.market_artifacts import (
    MarketRiskArtifactError,
    build_market_risk_package,
    validate_market_risk_package,
)
from spk_derivatives.policy_lab import extract_admitted_exposure
from spk_derivatives.scenario_risk import summarize_policy_contract_distribution
from spk_derivatives.scenario_set import SCENARIO_SET_SCHEMA, build_market_price_scenarios


def _context(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract(
        "floor",
        currency="USD",
        quantity_unit="kWh-claim",
        floor_price=0.10,
    )
    prices = [0.05, 0.08, 0.12, 0.15]
    distribution = summarize_policy_contract_distribution(
        exposure,
        prices,
        contract,
    )
    return exposure, contract, prices, distribution


def _build_package(policy_package):
    exposure, contract, _, distribution = _context(policy_package)
    return build_market_risk_package(
        exposure,
        distribution,
        contract,
        market_input={
            "kind": "historical-scenario-fixture",
            "source": "unit-test",
            "price_unit": "USD/kWh-claim",
        },
        scenario_model={
            "id": "empirical-replay",
            "scenario_count": 4,
        },
    )


def _build_scenario_bound_package(policy_package):
    exposure, contract, prices, distribution = _context(policy_package)
    scenario_set = build_market_price_scenarios(
        prices,
        price_unit=contract.price_unit,
        source="unit-test",
        source_hash="b" * 64,
        observed_at_utc="2026-08-29T02:00:00Z",
        model_id="historical-replay",
        model_parameters={"sample": "fixture"},
        seed=11,
    )
    package = build_market_risk_package(
        exposure,
        distribution,
        contract,
        market_input={
            "kind": "scenario-set",
            "schema": SCENARIO_SET_SCHEMA,
            "scenario_set_id": scenario_set.scenario_set_id,
            "source": scenario_set.source,
            "source_hash": scenario_set.source_hash,
            "observed_at_utc": scenario_set.observed_at_utc,
            "price_unit": scenario_set.price_unit,
        },
        scenario_model={
            "id": scenario_set.model_id,
            "parameters": dict(scenario_set.model_parameters),
            "seed": scenario_set.seed,
            "scenario_count": len(scenario_set.market_prices),
        },
    )
    return package, scenario_set


def test_market_risk_package_is_deterministic(policy_package):
    first = _build_package(policy_package)
    second = _build_package(policy_package)
    assert first["artifact_id"] == second["artifact_id"]
    assert first["package_content_id"] == second["package_content_id"]
    assert validate_market_risk_package(first)
    assert first["risk"]["quantity"] == 1000.0
    assert first["authority"]["policy_id"] == "policy-a"


def test_market_risk_artifact_detects_tampering(policy_package):
    package = _build_package(policy_package)
    mutated = copy.deepcopy(package)
    mutated["risk"]["contract_value_mean"] += 1.0
    with pytest.raises(MarketRiskArtifactError, match="protection_value_mean|artifact_id"):
        validate_market_risk_package(mutated)


def test_market_risk_artifact_rejects_unit_mutation(policy_package):
    package = _build_package(policy_package)
    mutated = copy.deepcopy(package)
    mutated["contract"]["quantity_unit"] = "MWh"
    with pytest.raises(MarketRiskArtifactError, match="quantity units"):
        validate_market_risk_package(mutated, verify_identity=False)


def test_scenario_bound_market_risk_package_is_valid(policy_package):
    package, scenario_set = _build_scenario_bound_package(policy_package)

    assert validate_market_risk_package(package)
    assert package["market"]["input"]["schema"] == SCENARIO_SET_SCHEMA
    assert package["market"]["input"]["scenario_set_id"] == scenario_set.scenario_set_id
    assert package["market"]["scenario_model"]["scenario_count"] == package["risk"]["scenarios"]


def test_scenario_bound_market_risk_rejects_malformed_scenario_identity(policy_package):
    package, _ = _build_scenario_bound_package(policy_package)
    mutated = copy.deepcopy(package)
    mutated["market"]["input"]["scenario_set_id"] = "not-a-hash"

    with pytest.raises(MarketRiskArtifactError, match="scenario_set_id"):
        validate_market_risk_package(mutated, verify_identity=False)


def test_scenario_bound_market_risk_rejects_scenario_count_mismatch(policy_package):
    package, _ = _build_scenario_bound_package(policy_package)
    mutated = copy.deepcopy(package)
    mutated["market"]["scenario_model"]["scenario_count"] += 1

    with pytest.raises(MarketRiskArtifactError, match="count does not match"):
        validate_market_risk_package(mutated, verify_identity=False)


def test_scenario_bound_market_risk_rejects_price_unit_mismatch(policy_package):
    package, _ = _build_scenario_bound_package(policy_package)
    mutated = copy.deepcopy(package)
    mutated["market"]["input"]["price_unit"] = "EUR/MWh"

    with pytest.raises(MarketRiskArtifactError, match="price units"):
        validate_market_risk_package(mutated, verify_identity=False)
