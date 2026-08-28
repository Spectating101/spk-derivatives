"""Deterministic scenario-set manifests for reproducible energy-risk analysis.

Scenario values are quantitative inputs, not authority. A manifest records the
scenario kind, units, provenance, model declaration, and deterministic content
identity so downstream artifacts can refer to one exact scenario set.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .artifacts import sha256_hex


SCENARIO_SET_SCHEMA = "spk_derivatives.scenario_set.v0.1"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class ScenarioSetError(ValueError):
    """Raised when a scenario manifest is malformed or inconsistent."""


def _finite_tuple(values: Iterable[float], name: str) -> Tuple[float, ...]:
    result = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ScenarioSetError(f"{name}[{index}] must be numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ScenarioSetError(f"{name}[{index}] must be finite")
        result.append(number)
    if len(result) < 2:
        raise ScenarioSetError(f"{name} requires at least two scenarios")
    return tuple(result)


@dataclass(frozen=True)
class ScenarioSet:
    kind: str
    price_unit: str
    market_prices: Tuple[float, ...]
    source: str
    observed_at_utc: str
    model_id: str
    model_parameters: Mapping[str, Any]
    quantity_unit: Optional[str] = None
    quantities: Optional[Tuple[float, ...]] = None
    source_hash: Optional[str] = None
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        kind = self.kind.strip().lower()
        if kind not in {"market-price", "joint-volume-price"}:
            raise ScenarioSetError("kind must be 'market-price' or 'joint-volume-price'")
        if not self.price_unit.strip():
            raise ScenarioSetError("price_unit must be non-empty")
        if not self.source.strip() or not self.observed_at_utc.strip() or not self.model_id.strip():
            raise ScenarioSetError("source, observed_at_utc, and model_id must be non-empty")
        prices = _finite_tuple(self.market_prices, "market_prices")
        object.__setattr__(self, "market_prices", prices)
        if self.source_hash is not None and not _SHA256.fullmatch(self.source_hash):
            raise ScenarioSetError("source_hash must be a lowercase SHA-256 hex string")
        if self.seed is not None and (isinstance(self.seed, bool) or not isinstance(self.seed, int)):
            raise ScenarioSetError("seed must be an integer or null")
        if not isinstance(self.model_parameters, Mapping):
            raise ScenarioSetError("model_parameters must be a mapping")

        if kind == "market-price":
            if self.quantities is not None or self.quantity_unit is not None:
                raise ScenarioSetError("market-price scenario sets cannot carry quantity scenarios")
        else:
            if self.quantities is None or not self.quantity_unit or not self.quantity_unit.strip():
                raise ScenarioSetError("joint-volume-price scenario sets require quantities and quantity_unit")
            quantities = _finite_tuple(self.quantities, "quantities")
            if len(quantities) != len(prices):
                raise ScenarioSetError("quantities and market_prices must have equal length")
            if any(value < 0 for value in quantities):
                raise ScenarioSetError("quantity scenarios cannot be negative")
            object.__setattr__(self, "quantities", quantities)

    @property
    def normalized_kind(self) -> str:
        return self.kind.strip().lower()

    def identity_body(self) -> Dict[str, Any]:
        return {
            "schema": SCENARIO_SET_SCHEMA,
            "kind": self.normalized_kind,
            "price_unit": self.price_unit,
            "market_prices": list(self.market_prices),
            "quantity_unit": self.quantity_unit,
            "quantities": list(self.quantities) if self.quantities is not None else None,
            "source": self.source,
            "source_hash": self.source_hash,
            "observed_at_utc": self.observed_at_utc,
            "model_id": self.model_id,
            "model_parameters": dict(self.model_parameters),
            "seed": self.seed,
        }

    @property
    def scenario_set_id(self) -> str:
        return sha256_hex(self.identity_body())

    def to_dict(self) -> Dict[str, Any]:
        payload = self.identity_body()
        payload["scenario_set_id"] = self.scenario_set_id
        payload["scenario_count"] = len(self.market_prices)
        return payload


def build_market_price_scenarios(
    prices: Iterable[float],
    *,
    price_unit: str,
    source: str,
    observed_at_utc: str,
    model_id: str,
    model_parameters: Optional[Mapping[str, Any]] = None,
    source_hash: Optional[str] = None,
    seed: Optional[int] = None,
) -> ScenarioSet:
    return ScenarioSet(
        kind="market-price",
        price_unit=price_unit,
        market_prices=_finite_tuple(prices, "market_prices"),
        source=source,
        observed_at_utc=observed_at_utc,
        model_id=model_id,
        model_parameters=dict(model_parameters or {}),
        source_hash=source_hash,
        seed=seed,
    )


def build_joint_scenarios(
    quantities: Iterable[float],
    prices: Iterable[float],
    *,
    quantity_unit: str,
    price_unit: str,
    source: str,
    observed_at_utc: str,
    model_id: str,
    model_parameters: Optional[Mapping[str, Any]] = None,
    source_hash: Optional[str] = None,
    seed: Optional[int] = None,
) -> ScenarioSet:
    return ScenarioSet(
        kind="joint-volume-price",
        price_unit=price_unit,
        market_prices=_finite_tuple(prices, "market_prices"),
        quantity_unit=quantity_unit,
        quantities=_finite_tuple(quantities, "quantities"),
        source=source,
        observed_at_utc=observed_at_utc,
        model_id=model_id,
        model_parameters=dict(model_parameters or {}),
        source_hash=source_hash,
        seed=seed,
    )
