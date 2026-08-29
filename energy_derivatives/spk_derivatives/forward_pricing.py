"""Forward-curve option valuation with retained market-data provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

from .market_calibration import ForwardCurve
from .market_models import ForwardOptionValue, bachelier_option_price, black76_option_price


class ForwardPricingError(ValueError):
    """Raised when a forward-curve pricing request is invalid."""


@dataclass(frozen=True)
class CurveOptionValue:
    model: str
    option_type: str
    maturity_years: float
    forward: float
    strike: float
    risk_free_rate: float
    volatility: float
    volatility_unit: str
    unit_value: float
    price_unit: str
    curve_observed_at_utc: str
    curve_source: str
    curve_source_hash: str | None
    curve_interpolation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def price_forward_curve_option(
    curve: ForwardCurve,
    maturity_years: float,
    strike: float,
    risk_free_rate: float,
    volatility: float,
    *,
    model: str = "black-76",
    option_type: str = "call",
) -> CurveOptionValue:
    """Price a forward option at one observed/interpolated curve maturity.

    The curve provides only the market forward and provenance. Model choice and
    volatility remain explicit caller inputs. Extrapolation behavior is inherited
    from ``ForwardCurve`` and therefore fails closed outside observed tenors.
    """
    normalized = model.strip().lower()
    forward = curve.forward_at(maturity_years)
    if normalized == "black-76":
        priced = black76_option_price(
            forward,
            strike,
            maturity_years,
            risk_free_rate,
            volatility,
            option_type=option_type,
        )
    elif normalized == "bachelier":
        priced = bachelier_option_price(
            forward,
            strike,
            maturity_years,
            risk_free_rate,
            volatility,
            option_type=option_type,
        )
    else:
        raise ForwardPricingError("model must be 'black-76' or 'bachelier'")
    return _bind_curve(priced, curve)


def _bind_curve(priced: ForwardOptionValue, curve: ForwardCurve) -> CurveOptionValue:
    return CurveOptionValue(
        model=priced.model,
        option_type=priced.option_type,
        maturity_years=priced.maturity_years,
        forward=priced.forward,
        strike=priced.strike,
        risk_free_rate=priced.risk_free_rate,
        volatility=priced.volatility,
        volatility_unit=priced.volatility_unit,
        unit_value=priced.value,
        price_unit=curve.price_unit,
        curve_observed_at_utc=curve.observed_at_utc,
        curve_source=curve.source,
        curve_source_hash=curve.source_hash,
        curve_interpolation=curve.interpolation,
    )
