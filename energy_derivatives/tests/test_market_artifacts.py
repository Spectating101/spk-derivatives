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


def _build_package(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract(
        "floor",
        currency="USD",
        quantity_unit="kWh-claim",
        floor_price=0.10,
    )
    distribution = summarize_policy_contract_distribution(
        exposure,
        [0.05, 0.08, 0.12, 0.15],
        contract,
    )
    package = build_market_risk_package(
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
    return package


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
