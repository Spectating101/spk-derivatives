import pytest

from spk_derivatives.energy_contracts import EnergyContract
from spk_derivatives.joint_risk import (
    JointRiskError,
    summarize_joint_exposure,
    summarize_policy_joint_exposure,
)
from spk_derivatives.policy_lab import extract_admitted_exposure


def test_joint_volume_price_distribution_preserves_pairing():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    result = summarize_joint_exposure(
        [10.0, 20.0, 30.0, 40.0],
        "MWh",
        [80.0, 60.0, 40.0, 20.0],
        contract,
        authority_cap=50.0,
    )
    assert result.quantity_price_correlation == pytest.approx(-1.0)
    assert result.cap_utilization_mean == pytest.approx(0.5)
    assert result.merchant_value_mean == pytest.approx((800 + 1200 + 1200 + 800) / 4)


def test_policy_joint_scenarios_cannot_exceed_admitted_quantity(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract("merchant", currency="USD", quantity_unit="kWh-claim")
    with pytest.raises(JointRiskError, match="authority cap"):
        summarize_policy_joint_exposure(
            exposure,
            [500.0, 1001.0],
            [0.10, 0.12],
            contract,
        )


def test_policy_joint_distribution_retains_authority(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    contract = EnergyContract(
        "floor",
        currency="USD",
        quantity_unit="kWh-claim",
        floor_price=0.10,
    )
    result = summarize_policy_joint_exposure(
        exposure,
        [800.0, 900.0, 1000.0],
        [0.05, 0.10, 0.15],
        contract,
    )
    assert result.distribution.authority_cap == exposure.quantity
    assert result.assessment_id == exposure.assessment_id
    assert result.policy_id == exposure.policy_id
    assert result.evidence_hash == exposure.evidence_hash


def test_joint_scenarios_require_equal_lengths():
    contract = EnergyContract("merchant", currency="USD", quantity_unit="MWh")
    with pytest.raises(JointRiskError, match="equal length"):
        summarize_joint_exposure([1.0, 2.0], "MWh", [3.0, 4.0, 5.0], contract)
