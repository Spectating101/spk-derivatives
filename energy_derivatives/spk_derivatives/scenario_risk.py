"""Scenario distributions and model-sensitivity analysis for energy contracts.

This layer holds Policy Lab-admitted quantity fixed while varying market-price
scenarios. It therefore measures market/model consequences conditional on the
same upstream authority and contract terms.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Iterable, Mapping, Tuple

import numpy as np

from .energy_contracts import EnergyContract, EnergyContractError, settled_unit_price
from .policy_lab import PolicyLabExposure


class ScenarioRiskError(ValueError):
    """Raised when scenario inputs are malformed or incomparable."""


def _prices(values: Iterable[float]) -> np.ndarray:
    try:
        arr = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise ScenarioRiskError("market_prices must be numeric") from exc
    if arr.ndim != 1 or arr.size < 2:
        raise ScenarioRiskError("market_prices requires at least two observations")
    if not np.all(np.isfinite(arr)):
        raise ScenarioRiskError("market_prices must contain only finite values")
    return arr


@dataclass(frozen=True)
class SettlementDistribution:
    contract_type: str
    quantity: float
    quantity_unit: str
    currency: str
    price_unit: str
    scenarios: int
    market_price_mean: float
    market_price_std: float
    contract_value_mean: float
    contract_value_std: float
    contract_value_p05: float
    contract_value_p50: float
    contract_value_p95: float
    market_value_mean: float
    protection_value_mean: float
    probability_negative_contract_value: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicySettlementDistribution:
    distribution: SettlementDistribution
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


@dataclass(frozen=True)
class MarketModelOutcome:
    model_id: str
    distribution: SettlementDistribution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "distribution": self.distribution.to_dict(),
        }


@dataclass(frozen=True)
class MarketModelComparison:
    quantity: float
    quantity_unit: str
    currency: str
    contract_type: str
    outcomes: Tuple[MarketModelOutcome, ...]
    expected_value_min: float
    expected_value_max: float
    expected_value_range: float
    p05_min: float
    p05_max: float
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quantity": self.quantity,
            "quantity_unit": self.quantity_unit,
            "currency": self.currency,
            "contract_type": self.contract_type,
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "expected_value_min": self.expected_value_min,
            "expected_value_max": self.expected_value_max,
            "expected_value_range": self.expected_value_range,
            "p05_min": self.p05_min,
            "p05_max": self.p05_max,
            "interpretation": self.interpretation,
        }


def summarize_contract_distribution(
    quantity: float,
    quantity_unit: str,
    market_prices: Iterable[float],
    contract: EnergyContract,
) -> SettlementDistribution:
    """Summarize one contract over a market-price scenario distribution."""
    if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
        raise ScenarioRiskError("quantity must be numeric")
    amount = float(quantity)
    if not math.isfinite(amount) or amount < 0:
        raise ScenarioRiskError("quantity must be finite and non-negative")
    if quantity_unit != contract.quantity_unit:
        raise ScenarioRiskError(
            f"quantity unit mismatch: exposure={quantity_unit}, contract={contract.quantity_unit}"
        )

    prices = _prices(market_prices)
    try:
        settled = np.asarray([settled_unit_price(float(price), contract) for price in prices])
    except EnergyContractError as exc:
        raise ScenarioRiskError(str(exc)) from exc

    market_values = amount * prices
    contract_values = amount * settled
    protection = contract_values - market_values

    return SettlementDistribution(
        contract_type=contract.normalized_type,
        quantity=amount,
        quantity_unit=quantity_unit,
        currency=contract.currency,
        price_unit=contract.price_unit,
        scenarios=int(prices.size),
        market_price_mean=float(np.mean(prices)),
        market_price_std=float(np.std(prices, ddof=1)),
        contract_value_mean=float(np.mean(contract_values)),
        contract_value_std=float(np.std(contract_values, ddof=1)),
        contract_value_p05=float(np.quantile(contract_values, 0.05)),
        contract_value_p50=float(np.quantile(contract_values, 0.50)),
        contract_value_p95=float(np.quantile(contract_values, 0.95)),
        market_value_mean=float(np.mean(market_values)),
        protection_value_mean=float(np.mean(protection)),
        probability_negative_contract_value=float(np.mean(contract_values < 0.0)),
    )


def summarize_policy_contract_distribution(
    exposure: PolicyLabExposure,
    market_prices: Iterable[float],
    contract: EnergyContract,
) -> PolicySettlementDistribution:
    """Summarize market scenarios without mutating Policy Lab-admitted quantity."""
    distribution = summarize_contract_distribution(
        exposure.quantity,
        exposure.unit,
        market_prices,
        contract,
    )
    return PolicySettlementDistribution(
        distribution=distribution,
        assessment_id=exposure.assessment_id,
        package_content_id=exposure.package_content_id,
        claim_id=exposure.claim_id,
        policy_id=exposure.policy_id,
        decision_id=exposure.decision_id,
        evidence_hash=exposure.evidence_hash,
        evidence_assurance=exposure.evidence_assurance,
    )


def compare_market_model_scenarios(
    quantity: float,
    quantity_unit: str,
    model_prices: Mapping[str, Iterable[float]],
    contract: EnergyContract,
) -> MarketModelComparison:
    """Compare price-model consequences under one fixed quantity and contract.

    The resulting range is model sensitivity. It is not evidence uncertainty,
    governance uncertainty, or a claim that any supplied model is correct.
    """
    if not isinstance(model_prices, Mapping) or len(model_prices) < 2:
        raise ScenarioRiskError("model_prices requires at least two named models")

    outcomes = []
    seen = set()
    for model_id, prices in model_prices.items():
        if not isinstance(model_id, str) or not model_id.strip():
            raise ScenarioRiskError("model identifiers must be non-empty strings")
        normalized = model_id.strip()
        if normalized in seen:
            raise ScenarioRiskError(f"duplicate model identifier: {normalized}")
        seen.add(normalized)
        outcomes.append(
            MarketModelOutcome(
                model_id=normalized,
                distribution=summarize_contract_distribution(
                    quantity, quantity_unit, prices, contract
                ),
            )
        )

    outcomes.sort(key=lambda item: item.model_id)
    expected = [item.distribution.contract_value_mean for item in outcomes]
    p05 = [item.distribution.contract_value_p05 for item in outcomes]
    return MarketModelComparison(
        quantity=float(quantity),
        quantity_unit=quantity_unit,
        currency=contract.currency,
        contract_type=contract.normalized_type,
        outcomes=tuple(outcomes),
        expected_value_min=float(min(expected)),
        expected_value_max=float(max(expected)),
        expected_value_range=float(max(expected) - min(expected)),
        p05_min=float(min(p05)),
        p05_max=float(max(p05)),
        interpretation=(
            "Range across supplied market-price models under the same quantity and "
            "contract terms; this is model sensitivity, not evidence or policy truth."
        ),
    )
