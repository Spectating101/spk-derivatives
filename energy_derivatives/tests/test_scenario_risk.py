import pytest

from spk_derivatives.energy_contracts import EnergyContract
from spk_derivatives.policy_lab import extract_admitted_exposure
from spk_derivatives.scenario_risk import (
    ScenarioRiskError,
    compare_market_model_scenarios,
    summarize_contract_distribution,
    summarize_policy_contract_distribution,
)


def test_fixed_price_distribution_holds_contract_value_constant():
    contract = EnergyContract(
        "fixed-price",
        currency="USD",
        quantity_unit="MWh",
        fixed_price=50.0,
    )
    result = summarize_contract_distribution(10.0, "MWh", [-20.0, 40.0, 100.0], contract)
    assert result.contract_value_mean == pytest.approx(500.0)
    assert result.contract_value_std == pytest.approx(0.0)
    assert result.market_value_mean == pytest.approx(400.0)
    assert result.protection_value_mean == pytest.approx(100.0)


def test_merchant_distribution_reports_negative_value_probability():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    result = summarize_contract_distribution(2.0, "MWh", [-10.0, 5.0, 15.0, -2.0], contract)
    assert result.probability_negative_contract_value == pytest.approx(0.5)


def test_policy_distribution_preserves_authority(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract("merchant", currency="USD", quantity_unit="kWh-claim")
    result = summarize_policy_contract_distribution(exposure, [0.08, 0.10, 0.12], contract)
    assert result.distribution.quantity == exposure.quantity
    assert result.assessment_id == exposure.assessment_id
    assert result.policy_id == exposure.policy_id
    assert result.decision_id == exposure.decision_id
    assert result.evidence_hash == exposure.evidence_hash


def test_market_model_comparison_is_explicit_model_sensitivity():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    comparison = compare_market_model_scenarios(
        10.0,
        "MWh",
        {
            "bachelier": [30.0, 40.0, 50.0, 60.0],
            "ou": [20.0, 30.0, 40.0, 50.0],
        },
        contract,
    )
    assert [item.model_id for item in comparison.outcomes] == ["bachelier", "ou"]
    assert comparison.expected_value_min == pytest.approx(350.0)
    assert comparison.expected_value_max == pytest.approx(450.0)
    assert comparison.expected_value_range == pytest.approx(100.0)
    assert "model sensitivity" in comparison.interpretation


def test_scenario_distribution_rejects_hidden_unit_conversion():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    with pytest.raises(ScenarioRiskError, match="unit mismatch"):
        summarize_contract_distribution(1000.0, "kWh", [40.0, 50.0], contract)
