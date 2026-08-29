import copy

import pytest

from spk_derivatives.energy_contracts import EnergyContract
from spk_derivatives.policy_bound_market_risk import (
    POLICY_BOUND_MARKET_RISK_SCHEMA,
    PolicyBoundMarketRiskError,
    build_policy_bound_market_risk_package,
    validate_policy_bound_market_risk_package,
)
from spk_derivatives.policy_lab import extract_admitted_exposure
from spk_derivatives.policy_market_bridge import (
    BASIS_DECLARED_SEMANTIC,
    build_policy_market_binding,
)
from spk_derivatives.scenario_set import build_market_price_scenarios


def _bound_case(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    binding = build_policy_market_binding(
        exposure,
        market_quantity_unit="MWh",
        basis_kind=BASIS_DECLARED_SEMANTIC,
        factor=0.001,
        authority="Research scenario convention",
        reference="unit-test market mapping v1",
        semantics="For this scenario only, one kWh-claim maps to 0.001 MWh market quantity.",
    )
    scenarios = build_market_price_scenarios(
        [-25.0, 50.0, 100.0, 250.0],
        price_unit="AUD/MWh",
        source="unit-test-aemo-like-prices",
        source_hash="f" * 64,
        observed_at_utc="2026-08-30T00:00:00Z",
        model_id="historical-replay",
        model_parameters={"region": "NSW1"},
    )
    contract = EnergyContract(
        "floor",
        currency="AUD",
        quantity_unit="MWh",
        floor_price=60.0,
    )
    return exposure, binding, scenarios, contract


def test_bound_market_risk_preserves_claim_and_market_quantities(policy_package):
    exposure, binding, scenarios, contract = _bound_case(policy_package)

    package = build_policy_bound_market_risk_package(
        exposure,
        binding,
        scenarios,
        contract,
    )

    assert package["schema"] == POLICY_BOUND_MARKET_RISK_SCHEMA
    assert package["admitted_claim"]["quantity"] == 1000.0
    assert package["admitted_claim"]["unit"] == "kWh-claim"
    assert package["market_binding"]["binding_id"] == binding.binding_id
    assert package["market_exposure"]["quantity"] == pytest.approx(1.0)
    assert package["market_exposure"]["unit"] == "MWh"
    assert package["contract"]["price_unit"] == "AUD/MWh"
    assert package["risk"]["quantity"] == pytest.approx(1.0)
    assert package["risk"]["scenarios"] == 4
    assert package["market"]["input"]["scenario_set_id"] == scenarios.scenario_set_id
    assert len(package["artifact_id"]) == 64
    assert len(package["package_content_id"]) == 64
    validate_policy_bound_market_risk_package(package)


def test_bound_market_risk_rejects_contract_unit_mismatch(policy_package):
    exposure, binding, scenarios, _ = _bound_case(policy_package)
    bad_contract = EnergyContract(
        "merchant",
        currency="AUD",
        quantity_unit="kWh-claim",
    )

    with pytest.raises(PolicyBoundMarketRiskError, match="contract quantity unit"):
        build_policy_bound_market_risk_package(
            exposure,
            binding,
            scenarios,
            bad_contract,
        )


def test_bound_market_risk_rejects_scenario_price_unit_mismatch(policy_package):
    exposure, binding, _, contract = _bound_case(policy_package)
    scenarios = build_market_price_scenarios(
        [10.0, 20.0],
        price_unit="USD/MWh",
        source="wrong-currency",
        observed_at_utc="2026-08-30T00:00:00Z",
        model_id="historical-replay",
    )

    with pytest.raises(PolicyBoundMarketRiskError, match="scenario-set price unit"):
        build_policy_bound_market_risk_package(
            exposure,
            binding,
            scenarios,
            contract,
        )


def test_bound_market_risk_detects_binding_mutation(policy_package):
    exposure, binding, scenarios, contract = _bound_case(policy_package)
    package = build_policy_bound_market_risk_package(
        exposure,
        binding,
        scenarios,
        contract,
    )
    mutated = copy.deepcopy(package)
    mutated["market_binding"]["reference"] = "silently changed reference"

    with pytest.raises(PolicyBoundMarketRiskError, match="binding_id"):
        validate_policy_bound_market_risk_package(mutated)


def test_bound_market_risk_detects_market_exposure_mutation(policy_package):
    exposure, binding, scenarios, contract = _bound_case(policy_package)
    package = build_policy_bound_market_risk_package(
        exposure,
        binding,
        scenarios,
        contract,
    )
    mutated = copy.deepcopy(package)
    mutated["market_exposure"]["quantity"] = 2.0

    with pytest.raises(PolicyBoundMarketRiskError, match="market exposure"):
        validate_policy_bound_market_risk_package(mutated)
