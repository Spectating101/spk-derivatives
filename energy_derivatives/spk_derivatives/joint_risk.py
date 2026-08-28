"""Joint physical-volume and market-price scenario analysis.

Policy Lab establishes the maximum admitted quantity for the selected policy.
This module can model realized physical quantity scenarios at or below that cap
alongside paired market-price scenarios. Quantity and price remain distinct but
may be statistically dependent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Iterable, Optional

import numpy as np

from .energy_contracts import EnergyContract, EnergyContractError, settled_unit_price
from .policy_lab import PolicyLabExposure


class JointRiskError(ValueError):
    """Raised when paired physical/market scenarios are invalid."""


def _array(values: Iterable[float], name: str) -> np.ndarray:
    try:
        arr = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise JointRiskError(f"{name} must be numeric") from exc
    if arr.ndim != 1 or arr.size < 2:
        raise JointRiskError(f"{name} requires at least two observations")
    if not np.all(np.isfinite(arr)):
        raise JointRiskError(f"{name} must contain only finite values")
    return arr


@dataclass(frozen=True)
class JointExposureDistribution:
    contract_type: str
    scenarios: int
    quantity_unit: str
    currency: str
    price_unit: str
    authority_cap: Optional[float]
    quantity_mean: float
    quantity_std: float
    cap_utilization_mean: Optional[float]
    market_price_mean: float
    market_price_std: float
    quantity_price_correlation: Optional[float]
    merchant_value_mean: float
    contract_value_mean: float
    contract_value_std: float
    contract_value_p05: float
    contract_value_p50: float
    contract_value_p95: float
    protection_value_mean: float
    probability_negative_contract_value: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyJointExposureDistribution:
    distribution: JointExposureDistribution
    assessment_id: str
    package_content_id: str
    claim_id: str
    policy_id: str
    decision_id: str
    evidence_hash: str
    evidence_assurance: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["distribution"] = self.distribution.to_dict()
        return payload


def summarize_joint_exposure(
    quantity_scenarios: Iterable[float],
    quantity_unit: str,
    market_prices: Iterable[float],
    contract: EnergyContract,
    *,
    authority_cap: Optional[float] = None,
) -> JointExposureDistribution:
    """Summarize paired quantity/price scenarios under explicit contract terms."""
    quantities = _array(quantity_scenarios, "quantity_scenarios")
    prices = _array(market_prices, "market_prices")
    if quantities.size != prices.size:
        raise JointRiskError("quantity_scenarios and market_prices must have equal length")
    if np.any(quantities < 0):
        raise JointRiskError("quantity scenarios cannot be negative")
    if quantity_unit != contract.quantity_unit:
        raise JointRiskError(
            f"quantity unit mismatch: exposure={quantity_unit}, contract={contract.quantity_unit}"
        )

    cap = None
    if authority_cap is not None:
        if isinstance(authority_cap, bool) or not isinstance(authority_cap, (int, float)):
            raise JointRiskError("authority_cap must be numeric")
        cap = float(authority_cap)
        if not math.isfinite(cap) or cap < 0:
            raise JointRiskError("authority_cap must be finite and non-negative")
        tolerance = max(1e-12, abs(cap) * 1e-12)
        if np.any(quantities > cap + tolerance):
            raise JointRiskError(
                "quantity scenario exceeds the declared authority cap; "
                "SPK will not silently expand Policy Lab-admitted quantity"
            )

    try:
        settled_prices = np.asarray(
            [settled_unit_price(float(price), contract) for price in prices],
            dtype=float,
        )
    except EnergyContractError as exc:
        raise JointRiskError(str(exc)) from exc

    merchant_values = quantities * prices
    contract_values = quantities * settled_prices
    protection_values = contract_values - merchant_values

    quantity_std = float(np.std(quantities, ddof=1))
    price_std = float(np.std(prices, ddof=1))
    if quantity_std > 0 and price_std > 0:
        correlation = float(np.corrcoef(quantities, prices)[0, 1])
    else:
        correlation = None

    cap_utilization = None
    if cap is not None:
        if cap == 0:
            cap_utilization = 0.0 if np.all(quantities == 0) else None
        else:
            cap_utilization = float(np.mean(quantities / cap))

    return JointExposureDistribution(
        contract_type=contract.normalized_type,
        scenarios=int(quantities.size),
        quantity_unit=quantity_unit,
        currency=contract.currency,
        price_unit=contract.price_unit,
        authority_cap=cap,
        quantity_mean=float(np.mean(quantities)),
        quantity_std=quantity_std,
        cap_utilization_mean=cap_utilization,
        market_price_mean=float(np.mean(prices)),
        market_price_std=price_std,
        quantity_price_correlation=correlation,
        merchant_value_mean=float(np.mean(merchant_values)),
        contract_value_mean=float(np.mean(contract_values)),
        contract_value_std=float(np.std(contract_values, ddof=1)),
        contract_value_p05=float(np.quantile(contract_values, 0.05)),
        contract_value_p50=float(np.quantile(contract_values, 0.50)),
        contract_value_p95=float(np.quantile(contract_values, 0.95)),
        protection_value_mean=float(np.mean(protection_values)),
        probability_negative_contract_value=float(np.mean(contract_values < 0.0)),
    )


def summarize_policy_joint_exposure(
    exposure: PolicyLabExposure,
    quantity_scenarios: Iterable[float],
    market_prices: Iterable[float],
    contract: EnergyContract,
) -> PolicyJointExposureDistribution:
    """Analyze realized quantity/price scenarios bounded by Policy Lab authority."""
    distribution = summarize_joint_exposure(
        quantity_scenarios,
        exposure.unit,
        market_prices,
        contract,
        authority_cap=exposure.quantity,
    )
    return PolicyJointExposureDistribution(
        distribution=distribution,
        assessment_id=exposure.assessment_id,
        package_content_id=exposure.package_content_id,
        claim_id=exposure.claim_id,
        policy_id=exposure.policy_id,
        decision_id=exposure.decision_id,
        evidence_hash=exposure.evidence_hash,
        evidence_assurance=exposure.evidence_assurance,
    )
