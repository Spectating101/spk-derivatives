"""Policy-sensitivity analysis over Policy Lab claim-assessment packages.

This module treats governance policy as an explicit model dimension rather than a
hidden software default. It never re-evaluates Policy Lab rules: it compares the
already-recorded policy outcomes, optionally prices every admitted outcome under
one common market/model assumption set, and emits a deterministic comparison
package whose identity changes if authority, assumptions, or results change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .artifacts import sha256_hex
from .policy_lab import (
    ADMITTED_READINGS,
    POLICY_LAB_PROFILE,
    POLICY_LAB_SCHEMA,
    PackageSource,
    PolicyLabPackageError,
    extract_admitted_exposure,
    load_claim_assessment,
    price_admitted_exposure,
)


SPK_POLICY_COMPARISON_SCHEMA = "spk_derivatives.policy_comparison_package.v0.1"


class PolicyComparisonError(ValueError):
    """Raised when a policy comparison cannot be constructed safely."""


@dataclass(frozen=True)
class PolicyOutcome:
    policy_id: str
    policy_version: Optional[str]
    policy_name: str
    decision_id: str
    external_reading: str
    admitted: bool
    supported_quantity: Optional[float]
    quantity_unit: Optional[str]
    binding_calculators: Tuple[str, ...]
    blocking_calculators: Tuple[str, ...]
    reasons: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["binding_calculators"] = list(self.binding_calculators)
        value["blocking_calculators"] = list(self.blocking_calculators)
        value["reasons"] = list(self.reasons)
        return value


@dataclass(frozen=True)
class PolicyPricedOutcome:
    policy_id: str
    decision_id: str
    admitted_quantity: float
    quantity_unit: str
    unit_price: float
    total_value: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PolicyComparisonError(f"{context} must be an object")
    return value


def _text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyComparisonError(f"{context} must be a non-empty string")
    return value


def _finite_optional(value: Any, context: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyComparisonError(f"{context} must be numeric or null")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise PolicyComparisonError(f"{context} must be finite and non-negative")
    return number


def _strings(value: Any, context: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise PolicyComparisonError(f"{context} must be an array of non-empty strings")
    return tuple(value)


def _rule_reasons(evaluation: Mapping[str, Any]) -> Tuple[str, ...]:
    rules = evaluation.get("rule_evaluations", [])
    if not isinstance(rules, list):
        raise PolicyComparisonError("evaluation.rule_evaluations must be an array")
    reasons: List[str] = []
    for rule in rules:
        if not isinstance(rule, Mapping):
            continue
        calculator = str(rule.get("calculator_id") or "rule")
        status = str(rule.get("status") or "UNKNOWN")
        explanation = str(rule.get("explanation") or "").strip()
        boundary = str(rule.get("boundary") or "").strip()
        if explanation:
            reasons.append(f"{calculator} [{status}]: {explanation}")
        elif boundary:
            reasons.append(f"{calculator} [{status}]: {boundary}")
    return tuple(reasons)


def compare_policy_outcomes(source: PackageSource) -> Tuple[PolicyOutcome, ...]:
    """Return every recorded policy outcome without choosing a preferred policy."""
    package = load_claim_assessment(source)
    if package.get("schema") != POLICY_LAB_SCHEMA:
        raise PolicyComparisonError("Unsupported Policy Lab claim-assessment schema")
    profile = _mapping(package.get("profile"), "package.profile")
    if profile.get("id") != POLICY_LAB_PROFILE:
        raise PolicyComparisonError("Unsupported Policy Lab profile")

    evaluations = package.get("evaluations")
    if not isinstance(evaluations, list) or not evaluations:
        raise PolicyComparisonError("package.evaluations must be a non-empty array")

    outcomes: List[PolicyOutcome] = []
    seen = set()
    for index, raw in enumerate(evaluations):
        evaluation = _mapping(raw, f"package.evaluations[{index}]")
        policy = _mapping(evaluation.get("policy"), f"package.evaluations[{index}].policy")
        policy_id = _text(policy.get("id"), f"package.evaluations[{index}].policy.id")
        if policy_id in seen:
            raise PolicyComparisonError(f"Duplicate policy evaluation: {policy_id}")
        seen.add(policy_id)

        reading = _text(
            evaluation.get("external_reading"),
            f"package.evaluations[{index}].external_reading",
        )
        admitted = reading in ADMITTED_READINGS
        supported = evaluation.get("supported_quantity")
        quantity: Optional[float] = None
        unit: Optional[str] = None
        if supported is not None:
            supported_map = _mapping(supported, f"package.evaluations[{index}].supported_quantity")
            quantity = _finite_optional(
                supported_map.get("value"),
                f"package.evaluations[{index}].supported_quantity.value",
            )
            unit = _text(
                supported_map.get("unit"),
                f"package.evaluations[{index}].supported_quantity.unit",
            )
        if admitted and (quantity is None or unit is None):
            raise PolicyComparisonError(
                f"Admitted policy {policy_id} has no supported quantity"
            )
        if not admitted and supported is not None:
            raise PolicyComparisonError(
                f"Non-admitted policy {policy_id} unexpectedly carries a supported quantity"
            )

        version = policy.get("version")
        outcomes.append(
            PolicyOutcome(
                policy_id=policy_id,
                policy_version=None if version is None else str(version),
                policy_name=_text(policy.get("name"), f"package.evaluations[{index}].policy.name"),
                decision_id=_text(
                    evaluation.get("decision_id"),
                    f"package.evaluations[{index}].decision_id",
                ),
                external_reading=reading,
                admitted=admitted,
                supported_quantity=quantity,
                quantity_unit=unit,
                binding_calculators=_strings(
                    evaluation.get("binding_calculators", []),
                    f"package.evaluations[{index}].binding_calculators",
                ),
                blocking_calculators=_strings(
                    evaluation.get("blocking_calculators", []),
                    f"package.evaluations[{index}].blocking_calculators",
                ),
                reasons=_rule_reasons(evaluation),
            )
        )
    return tuple(outcomes)


def price_admitted_policies(
    source: PackageSource,
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
) -> Tuple[PolicyPricedOutcome, ...]:
    """Price every admitted policy using exactly one common assumption set."""
    outcomes = compare_policy_outcomes(source)
    priced: List[PolicyPricedOutcome] = []
    for outcome in outcomes:
        if not outcome.admitted:
            continue
        exposure = extract_admitted_exposure(source, policy_id=outcome.policy_id)
        result = price_admitted_exposure(
            exposure,
            S0=S0,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            method=method,
            steps=steps,
            num_simulations=num_simulations,
            seed=seed,
            payoff_type=payoff_type,
        )
        priced.append(
            PolicyPricedOutcome(
                policy_id=outcome.policy_id,
                decision_id=outcome.decision_id,
                admitted_quantity=result.admitted_quantity,
                quantity_unit=result.quantity_unit,
                unit_price=result.unit_price,
                total_value=result.total_value,
                method=result.method,
            )
        )
    return tuple(priced)


def _comparison_identity_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema": package.get("schema"),
        "authority": package.get("authority"),
        "policy_outcomes": package.get("policy_outcomes"),
        "model": package.get("model"),
        "priced_outcomes": package.get("priced_outcomes"),
    }


def _comparison_content_body(package: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in package.items() if k != "package_content_id"}


def build_policy_comparison_package(
    source: PackageSource,
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
    assumptions: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a deterministic governance-sensitivity pricing package."""
    package = load_claim_assessment(source)
    outcomes = compare_policy_outcomes(package)
    priced = price_admitted_policies(
        package,
        S0=S0,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        method=method,
        steps=steps,
        num_simulations=num_simulations,
        seed=seed,
        payoff_type=payoff_type,
    )
    claim = _mapping(package.get("claim"), "package.claim")
    evidence = _mapping(package.get("evidence"), "package.evidence")

    result: Dict[str, Any] = {
        "schema": SPK_POLICY_COMPARISON_SCHEMA,
        "comparison_id": "",
        "package_content_id": "",
        "authority": {
            "source_schema": package.get("schema"),
            "profile_id": _mapping(package.get("profile"), "package.profile").get("id"),
            "assessment_id": package.get("assessment_id"),
            "source_package_content_id": package.get("package_content_id"),
            "claim_id": claim.get("claim_id"),
            "case_id": claim.get("case_id"),
            "evidence_hash": evidence.get("evidence_hash"),
            "evidence_assurance": evidence.get("assurance"),
        },
        "policy_outcomes": [item.to_dict() for item in outcomes],
        "model": {
            "engine": method.strip().lower().replace("_", "-"),
            "inputs": {
                "spot_per_quantity_unit": float(S0),
                "strike_per_quantity_unit": float(K),
                "maturity_years": float(T),
                "risk_free_rate": float(r),
                "volatility": float(sigma),
                "payoff_type": payoff_type,
            },
            "reproducibility": {
                "steps": steps if method.strip().lower().replace("_", "-") == "binomial" else None,
                "num_simulations": num_simulations if method.strip().lower().replace("_", "-") in {"monte-carlo", "mc"} else None,
                "seed": seed,
            },
            "assumptions": [str(item) for item in assumptions],
        },
        "priced_outcomes": [item.to_dict() for item in priced],
        "comparison": {
            "admitted_policy_count": sum(1 for item in outcomes if item.admitted),
            "blocked_policy_count": sum(1 for item in outcomes if not item.admitted),
            "minimum_admitted_quantity": min(
                (item.supported_quantity for item in outcomes if item.admitted and item.supported_quantity is not None),
                default=None,
            ),
            "maximum_admitted_quantity": max(
                (item.supported_quantity for item in outcomes if item.admitted and item.supported_quantity is not None),
                default=None,
            ),
            "minimum_total_value": min((item.total_value for item in priced), default=None),
            "maximum_total_value": max((item.total_value for item in priced), default=None),
            "interpretation": "Differences across rows are policy sensitivity under common market/model assumptions, not alternate evidence truth.",
        },
        "non_claims": [
            "This package does not choose a preferred governance policy.",
            "Blocked Policy Lab outcomes remain blocked and are never priced.",
            "Policy sensitivity is distinct from market, evidence, settlement, legal, and liquidity risk.",
        ],
    }
    result["comparison_id"] = sha256_hex(_comparison_identity_body(result))
    result["package_content_id"] = sha256_hex(_comparison_content_body(result))
    validate_policy_comparison_package(result)
    return result


def validate_policy_comparison_package(source: Union[Mapping[str, Any], str, Path]) -> bool:
    """Validate comparison identities and cross-policy invariants."""
    if isinstance(source, Mapping):
        package = dict(source)
    else:
        import json
        try:
            package = json.loads(Path(source).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PolicyComparisonError(f"Could not read comparison package: {exc}") from exc
    if package.get("schema") != SPK_POLICY_COMPARISON_SCHEMA:
        raise PolicyComparisonError("Unsupported policy comparison schema")
    outcomes = package.get("policy_outcomes")
    priced = package.get("priced_outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise PolicyComparisonError("policy_outcomes must be a non-empty array")
    if not isinstance(priced, list):
        raise PolicyComparisonError("priced_outcomes must be an array")

    admitted_ids = {
        item.get("policy_id")
        for item in outcomes
        if isinstance(item, Mapping) and item.get("admitted") is True
    }
    blocked_ids = {
        item.get("policy_id")
        for item in outcomes
        if isinstance(item, Mapping) and item.get("admitted") is False
    }
    priced_ids = {
        item.get("policy_id") for item in priced if isinstance(item, Mapping)
    }
    if priced_ids != admitted_ids:
        raise PolicyComparisonError("priced_outcomes must match all and only admitted policies")
    if priced_ids & blocked_ids:
        raise PolicyComparisonError("Blocked policies cannot appear in priced_outcomes")

    expected_id = sha256_hex(_comparison_identity_body(package))
    expected_content = sha256_hex(_comparison_content_body(package))
    if package.get("comparison_id") != expected_id:
        raise PolicyComparisonError("comparison_id does not match semantic content")
    if package.get("package_content_id") != expected_content:
        raise PolicyComparisonError("package_content_id does not match package content")
    return True
