"""Explicit bridge from Policy Lab claim authority to SPK market quantity.

Policy Lab decides what claim quantity is admissible. SPK Derivatives must not
silently reinterpret that semantic claim unit as physical energy or as a market
settlement unit. This module makes the missing semantic step explicit.

A ``PolicyMarketBinding`` is an SPK-owned downstream declaration. It can record
an exact SI conversion when the upstream unit is itself physical energy, or a
declared semantic mapping when some external basis relates an admitted claim to
a market quantity. The latter does not become true merely because it is hashed:
the declared authority/reference remain visible and must be evaluated on their
own merits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Optional, Tuple

from .artifacts import sha256_hex
from .policy_lab import PolicyLabExposure
from .units import UnitConversionError, si_energy_conversion


POLICY_MARKET_BINDING_SCHEMA = "spk_derivatives.policy_market_binding.v0.1"
POLICY_LAB_UPSTREAM_REPOSITORY = "Spectating101/solarpunk-coin"
POLICY_LAB_PINNED_COMMIT = "55fd6f2cf2eed25b589e91b5e3161e6ced68f5de"
POLICY_LAB_PINNED_SCHEMA_BLOB = "5b1a312ee714abaf96453a3be5c628556becef36"

BASIS_EXACT_SI = "exact-si-energy-conversion"
BASIS_DECLARED_SEMANTIC = "declared-semantic-mapping"
SUPPORTED_BASIS_KINDS = {BASIS_EXACT_SI, BASIS_DECLARED_SEMANTIC}

BRIDGE_NON_CLAIMS: Tuple[str, ...] = (
    "This binding does not modify or upgrade Policy Lab evidence or policy authority.",
    "A declared semantic mapping is not established as true merely because it is deterministic.",
    "This binding does not create legal settlement, issuance, redemption, or trading authority.",
    "Market quantity and market value remain downstream analytical constructs under declared assumptions.",
)


class PolicyMarketBridgeError(ValueError):
    """Raised when a Policy Lab-to-market binding is missing, ambiguous, or inconsistent."""


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyMarketBridgeError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyMarketBridgeError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise PolicyMarketBridgeError(f"{name} must be positive and finite")
    return number


@dataclass(frozen=True)
class PolicyMarketBinding:
    """One explicit mapping from a Policy Lab exposure to a market quantity."""

    schema: str
    binding_id: str
    assessment_id: str
    source_package_content_id: str
    claim_id: str
    policy_id: str
    decision_id: str
    evidence_hash: str
    evidence_assurance: str
    admitted_quantity: float
    claim_unit: str
    market_quantity: float
    market_quantity_unit: str
    factor: float
    basis_kind: str
    authority: str
    reference: str
    semantics: str
    period_start_utc: str
    period_end_utc: str
    non_claims: Tuple[str, ...] = BRIDGE_NON_CLAIMS

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["non_claims"] = list(self.non_claims)
        return payload


def policy_market_binding_identity_body(binding: PolicyMarketBinding) -> Dict[str, Any]:
    """Return the semantic body covered by ``binding_id``."""
    return {
        "schema": binding.schema,
        "authority": {
            "assessment_id": binding.assessment_id,
            "source_package_content_id": binding.source_package_content_id,
            "claim_id": binding.claim_id,
            "policy_id": binding.policy_id,
            "decision_id": binding.decision_id,
            "evidence_hash": binding.evidence_hash,
            "evidence_assurance": binding.evidence_assurance,
        },
        "admitted": {
            "quantity": float(binding.admitted_quantity),
            "unit": binding.claim_unit,
            "period_utc": {
                "start": binding.period_start_utc,
                "end": binding.period_end_utc,
            },
        },
        "market_quantity": {
            "quantity": float(binding.market_quantity),
            "unit": binding.market_quantity_unit,
        },
        "mapping": {
            "factor": float(binding.factor),
            "basis_kind": binding.basis_kind,
            "authority": binding.authority,
            "reference": binding.reference,
            "semantics": binding.semantics,
        },
        "non_claims": list(binding.non_claims),
    }


def compute_policy_market_binding_id(binding: PolicyMarketBinding) -> str:
    return sha256_hex(policy_market_binding_identity_body(binding))


def build_policy_market_binding(
    exposure: PolicyLabExposure,
    *,
    market_quantity_unit: str,
    basis_kind: str,
    factor: Optional[float] = None,
    authority: Optional[str] = None,
    reference: Optional[str] = None,
    semantics: Optional[str] = None,
) -> PolicyMarketBinding:
    """Create an explicit, deterministic Policy Lab-to-market quantity binding.

    ``exact-si-energy-conversion`` is allowed only when both the Policy Lab
    admitted unit and target unit are literal physical Wh/kWh/MWh/GWh/TWh units.
    Semantic units such as ``kWh-claim`` are deliberately rejected by this path.

    ``declared-semantic-mapping`` requires an explicit factor plus a named
    authority, reference, and semantic explanation. SPK records those claims but
    does not elevate them into Policy Lab or legal authority.
    """
    target_unit = _nonempty(market_quantity_unit, "market_quantity_unit")
    normalized_basis = _nonempty(basis_kind, "basis_kind")
    if normalized_basis not in SUPPORTED_BASIS_KINDS:
        raise PolicyMarketBridgeError(
            "basis_kind must be 'exact-si-energy-conversion' or 'declared-semantic-mapping'"
        )

    if normalized_basis == BASIS_EXACT_SI:
        try:
            conversion = si_energy_conversion(exposure.unit, target_unit)
        except UnitConversionError as exc:
            raise PolicyMarketBridgeError(
                "exact SI binding requires literal physical Wh/kWh/MWh/GWh/TWh units; "
                "semantic claim units require declared-semantic-mapping"
            ) from exc
        exact_factor = float(conversion.factor)
        if factor is not None and not math.isclose(
            _positive_finite(factor, "factor"), exact_factor, rel_tol=0.0, abs_tol=1e-15
        ):
            raise PolicyMarketBridgeError("factor conflicts with exact SI conversion")
        resolved_factor = exact_factor
        resolved_authority = "SI decimal-prefix definition"
        resolved_reference = conversion.reference
        resolved_semantics = (
            f"Exact physical energy conversion from {exposure.unit} to {target_unit}."
        )
    else:
        if factor is None:
            raise PolicyMarketBridgeError("declared semantic mapping requires factor")
        resolved_factor = _positive_finite(factor, "factor")
        resolved_authority = _nonempty(authority or "", "authority")
        resolved_reference = _nonempty(reference or "", "reference")
        resolved_semantics = _nonempty(semantics or "", "semantics")

    market_quantity = float(exposure.quantity) * resolved_factor
    draft = PolicyMarketBinding(
        schema=POLICY_MARKET_BINDING_SCHEMA,
        binding_id="0" * 64,
        assessment_id=exposure.assessment_id,
        source_package_content_id=exposure.package_content_id,
        claim_id=exposure.claim_id,
        policy_id=exposure.policy_id,
        decision_id=exposure.decision_id,
        evidence_hash=exposure.evidence_hash,
        evidence_assurance=exposure.evidence_assurance,
        admitted_quantity=float(exposure.quantity),
        claim_unit=exposure.unit,
        market_quantity=market_quantity,
        market_quantity_unit=target_unit,
        factor=resolved_factor,
        basis_kind=normalized_basis,
        authority=resolved_authority,
        reference=resolved_reference,
        semantics=resolved_semantics,
        period_start_utc=exposure.period_start_utc,
        period_end_utc=exposure.period_end_utc,
    )
    binding_id = compute_policy_market_binding_id(draft)
    return PolicyMarketBinding(**{**draft.__dict__, "binding_id": binding_id})


def validate_policy_market_binding(binding: PolicyMarketBinding) -> None:
    """Fail closed if a binding is internally inconsistent or has been mutated."""
    if binding.schema != POLICY_MARKET_BINDING_SCHEMA:
        raise PolicyMarketBridgeError(f"unsupported binding schema: {binding.schema!r}")
    if binding.basis_kind not in SUPPORTED_BASIS_KINDS:
        raise PolicyMarketBridgeError("unsupported basis_kind")
    _positive_finite(binding.factor, "factor")
    _nonempty(binding.claim_unit, "claim_unit")
    _nonempty(binding.market_quantity_unit, "market_quantity_unit")
    _nonempty(binding.authority, "authority")
    _nonempty(binding.reference, "reference")
    _nonempty(binding.semantics, "semantics")
    expected_quantity = float(binding.admitted_quantity) * float(binding.factor)
    if not math.isclose(
        float(binding.market_quantity), expected_quantity, rel_tol=1e-12, abs_tol=1e-12
    ):
        raise PolicyMarketBridgeError("market_quantity does not match admitted_quantity * factor")
    if binding.basis_kind == BASIS_EXACT_SI:
        try:
            exact = si_energy_conversion(binding.claim_unit, binding.market_quantity_unit)
        except UnitConversionError as exc:
            raise PolicyMarketBridgeError("exact SI binding contains a non-physical unit") from exc
        if not math.isclose(float(binding.factor), float(exact.factor), rel_tol=0.0, abs_tol=1e-15):
            raise PolicyMarketBridgeError("exact SI binding factor is inconsistent")
    expected_id = compute_policy_market_binding_id(binding)
    if binding.binding_id != expected_id:
        raise PolicyMarketBridgeError("binding_id does not match binding contents")
