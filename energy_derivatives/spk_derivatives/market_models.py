"""Market-price models for energy exposures.

Physical renewable quantity and market-price dynamics are separate concerns.
Policy Lab and the SPK policy bridge determine admissible quantity; this module
models only the financial/market side of an exposure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Optional, Tuple

import numpy as np


class MarketModelError(ValueError):
    """Raised when a market-model configuration is invalid."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketModelError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise MarketModelError(f"{name} must be finite")
    return number


def _norm_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _norm_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


@dataclass(frozen=True)
class ForwardOptionValue:
    model: str
    option_type: str
    forward: float
    strike: float
    maturity_years: float
    risk_free_rate: float
    volatility: float
    volatility_unit: str
    discount_factor: float
    value: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def black76_option_price(
    forward: float,
    strike: float,
    maturity_years: float,
    risk_free_rate: float,
    volatility: float,
    *,
    option_type: str = "call",
) -> ForwardOptionValue:
    """Price a European option on a positive forward using Black-76."""
    forward = _finite(forward, "forward")
    strike = _finite(strike, "strike")
    maturity_years = _finite(maturity_years, "maturity_years")
    risk_free_rate = _finite(risk_free_rate, "risk_free_rate")
    volatility = _finite(volatility, "volatility")
    kind = option_type.strip().lower()
    if kind not in {"call", "put"}:
        raise MarketModelError("option_type must be 'call' or 'put'")
    if forward <= 0 or strike <= 0:
        raise MarketModelError("Black-76 requires positive forward and strike")
    if maturity_years < 0:
        raise MarketModelError("maturity_years cannot be negative")
    if volatility < 0:
        raise MarketModelError("volatility cannot be negative")
    discount = math.exp(-risk_free_rate * maturity_years)
    intrinsic = max(forward - strike, 0.0) if kind == "call" else max(strike - forward, 0.0)
    if maturity_years == 0 or volatility == 0:
        value = discount * intrinsic
    else:
        std = volatility * math.sqrt(maturity_years)
        d1 = (math.log(forward / strike) + 0.5 * std * std) / std
        d2 = d1 - std
        if kind == "call":
            value = discount * (forward * _norm_cdf(d1) - strike * _norm_cdf(d2))
        else:
            value = discount * (strike * _norm_cdf(-d2) - forward * _norm_cdf(-d1))
    return ForwardOptionValue(
        model="black-76",
        option_type=kind,
        forward=forward,
        strike=strike,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        volatility_unit="annualized-lognormal",
        discount_factor=discount,
        value=float(value),
    )


def bachelier_option_price(
    forward: float,
    strike: float,
    maturity_years: float,
    risk_free_rate: float,
    normal_volatility: float,
    *,
    option_type: str = "call",
) -> ForwardOptionValue:
    """Price a European option on a forward using the Bachelier normal model.

    Negative forwards and strikes are supported. ``normal_volatility`` has price
    units per square-root year rather than percentage/lognormal-volatility units.
    """
    forward = _finite(forward, "forward")
    strike = _finite(strike, "strike")
    maturity_years = _finite(maturity_years, "maturity_years")
    risk_free_rate = _finite(risk_free_rate, "risk_free_rate")
    normal_volatility = _finite(normal_volatility, "normal_volatility")
    kind = option_type.strip().lower()
    if kind not in {"call", "put"}:
        raise MarketModelError("option_type must be 'call' or 'put'")
    if maturity_years < 0:
        raise MarketModelError("maturity_years cannot be negative")
    if normal_volatility < 0:
        raise MarketModelError("normal_volatility cannot be negative")
    discount = math.exp(-risk_free_rate * maturity_years)
    intrinsic = max(forward - strike, 0.0) if kind == "call" else max(strike - forward, 0.0)
    std = normal_volatility * math.sqrt(maturity_years)
    if maturity_years == 0 or std == 0:
        value = discount * intrinsic
    else:
        d = (forward - strike) / std
        call = discount * ((forward - strike) * _norm_cdf(d) + std * _norm_pdf(d))
        value = call if kind == "call" else call - discount * (forward - strike)
    return ForwardOptionValue(
        model="bachelier",
        option_type=kind,
        forward=forward,
        strike=strike,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=normal_volatility,
        volatility_unit="price-per-sqrt-year",
        discount_factor=discount,
        value=float(value),
    )


def ou_terminal_moments(
    initial_price: float,
    long_run_mean: float,
    mean_reversion: float,
    volatility: float,
    horizon_years: float,
) -> Tuple[float, float]:
    """Return exact mean and variance for an Ornstein-Uhlenbeck terminal price."""
    initial_price = _finite(initial_price, "initial_price")
    long_run_mean = _finite(long_run_mean, "long_run_mean")
    mean_reversion = _finite(mean_reversion, "mean_reversion")
    volatility = _finite(volatility, "volatility")
    horizon_years = _finite(horizon_years, "horizon_years")
    if mean_reversion < 0:
        raise MarketModelError("mean_reversion cannot be negative")
    if volatility < 0:
        raise MarketModelError("volatility cannot be negative")
    if horizon_years < 0:
        raise MarketModelError("horizon_years cannot be negative")
    if mean_reversion == 0:
        return initial_price, volatility * volatility * horizon_years
    decay = math.exp(-mean_reversion * horizon_years)
    mean = long_run_mean + (initial_price - long_run_mean) * decay
    variance = volatility * volatility * (1.0 - math.exp(-2.0 * mean_reversion * horizon_years)) / (2.0 * mean_reversion)
    return float(mean), float(variance)


def simulate_ou_terminal_prices(
    initial_price: float,
    long_run_mean: float,
    mean_reversion: float,
    volatility: float,
    horizon_years: float,
    *,
    num_simulations: int = 10_000,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Sample exact OU terminal-price scenarios with deterministic seeding.

    This is a scenario generator, not a claim that the process is the correct
    risk-neutral measure for a particular electricity derivative.
    """
    if isinstance(num_simulations, bool) or not isinstance(num_simulations, int):
        raise MarketModelError("num_simulations must be an integer")
    if num_simulations < 1:
        raise MarketModelError("num_simulations must be at least 1")
    mean, variance = ou_terminal_moments(
        initial_price, long_run_mean, mean_reversion, volatility, horizon_years
    )
    rng = np.random.default_rng(seed)
    if variance == 0:
        return np.full(num_simulations, mean, dtype=float)
    return rng.normal(mean, math.sqrt(variance), num_simulations)
