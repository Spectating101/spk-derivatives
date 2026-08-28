import numpy as np
import pytest

from spk_derivatives.spike_models import (
    MeanRevertingJumpConfig,
    SpikeModelError,
    simulate_mean_reverting_jump_terminal_prices,
)


def test_jump_scenarios_are_seed_reproducible():
    config = MeanRevertingJumpConfig(
        initial_price=50.0,
        long_run_mean=45.0,
        mean_reversion=3.0,
        diffusion_volatility=10.0,
        jump_intensity_per_year=5.0,
        jump_mean=30.0,
        jump_volatility=8.0,
        horizon_years=0.5,
        steps=50,
    )
    first = simulate_mean_reverting_jump_terminal_prices(config, num_simulations=500, seed=9)
    second = simulate_mean_reverting_jump_terminal_prices(config, num_simulations=500, seed=9)
    assert np.array_equal(first, second)


def test_zero_horizon_returns_initial_price():
    config = MeanRevertingJumpConfig(
        initial_price=-20.0,
        long_run_mean=10.0,
        mean_reversion=2.0,
        diffusion_volatility=10.0,
        jump_intensity_per_year=10.0,
        jump_mean=50.0,
        jump_volatility=10.0,
        horizon_years=0.0,
    )
    result = simulate_mean_reverting_jump_terminal_prices(config, num_simulations=20, seed=1)
    assert np.all(result == -20.0)


def test_positive_deterministic_jumps_create_spike_scenarios():
    config = MeanRevertingJumpConfig(
        initial_price=0.0,
        long_run_mean=0.0,
        mean_reversion=0.0,
        diffusion_volatility=0.0,
        jump_intensity_per_year=20.0,
        jump_mean=100.0,
        jump_volatility=0.0,
        horizon_years=1.0,
        steps=20,
    )
    result = simulate_mean_reverting_jump_terminal_prices(config, num_simulations=200, seed=4)
    assert np.max(result) > 0.0
    assert np.mean(result) > 0.0


def test_spike_model_rejects_negative_jump_intensity():
    with pytest.raises(SpikeModelError, match="jump_intensity"):
        MeanRevertingJumpConfig(
            initial_price=50.0,
            long_run_mean=50.0,
            mean_reversion=2.0,
            diffusion_volatility=10.0,
            jump_intensity_per_year=-1.0,
            jump_mean=20.0,
            jump_volatility=5.0,
            horizon_years=1.0,
        )
