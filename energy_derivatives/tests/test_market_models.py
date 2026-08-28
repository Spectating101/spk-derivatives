import math

import numpy as np
import pytest

from spk_derivatives.market_models import (
    MarketModelError,
    bachelier_option_price,
    black76_option_price,
    ou_terminal_moments,
    simulate_ou_terminal_prices,
)


def test_black76_put_call_parity():
    call = black76_option_price(100.0, 95.0, 1.25, 0.03, 0.30, option_type="call")
    put = black76_option_price(100.0, 95.0, 1.25, 0.03, 0.30, option_type="put")
    discount = math.exp(-0.03 * 1.25)
    assert call.value - put.value == pytest.approx(discount * (100.0 - 95.0), rel=1e-12)


def test_black76_rejects_nonpositive_forward():
    with pytest.raises(MarketModelError, match="positive forward"):
        black76_option_price(0.0, 95.0, 1.0, 0.03, 0.30)


def test_bachelier_supports_negative_forward_and_parity():
    call = bachelier_option_price(-15.0, -20.0, 0.5, 0.02, 12.0, option_type="call")
    put = bachelier_option_price(-15.0, -20.0, 0.5, 0.02, 12.0, option_type="put")
    discount = math.exp(-0.02 * 0.5)
    assert call.value > 0
    assert call.value - put.value == pytest.approx(discount * 5.0, rel=1e-12)
    assert call.volatility_unit == "price-per-sqrt-year"


def test_zero_volatility_reduces_to_discounted_intrinsic():
    result = bachelier_option_price(80.0, 100.0, 2.0, 0.05, 0.0, option_type="put")
    assert result.value == pytest.approx(math.exp(-0.1) * 20.0)


def test_ou_moments_mean_revert_and_allow_negative_prices():
    mean, variance = ou_terminal_moments(-40.0, 25.0, 3.0, 18.0, 0.5)
    assert -40.0 < mean < 25.0
    assert variance > 0


def test_ou_simulation_is_seed_reproducible():
    first = simulate_ou_terminal_prices(50.0, 45.0, 2.0, 10.0, 0.25, num_simulations=128, seed=7)
    second = simulate_ou_terminal_prices(50.0, 45.0, 2.0, 10.0, 0.25, num_simulations=128, seed=7)
    assert np.array_equal(first, second)
