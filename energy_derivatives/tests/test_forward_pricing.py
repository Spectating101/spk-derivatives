import pytest

from spk_derivatives.forward_pricing import ForwardPricingError, price_forward_curve_option
from spk_derivatives.market_calibration import MarketCalibrationError, build_forward_curve


def _curve():
    return build_forward_curve(
        [(0.25, 40.0), (0.50, 50.0), (1.00, 60.0)],
        currency="USD",
        quantity_unit="MWh",
        observed_at_utc="2026-08-29T00:00:00Z",
        source="curve fixture",
        source_hash="a" * 64,
    )


def test_black76_curve_pricing_retains_market_provenance():
    result = price_forward_curve_option(
        _curve(), 0.5, 50.0, 0.03, 0.25, model="black-76"
    )
    assert result.model == "black-76"
    assert result.forward == 50.0
    assert result.price_unit == "USD/MWh"
    assert result.curve_source == "curve fixture"
    assert result.curve_source_hash == "a" * 64
    assert result.unit_value > 0


def test_bachelier_curve_pricing_can_use_negative_forward():
    curve = build_forward_curve(
        [(0.25, -20.0), (0.50, -10.0)],
        currency="EUR",
        quantity_unit="MWh",
        observed_at_utc="2026-08-29T00:00:00Z",
        source="negative fixture",
    )
    result = price_forward_curve_option(
        curve, 0.25, -15.0, 0.02, 10.0, model="bachelier"
    )
    assert result.forward == -20.0
    assert result.unit_value >= 0


def test_curve_pricing_rejects_hidden_extrapolation():
    with pytest.raises(MarketCalibrationError, match="outside observed"):
        price_forward_curve_option(_curve(), 2.0, 50.0, 0.03, 0.25)


def test_curve_pricing_requires_declared_model():
    with pytest.raises(ForwardPricingError, match="black-76"):
        price_forward_curve_option(_curve(), 0.5, 50.0, 0.03, 0.25, model="magic")
