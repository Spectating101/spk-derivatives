"""Explicit quantity conversions for SPK Derivatives.

Core pricing and contract functions intentionally reject unit mismatches. When a
conversion is required, it must be represented as a first-class object rather
than occurring implicitly inside valuation code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict

from .artifacts import sha256_hex


class UnitConversionError(ValueError):
    """Raised when an explicit quantity conversion is invalid."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UnitConversionError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise UnitConversionError(f"{name} must be finite")
    return number


@dataclass(frozen=True)
class QuantityConversion:
    source_unit: str
    target_unit: str
    factor: float
    method: str
    reference: str

    def __post_init__(self) -> None:
        if not self.source_unit.strip() or not self.target_unit.strip():
            raise UnitConversionError("source_unit and target_unit must be non-empty")
        factor = _finite(self.factor, "factor")
        if factor <= 0:
            raise UnitConversionError("factor must be positive")
        if not self.method.strip():
            raise UnitConversionError("method must be non-empty")
        if not self.reference.strip():
            raise UnitConversionError("reference must be non-empty")

    @property
    def conversion_id(self) -> str:
        return sha256_hex(
            {
                "source_unit": self.source_unit,
                "target_unit": self.target_unit,
                "factor": float(self.factor),
                "method": self.method,
                "reference": self.reference,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["conversion_id"] = self.conversion_id
        return payload


@dataclass(frozen=True)
class ConvertedQuantity:
    source_value: float
    source_unit: str
    target_value: float
    target_unit: str
    factor: float
    conversion_id: str
    method: str
    reference: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def convert_quantity(value: float, conversion: QuantityConversion) -> ConvertedQuantity:
    """Apply one declared conversion and retain its identity."""
    source = _finite(value, "value")
    if source < 0:
        raise UnitConversionError("quantity cannot be negative")
    return ConvertedQuantity(
        source_value=source,
        source_unit=conversion.source_unit,
        target_value=source * float(conversion.factor),
        target_unit=conversion.target_unit,
        factor=float(conversion.factor),
        conversion_id=conversion.conversion_id,
        method=conversion.method,
        reference=conversion.reference,
    )


_SI_WATT_HOUR_SCALE = {
    "Wh": 1.0,
    "kWh": 1e3,
    "MWh": 1e6,
    "GWh": 1e9,
    "TWh": 1e12,
}


def si_energy_conversion(source_unit: str, target_unit: str) -> QuantityConversion:
    """Return an explicit SI watt-hour prefix conversion.

    This helper is intentionally narrow. Semantic units such as ``kWh-claim`` or
    certificates are not assumed equivalent to physical watt-hours.
    """
    if source_unit not in _SI_WATT_HOUR_SCALE or target_unit not in _SI_WATT_HOUR_SCALE:
        raise UnitConversionError(
            "SI energy conversion supports only Wh, kWh, MWh, GWh, and TWh"
        )
    factor = _SI_WATT_HOUR_SCALE[source_unit] / _SI_WATT_HOUR_SCALE[target_unit]
    return QuantityConversion(
        source_unit=source_unit,
        target_unit=target_unit,
        factor=factor,
        method="SI-watt-hour-prefix",
        reference="Exact SI decimal prefix conversion",
    )
