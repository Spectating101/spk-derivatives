"""Forward curves and transparent market-model calibration utilities.

SPK separates renewable quantity from market price. This module handles market
observations only: forward-curve interpolation and small, explicit calibration
helpers for normal, lognormal, and Ornstein-Uhlenbeck price dynamics.

The estimators are diagnostics for research/scenario work. They do not imply
that a fitted historical process is a risk-neutral pricing measure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import numpy as np


class MarketCalibrationError(ValueError):
    """Raised when market observations or calibration inputs are invalid."""


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketCalibrationError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise MarketCalibrationError(f"{name} must be finite")
    return number


def _series(values: Iterable[float], name: str, *, minimum: int = 3) -> np.ndarray:
    try:
        arr = np.asarray(list(values), dtype=float)
    except (TypeError, ValueError) as exc:
        raise MarketCalibrationError(f"{name} must be numeric") from exc
    if arr.ndim != 1 or arr.size < minimum:
        raise MarketCalibrationError(f"{name} requires at least {minimum} observations")
    if not np.all(np.isfinite(arr)):
        raise MarketCalibrationError(f"{name} must contain only finite values")
    return arr


@dataclass(frozen=True)
class ForwardCurveNode:
    maturity_years: float
    forward: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class ForwardCurve:
    """Observed forward curve with explicit units and provenance.

    Interpolation is linear between observed nodes. Extrapolation is deliberately
    rejected so an unobserved tenor cannot silently become a market input.
    """

    currency: str
    quantity_unit: str
    nodes: Tuple[ForwardCurveNode, ...]
    observed_at_utc: str
    source: str
    source_hash: Optional[str] = None
    interpolation: str = "linear"

    def __post_init__(self) -> None:
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise MarketCalibrationError("currency must be non-empty")
        if not isinstance(self.quantity_unit, str) or not self.quantity_unit.strip():
            raise MarketCalibrationError("quantity_unit must be non-empty")
        if not isinstance(self.observed_at_utc, str) or not self.observed_at_utc.strip():
            raise MarketCalibrationError("observed_at_utc must be non-empty")
        if not isinstance(self.source, str) or not self.source.strip():
            raise MarketCalibrationError("source must be non-empty")
        if self.interpolation != "linear":
            raise MarketCalibrationError("only linear interpolation is supported")
        if self.source_hash is not None and not _SHA256.fullmatch(self.source_hash):
            raise MarketCalibrationError("source_hash must be a lowercase SHA-256 hex string")
        if len(self.nodes) < 2:
            raise MarketCalibrationError("forward curve requires at least two nodes")

        previous = -math.inf
        for index, node in enumerate(self.nodes):
            if not isinstance(node, ForwardCurveNode):
                raise MarketCalibrationError(f"nodes[{index}] must be ForwardCurveNode")
            maturity = _finite(node.maturity_years, f"nodes[{index}].maturity_years")
            _finite(node.forward, f"nodes[{index}].forward")
            if maturity < 0:
                raise MarketCalibrationError("forward-curve maturity cannot be negative")
            if maturity <= previous:
                raise MarketCalibrationError("forward-curve maturities must be strictly increasing")
            previous = maturity

    @property
    def price_unit(self) -> str:
        return f"{self.currency.strip()}/{self.quantity_unit.strip()}"

    def forward_at(self, maturity_years: float) -> float:
        maturity = _finite(maturity_years, "maturity_years")
        if maturity < self.nodes[0].maturity_years or maturity > self.nodes[-1].maturity_years:
            raise MarketCalibrationError(
                "requested maturity lies outside observed forward-curve range; "
                "explicit extrapolation is required upstream"
            )
        for node in self.nodes:
            if maturity == node.maturity_years:
                return float(node.forward)
        for left, right in zip(self.nodes[:-1], self.nodes[1:]):
            if left.maturity_years < maturity < right.maturity_years:
                weight = (maturity - left.maturity_years) / (
                    right.maturity_years - left.maturity_years
                )
                return float(left.forward + weight * (right.forward - left.forward))
        raise MarketCalibrationError("could not resolve forward-curve maturity")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "currency": self.currency.strip(),
            "quantity_unit": self.quantity_unit.strip(),
            "price_unit": self.price_unit,
            "observed_at_utc": self.observed_at_utc,
            "source": self.source,
            "source_hash": self.source_hash,
            "interpolation": self.interpolation,
            "nodes": [node.to_dict() for node in self.nodes],
        }


def build_forward_curve(
    nodes: Sequence[Tuple[float, float]],
    *,
    currency: str,
    quantity_unit: str,
    observed_at_utc: str,
    source: str,
    source_hash: Optional[str] = None,
) -> ForwardCurve:
    """Build a validated forward curve from ``(maturity_years, forward)`` pairs."""
    return ForwardCurve(
        currency=currency,
        quantity_unit=quantity_unit,
        nodes=tuple(ForwardCurveNode(float(maturity), float(forward)) for maturity, forward in nodes),
        observed_at_utc=observed_at_utc,
        source=source,
        source_hash=source_hash,
    )


@dataclass(frozen=True)
class VolatilityEstimate:
    method: str
    observations: int
    step_years: float
    volatility: float
    volatility_unit: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def estimate_normal_volatility(
    prices: Iterable[float],
    step_years: float,
) -> VolatilityEstimate:
    """Annualize standard deviation of price changes for Bachelier-style use."""
    values = _series(prices, "prices")
    step = _finite(step_years, "step_years")
    if step <= 0:
        raise MarketCalibrationError("step_years must be positive")
    changes = np.diff(values)
    sigma = float(np.std(changes, ddof=1) / math.sqrt(step))
    return VolatilityEstimate(
        method="historical-normal-price-change",
        observations=int(values.size),
        step_years=step,
        volatility=sigma,
        volatility_unit="price-per-sqrt-year",
    )


def estimate_lognormal_volatility(
    prices: Iterable[float],
    step_years: float,
) -> VolatilityEstimate:
    """Annualize log-return volatility for positive-price benchmark models."""
    values = _series(prices, "prices")
    step = _finite(step_years, "step_years")
    if step <= 0:
        raise MarketCalibrationError("step_years must be positive")
    if np.any(values <= 0):
        raise MarketCalibrationError("lognormal volatility requires strictly positive prices")
    returns = np.diff(np.log(values))
    sigma = float(np.std(returns, ddof=1) / math.sqrt(step))
    return VolatilityEstimate(
        method="historical-log-return",
        observations=int(values.size),
        step_years=step,
        volatility=sigma,
        volatility_unit="annualized-lognormal",
    )


@dataclass(frozen=True)
class OUCalibration:
    observations: int
    step_years: float
    long_run_mean: float
    mean_reversion: float
    volatility: float
    intercept: float
    autoregressive_coefficient: float
    residual_std: float
    r_squared: float
    method: str = "discrete-ar1-to-ou-ols"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calibrate_ou_from_series(
    prices: Iterable[float],
    step_years: float,
) -> OUCalibration:
    """Fit an OU diagnostic through the exact AR(1) discretization.

    For equally spaced observations ``X[t+1] = a + b X[t] + eps`` with
    ``0 < b < 1``:

    ``kappa = -log(b) / dt``
    ``theta = a / (1 - b)``

    and diffusion volatility is recovered from the exact OU innovation variance.
    Fits with non-mean-reverting ``b`` are rejected instead of being coerced.
    """
    values = _series(prices, "prices", minimum=4)
    step = _finite(step_years, "step_years")
    if step <= 0:
        raise MarketCalibrationError("step_years must be positive")

    x = values[:-1]
    y = values[1:]
    design = np.column_stack((np.ones_like(x), x))
    coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank < 2:
        raise MarketCalibrationError("OU calibration requires variation in lagged prices")
    intercept = float(coefficients[0])
    phi = float(coefficients[1])
    if not 0.0 < phi < 1.0:
        raise MarketCalibrationError(
            "fitted AR(1) coefficient must lie strictly between 0 and 1 "
            "for a stationary mean-reverting OU mapping"
        )

    fitted = intercept + phi * x
    residuals = y - fitted
    degrees = residuals.size - 2
    if degrees < 1:
        raise MarketCalibrationError("insufficient degrees of freedom for OU residual variance")
    residual_variance = float(np.sum(residuals * residuals) / degrees)
    residual_std = math.sqrt(max(residual_variance, 0.0))

    kappa = -math.log(phi) / step
    theta = intercept / (1.0 - phi)
    denominator = 1.0 - phi * phi
    sigma = residual_std * math.sqrt(2.0 * kappa / denominator)

    centered = y - float(np.mean(y))
    total = float(np.sum(centered * centered))
    residual_sum = float(np.sum(residuals * residuals))
    r_squared = 1.0 - residual_sum / total if total > 0 else 1.0

    return OUCalibration(
        observations=int(values.size),
        step_years=step,
        long_run_mean=float(theta),
        mean_reversion=float(kappa),
        volatility=float(sigma),
        intercept=intercept,
        autoregressive_coefficient=phi,
        residual_std=float(residual_std),
        r_squared=float(r_squared),
    )
