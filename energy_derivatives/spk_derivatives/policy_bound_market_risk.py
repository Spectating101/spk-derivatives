"""Market-risk artifacts that preserve an explicit Policy Lab-to-market binding.

The existing ``market_risk_package.v0.1`` deliberately assumes the market
quantity unit is exactly the Policy Lab admitted unit. This module covers the
more realistic case where Policy Lab admits a semantic claim quantity while the
market is quoted in a different physical/settlement unit.

The required bridge is ``PolicyMarketBinding``. SPK will not construct this
artifact by silently converting or reinterpreting the upstream claim unit.
"""

from __future__ import annotations

from dataclasses import fields
import json
import math
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Sequence, Union

from .artifacts import SPK_CANONICALIZATION, sha256_hex
from .energy_contracts import EnergyContract
from .policy_lab import POLICY_LAB_PROFILE, POLICY_LAB_SCHEMA, PolicyLabExposure
from .policy_market_bridge import (
    POLICY_MARKET_BINDING_SCHEMA,
    PolicyMarketBinding,
    PolicyMarketBridgeError,
    validate_policy_market_binding,
)
from .scenario_risk import summarize_contract_distribution
from .scenario_set import SCENARIO_SET_SCHEMA, ScenarioSet, validate_scenario_set


POLICY_BOUND_MARKET_RISK_SCHEMA = "spk_derivatives.policy_bound_market_risk_package.v0.1"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")

POLICY_BOUND_MARKET_RISK_NON_CLAIMS = (
    "The Policy Lab decision remains the authority for admitted claim quantity only.",
    "The policy-market binding is a separate downstream declaration and does not upgrade upstream authority.",
    "A deterministic mapping identity does not establish legal or empirical equivalence between claim and market units.",
    "Scenario distributions are not execution, liquidity, legal settlement, issuance, redemption, or regulatory authority.",
)


class PolicyBoundMarketRiskError(ValueError):
    """Raised when a bound market-risk package is inconsistent or mutated."""


PackageSource = Union[Mapping[str, Any], str, Path]


def policy_bound_market_risk_identity_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema": package.get("schema"),
        "authority": package.get("authority"),
        "admitted_claim": package.get("admitted_claim"),
        "market_binding": package.get("market_binding"),
        "market_exposure": package.get("market_exposure"),
        "market": package.get("market"),
        "contract": package.get("contract"),
        "risk": package.get("risk"),
    }


def policy_bound_market_risk_content_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in package.items() if key != "package_content_id"}


def compute_policy_bound_market_risk_artifact_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(policy_bound_market_risk_identity_body(package))


def compute_policy_bound_market_risk_content_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(policy_bound_market_risk_content_body(package))


def _binding_matches_exposure(exposure: PolicyLabExposure, binding: PolicyMarketBinding) -> None:
    checks = {
        "assessment_id": (exposure.assessment_id, binding.assessment_id),
        "source_package_content_id": (exposure.package_content_id, binding.source_package_content_id),
        "claim_id": (exposure.claim_id, binding.claim_id),
        "policy_id": (exposure.policy_id, binding.policy_id),
        "decision_id": (exposure.decision_id, binding.decision_id),
        "evidence_hash": (exposure.evidence_hash, binding.evidence_hash),
        "evidence_assurance": (exposure.evidence_assurance, binding.evidence_assurance),
        "claim_unit": (exposure.unit, binding.claim_unit),
        "period_start_utc": (exposure.period_start_utc, binding.period_start_utc),
        "period_end_utc": (exposure.period_end_utc, binding.period_end_utc),
    }
    for name, (expected, actual) in checks.items():
        if expected != actual:
            raise PolicyBoundMarketRiskError(f"binding {name} does not match Policy Lab exposure")
    if not math.isclose(
        float(exposure.quantity), float(binding.admitted_quantity), rel_tol=1e-12, abs_tol=1e-12
    ):
        raise PolicyBoundMarketRiskError("binding admitted_quantity does not match Policy Lab exposure")


def build_policy_bound_market_risk_package(
    exposure: PolicyLabExposure,
    binding: PolicyMarketBinding,
    scenario_set: ScenarioSet,
    contract: EnergyContract,
    *,
    warnings: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build risk output over the explicitly mapped market quantity."""
    try:
        validate_policy_market_binding(binding)
    except PolicyMarketBridgeError as exc:
        raise PolicyBoundMarketRiskError(str(exc)) from exc
    _binding_matches_exposure(exposure, binding)
    validate_scenario_set(scenario_set)
    if scenario_set.normalized_kind != "market-price":
        raise PolicyBoundMarketRiskError("policy-bound market risk requires market-price scenarios")
    if contract.quantity_unit != binding.market_quantity_unit:
        raise PolicyBoundMarketRiskError("contract quantity unit does not match bound market quantity")
    if scenario_set.price_unit != contract.price_unit:
        raise PolicyBoundMarketRiskError("scenario-set price unit does not match contract price unit")

    distribution = summarize_contract_distribution(
        binding.market_quantity,
        binding.market_quantity_unit,
        scenario_set.market_prices,
        contract,
    )
    scenario_payload = scenario_set.to_dict()
    package: Dict[str, Any] = {
        "schema": POLICY_BOUND_MARKET_RISK_SCHEMA,
        "artifact_id": "",
        "package_content_id": "",
        "authority": {
            "kind": "policy-lab-claim-assessment",
            "source_schema": exposure.schema,
            "profile_id": exposure.profile_id,
            "assessment_id": exposure.assessment_id,
            "source_package_content_id": exposure.package_content_id,
            "claim_id": exposure.claim_id,
            "case_id": exposure.case_id,
            "policy_id": exposure.policy_id,
            "policy_version": exposure.policy_version,
            "decision_id": exposure.decision_id,
            "external_reading": exposure.external_reading,
            "evidence_hash": exposure.evidence_hash,
            "evidence_assurance": exposure.evidence_assurance,
        },
        "admitted_claim": {
            "subject": exposure.subject,
            "quantity": float(exposure.quantity),
            "unit": exposure.unit,
            "period_utc": {
                "start": exposure.period_start_utc,
                "end": exposure.period_end_utc,
            },
        },
        "market_binding": binding.to_dict(),
        "market_exposure": {
            "quantity": float(binding.market_quantity),
            "unit": binding.market_quantity_unit,
        },
        "market": {
            "input": {
                "kind": "scenario-set",
                "schema": SCENARIO_SET_SCHEMA,
                "scenario_set_id": scenario_set.scenario_set_id,
                "source": scenario_set.source,
                "source_hash": scenario_set.source_hash,
                "observed_at_utc": scenario_set.observed_at_utc,
                "price_unit": scenario_set.price_unit,
            },
            "scenario_model": {
                "id": scenario_set.model_id,
                "parameters": dict(scenario_set.model_parameters),
                "seed": scenario_set.seed,
                "scenario_count": scenario_payload["scenario_count"],
            },
        },
        "contract": contract.to_dict(),
        "risk": distribution.to_dict(),
        "warnings": list(dict.fromkeys(str(item) for item in warnings)),
        "non_claims": list(POLICY_BOUND_MARKET_RISK_NON_CLAIMS),
        "verification": {
            "algorithm": "SHA-256",
            "canonicalization": SPK_CANONICALIZATION,
            "artifact_identity": (
                "schema + Policy Lab authority + admitted claim + policy-market binding + "
                "market exposure + scenario identity + contract + risk"
            ),
            "package_content_identity": "all fields except package_content_id",
        },
    }
    package["artifact_id"] = compute_policy_bound_market_risk_artifact_id(package)
    package["package_content_id"] = compute_policy_bound_market_risk_content_id(package)
    validate_policy_bound_market_risk_package(package)
    return package


def _load(source: PackageSource) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PolicyBoundMarketRiskError(f"Could not read bound market-risk package: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyBoundMarketRiskError(f"Bound market-risk package is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise PolicyBoundMarketRiskError("Bound market-risk package must be a JSON object")
    return payload


def _binding_from_mapping(payload: Mapping[str, Any]) -> PolicyMarketBinding:
    expected = {field.name for field in fields(PolicyMarketBinding)}
    if set(payload) != expected:
        missing = sorted(expected - set(payload))
        extra = sorted(set(payload) - expected)
        raise PolicyBoundMarketRiskError(
            f"market_binding fields do not match contract; missing={missing}, extra={extra}"
        )
    values = dict(payload)
    non_claims = values.get("non_claims")
    if not isinstance(non_claims, list) or any(not isinstance(item, str) for item in non_claims):
        raise PolicyBoundMarketRiskError("market_binding.non_claims must be an array of strings")
    values["non_claims"] = tuple(non_claims)
    try:
        return PolicyMarketBinding(**values)
    except (TypeError, ValueError) as exc:
        raise PolicyBoundMarketRiskError(f"invalid market_binding: {exc}") from exc


def _require_mapping(parent: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise PolicyBoundMarketRiskError(f"Missing or invalid {context}.{key}")
    return value


def _require_string(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PolicyBoundMarketRiskError(f"Missing or invalid {context}.{key}")
    return value


def _require_sha(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = _require_string(parent, key, context)
    if not _SHA256.fullmatch(value):
        raise PolicyBoundMarketRiskError(f"{context}.{key} must be lowercase SHA-256 hex")
    return value


def _finite(parent: Mapping[str, Any], key: str, context: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyBoundMarketRiskError(f"{context}.{key} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise PolicyBoundMarketRiskError(f"{context}.{key} must be finite")
    return number


def validate_policy_bound_market_risk_package(
    source: PackageSource,
    *,
    verify_identity: bool = True,
) -> bool:
    package = _load(source)
    if package.get("schema") != POLICY_BOUND_MARKET_RISK_SCHEMA:
        raise PolicyBoundMarketRiskError(f"unsupported schema: {package.get('schema')!r}")
    artifact_id = _require_sha(package, "artifact_id", "package")
    content_id = _require_sha(package, "package_content_id", "package")

    authority = _require_mapping(package, "authority", "package")
    if authority.get("kind") != "policy-lab-claim-assessment":
        raise PolicyBoundMarketRiskError("package.authority.kind is unsupported")
    if authority.get("source_schema") != POLICY_LAB_SCHEMA:
        raise PolicyBoundMarketRiskError("package.authority.source_schema is unsupported")
    if authority.get("profile_id") != POLICY_LAB_PROFILE:
        raise PolicyBoundMarketRiskError("package.authority.profile_id is unsupported")
    for key in ("assessment_id", "source_package_content_id", "decision_id", "evidence_hash"):
        _require_sha(authority, key, "package.authority")
    for key in ("claim_id", "case_id", "policy_id", "evidence_assurance"):
        _require_string(authority, key, "package.authority")

    admitted = _require_mapping(package, "admitted_claim", "package")
    admitted_quantity = _finite(admitted, "quantity", "package.admitted_claim")
    admitted_unit = _require_string(admitted, "unit", "package.admitted_claim")
    if admitted_quantity < 0:
        raise PolicyBoundMarketRiskError("admitted claim quantity cannot be negative")

    binding_payload = _require_mapping(package, "market_binding", "package")
    binding = _binding_from_mapping(binding_payload)
    try:
        validate_policy_market_binding(binding)
    except PolicyMarketBridgeError as exc:
        raise PolicyBoundMarketRiskError(str(exc)) from exc
    if binding.schema != POLICY_MARKET_BINDING_SCHEMA:
        raise PolicyBoundMarketRiskError("unsupported policy-market binding schema")

    identity_pairs = {
        "assessment_id": (authority["assessment_id"], binding.assessment_id),
        "source_package_content_id": (
            authority["source_package_content_id"],
            binding.source_package_content_id,
        ),
        "claim_id": (authority["claim_id"], binding.claim_id),
        "policy_id": (authority["policy_id"], binding.policy_id),
        "decision_id": (authority["decision_id"], binding.decision_id),
        "evidence_hash": (authority["evidence_hash"], binding.evidence_hash),
        "evidence_assurance": (authority["evidence_assurance"], binding.evidence_assurance),
    }
    for name, (left, right) in identity_pairs.items():
        if left != right:
            raise PolicyBoundMarketRiskError(f"authority/binding {name} mismatch")
    if admitted_unit != binding.claim_unit or not math.isclose(
        admitted_quantity, float(binding.admitted_quantity), rel_tol=1e-12, abs_tol=1e-12
    ):
        raise PolicyBoundMarketRiskError("admitted claim does not match policy-market binding")

    market_exposure = _require_mapping(package, "market_exposure", "package")
    market_quantity = _finite(market_exposure, "quantity", "package.market_exposure")
    market_unit = _require_string(market_exposure, "unit", "package.market_exposure")
    if market_unit != binding.market_quantity_unit or not math.isclose(
        market_quantity, float(binding.market_quantity), rel_tol=1e-12, abs_tol=1e-12
    ):
        raise PolicyBoundMarketRiskError("market exposure does not match policy-market binding")

    market = _require_mapping(package, "market", "package")
    market_input = _require_mapping(market, "input", "package.market")
    if market_input.get("kind") != "scenario-set":
        raise PolicyBoundMarketRiskError("package.market.input.kind must be scenario-set")
    if market_input.get("schema") != SCENARIO_SET_SCHEMA:
        raise PolicyBoundMarketRiskError("package.market.input.schema is unsupported")
    _require_sha(market_input, "scenario_set_id", "package.market.input")
    price_unit = _require_string(market_input, "price_unit", "package.market.input")
    scenario_model = _require_mapping(market, "scenario_model", "package.market")
    scenario_count = scenario_model.get("scenario_count")
    if isinstance(scenario_count, bool) or not isinstance(scenario_count, int) or scenario_count < 2:
        raise PolicyBoundMarketRiskError("scenario_count must be an integer >= 2")

    contract = _require_mapping(package, "contract", "package")
    contract_unit = _require_string(contract, "quantity_unit", "package.contract")
    contract_currency = _require_string(contract, "currency", "package.contract")
    contract_price_unit = _require_string(contract, "price_unit", "package.contract")
    if contract_unit != market_unit:
        raise PolicyBoundMarketRiskError("contract quantity unit does not match market exposure")
    if contract_price_unit != f"{contract_currency}/{market_unit}":
        raise PolicyBoundMarketRiskError("contract price unit is inconsistent")
    if price_unit != contract_price_unit:
        raise PolicyBoundMarketRiskError("scenario-set price unit does not match contract")

    risk = _require_mapping(package, "risk", "package")
    risk_quantity = _finite(risk, "quantity", "package.risk")
    risk_unit = _require_string(risk, "quantity_unit", "package.risk")
    risk_currency = _require_string(risk, "currency", "package.risk")
    risk_scenarios = risk.get("scenarios")
    if risk_unit != market_unit or risk_currency != contract_currency:
        raise PolicyBoundMarketRiskError("risk unit/currency does not match market exposure/contract")
    if not math.isclose(risk_quantity, market_quantity, rel_tol=1e-12, abs_tol=1e-12):
        raise PolicyBoundMarketRiskError("risk quantity does not match market exposure")
    if risk_scenarios != scenario_count:
        raise PolicyBoundMarketRiskError("risk scenario count does not match scenario model")

    warnings = package.get("warnings")
    non_claims = package.get("non_claims")
    if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
        raise PolicyBoundMarketRiskError("package.warnings must be an array of strings")
    if not isinstance(non_claims, list) or any(not isinstance(item, str) for item in non_claims):
        raise PolicyBoundMarketRiskError("package.non_claims must be an array of strings")

    if verify_identity:
        if artifact_id != compute_policy_bound_market_risk_artifact_id(package):
            raise PolicyBoundMarketRiskError("artifact_id does not match package contents")
        if content_id != compute_policy_bound_market_risk_content_id(package):
            raise PolicyBoundMarketRiskError("package_content_id does not match package contents")
    return True


def write_policy_bound_market_risk_package(
    package: Mapping[str, Any], path: Union[str, Path]
) -> Path:
    validate_policy_bound_market_risk_package(package)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return target
