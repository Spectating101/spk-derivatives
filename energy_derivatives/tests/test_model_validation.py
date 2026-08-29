import numpy as np
import pytest

from spk_derivatives.model_validation import (
    ModelValidationError,
    historical_replay_metrics,
    validate_bachelier_monte_carlo,
    validate_black76_monte_carlo,
)


def test_black76_analytic_matches_seeded_monte_carlo_within_sampling_error():
    result = validate_black76_monte_carlo(
        100.0,
        95.0,
        1.0,
        0.03,
        0.25,
        simulations=50_000,
        seed=11,
    )
    assert abs(result.z_score) < 4.0
    assert result.relative_error < 0.03


def test_bachelier_validation_supports_negative_forward():
    result = validate_bachelier_monte_carlo(
        -10.0,
        -15.0,
        0.5,
        0.02,
        12.0,
        simulations=50_000,
        seed=13,
    )
    assert abs(result.z_score) < 4.0
    assert result.relative_error < 0.03


def test_validation_is_seed_reproducible():
    first = validate_black76_monte_carlo(
        100.0, 100.0, 0.5, 0.02, 0.20, simulations=10_000, seed=5
    )
    second = validate_black76_monte_carlo(
        100.0, 100.0, 0.5, 0.02, 0.20, simulations=10_000, seed=5
    )
    assert first == second


def test_historical_replay_metrics_are_explicit_diagnostics():
    metrics = historical_replay_metrics(
        np.array([10.0, 20.0, 30.0]),
        np.array([12.0, 18.0, 33.0]),
    )
    assert metrics.mae == pytest.approx(7.0 / 3.0)
    assert metrics.rmse > metrics.mae
    assert metrics.bias == pytest.approx(1.0)
    assert metrics.correlation is not None


def test_validation_rejects_too_few_simulations():
    with pytest.raises(ModelValidationError, match=">= 100"):
        validate_bachelier_monte_carlo(10.0, 10.0, 1.0, 0.0, 2.0, simulations=99)
