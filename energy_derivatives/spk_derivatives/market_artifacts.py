"""Deterministic artifacts for market-scenario and contract-risk results."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Sequence, Union

from .artifacts import SPK_CANONICALIZATION, sha256_hex
from .energy_contracts import EnergyContract
from .policy_lab import POLICY_LAB_PROFILE, POLICY_LAB_SCHEMA, PolicyLabExposure
from .scenario_risk import PolicySettlementDistribution


SPK_MARKET_RISK_SCHEMA = "spk_derivatives.market_risk_package.v0.1"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")

MARKET_RISK_NON_CLAIMS = (
    "This artifact holds the Policy Lab-admitted quantity fixed unless explicitly stated otherwise.",
    "Market/model sensitivity is not evidence uncertainty or governance-policy sensitivity.",
    "Historical calibration does not automatically define a risk-neutral pricing measure.",
    "Scenario distributions are not execution, liquidity, legal settlement, or regulatory authority.",
)


class MarketRiskArtifactError(ValueError):
    """Raised when a market-risk artifact is malformed or internally inconsistent."""


ArtifactSource = Union[Mapping[str, Any], str, Path]


def market_risk_identity_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema": package.get("schema"),
        "authority": package.get("authority"),
        "exposure": package.get("exposure"),
        "market": package.get("market"),
        "contract": package.get("contract"),
        "risk": package.get("risk"),
    }


def market_risk_content_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in package.items() if key != "package_content_id"}


def compute_market_risk_artifact_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(market_risk_identity_body(package))


def compute_market_risk_content_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(market_risk_content_body(package))


def _finite(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketRiskArtifactError(f"{context} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise MarketRiskArtifactError(f"{context} must be finite")
    return number


def _mapping(parent: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise MarketRiskArtifactError(f"Missing or invalid {context}.{key}")
    return value


def _string(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MarketRiskArtifactError(f"Missing or invalid {context}.{key}")
    return value


def _sha(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = _string(parent, key, context)
    if not _SHA256.fullmatch(value):
        raise MarketRiskArtifactError(f"{context}.{key} must be lowercase SHA-256 hex")
    return value


def build_market_risk_package(
    exposure: PolicyLabExposure,
    policy_distribution: PolicySettlementDistribution,
    contract: EnergyContract,
    *,
    market_input: Mapping[str, Any],
    scenario_model: Mapping[str, Any],
    warnings: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a deterministic result package around one market-scenario distribution."""
    for field in (
        "assessment_id",
        "package_content_id",
        "claim_id",
        "policy_id",
        "decision_id",
        "evidence_hash",
        "evidence_assurance",
    ):
        if getattr(policy_distribution, field) != getattr(exposure, field):
            raise MarketRiskArtifactError(
                f"policy distribution {field} does not match Policy Lab exposure"
            )
    distribution = policy_distribution.distribution
    if distribution.quantity != exposure.quantity or distribution.quantity_unit != exposure.unit:
        raise MarketRiskArtifactError("policy distribution quantity does not match exposure")
    if distribution.quantity_unit != contract.quantity_unit:
        raise MarketRiskArtifactError("contract quantity unit does not match exposure")
    if distribution.currency != contract.currency:
        raise MarketRiskArtifactError("contract currency does not match distribution")

    package: Dict[str, Any] = {
        "schema": SPK_MARKET_RISK_SCHEMA,
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
        "exposure": {
            "subject": exposure.subject,
            "admitted_quantity": float(exposure.quantity),
            "quantity_unit": exposure.unit,
            "period_utc": {
                "start": exposure.period_start_utc,
                "end": exposure.period_end_utc,
            },
        },
        "market": {
            "input": dict(market_input),
            "scenario_model": dict(scenario_model),
        },
        "contract": contract.to_dict(),
        "risk": distribution.to_dict(),
        "warnings": list(dict.fromkeys(str(item) for item in warnings)),
        "non_claims": list(MARKET_RISK_NON_CLAIMS),
        "verification": {
            "algorithm": "SHA-256",
            "canonicalization": SPK_CANONICALIZATION,
            "artifact_identity": "schema + authority + exposure + market + contract + risk",
            "package_content_identity": "all fields except package_content_id",
        },
    }
    package["artifact_id"] = compute_market_risk_artifact_id(package)
    package["package_content_id"] = compute_market_risk_content_id(package)
    validate_market_risk_package(package)
    return package


def load_market_risk_package(source: ArtifactSource) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MarketRiskArtifactError(f"Could not read market-risk package: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MarketRiskArtifactError(f"Market-risk package is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise MarketRiskArtifactError("Market-risk package must be a JSON object")
    return payload


def write_market_risk_package(package: Mapping[str, Any], path: Union[str, Path]) -> Path:
    validate_market_risk_package(package)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return target


def validate_market_risk_package(
    source: ArtifactSource,
    *,
    verify_identity: bool = True,
) -> bool:
    package = load_market_risk_package(source)
    if package.get("schema") != SPK_MARKET_RISK_SCHEMA:
        raise MarketRiskArtifactError(f"Unsupported market-risk schema: {package.get('schema')!r}")
    artifact_id = _sha(package, "artifact_id", "package")
    content_id = _sha(package, "package_content_id", "package")

    authority = _mapping(package, "authority", "package")
    if authority.get("kind") != "policy-lab-claim-assessment":
        raise MarketRiskArtifactError("package.authority.kind is unsupported")
    if authority.get("source_schema") != POLICY_LAB_SCHEMA:
        raise MarketRiskArtifactError("package.authority.source_schema is unsupported")
    if authority.get("profile_id") != POLICY_LAB_PROFILE:
        raise MarketRiskArtifactError("package.authority.profile_id is unsupported")
    _sha(authority, "assessment_id", "package.authority")
    _sha(authority, "source_package_content_id", "package.authority")
    _sha(authority, "decision_id", "package.authority")
    _sha(authority, "evidence_hash", "package.authority")
    _string(authority, "claim_id", "package.authority")
    _string(authority, "case_id", "package.authority")
    _string(authority, "policy_id", "package.authority")
    assurance = _string(authority, "evidence_assurance", "package.authority")
    if not re.fullmatch(r"L[0-4]", assurance):
        raise MarketRiskArtifactError("package.authority.evidence_assurance must be L0-L4")

    exposure = _mapping(package, "exposure", "package")
    quantity = _finite(exposure.get("admitted_quantity"), "package.exposure.admitted_quantity")
    if quantity < 0:
        raise MarketRiskArtifactError("package.exposure.admitted_quantity cannot be negative")
    quantity_unit = _string(exposure, "quantity_unit", "package.exposure")
    period = _mapping(exposure, "period_utc", "package.exposure")
    _string(period, "start", "package.exposure.period_utc")
    _string(period, "end", "package.exposure.period_utc")

    market = _mapping(package, "market", "package")
    if not isinstance(market.get("input"), Mapping):
        raise MarketRiskArtifactError("package.market.input must be an object")
    if not isinstance(market.get("scenario_model"), Mapping):
        raise MarketRiskArtifactError("package.market.scenario_model must be an object")

    contract = _mapping(package, "contract", "package")
    contract_quantity_unit = _string(contract, "quantity_unit", "package.contract")
    currency = _string(contract, "currency", "package.contract")
    price_unit = _string(contract, "price_unit", "package.contract")
    if contract_quantity_unit != quantity_unit:
        raise MarketRiskArtifactError("contract/exposure quantity units do not match")
    if price_unit != f"{currency}/{quantity_unit}":
        raise MarketRiskArtifactError("package.contract.price_unit is inconsistent")

    risk = _mapping(package, "risk", "package")
    if _string(risk, "quantity_unit", "package.risk") != quantity_unit:
        raise MarketRiskArtifactError("risk/exposure quantity units do not match")
    if _string(risk, "currency", "package.risk") != currency:
        raise MarketRiskArtifactError("risk/contract currencies do not match")
    risk_quantity = _finite(risk.get("quantity"), "package.risk.quantity")
    if not math.isclose(risk_quantity, quantity, rel_tol=1e-12, abs_tol=1e-12):
        raise MarketRiskArtifactError("risk quantity does not match admitted quantity")
    scenarios = risk.get("scenarios")
    if isinstance(scenarios, bool) or not isinstance(scenarios, int) or scenarios < 2:
        raise MarketRiskArtifactError("package.risk.scenarios must be an integer >= 2")
    for key in (
        "market_price_mean",
        "market_price_std",
        "contract_value_mean",
        "contract_value_std",
        "contract_value_p05",
        "contract_value_p50",
        "contract_value_p95",
        "market_value_mean",
        "protection_value_mean",
        "probability_negative_contract_value",
    ):
        _finite(risk.get(key), f"package.risk.{key}")
    probability = float(risk["probability_negative_contract_value"])
    if not 0.0 <= probability <= 1.0:
        raise MarketRiskArtifactError("negative-value probability must lie in [0, 1]")
    if not (
        float(risk["contract_value_p05"])
        <= float(risk["contract_value_p50"])
        <= float(risk["contract_value_p95"])
    ):
        raise MarketRiskArtifactError("risk quantiles are not ordered")
    expected_protection = float(risk["contract_value_mean"]) - float(risk["market_value_mean"])
    if not math.isclose(
        float(risk["protection_value_mean"]),
        expected_protection,
        rel_tol=1e-10,
        abs_tol=1e-10,
    ):
        raise MarketRiskArtifactError("protection_value_mean is inconsistent")

    warnings = package.get("warnings")
    non_claims = package.get("non_claims")
    if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
        raise MarketRiskArtifactError("package.warnings must be an array of strings")
    if not isinstance(non_claims, list) or any(not isinstance(item, str) for item in non_claims):
        raise MarketRiskArtifactError("package.non_claims must be an array of strings")

    if verify_identity:
        expected_artifact = compute_market_risk_artifact_id(package)
        expected_content = compute_market_risk_content_id(package)
        if artifact_id != expected_artifact:
            raise MarketRiskArtifactError("market-risk artifact_id does not match content")
        if content_id != expected_content:
            raise MarketRiskArtifactError("market-risk package_content_id does not match content")
    return True
