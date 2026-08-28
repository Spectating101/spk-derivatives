import copy

import pytest

from spk_derivatives.policy_lab import (
    PolicyLabPackageError,
    extract_admitted_exposure,
    price_admitted_exposure,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _package():
    return {
        "schema": "policylab.claim_assessment_package.v0.1",
        "assessment_id": HASH_A,
        "package_content_id": HASH_B,
        "claim": {
            "claim_id": "claim-1",
            "case_id": "case-1",
            "subject": "Example solar delivery",
            "request_mode": "MAXIMUM_SUPPORTABLE",
            "requested_quantity": None,
            "period": {
                "canonical_utc": {
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2026-01-31T23:59:59Z",
                }
            },
        },
        "evidence": {
            "assurance": "L2",
            "evidence_hash": HASH_C,
            "eligible_quantity": {
                "value": 1250.0,
                "unit": "kWh",
            },
            "warnings": [
                {"code": "SOURCE_SCOPE", "detail": "Synthetic test fixture"}
            ],
        },
        "evaluations": [
            {
                "policy": {
                    "id": "policy-a",
                    "version": "1",
                    "name": "Conservative policy",
                },
                "decision_id": HASH_D,
                "external_reading": "ADMITTED_WITH_LIMIT_UNDER_POLICY",
                "supported_quantity": {
                    "value": 1000.0,
                    "unit": "kWh-claim",
                },
                "binding_calculators": ["EVIDENCE_BACKED_CAPACITY"],
                "rule_evaluations": [
                    {
                        "calculator_id": "EVIDENCE_BACKED_CAPACITY",
                        "warnings": ["Capacity binds"],
                    }
                ],
            }
        ],
        "settlement": {"scenario_only": True},
    }


def test_extracts_policy_admitted_quantity_and_provenance():
    exposure = extract_admitted_exposure(_package())

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


def test_blocked_policy_never_becomes_exposure():
    package = _package()
    package["evaluations"][0]["external_reading"] = "BLOCKED_UNDER_POLICY"
    package["evaluations"][0]["supported_quantity"] = None

    with pytest.raises(PolicyLabPackageError, match="No admitted supported quantity"):
        extract_admitted_exposure(package)


def test_multiple_admitted_policies_require_explicit_selection():
    package = _package()
    alternate = copy.deepcopy(package["evaluations"][0])
    alternate["policy"]["id"] = "policy-b"
    alternate["policy"]["name"] = "Alternative policy"
    alternate["decision_id"] = "e" * 64
    alternate["supported_quantity"]["value"] = 800.0
    package["evaluations"].append(alternate)

    with pytest.raises(PolicyLabPackageError, match="Multiple admitted policy"):
        extract_admitted_exposure(package)

    exposure = extract_admitted_exposure(package, policy_id="policy-b")
    assert exposure.policy_id == "policy-b"
    assert exposure.quantity == 800.0


def test_rejects_unknown_schema():
    package = _package()
    package["schema"] = "policylab.claim_assessment_package.v999"

    with pytest.raises(PolicyLabPackageError, match="Unsupported Policy Lab schema"):
        extract_admitted_exposure(package)


def test_binomial_pricing_scales_only_by_admitted_quantity():
    exposure = extract_admitted_exposure(_package())

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
