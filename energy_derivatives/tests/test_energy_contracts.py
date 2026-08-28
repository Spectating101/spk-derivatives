import pytest

from spk_derivatives.energy_contracts import (
    EnergyContract,
    EnergyContractError,
    settle_energy_contract,
    settle_policy_exposure,
)
from spk_derivatives.policy_lab import extract_admitted_exposure


def test_fixed_price_contract_keeps_quantity_and_price_separate():
    contract = EnergyContract(
        "fixed-price",
        currency="CNY",
        quantity_unit="MWh",
        fixed_price=380.0,
    )
    result = settle_energy_contract(100.0, "MWh", 420.0, contract)
    assert result.market_value == pytest.approx(42_000.0)
    assert result.contract_value == pytest.approx(38_000.0)
    assert result.value_difference == pytest.approx(-4_000.0)
    assert result.price_unit == "CNY/MWh"


def test_floor_handles_negative_market_price():
    contract = EnergyContract(
        "floor",
        currency="CNY",
        quantity_unit="MWh",
        floor_price=0.0,
    )
    result = settle_energy_contract(10.0, "MWh", -20.0, contract)
    assert result.market_value == pytest.approx(-200.0)
    assert result.contract_value == pytest.approx(0.0)
    assert result.value_difference == pytest.approx(200.0)


def test_collar_clamps_market_price():
    contract = EnergyContract(
        "collar",
        currency="USD",
        quantity_unit="MWh",
        floor_price=35.0,
        cap_price=80.0,
    )
    assert settle_energy_contract(1.0, "MWh", 20.0, contract).settled_price == 35.0
    assert settle_energy_contract(1.0, "MWh", 60.0, contract).settled_price == 60.0
    assert settle_energy_contract(1.0, "MWh", 120.0, contract).settled_price == 80.0


def test_contract_rejects_unit_mismatch():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    with pytest.raises(EnergyContractError, match="unit mismatch"):
        settle_energy_contract(10.0, "kWh", 50.0, contract)


def test_policy_settlement_preserves_authority_identity(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract(
        "fixed-price",
        currency="USD",
        quantity_unit="kWh-claim",
        fixed_price=0.12,
    )
    result = settle_policy_exposure(exposure, 0.15, contract)
    assert result.settlement.quantity == 1000.0
    assert result.settlement.contract_value == pytest.approx(120.0)
    assert result.assessment_id == exposure.assessment_id
    assert result.decision_id == exposure.decision_id
    assert result.evidence_hash == exposure.evidence_hash


def test_invalid_collar_is_rejected():
    with pytest.raises(EnergyContractError, match="cannot exceed"):
        EnergyContract(
            "collar",
            currency="USD",
            quantity_unit="MWh",
            floor_price=80.0,
            cap_price=35.0,
        )
