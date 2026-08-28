"""Chronological empirical validation for source-bound electricity-price series.

The first implementation is intentionally narrow: fit an OU diagnostic on an
AEMO NEM training prefix, then compare one-step conditional-mean forecasts with
a persistence baseline on the held-out suffix. This is an empirical model-fit
check, not a risk-neutral calibration or trading-strategy backtest.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict

import numpy as np

from .aemo_nem import AEMOPriceSeries
from .artifacts import sha256_hex
from .market_calibration import (
    OUCalibration,
    VolatilityEstimate,
    calibrate_ou_from_series,
    estimate_normal_volatility,
)
from .model_validation import ReplayMetrics, historical_replay_metrics


FIVE_MINUTES_IN_YEARS = 5.0 / (60.0 * 24.0 * 365.25)


class EmpiricalValidationError(ValueError):
    """Raised when an empirical validation design is invalid."""


@dataclass(frozen=True)
class AEMOOUValidation:
    region_id: str
    price_unit: str
    source_hash: str
    observations: int
    train_observations: int
    test_observations: int
    step_years: float
    split_fraction: float
    calibration: OUCalibration
    normal_volatility: VolatilityEstimate
    persistence_metrics: ReplayMetrics
    ou_metrics: ReplayMetrics
    ou_lower_rmse_than_persistence: bool
    design: str = "chronological-prefix-fit-one-step-holdout"

    def identity_body(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "price_unit": self.price_unit,
            "source_hash": self.source_hash,
            "observations": self.observations,
            "train_observations": self.train_observations,
            "test_observations": self.test_observations,
            "step_years": self.step_years,
            "split_fraction": self.split_fraction,
            "calibration": self.calibration.to_dict(),
            "normal_volatility": self.normal_volatility.to_dict(),
            "persistence_metrics": self.persistence_metrics.to_dict(),
            "ou_metrics": self.ou_metrics.to_dict(),
            "ou_lower_rmse_than_persistence": self.ou_lower_rmse_than_persistence,
            "design": self.design,
        }

    @property
    def validation_id(self) -> str:
        return sha256_hex(self.identity_body())

    def to_dict(self) -> Dict[str, Any]:
        payload = self.identity_body()
        payload["validation_id"] = self.validation_id
        return payload


def validate_aemo_ou_holdout(
    series: AEMOPriceSeries,
    *,
    train_fraction: float = 0.70,
    step_years: float = FIVE_MINUTES_IN_YEARS,
) -> AEMOOUValidation:
    """Fit OU on a chronological prefix and score one-step holdout predictions.

    The holdout uses only the previous observed price as state. Parameters are
    fixed from the training prefix; the test suffix is never used to re-fit the
    OU process. Persistence (`P[t+1] = P[t]`) is reported as the minimum useful
    benchmark so a low absolute error is not mistaken for model value.
    """
    if isinstance(train_fraction, bool) or not isinstance(train_fraction, (int, float)):
        raise EmpiricalValidationError("train_fraction must be numeric")
    fraction = float(train_fraction)
    if not 0.5 <= fraction < 0.95:
        raise EmpiricalValidationError("train_fraction must lie in [0.5, 0.95)")
    if isinstance(step_years, bool) or not isinstance(step_years, (int, float)):
        raise EmpiricalValidationError("step_years must be numeric")
    step = float(step_years)
    if not math.isfinite(step) or step <= 0:
        raise EmpiricalValidationError("step_years must be finite and positive")

    prices = np.asarray(series.prices, dtype=float)
    if prices.ndim != 1 or prices.size < 20:
        raise EmpiricalValidationError("empirical holdout requires at least 20 observations")
    split = int(math.floor(prices.size * fraction))
    if split < 10 or prices.size - split < 5:
        raise EmpiricalValidationError("train/test split is too small for validation")

    train = prices[:split]
    calibration = calibrate_ou_from_series(train, step)
    normal_volatility = estimate_normal_volatility(train, step)

    previous = prices[split - 1 : -1]
    actual = prices[split:]
    persistence = previous.copy()
    decay = math.exp(-calibration.mean_reversion * step)
    ou_prediction = calibration.long_run_mean + (
        previous - calibration.long_run_mean
    ) * decay

    persistence_metrics = historical_replay_metrics(actual, persistence)
    ou_metrics = historical_replay_metrics(actual, ou_prediction)

    return AEMOOUValidation(
        region_id=series.region_id,
        price_unit=series.price_unit,
        source_hash=series.source_hash,
        observations=int(prices.size),
        train_observations=int(split),
        test_observations=int(actual.size),
        step_years=step,
        split_fraction=fraction,
        calibration=calibration,
        normal_volatility=normal_volatility,
        persistence_metrics=persistence_metrics,
        ou_metrics=ou_metrics,
        ou_lower_rmse_than_persistence=ou_metrics.rmse < persistence_metrics.rmse,
    )
