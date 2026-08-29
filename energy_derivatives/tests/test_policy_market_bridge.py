import json
from dataclasses import replace
from pathlib import Path

import pytest

from spk_derivatives.policy_lab import extract_admitted_exposure
from spk_derivatives.policy_market_bridge import (
    BASIS_DECLARED_SEMANTIC,
    BASIS_EXACT_SI,
    POLICY_LAB_PINNED_COMMIT,
    POLICY_LAB_PINNED_SCHEMA_BLOB,
    POLICY_MARKET_BINDING_SCHEMA,
    PolicyMarketBridgeError,
    build_policy_market_binding,
    validate_policy_market_binding,
)


def test_declared_semantic_mapping_is_explicit_and_deterministic(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    binding = build_policy_market_binding(
        exposure,
        market_quantity_unit="MWh",
        basis_kind=BASIS_DECLARED_SEMANTIC,
        factor=0.001,
        authority="Research scenario convention",
        reference="unit-test mapping v1",
        semantics="For this scenario only, one kWh-claim maps to 0.001 MWh market quantity.",
    )
    repeated = build_policy_market_binding(
        exposure,
        market_quantity_unit="MWh",
        basis_kind=BASIS_DECLARED_SEMANTIC,
        factor=0.001,
        authority="Research scenario convention",
        reference="unit-test mapping v1",
        semantics="For this scenario only, one kWh-claim maps to 0.001 MWh market quantity.",
    )

    assert binding.schema == POLICY_MARKET_BINDING_SCHEMA
    assert binding.claim_unit == "kWh-claim"
    assert binding.market_quantity_unit == "MWh"
    assert binding.market_quantity == pytest.approx(1.0)
    assert binding.binding_id == repeated.binding_id
    assert binding.assessment_id == exposure.assessment_id
    assert binding.policy_id == exposure.policy_id
    assert binding.decision_id == exposure.decision_id
    validate_policy_market_binding(binding)


def test_semantic_claim_unit_cannot_use_exact_si_shortcut(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    with pytest.raises(PolicyMarketBridgeError, match="semantic claim units"):
        build_policy_market_binding(
            exposure,
            market_quantity_unit="MWh",
            basis_kind=BASIS_EXACT_SI,
        )


def test_exact_si_binding_works_only_for_literal_physical_energy(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    physical = replace(exposure, quantity=1000.0, unit="kWh")

    binding = build_policy_market_binding(
        physical,
        market_quantity_unit="MWh",
        basis_kind=BASIS_EXACT_SI,
    )

    assert binding.factor == pytest.approx(0.001)
    assert binding.market_quantity == pytest.approx(1.0)
    assert binding.authority == "SI decimal-prefix definition"
    validate_policy_market_binding(binding)


def test_declared_mapping_requires_named_basis(policy_package):
    exposure = extract_admitted_exposure(policy_package)

    with pytest.raises(PolicyMarketBridgeError, match="authority"):
        build_policy_market_binding(
            exposure,
            market_quantity_unit="MWh",
            basis_kind=BASIS_DECLARED_SEMANTIC,
            factor=0.001,
            reference="some reference",
            semantics="Some mapping",
        )


def test_binding_detects_quantity_or_identity_mutation(policy_package):
    exposure = extract_admitted_exposure(policy_package)
    binding = build_policy_market_binding(
        exposure,
        market_quantity_unit="MWh",
        basis_kind=BASIS_DECLARED_SEMANTIC,
        factor=0.001,
        authority="Research scenario convention",
        reference="unit-test mapping v1",
        semantics="Explicit scenario-only mapping.",
    )

    with pytest.raises(PolicyMarketBridgeError, match="market_quantity"):
        validate_policy_market_binding(replace(binding, market_quantity=2.0))

    with pytest.raises(PolicyMarketBridgeError, match="binding_id"):
        validate_policy_market_binding(replace(binding, reference="mutated reference"))


def test_policy_lab_compatibility_manifest_pins_upstream_contract():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "POLICY_LAB_COMPATIBILITY.json").read_text(encoding="utf-8"))

    assert manifest["schema"] == "spk_derivatives.policy_lab_compatibility.v0.1"
    assert manifest["upstream"]["commit"] == POLICY_LAB_PINNED_COMMIT
    assert manifest["upstream"]["schema_git_blob_sha"] == POLICY_LAB_PINNED_SCHEMA_BLOB
    assert manifest["upstream"]["schema"] == "policylab.claim_assessment_package.v0.1"
    assert manifest["upstream"]["profile"] == "policylab.energy_linked_claim.v0"
    assert "BLOCKED_UNDER_POLICY" in manifest["blocked_external_readings"]
    assert any("semantic claim unit" in rule for rule in manifest["consumer_rules"])
