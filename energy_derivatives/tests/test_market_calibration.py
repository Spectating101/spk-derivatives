import math

import pytest

from spk_derivatives.market_calibration import (
    MarketCalibrationError,
    build_forward_curve,
    calibrate_ou_from_series,
    estimate_lognormal_volatility,
    estimate_normal_volatility,
)


def test_forward_curve_interpolates_without_hiding_extrapolation():
    curve = build_forward_curve(
        [(0.25, 40.0), (0.50, 50.0), (1.00, 30.0)],
        currency="CNY",
        quantity_unit="MWh",
        observed_at_utc="2026-08-29T00:00:00Z",
        source="synthetic fixture",
    )
    assert curve.forward_at(0.375) == pytest.approx(45.0)
    assert curve.price_unit == "CNY/MWh"
    with pytest.raises(MarketCalibrationError, match="outside observed"):
        curve.forward_at(1.5)


def test_forward_curve_allows_negative_observed_prices():
    curve = build_forward_curve(
        [(0.25, -10.0), (0.50, 5.0)],
        currency="EUR",
        quantity_unit="MWh",
        observed_at_utc="2026-08-29T00:00:00Z",
        source="negative-price fixture",
    )
    assert curve.forward_at(0.25) == -10.0


def test_normal_volatility_uses_price_change_units():
    estimate = estimate_normal_volatility([10.0, 12.0, 9.0, 13.0], 0.25)
    assert estimate.volatility > 0
    assert estimate.volatility_unit == "price-per-sqrt-year"


def test_lognormal_volatility_rejects_nonpositive_prices():
    with pytest.raises(MarketCalibrationError, match="strictly positive"):
        estimate_lognormal_volatility([10.0, 0.0, 11.0], 1 / 252)


def test_ou_calibration_recovers_exact_ar1_mapping():
    values = [10.0]
    for _ in range(12):
        values.append(5.0 + 0.8 * values[-1])
    calibration = calibrate_ou_from_series(values, 0.25)
    assert calibration.autoregressive_coefficient == pytest.approx(0.8, rel=1e-10)
    assert calibration.long_run_mean == pytest.approx(25.0, rel=1e-10)
    assert calibration.mean_reversion == pytest.approx(-math.log(0.8) / 0.25, rel=1e-10)
    assert calibration.r_squared == pytest.approx(1.0, rel=1e-10)


def test_ou_calibration_rejects_non_mean_reverting_fit():
    with pytest.raises(MarketCalibrationError, match="strictly between 0 and 1"):
        calibrate_ou_from_series([1.0, 2.0, 4.0, 8.0, 16.0], 1.0)
