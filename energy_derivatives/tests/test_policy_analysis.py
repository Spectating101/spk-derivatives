import copy

import pytest

from spk_derivatives.policy_analysis import (
    PolicyComparisonError,
    build_policy_comparison_package,
    compare_policy_outcomes,
    price_admitted_policies,
    validate_policy_comparison_package,
)


def _add_blocked_policy(package):
    blocked = copy.deepcopy(package["evaluations"][0])
    blocked["policy"] = {
        "id": "policy-blocked",
        "version": "2",
        "name": "Strict policy",
    }
    blocked["decision_id"] = "e" * 64
    blocked["external_reading"] = "BLOCKED_UNDER_POLICY"
    blocked["supported_quantity"] = None
    blocked["binding_calculators"] = []
    blocked["blocking_calculators"] = ["PROVENANCE_FLOOR"]
    blocked["rule_evaluations"] = [
        {
            "calculator_id": "PROVENANCE_FLOOR",
            "status": "BLOCK",
            "explanation": "L4 external corroboration is required.",
            "boundary": "Observed assurance is L2.",
            "warnings": [],
        }
    ]
    package["evaluations"].append(blocked)


def _add_second_admitted_policy(package):
    alternate = copy.deepcopy(package["evaluations"][0])
    alternate["policy"] = {
        "id": "policy-b",
        "version": "3",
        "name": "Pilot haircut policy",
    }
    alternate["decision_id"] = "f" * 64
    alternate["supported_quantity"]["value"] = 700.0
    alternate["binding_calculators"] = ["POLICY_HAIRCUT"]
    alternate["blocking_calculators"] = []
    alternate["rule_evaluations"] = [
        {
            "calculator_id": "POLICY_HAIRCUT",
            "status": "LIMIT",
            "explanation": "Policy admits 70% of evidence-backed capacity.",
            "boundary": "Haircut = 30%.",
            "warnings": [],
        }
    ]
    package["evaluations"].append(alternate)


def test_policy_comparison_preserves_blocked_outcome(policy_package):
    _add_blocked_policy(policy_package)

    outcomes = compare_policy_outcomes(policy_package)

    assert len(outcomes) == 2
    blocked = next(item for item in outcomes if item.policy_id == "policy-blocked")
    assert blocked.admitted is False
    assert blocked.supported_quantity is None
    assert blocked.blocking_calculators == ("PROVENANCE_FLOOR",)
    assert any("L4 external corroboration" in reason for reason in blocked.reasons)


def test_common_model_assumptions_expose_policy_quantity_sensitivity(policy_package):
    _add_second_admitted_policy(policy_package)

    priced = price_admitted_policies(
        policy_package,
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=0.20,
        method="binomial",
        steps=100,
    )

    assert len(priced) == 2
    by_policy = {item.policy_id: item for item in priced}
    assert by_policy["policy-a"].unit_price == pytest.approx(by_policy["policy-b"].unit_price)
    assert by_policy["policy-a"].total_value / by_policy["policy-b"].total_value == pytest.approx(
        1000.0 / 700.0
    )


def test_comparison_package_is_deterministic_and_excludes_blocked_from_pricing(policy_package):
    _add_second_admitted_policy(policy_package)
    _add_blocked_policy(policy_package)

    kwargs = dict(
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=0.20,
        method="binomial",
        steps=75,
        assumptions=["Common market assumptions across governance policies."],
    )
    first = build_policy_comparison_package(policy_package, **kwargs)
    second = build_policy_comparison_package(policy_package, **kwargs)

    assert first == second
    assert validate_policy_comparison_package(first)
    assert first["comparison"]["admitted_policy_count"] == 2
    assert first["comparison"]["blocked_policy_count"] == 1
    assert {item["policy_id"] for item in first["priced_outcomes"]} == {"policy-a", "policy-b"}


def test_comparison_package_detects_result_tampering(policy_package):
    _add_second_admitted_policy(policy_package)
    package = build_policy_comparison_package(
        policy_package,
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=0.20,
    )
    package["priced_outcomes"][0]["total_value"] += 1.0

    with pytest.raises(PolicyComparisonError, match="comparison_id"):
        validate_policy_comparison_package(package)


def test_non_admitted_policy_cannot_carry_supported_quantity(policy_package):
    policy_package["evaluations"][0]["external_reading"] = "BLOCKED_UNDER_POLICY"

    with pytest.raises(PolicyComparisonError, match="unexpectedly carries"):
        compare_policy_outcomes(policy_package)
