"""Mean-reverting jump/spike scenario models for electricity prices.

Electricity markets can display transient spikes that a Gaussian OU process does
not represent. This module adds a transparent compound-Poisson jump extension
for scenario analysis. It is not presented as a calibrated risk-neutral pricing
measure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, Optional

import numpy as np


class SpikeModelError(ValueError):
    """Raised when a jump/spike scenario configuration is invalid."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpikeModelError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise SpikeModelError(f"{name} must be finite")
    return number


@dataclass(frozen=True)
class MeanRevertingJumpConfig:
    initial_price: float
    long_run_mean: float
    mean_reversion: float
    diffusion_volatility: float
    jump_intensity_per_year: float
    jump_mean: float
    jump_volatility: float
    horizon_years: float
    steps: int = 365

    def __post_init__(self) -> None:
        for name in (
            "initial_price",
            "long_run_mean",
            "mean_reversion",
            "diffusion_volatility",
            "jump_intensity_per_year",
            "jump_mean",
            "jump_volatility",
            "horizon_years",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.mean_reversion < 0:
            raise SpikeModelError("mean_reversion cannot be negative")
        if self.diffusion_volatility < 0:
            raise SpikeModelError("diffusion_volatility cannot be negative")
        if self.jump_intensity_per_year < 0:
            raise SpikeModelError("jump_intensity_per_year cannot be negative")
        if self.jump_volatility < 0:
            raise SpikeModelError("jump_volatility cannot be negative")
        if self.horizon_years < 0:
            raise SpikeModelError("horizon_years cannot be negative")
        if isinstance(self.steps, bool) or not isinstance(self.steps, int) or self.steps < 1:
            raise SpikeModelError("steps must be an integer >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def simulate_mean_reverting_jump_terminal_prices(
    config: MeanRevertingJumpConfig,
    *,
    num_simulations: int = 10_000,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Simulate terminal prices under OU diffusion plus compound-Poisson jumps.

    Between jump times, each discrete step uses the exact Gaussian OU transition.
    Jump counts are Poisson with intensity ``lambda * dt``. Conditional on count
    ``n``, the compound jump is Normal(``n * jump_mean``,
    ``sqrt(n) * jump_volatility``). Subsequent OU transitions mean-revert prior
    spikes toward the declared long-run mean.
    """
    if not isinstance(config, MeanRevertingJumpConfig):
        raise SpikeModelError("config must be MeanRevertingJumpConfig")
    if isinstance(num_simulations, bool) or not isinstance(num_simulations, int):
        raise SpikeModelError("num_simulations must be an integer")
    if num_simulations < 1:
        raise SpikeModelError("num_simulations must be at least 1")
    if config.horizon_years == 0:
        return np.full(num_simulations, config.initial_price, dtype=float)

    dt = config.horizon_years / config.steps
    if config.mean_reversion == 0:
        decay = 1.0
        diffusion_std = config.diffusion_volatility * math.sqrt(dt)
    else:
        decay = math.exp(-config.mean_reversion * dt)
        diffusion_variance = (
            config.diffusion_volatility
            * config.diffusion_volatility
            * (1.0 - math.exp(-2.0 * config.mean_reversion * dt))
            / (2.0 * config.mean_reversion)
        )
        diffusion_std = math.sqrt(max(diffusion_variance, 0.0))

    rng = np.random.default_rng(seed)
    prices = np.full(num_simulations, config.initial_price, dtype=float)
    jump_lambda = config.jump_intensity_per_year * dt

    for _ in range(config.steps):
        conditional_mean = config.long_run_mean + (prices - config.long_run_mean) * decay
        if diffusion_std > 0:
            prices = conditional_mean + diffusion_std * rng.standard_normal(num_simulations)
        else:
            prices = conditional_mean

        if jump_lambda > 0:
            counts = rng.poisson(jump_lambda, num_simulations)
            active = counts > 0
            if np.any(active):
                active_counts = counts[active].astype(float)
                jump = active_counts * config.jump_mean
                if config.jump_volatility > 0:
                    jump = jump + np.sqrt(active_counts) * config.jump_volatility * rng.standard_normal(
                        int(np.sum(active))
                    )
                prices[active] += jump

    return prices
