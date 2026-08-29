import spk_derivatives


def test_canonical_scenario_io_is_top_level_exported():
    assert spk_derivatives.SCENARIO_SET_SCHEMA == "spk_derivatives.scenario_set.v0.1"
    assert callable(spk_derivatives.load_scenario_set)
    assert callable(spk_derivatives.validate_scenario_set)
    assert callable(spk_derivatives.write_scenario_set)


def test_spike_scenario_surface_is_top_level_exported():
    assert spk_derivatives.spike_models is not None
    config = spk_derivatives.MeanRevertingJumpConfig(
        initial_price=50.0,
        long_run_mean=45.0,
        mean_reversion=2.0,
        diffusion_volatility=8.0,
        jump_intensity_per_year=3.0,
        jump_mean=20.0,
        jump_volatility=5.0,
        horizon_years=0.25,
        steps=10,
    )
    prices = spk_derivatives.simulate_mean_reverting_jump_terminal_prices(
        config,
        num_simulations=10,
        seed=3,
    )
    assert len(prices) == 10
