"""Explicit energy-contract settlement with separate physical quantity and price.

Policy Lab determines whether a quantity is admissible. This module never changes
that authority result. It maps an admitted quantity to an explicit market price
and contract settlement rule without implicit unit conversion.

The functions here perform deterministic scenario/settlement arithmetic. They do
not create legal settlement authority, execute trades, or replace stochastic
option valuation when a contract requires one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Optional

from .policy_lab import PolicyLabExposure


class EnergyContractError(ValueError):
    """Raised when contract terms or settlement inputs are inconsistent."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EnergyContractError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise EnergyContractError(f"{name} must be finite")
    return number


@dataclass(frozen=True)
class EnergyContract:
    """Deterministic settlement-price rule for an energy quantity.

    Supported contract types:
    ``merchant`` uses the market price directly;
    ``fixed-price`` settles at ``fixed_price``;
    ``floor`` settles at max(market, floor);
    ``cap`` settles at min(market, cap);
    ``collar`` clamps market price between floor and cap.
    """

    contract_type: str
    currency: str
    quantity_unit: str
    fixed_price: Optional[float] = None
    floor_price: Optional[float] = None
    cap_price: Optional[float] = None

    def __post_init__(self) -> None:
        kind = self.contract_type.strip().lower()
        if kind not in {"merchant", "fixed-price", "floor", "cap", "collar"}:
            raise EnergyContractError(f"Unsupported contract_type: {self.contract_type}")
        if not self.currency.strip():
            raise EnergyContractError("currency must be non-empty")
        if not self.quantity_unit.strip():
            raise EnergyContractError("quantity_unit must be non-empty")
        if self.fixed_price is not None:
            _finite(self.fixed_price, "fixed_price")
        if self.floor_price is not None:
            _finite(self.floor_price, "floor_price")
        if self.cap_price is not None:
            _finite(self.cap_price, "cap_price")
        if kind == "fixed-price" and self.fixed_price is None:
            raise EnergyContractError("fixed-price contract requires fixed_price")
        if kind == "floor" and self.floor_price is None:
            raise EnergyContractError("floor contract requires floor_price")
        if kind == "cap" and self.cap_price is None:
            raise EnergyContractError("cap contract requires cap_price")
        if kind == "collar":
            if self.floor_price is None or self.cap_price is None:
                raise EnergyContractError("collar contract requires floor_price and cap_price")
            if float(self.floor_price) > float(self.cap_price):
                raise EnergyContractError("collar floor_price cannot exceed cap_price")

    @property
    def normalized_type(self) -> str:
        return self.contract_type.strip().lower()

    @property
    def price_unit(self) -> str:
        return f"{self.currency.strip()}/{self.quantity_unit.strip()}"

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["contract_type"] = self.normalized_type
        payload["price_unit"] = self.price_unit
        return payload


@dataclass(frozen=True)
class ContractSettlement:
    contract_type: str
    quantity: float
    quantity_unit: str
    currency: str
    price_unit: str
    market_price: float
    settled_price: float
    market_value: float
    contract_value: float
    value_difference: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyContractSettlement:
    """Contract scenario retaining the exact upstream Policy Lab authority IDs."""

    settlement: ContractSettlement
    assessment_id: str
    package_content_id: str
    claim_id: str
    policy_id: str
    decision_id: str
    evidence_hash: str
    evidence_assurance: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["settlement"] = self.settlement.to_dict()
        return payload


def settled_unit_price(market_price: float, contract: EnergyContract) -> float:
    """Resolve the deterministic settlement price for one quantity unit."""
    market = _finite(market_price, "market_price")
    kind = contract.normalized_type
    if kind == "merchant":
        return market
    if kind == "fixed-price":
        return float(contract.fixed_price)
    if kind == "floor":
        return max(market, float(contract.floor_price))
    if kind == "cap":
        return min(market, float(contract.cap_price))
    return min(max(market, float(contract.floor_price)), float(contract.cap_price))


def settle_energy_contract(
    quantity: float,
    quantity_unit: str,
    market_price: float,
    contract: EnergyContract,
) -> ContractSettlement:
    """Settle an explicit quantity under one market-price scenario."""
    amount = _finite(quantity, "quantity")
    market = _finite(market_price, "market_price")
    if amount < 0:
        raise EnergyContractError("quantity cannot be negative")
    if quantity_unit != contract.quantity_unit:
        raise EnergyContractError(
            f"quantity unit mismatch: exposure={quantity_unit}, contract={contract.quantity_unit}"
        )
    settled = settled_unit_price(market, contract)
    market_value = amount * market
    contract_value = amount * settled
    return ContractSettlement(
        contract_type=contract.normalized_type,
        quantity=amount,
        quantity_unit=quantity_unit,
        currency=contract.currency,
        price_unit=contract.price_unit,
        market_price=market,
        settled_price=settled,
        market_value=market_value,
        contract_value=contract_value,
        value_difference=contract_value - market_value,
    )


def settle_policy_exposure(
    exposure: PolicyLabExposure,
    market_price: float,
    contract: EnergyContract,
) -> PolicyContractSettlement:
    """Apply contract settlement to a Policy Lab-admitted quantity only."""
    settlement = settle_energy_contract(exposure.quantity, exposure.unit, market_price, contract)
    return PolicyContractSettlement(
        settlement=settlement,
        assessment_id=exposure.assessment_id,
        package_content_id=exposure.package_content_id,
        claim_id=exposure.claim_id,
        policy_id=exposure.policy_id,
        decision_id=exposure.decision_id,
        evidence_hash=exposure.evidence_hash,
        evidence_assurance=exposure.evidence_assurance,
    )
