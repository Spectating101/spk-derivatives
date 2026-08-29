import copy

import pytest

from spk_derivatives.artifacts import (
    PricingArtifactError,
    build_policy_pricing_package,
    compute_artifact_id,
    compute_package_content_id,
    sha256_hex,
    stable_json_dumps,
    validate_pricing_result_package,
    write_pricing_result_package,
)
from spk_derivatives.policy_lab import extract_admitted_exposure, price_admitted_exposure


def _priced_package(policy_package, *, sigma=0.20, warnings=()):
    exposure = extract_admitted_exposure(policy_package)
    priced = price_admitted_exposure(
        exposure,
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=sigma,
        method="binomial",
        steps=200,
    )
    return build_policy_pricing_package(
        exposure,
        priced,
        S0=100.0,
        K=100.0,
        T=1.0,
        r=0.05,
        sigma=sigma,
        steps=200,
        assumptions=["Risk-neutral valuation", "Declared spot/strike share the claim unit"],
        warnings=warnings,
    )


def test_canonical_json_and_hash_ignore_mapping_key_order():
    left = {"b": 2, "nested": {"z": 1, "a": 3}, "a": 1}
    right = {"a": 1, "nested": {"a": 3, "z": 1}, "b": 2}

    assert stable_json_dumps(left) == stable_json_dumps(right)
    assert sha256_hex(left) == sha256_hex(right)


def test_builds_and_verifies_deterministic_pricing_package(policy_package):
    first = _priced_package(policy_package)
    second = _priced_package(policy_package)

    assert validate_pricing_result_package(first)
    assert first["artifact_id"] == second["artifact_id"]
    assert first["package_content_id"] == second["package_content_id"]
    assert first["authority"]["assessment_id"] == policy_package["assessment_id"]
    assert first["valuation"]["total_value"] == pytest.approx(
        first["valuation"]["unit_price"] * first["exposure"]["admitted_quantity"]
    )


def test_semantic_identity_changes_when_model_input_changes(policy_package):
    baseline = _priced_package(policy_package, sigma=0.20)
    changed = _priced_package(policy_package, sigma=0.30)

    assert baseline["artifact_id"] != changed["artifact_id"]
    assert baseline["package_content_id"] != changed["package_content_id"]


def test_content_identity_can_change_without_semantic_pricing_identity(policy_package):
    baseline = _priced_package(policy_package)
    warned = _priced_package(policy_package, warnings=["External market quote is provisional"])

    assert baseline["artifact_id"] == warned["artifact_id"]
    assert baseline["package_content_id"] != warned["package_content_id"]


def test_tampering_is_detected_by_semantic_identity(policy_package):
    package = _priced_package(policy_package)
    tampered = copy.deepcopy(package)
    tampered["model"]["inputs"]["volatility"] = 0.99
    tampered["package_content_id"] = compute_package_content_id(tampered)

    with pytest.raises(PricingArtifactError, match="artifact_id"):
        validate_pricing_result_package(tampered)


def test_inconsistent_total_is_rejected_even_if_ids_are_recomputed(policy_package):
    package = _priced_package(policy_package)
    tampered = copy.deepcopy(package)
    tampered["valuation"]["total_value"] += 1.0
    tampered["artifact_id"] = compute_artifact_id(tampered)
    tampered["package_content_id"] = compute_package_content_id(tampered)

    with pytest.raises(PricingArtifactError, match="total_value is inconsistent"):
        validate_pricing_result_package(tampered)


def test_write_and_reload_round_trip(policy_package, tmp_path):
    package = _priced_package(policy_package)
    path = write_pricing_result_package(package, tmp_path / "pricing-result.json")

    assert path.exists()
    assert validate_pricing_result_package(path)
