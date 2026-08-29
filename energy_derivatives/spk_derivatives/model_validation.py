"""Numerical validation helpers for transparent SPK market-model benchmarks.

These functions compare analytic forward-option formulas against seeded Monte
Carlo estimators under matching model assumptions. They validate implementation
consistency, not whether a model is empirically correct for a particular market.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict

import numpy as np

from .market_models import bachelier_option_price, black76_option_price


class ModelValidationError(ValueError):
    """Raised when a validation configuration is invalid."""


@dataclass(frozen=True)
class AnalyticMonteCarloValidation:
    model: str
    option_type: str
    analytic_value: float
    monte_carlo_value: float
    standard_error: float
    absolute_error: float
    relative_error: float
    z_score: float
    simulations: int
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _simulation_inputs(simulations: int, seed: int) -> tuple[int, int]:
    if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 100:
        raise ModelValidationError("simulations must be an integer >= 100")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ModelValidationError("seed must be an integer")
    return simulations, seed


def _summarize(
    *,
    model: str,
    option_type: str,
    analytic: float,
    discounted_payoffs: np.ndarray,
    simulations: int,
    seed: int,
) -> AnalyticMonteCarloValidation:
    estimate = float(np.mean(discounted_payoffs))
    standard_error = float(np.std(discounted_payoffs, ddof=1) / math.sqrt(simulations))
    absolute_error = abs(estimate - analytic)
    relative_error = absolute_error / abs(analytic) if analytic != 0 else absolute_error
    if standard_error > 0:
        z_score = (estimate - analytic) / standard_error
    else:
        z_score = 0.0 if estimate == analytic else math.copysign(math.inf, estimate - analytic)
    return AnalyticMonteCarloValidation(
        model=model,
        option_type=option_type,
        analytic_value=float(analytic),
        monte_carlo_value=estimate,
        standard_error=standard_error,
        absolute_error=float(absolute_error),
        relative_error=float(relative_error),
        z_score=float(z_score),
        simulations=simulations,
        seed=seed,
    )


def validate_black76_monte_carlo(
    forward: float,
    strike: float,
    maturity_years: float,
    risk_free_rate: float,
    volatility: float,
    *,
    option_type: str = "call",
    simulations: int = 100_000,
    seed: int = 7,
) -> AnalyticMonteCarloValidation:
    """Compare Black-76 analytic value with matching lognormal-forward Monte Carlo."""
    simulations, seed = _simulation_inputs(simulations, seed)
    analytic = black76_option_price(
        forward,
        strike,
        maturity_years,
        risk_free_rate,
        volatility,
        option_type=option_type,
    )
    if maturity_years < 0:
        raise ModelValidationError("maturity_years cannot be negative")
    rng = np.random.default_rng(seed)
    if maturity_years == 0 or volatility == 0:
        terminal = np.full(simulations, forward, dtype=float)
    else:
        z = rng.standard_normal(simulations)
        variance = volatility * volatility * maturity_years
        terminal = forward * np.exp(
            -0.5 * variance + volatility * math.sqrt(maturity_years) * z
        )
    if analytic.option_type == "call":
        payoff = np.maximum(terminal - strike, 0.0)
    else:
        payoff = np.maximum(strike - terminal, 0.0)
    discounted = analytic.discount_factor * payoff
    return _summarize(
        model="black-76",
        option_type=analytic.option_type,
        analytic=analytic.value,
        discounted_payoffs=discounted,
        simulations=simulations,
        seed=seed,
    )


def validate_bachelier_monte_carlo(
    forward: float,
    strike: float,
    maturity_years: float,
    risk_free_rate: float,
    normal_volatility: float,
    *,
    option_type: str = "call",
    simulations: int = 100_000,
    seed: int = 7,
) -> AnalyticMonteCarloValidation:
    """Compare Bachelier analytic value with matching normal-forward Monte Carlo."""
    simulations, seed = _simulation_inputs(simulations, seed)
    analytic = bachelier_option_price(
        forward,
        strike,
        maturity_years,
        risk_free_rate,
        normal_volatility,
        option_type=option_type,
    )
    rng = np.random.default_rng(seed)
    if maturity_years == 0 or normal_volatility == 0:
        terminal = np.full(simulations, forward, dtype=float)
    else:
        terminal = forward + normal_volatility * math.sqrt(maturity_years) * rng.standard_normal(
            simulations
        )
    if analytic.option_type == "call":
        payoff = np.maximum(terminal - strike, 0.0)
    else:
        payoff = np.maximum(strike - terminal, 0.0)
    discounted = analytic.discount_factor * payoff
    return _summarize(
        model="bachelier",
        option_type=analytic.option_type,
        analytic=analytic.value,
        discounted_payoffs=discounted,
        simulations=simulations,
        seed=seed,
    )


@dataclass(frozen=True)
class ReplayMetrics:
    observations: int
    mae: float
    rmse: float
    bias: float
    correlation: float | None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def historical_replay_metrics(observed: np.ndarray, modeled: np.ndarray) -> ReplayMetrics:
    """Report simple error diagnostics for aligned historical/model values."""
    try:
        actual = np.asarray(observed, dtype=float)
        estimate = np.asarray(modeled, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ModelValidationError("observed and modeled values must be numeric") from exc
    if actual.ndim != 1 or estimate.ndim != 1 or actual.size != estimate.size or actual.size < 2:
        raise ModelValidationError(
            "observed and modeled must be equal-length 1D arrays with >=2 values"
        )
    if not np.all(np.isfinite(actual)) or not np.all(np.isfinite(estimate)):
        raise ModelValidationError("observed and modeled must contain only finite values")
    errors = estimate - actual
    mae = float(np.mean(np.abs(errors)))
    rmse = float(math.sqrt(float(np.mean(errors * errors))))
    bias = float(np.mean(errors))
    if float(np.std(actual)) > 0 and float(np.std(estimate)) > 0:
        correlation = float(np.corrcoef(actual, estimate)[0, 1])
    else:
        correlation = None
    return ReplayMetrics(
        observations=int(actual.size),
        mae=mae,
        rmse=rmse,
        bias=bias,
        correlation=correlation,
    )
