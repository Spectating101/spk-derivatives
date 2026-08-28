"""Bridge Policy Lab claim assessments into SPK Derivatives.

Policy Lab is the authority/admissibility layer. This module deliberately does
not re-evaluate evidence or policy. It consumes a machine-readable
``policylab.claim_assessment_package.v0.1`` artifact and exposes only quantities
that Policy Lab has already admitted under a named policy.

The bridge fails closed on the subset of the upstream contract that SPK actually
consumes: schema/profile identity, cryptographic identifiers, assurance level,
unit mapping, policy selection, and admitted quantity. Full canonical package
production and governance validation remain Policy Lab responsibilities.
"""

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Optional, Tuple, Union


POLICY_LAB_SCHEMA = "policylab.claim_assessment_package.v0.1"
POLICY_LAB_PROFILE = "policylab.energy_linked_claim.v0"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ASSURANCE_PATTERN = re.compile(r"^L[0-4]$")
ADMITTED_READINGS = {
    "ADMITTED_WITH_LIMIT_UNDER_POLICY",
    "ADMITTED_UNDER_POLICY",
}


class PolicyLabPackageError(ValueError):
    """Raised when a Policy Lab package cannot be used safely downstream."""


@dataclass(frozen=True)
class PolicyLabExposure:
    """An exposure quantity already admitted by Policy Lab."""

    schema: str
    profile_id: str
    assessment_id: str
    package_content_id: str
    claim_id: str
    case_id: str
    subject: str
    request_mode: str
    requested_quantity: Optional[float]
    period_start_utc: str
    period_end_utc: str
    policy_id: str
    policy_version: Optional[str]
    policy_name: str
    decision_id: str
    external_reading: str
    quantity: float
    unit: str
    evidence_assurance: str
    evidence_hash: str
    evidence_quantity: float
    evidence_unit: str
    binding_calculators: Tuple[str, ...]
    warnings: Tuple[str, ...]
    settlement_scenario_only: Optional[bool]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        value = asdict(self)
        value["binding_calculators"] = list(self.binding_calculators)
        value["warnings"] = list(self.warnings)
        return value


@dataclass(frozen=True)
class PolicyPricedExposure:
    """A pricing result that retains its Policy Lab provenance."""

    method: str
    unit_price: float
    admitted_quantity: float
    quantity_unit: str
    total_value: float
    assessment_id: str
    package_content_id: str
    claim_id: str
    policy_id: str
    decision_id: str
    evidence_hash: str
    evidence_assurance: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


PackageSource = Union[Mapping[str, Any], str, Path]


def load_claim_assessment(source: PackageSource) -> Dict[str, Any]:
    """Load a Policy Lab claim-assessment package from a mapping or JSON file."""
    if isinstance(source, Mapping):
        return dict(source)

    path = Path(source)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PolicyLabPackageError(f"Could not read Policy Lab package: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyLabPackageError(f"Policy Lab package is not valid JSON: {path}") from exc

    if not isinstance(payload, dict):
        raise PolicyLabPackageError("Policy Lab package must be a JSON object")
    return payload


def _require_mapping(parent: Mapping[str, Any], key: str, context: str = "package") -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise PolicyLabPackageError(f"Missing or invalid {context}.{key}")
    return value


def _require_string(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PolicyLabPackageError(f"Missing or invalid {context}.{key}")
    return value


def _require_sha256(parent: Mapping[str, Any], key: str, context: str) -> str:
    value = _require_string(parent, key, context)
    if not SHA256_PATTERN.fullmatch(value):
        raise PolicyLabPackageError(f"{context}.{key} must be a lowercase SHA-256 hex string")
    return value


def _as_finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyLabPackageError(f"{context} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise PolicyLabPackageError(f"{context} must be finite")
    return number


def _evaluation_policy_id(evaluation: Mapping[str, Any]) -> Optional[str]:
    policy = evaluation.get("policy")
    if not isinstance(policy, Mapping):
        return None
    policy_id = policy.get("id")
    return policy_id if isinstance(policy_id, str) and policy_id else None


def _select_evaluation(
    package: Mapping[str, Any], policy_id: Optional[str]
) -> Mapping[str, Any]:
    evaluations = package.get("evaluations")
    if not isinstance(evaluations, list) or not evaluations:
        raise PolicyLabPackageError("Policy Lab package has no policy evaluations")

    candidates = [item for item in evaluations if isinstance(item, Mapping)]

    if policy_id is not None:
        matches = [item for item in candidates if _evaluation_policy_id(item) == policy_id]
        if not matches:
            raise PolicyLabPackageError(f"Policy evaluation not found: {policy_id}")
        if len(matches) > 1:
            raise PolicyLabPackageError(f"Policy evaluation is not unique: {policy_id}")
        return matches[0]

    admitted = [
        item
        for item in candidates
        if item.get("external_reading") in ADMITTED_READINGS
        and isinstance(item.get("supported_quantity"), Mapping)
    ]
    if not admitted:
        readings = sorted(
            {
                str(item.get("external_reading"))
                for item in candidates
                if item.get("external_reading") is not None
            }
        )
        detail = ", ".join(readings) if readings else "no readable decisions"
        raise PolicyLabPackageError(
            f"No admitted supported quantity is available ({detail})"
        )
    if len(admitted) > 1:
        policies = ", ".join(
            sorted(filter(None, (_evaluation_policy_id(item) for item in admitted)))
        )
        raise PolicyLabPackageError(
            "Multiple admitted policy evaluations are present; select policy_id explicitly"
            + (f": {policies}" if policies else "")
        )
    return admitted[0]


def extract_admitted_exposure(
    source: PackageSource, policy_id: Optional[str] = None
) -> PolicyLabExposure:
    """Extract one policy-admitted quantity without reinterpreting Policy Lab.

    If the package contains more than one admitted policy evaluation, callers
    must select ``policy_id`` explicitly. Blocked evaluations and evaluations
    without ``supported_quantity`` are never converted into exposures.
    """
    package = load_claim_assessment(source)

    schema = package.get("schema")
    if schema != POLICY_LAB_SCHEMA:
        raise PolicyLabPackageError(
            f"Unsupported Policy Lab schema: {schema!r}; expected {POLICY_LAB_SCHEMA!r}"
        )

    profile = _require_mapping(package, "profile")
    profile_id = _require_string(profile, "id", "profile")
    if profile_id != POLICY_LAB_PROFILE:
        raise PolicyLabPackageError(
            f"Unsupported Policy Lab profile: {profile_id!r}; expected {POLICY_LAB_PROFILE!r}"
        )
    unit_mapping = _require_mapping(profile, "unit_mapping", "profile")
    source_unit = _require_string(unit_mapping, "source_unit", "profile.unit_mapping")
    claim_unit = _require_string(unit_mapping, "claim_unit", "profile.unit_mapping")

    assessment_id = _require_sha256(package, "assessment_id", "package")
    package_content_id = _require_sha256(package, "package_content_id", "package")
    claim = _require_mapping(package, "claim")
    evidence = _require_mapping(package, "evidence")
    evaluation = _select_evaluation(package, policy_id)
    policy = _require_mapping(evaluation, "policy", "evaluation")
    supported = _require_mapping(evaluation, "supported_quantity", "evaluation")
    period = _require_mapping(claim, "period", "claim")
    canonical_utc = _require_mapping(period, "canonical_utc", "claim.period")
    eligible_quantity = _require_mapping(evidence, "eligible_quantity", "evidence")

    external_reading = _require_string(evaluation, "external_reading", "evaluation")
    if external_reading not in ADMITTED_READINGS:
        raise PolicyLabPackageError(
            f"Policy {policy.get('id', '<unknown>')} is not admitted: {external_reading}"
        )

    quantity = _as_finite_number(
        supported.get("value"), "evaluation.supported_quantity.value"
    )
    if quantity < 0:
        raise PolicyLabPackageError("Supported quantity cannot be negative")
    unit = _require_string(supported, "unit", "evaluation.supported_quantity")
    if unit != claim_unit:
        raise PolicyLabPackageError(
            "evaluation.supported_quantity.unit does not match profile.unit_mapping.claim_unit"
        )

    evidence_value = _as_finite_number(
        eligible_quantity.get("value"), "evidence.eligible_quantity.value"
    )
    if evidence_value < 0:
        raise PolicyLabPackageError("Evidence eligible quantity cannot be negative")
    evidence_unit = _require_string(
        eligible_quantity, "unit", "evidence.eligible_quantity"
    )
    if evidence_unit != source_unit:
        raise PolicyLabPackageError(
            "evidence.eligible_quantity.unit does not match profile.unit_mapping.source_unit"
        )

    assurance = _require_string(evidence, "assurance", "evidence")
    if not ASSURANCE_PATTERN.fullmatch(assurance):
        raise PolicyLabPackageError("evidence.assurance must be L0-L4")

    evidence_hash = _require_sha256(evidence, "evidence_hash", "evidence")
    decision_id = _require_sha256(evaluation, "decision_id", "evaluation")

    requested = claim.get("requested_quantity")
    requested_quantity = (
        None
        if requested is None
        else _as_finite_number(requested, "claim.requested_quantity")
    )
    if requested_quantity is not None and requested_quantity < 0:
        raise PolicyLabPackageError("claim.requested_quantity cannot be negative")

    binding_raw = evaluation.get("binding_calculators", [])
    if not isinstance(binding_raw, list) or any(
        not isinstance(item, str) or not item for item in binding_raw
    ):
        raise PolicyLabPackageError(
            "evaluation.binding_calculators must be an array of non-empty strings"
        )
    binding_calculators = tuple(binding_raw)

    warnings = []
    evidence_warnings = evidence.get("warnings", [])
    if not isinstance(evidence_warnings, list):
        raise PolicyLabPackageError("evidence.warnings must be an array")
    for warning in evidence_warnings:
        if isinstance(warning, Mapping):
            code = warning.get("code")
            detail = warning.get("detail")
            if code and detail:
                warnings.append(f"{code}: {detail}")
            elif code:
                warnings.append(str(code))
        elif warning:
            warnings.append(str(warning))

    rule_evaluations = evaluation.get("rule_evaluations", [])
    if not isinstance(rule_evaluations, list):
        raise PolicyLabPackageError("evaluation.rule_evaluations must be an array")
    for rule in rule_evaluations:
        if not isinstance(rule, Mapping):
            continue
        calculator_id = str(rule.get("calculator_id", "rule"))
        rule_warnings = rule.get("warnings", [])
        if not isinstance(rule_warnings, list):
            raise PolicyLabPackageError("rule_evaluation.warnings must be an array")
        warnings.extend(
            f"{calculator_id}: {warning}"
            for warning in rule_warnings
            if warning
        )

    settlement = package.get("settlement")
    scenario_only: Optional[bool] = None
    if isinstance(settlement, Mapping):
        raw_scenario = settlement.get("scenario_only")
        if isinstance(raw_scenario, bool):
            scenario_only = raw_scenario

    policy_version_raw = policy.get("version")
    policy_version = (
        str(policy_version_raw) if policy_version_raw is not None else None
    )

    return PolicyLabExposure(
        schema=schema,
        profile_id=profile_id,
        assessment_id=assessment_id,
        package_content_id=package_content_id,
        claim_id=_require_string(claim, "claim_id", "claim"),
        case_id=_require_string(claim, "case_id", "claim"),
        subject=_require_string(claim, "subject", "claim"),
        request_mode=_require_string(claim, "request_mode", "claim"),
        requested_quantity=requested_quantity,
        period_start_utc=_require_string(canonical_utc, "start", "claim.period.canonical_utc"),
        period_end_utc=_require_string(canonical_utc, "end", "claim.period.canonical_utc"),
        policy_id=_require_string(policy, "id", "evaluation.policy"),
        policy_version=policy_version,
        policy_name=_require_string(policy, "name", "evaluation.policy"),
        decision_id=decision_id,
        external_reading=external_reading,
        quantity=quantity,
        unit=unit,
        evidence_assurance=assurance,
        evidence_hash=evidence_hash,
        evidence_quantity=evidence_value,
        evidence_unit=evidence_unit,
        binding_calculators=binding_calculators,
        warnings=tuple(warnings),
        settlement_scenario_only=scenario_only,
    )


def price_admitted_exposure(
    exposure: PolicyLabExposure,
    *,
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    method: str = "binomial",
    steps: int = 100,
    num_simulations: int = 10000,
    seed: Optional[int] = None,
    payoff_type: str = "call",
) -> PolicyPricedExposure:
    """Price an admitted quantity while retaining Policy Lab provenance.

    ``S0`` and ``K`` are prices *per admitted quantity unit*. The function does
    not infer market data, perform unit conversion, or alter the admitted
    quantity. Total value is simply the model's per-unit price multiplied by the
    Policy Lab-supported quantity.
    """
    for value, name in (
        (S0, "S0"),
        (K, "K"),
        (T, "T"),
        (r, "r"),
        (sigma, "sigma"),
    ):
        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")
    if S0 < 0 or K < 0 or T <= 0 or sigma < 0:
        raise ValueError("S0/K/sigma must be non-negative and T must be positive")

    method_normalized = method.strip().lower().replace("_", "-")

    if method_normalized == "binomial":
        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
            raise ValueError("steps must be a positive integer")
        from .binomial import BinomialTree

        model = BinomialTree(
            S0=S0,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            N=steps,
            payoff_type=payoff_type,
        )
        unit_price = float(model.price())
        method_name = "binomial"
    elif method_normalized in {"monte-carlo", "mc"}:
        if (
            isinstance(num_simulations, bool)
            or not isinstance(num_simulations, int)
            or num_simulations < 1
        ):
            raise ValueError("num_simulations must be a positive integer")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise ValueError("seed must be an integer or null")
        from .monte_carlo import MonteCarloSimulator

        model = MonteCarloSimulator(
            S0=S0,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            num_simulations=num_simulations,
            seed=seed,
            payoff_type=payoff_type,
        )
        unit_price = float(model.price())
        method_name = "monte-carlo"
    else:
        raise ValueError("method must be 'binomial' or 'monte-carlo'")

    if not math.isfinite(unit_price) or unit_price < 0:
        raise ValueError("Pricing engine returned an invalid unit price")

    return PolicyPricedExposure(
        method=method_name,
        unit_price=unit_price,
        admitted_quantity=exposure.quantity,
        quantity_unit=exposure.unit,
        total_value=unit_price * exposure.quantity,
        assessment_id=exposure.assessment_id,
        package_content_id=exposure.package_content_id,
        claim_id=exposure.claim_id,
        policy_id=exposure.policy_id,
        decision_id=exposure.decision_id,
        evidence_hash=exposure.evidence_hash,
        evidence_assurance=exposure.evidence_assurance,
    )
