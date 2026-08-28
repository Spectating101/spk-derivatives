import copy

import pytest

from spk_derivatives.policy_lab import (
    PolicyLabPackageError,
    extract_admitted_exposure,
    price_admitted_exposure,
)


HASH_A = "a" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def test_extracts_policy_admitted_quantity_and_provenance(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    assert exposure.profile_id == "policylab.energy_linked_claim.v0"
    assert exposure.quantity == 1000.0
    assert exposure.unit == "kWh-claim"
    assert exposure.policy_id == "policy-a"
    assert exposure.assessment_id == HASH_A
    assert exposure.decision_id == HASH_D
    assert exposure.evidence_hash == HASH_C
    assert exposure.evidence_assurance == "L2"
    assert exposure.settlement_scenario_only is True
    assert "EVIDENCE_BACKED_CAPACITY" in exposure.binding_calculators
    assert any("SOURCE_SCOPE" in warning for warning in exposure.warnings)


def test_blocked_policy_never_becomes_exposure(policy_package):
    policy_package["evaluations"][0]["external_reading"] = "BLOCKED_UNDER_POLICY"
    policy_package["evaluations"][0]["supported_quantity"] = None

    with pytest.raises(PolicyLabPackageError, match="No admitted supported quantity"):
        extract_admitted_exposure(policy_package)


def test_multiple_admitted_policies_require_explicit_selection(policy_package):
    alternate = copy.deepcopy(policy_package["evaluations"][0])
    alternate["policy"]["id"] = "policy-b"
    alternate["policy"]["name"] = "Alternative policy"
    alternate["decision_id"] = "e" * 64
    alternate["supported_quantity"]["value"] = 800.0
    policy_package["evaluations"].append(alternate)

    with pytest.raises(PolicyLabPackageError, match="Multiple admitted policy"):
        extract_admitted_exposure(policy_package)

    exposure = extract_admitted_exposure(policy_package, policy_id="policy-b")
    assert exposure.policy_id == "policy-b"
    assert exposure.quantity == 800.0


def test_rejects_unknown_schema(policy_package):
    policy_package["schema"] = "policylab.claim_assessment_package.v999"

    with pytest.raises(PolicyLabPackageError, match="Unsupported Policy Lab schema"):
        extract_admitted_exposure(policy_package)


def test_rejects_unknown_profile(policy_package):
    policy_package["profile"]["id"] = "policylab.other.v0"

    with pytest.raises(PolicyLabPackageError, match="Unsupported Policy Lab profile"):
        extract_admitted_exposure(policy_package)


def test_rejects_malformed_upstream_identity(policy_package):
    policy_package["assessment_id"] = "not-a-hash"

    with pytest.raises(PolicyLabPackageError, match="assessment_id must be"):
        extract_admitted_exposure(policy_package)


def test_rejects_assurance_outside_policy_lab_scale(policy_package):
    policy_package["evidence"]["assurance"] = "L5"

    with pytest.raises(PolicyLabPackageError, match="assurance must be L0-L4"):
        extract_admitted_exposure(policy_package)


def test_rejects_profile_unit_mismatch(policy_package):
    policy_package["evaluations"][0]["supported_quantity"]["unit"] = "MWh-claim"

    with pytest.raises(PolicyLabPackageError, match="claim_unit"):
        extract_admitted_exposure(policy_package)


def test_binomial_pricing_scales_only_by_admitted_quantity(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    result = price_admitted_exposure(
        exposure,
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=0.20,
        method="binomial",
        steps=200,
    )

    assert result.unit_price > 0
    assert result.admitted_quantity == exposure.quantity
    assert result.total_value == pytest.approx(result.unit_price * exposure.quantity)
    assert result.assessment_id == exposure.assessment_id
    assert result.policy_id == exposure.policy_id
    assert result.evidence_hash == exposure.evidence_hash


def test_pricing_rejects_invalid_model_bounds(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    with pytest.raises(ValueError, match="T must be positive"):
        price_admitted_exposure(
            exposure,
            S0=100.0,
            K=100.0,
            T=0.0,
            r=0.05,
            sigma=0.20,
        )
