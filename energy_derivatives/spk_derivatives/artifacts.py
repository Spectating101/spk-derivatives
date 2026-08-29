"""Deterministic, provenance-preserving SPK pricing artifacts.

The artifact layer borrows Policy Lab's strongest architectural property: a
human-readable result is not the authority surface. A machine-readable package
carries the exact upstream decision identity, the model inputs, the valuation,
and deterministic identities that make silent mutation detectable.

This module intentionally does not recompute Policy Lab identities. It verifies
their shape and retains them verbatim; Policy Lab remains authoritative for its
own canonicalization and governance semantics.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Optional, Sequence, Union

from .policy_lab import (
    POLICY_LAB_PROFILE,
    POLICY_LAB_SCHEMA,
    PolicyLabExposure,
    PolicyPricedExposure,
)


SPK_PRICING_PACKAGE_SCHEMA = "spk_derivatives.pricing_result_package.v0.1"
SPK_CANONICALIZATION = "python-json-sort-keys-compact-utf8-v0.1"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

DEFAULT_NON_CLAIMS = (
    "This artifact does not upgrade Policy Lab evidence assurance.",
    "This artifact does not create policy, legal, settlement, or market authority.",
    "This artifact is a quantitative model projection under declared assumptions.",
    "Liquidity, execution, counterparty, basis, and regulatory risks are not implied away.",
)


class PricingArtifactError(ValueError):
    """Raised when a pricing artifact is malformed, inconsistent, or mutated."""


ArtifactSource = Union[Mapping[str, Any], str, Path]


def stable_json_dumps(value: Any) -> str:
    """Serialize JSON deterministically for SPK-owned artifact identities.

    This is SPK's canonicalization contract, not a claim of byte-for-byte
    compatibility with Policy Lab's JavaScript canonicalizer for every numeric
    edge case. Upstream Policy Lab identities are therefore retained rather than
    recomputed here.
    """
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PricingArtifactError(f"Value is not canonical JSON: {exc}") from exc


def sha256_hex(value: Any) -> str:
    """Return SHA-256 over SPK canonical JSON."""
    canonical = stable_json_dumps(value).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _runtime_version() -> str:
    try:
        return package_version("spk-derivatives")
    except PackageNotFoundError:
        return "0.5.0"


def _require_mapping(parent: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise PricingArtifactError(f"Missing or invalid {context}.{key}")
    return value


def _require_string(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PricingArtifactError(f"Missing or invalid {context}.{key}")
    return value


def _require_sha256(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = _require_string(parent, key, context)
    if not SHA256_PATTERN.fullmatch(value):
        raise PricingArtifactError(f"{context}.{key} must be a lowercase SHA-256 hex string")
    return value


def _finite(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PricingArtifactError(f"{context} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise PricingArtifactError(f"{context} must be finite")
    return number


def pricing_identity_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the semantic identity body for one pricing conclusion.

    Warnings, explanatory non-claims, and packaging metadata are intentionally
    excluded. The artifact identity changes when authority, exposure, model
    assumptions, reproducibility controls, or valuation change.
    """
    return {
        "schema": package.get("schema"),
        "authority": package.get("authority"),
        "exposure": package.get("exposure"),
        "model": package.get("model"),
        "valuation": package.get("valuation"),
    }


def package_content_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    """Return all package content except the content identity itself."""
    return {key: value for key, value in package.items() if key != "package_content_id"}


def compute_artifact_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(pricing_identity_body(package))


def compute_package_content_id(package: Mapping[str, Any]) -> str:
    return sha256_hex(package_content_body(package))


def build_policy_pricing_package(
    exposure: PolicyLabExposure,
    priced: PolicyPricedExposure,
    *,
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    payoff_type: str = "call",
    steps: Optional[int] = None,
    num_simulations: Optional[int] = None,
    seed: Optional[int] = None,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one deterministic Policy Lab → SPK pricing result package."""
    if priced.assessment_id != exposure.assessment_id:
        raise PricingArtifactError("Pricing result assessment_id does not match exposure")
    if priced.package_content_id != exposure.package_content_id:
        raise PricingArtifactError("Pricing result Policy Lab package_content_id does not match exposure")
    if priced.claim_id != exposure.claim_id or priced.policy_id != exposure.policy_id:
        raise PricingArtifactError("Pricing result claim/policy identity does not match exposure")
    if priced.decision_id != exposure.decision_id or priced.evidence_hash != exposure.evidence_hash:
        raise PricingArtifactError("Pricing result decision/evidence identity does not match exposure")

    model_inputs = {
        "spot_per_quantity_unit": float(S0),
        "strike_per_quantity_unit": float(K),
        "maturity_years": float(T),
        "risk_free_rate": float(r),
        "volatility": float(sigma),
        "payoff_type": str(payoff_type),
    }
    reproducibility: Dict[str, Any] = {
        "spk_derivatives_version": _runtime_version(),
    }
    if priced.method == "binomial":
        reproducibility["steps"] = int(steps if steps is not None else 100)
    elif priced.method == "monte-carlo":
        reproducibility["num_simulations"] = int(
            num_simulations if num_simulations is not None else 10000
        )
        reproducibility["seed"] = seed
    else:
        raise PricingArtifactError(f"Unsupported pricing method: {priced.method}")

    package: Dict[str, Any] = {
        "schema": SPK_PRICING_PACKAGE_SCHEMA,
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
            "period_utc": {
                "start": exposure.period_start_utc,
                "end": exposure.period_end_utc,
            },
            "admitted_quantity": float(exposure.quantity),
            "quantity_unit": exposure.unit,
            "evidence_quantity": float(exposure.evidence_quantity),
            "evidence_unit": exposure.evidence_unit,
            "binding_calculators": list(exposure.binding_calculators),
            "settlement_scenario_only": exposure.settlement_scenario_only,
        },
        "model": {
            "engine": priced.method,
            "inputs": model_inputs,
            "reproducibility": reproducibility,
            "assumptions": [str(item) for item in assumptions],
        },
        "valuation": {
            "unit_price": float(priced.unit_price),
            "admitted_quantity": float(priced.admitted_quantity),
            "quantity_unit": priced.quantity_unit,
            "total_value": float(priced.total_value),
            "value_semantics": "model value = unit_price × Policy Lab admitted quantity",
        },
        "warnings": list(dict.fromkeys([*exposure.warnings, *map(str, warnings)])),
        "non_claims": list(DEFAULT_NON_CLAIMS),
        "verification": {
            "algorithm": "SHA-256",
            "canonicalization": SPK_CANONICALIZATION,
            "artifact_identity": "schema + authority + exposure + model + valuation",
            "package_content_identity": "all fields except package_content_id",
        },
    }

    package["artifact_id"] = compute_artifact_id(package)
    package["package_content_id"] = compute_package_content_id(package)
    validate_pricing_result_package(package)
    return package


def load_pricing_result_package(source: ArtifactSource) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PricingArtifactError(f"Could not read pricing package: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PricingArtifactError(f"Pricing package is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise PricingArtifactError("Pricing package must be a JSON object")
    return payload


def write_pricing_result_package(package: Mapping[str, Any], path: Union[str, Path]) -> Path:
    """Validate and write a canonical human-readable JSON artifact."""
    validate_pricing_result_package(package)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(package, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return target


def validate_pricing_result_package(
    source: ArtifactSource,
    *,
    verify_identity: bool = True,
) -> bool:
    """Fail closed on malformed or internally inconsistent pricing artifacts."""
    package = load_pricing_result_package(source)
    if package.get("schema") != SPK_PRICING_PACKAGE_SCHEMA:
        raise PricingArtifactError(
            f"Unsupported pricing package schema: {package.get('schema')!r}"
        )

    artifact_id = _require_sha256(package, "artifact_id", "package")
    package_content_id = _require_sha256(package, "package_content_id", "package")

    authority = _require_mapping(package, "authority", "package")
    if authority.get("kind") != "policy-lab-claim-assessment":
        raise PricingArtifactError("package.authority.kind is unsupported")
    if authority.get("source_schema") != POLICY_LAB_SCHEMA:
        raise PricingArtifactError("package.authority.source_schema is unsupported")
    if authority.get("profile_id") != POLICY_LAB_PROFILE:
        raise PricingArtifactError("package.authority.profile_id is unsupported")
    _require_sha256(authority, "assessment_id", "package.authority")
    _require_sha256(authority, "source_package_content_id", "package.authority")
    _require_sha256(authority, "decision_id", "package.authority")
    _require_sha256(authority, "evidence_hash", "package.authority")
    _require_string(authority, "claim_id", "package.authority")
    _require_string(authority, "case_id", "package.authority")
    _require_string(authority, "policy_id", "package.authority")
    assurance = _require_string(authority, "evidence_assurance", "package.authority")
    if not re.fullmatch(r"L[0-4]", assurance):
        raise PricingArtifactError("package.authority.evidence_assurance must be L0-L4")

    exposure = _require_mapping(package, "exposure", "package")
    quantity = _finite(exposure.get("admitted_quantity"), "package.exposure.admitted_quantity")
    if quantity < 0:
        raise PricingArtifactError("package.exposure.admitted_quantity cannot be negative")
    quantity_unit = _require_string(exposure, "quantity_unit", "package.exposure")
    evidence_quantity = _finite(
        exposure.get("evidence_quantity"), "package.exposure.evidence_quantity"
    )
    if evidence_quantity < 0:
        raise PricingArtifactError("package.exposure.evidence_quantity cannot be negative")
    _require_string(exposure, "evidence_unit", "package.exposure")
    period = _require_mapping(exposure, "period_utc", "package.exposure")
    _require_string(period, "start", "package.exposure.period_utc")
    _require_string(period, "end", "package.exposure.period_utc")
    binding = exposure.get("binding_calculators")
    if not isinstance(binding, list) or any(not isinstance(item, str) or not item for item in binding):
        raise PricingArtifactError("package.exposure.binding_calculators must be an array of strings")

    model = _require_mapping(package, "model", "package")
    engine = _require_string(model, "engine", "package.model")
    if engine not in {"binomial", "monte-carlo"}:
        raise PricingArtifactError("package.model.engine is unsupported")
    inputs = _require_mapping(model, "inputs", "package.model")
    spot = _finite(inputs.get("spot_per_quantity_unit"), "package.model.inputs.spot_per_quantity_unit")
    strike = _finite(
        inputs.get("strike_per_quantity_unit"), "package.model.inputs.strike_per_quantity_unit"
    )
    maturity = _finite(inputs.get("maturity_years"), "package.model.inputs.maturity_years")
    _finite(inputs.get("risk_free_rate"), "package.model.inputs.risk_free_rate")
    volatility = _finite(inputs.get("volatility"), "package.model.inputs.volatility")
    _require_string(inputs, "payoff_type", "package.model.inputs")
    if spot < 0 or strike < 0 or maturity <= 0 or volatility < 0:
        raise PricingArtifactError("Pricing inputs violate non-negative/positive model bounds")

    reproducibility = _require_mapping(model, "reproducibility", "package.model")
    _require_string(reproducibility, "spk_derivatives_version", "package.model.reproducibility")
    if engine == "binomial":
        steps = reproducibility.get("steps")
        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
            raise PricingArtifactError("Binomial reproducibility.steps must be a positive integer")
    else:
        simulations = reproducibility.get("num_simulations")
        if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 1:
            raise PricingArtifactError(
                "Monte-Carlo reproducibility.num_simulations must be a positive integer"
            )
        seed = reproducibility.get("seed")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise PricingArtifactError("Monte-Carlo reproducibility.seed must be an integer or null")

    assumptions = model.get("assumptions")
    if not isinstance(assumptions, list) or any(not isinstance(item, str) for item in assumptions):
        raise PricingArtifactError("package.model.assumptions must be an array of strings")

    valuation = _require_mapping(package, "valuation", "package")
    unit_price = _finite(valuation.get("unit_price"), "package.valuation.unit_price")
    valuation_quantity = _finite(
        valuation.get("admitted_quantity"), "package.valuation.admitted_quantity"
    )
    total_value = _finite(valuation.get("total_value"), "package.valuation.total_value")
    valuation_unit = _require_string(valuation, "quantity_unit", "package.valuation")
    if unit_price < 0 or valuation_quantity < 0 or total_value < 0:
        raise PricingArtifactError("Valuation amounts cannot be negative")
    if valuation_unit != quantity_unit or not math.isclose(
        valuation_quantity, quantity, rel_tol=0.0, abs_tol=1e-12
    ):
        raise PricingArtifactError("Valuation quantity must equal the admitted exposure")
    if not math.isclose(total_value, unit_price * quantity, rel_tol=1e-12, abs_tol=1e-12):
        raise PricingArtifactError("package.valuation.total_value is inconsistent")

    for key in ("warnings", "non_claims"):
        values = package.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise PricingArtifactError(f"package.{key} must be an array of strings")

    verification = _require_mapping(package, "verification", "package")
    if verification.get("algorithm") != "SHA-256":
        raise PricingArtifactError("package.verification.algorithm must be SHA-256")
    if verification.get("canonicalization") != SPK_CANONICALIZATION:
        raise PricingArtifactError("package.verification.canonicalization is unsupported")

    if verify_identity:
        expected_artifact_id = compute_artifact_id(package)
        if artifact_id != expected_artifact_id:
            raise PricingArtifactError("artifact_id does not match semantic pricing content")
        expected_content_id = compute_package_content_id(package)
        if package_content_id != expected_content_id:
            raise PricingArtifactError("package_content_id does not match package content")

    return True
