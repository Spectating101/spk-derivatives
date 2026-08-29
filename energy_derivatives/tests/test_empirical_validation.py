from datetime import datetime, timedelta, timezone

import pytest

from spk_derivatives.aemo_nem import AEMOPriceObservation, AEMOPriceSeries
from spk_derivatives.empirical_validation import (
    EmpiricalValidationError,
    validate_aemo_ou_holdout,
)


def _mean_reverting_series(count=80):
    values = []
    price = 90.0
    noise = (2.0, -1.5, 0.5, -0.75, 1.25, -0.25)
    for index in range(count):
        price = 50.0 + 0.82 * (price - 50.0) + noise[index % len(noise)]
        values.append(price)

    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    observations = tuple(
        AEMOPriceObservation(
            settlement_utc=(start + timedelta(minutes=5 * index)).isoformat().replace(
                "+00:00", "Z"
            ),
            region_id="NSW1",
            rrp_aud_per_mwh=value,
            intervention="0",
        )
        for index, value in enumerate(values)
    )
    return AEMOPriceSeries(
        region_id="NSW1",
        price_unit="AUD/MWh",
        observations=observations,
        source="synthetic-aemo-format-fixture",
        source_hash="a" * 64,
        report_dataset="DISPATCH",
        report_table="PRICE",
        intervention_filter="0",
    )


def test_aemo_ou_holdout_is_chronological_and_deterministic():
    series = _mean_reverting_series()

    first = validate_aemo_ou_holdout(series, train_fraction=0.7)
    second = validate_aemo_ou_holdout(series, train_fraction=0.7)

    assert first.train_observations == 56
    assert first.test_observations == 24
    assert first.observations == 80
    assert first.calibration.autoregressive_coefficient > 0
    assert first.calibration.autoregressive_coefficient < 1
    assert first.persistence_metrics.observations == 24
    assert first.ou_metrics.observations == 24
    assert isinstance(first.ou_lower_rmse_than_persistence, bool)
    assert first.validation_id == second.validation_id
    assert len(first.validation_id) == 64


def test_aemo_ou_holdout_does_not_refit_on_test_suffix():
    original = _mean_reverting_series()
    changed = _mean_reverting_series()
    observations = list(changed.observations)
    for index in range(56, len(observations)):
        item = observations[index]
        observations[index] = AEMOPriceObservation(
            settlement_utc=item.settlement_utc,
            region_id=item.region_id,
            rrp_aud_per_mwh=item.rrp_aud_per_mwh + 500.0,
            intervention=item.intervention,
        )
    changed = AEMOPriceSeries(
        region_id=changed.region_id,
        price_unit=changed.price_unit,
        observations=tuple(observations),
        source=changed.source,
        source_hash="b" * 64,
        report_dataset=changed.report_dataset,
        report_table=changed.report_table,
        intervention_filter=changed.intervention_filter,
    )

    first = validate_aemo_ou_holdout(original, train_fraction=0.7)
    second = validate_aemo_ou_holdout(changed, train_fraction=0.7)

    assert first.calibration == second.calibration
    assert first.ou_metrics != second.ou_metrics
    assert first.validation_id != second.validation_id


def test_aemo_ou_holdout_rejects_too_short_series():
    series = _mean_reverting_series(count=19)

    with pytest.raises(EmpiricalValidationError, match="at least 20"):
        validate_aemo_ou_holdout(series)


def test_aemo_ou_holdout_rejects_bad_split_fraction():
    series = _mean_reverting_series()

    with pytest.raises(EmpiricalValidationError, match="train_fraction"):
        validate_aemo_ou_holdout(series, train_fraction=0.99)
