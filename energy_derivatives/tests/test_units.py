import pytest

from spk_derivatives.units import (
    QuantityConversion,
    UnitConversionError,
    convert_quantity,
    si_energy_conversion,
)


def test_si_energy_conversion_is_explicit_and_deterministic():
    conversion = si_energy_conversion("kWh", "MWh")
    result = convert_quantity(1500.0, conversion)
    assert result.target_value == pytest.approx(1.5)
    assert result.source_unit == "kWh"
    assert result.target_unit == "MWh"
    assert len(result.conversion_id) == 64
    assert result.conversion_id == conversion.conversion_id


def test_semantic_claim_unit_is_not_assumed_physical_energy():
    with pytest.raises(UnitConversionError, match="supports only"):
        si_energy_conversion("kWh-claim", "MWh")


def test_custom_conversion_requires_positive_factor_and_reference():
    with pytest.raises(UnitConversionError, match="positive"):
        QuantityConversion("a", "b", 0.0, "manual", "test")
    with pytest.raises(UnitConversionError, match="reference"):
        QuantityConversion("a", "b", 2.0, "manual", "")
