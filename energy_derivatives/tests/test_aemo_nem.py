import hashlib
import zipfile

import pytest

from spk_derivatives.aemo_nem import (
    AEMONEMError,
    AEMO_NEM_PRICE_UNIT,
    aemo_price_series_to_scenario_set,
    load_aemo_nem_dispatch_prices,
)


AEMO_FIXTURE = """C,NEMP.WORLD,TEST,AEMO,PUBLIC,2026/08/29,00:00:00,1
I,DISPATCH,PRICE,5,SETTLEMENTDATE,REGIONID,RRP,INTERVENTION
D,DISPATCH,PRICE,5,\"2026/06/01 00:05:00\",NSW1,-25.50,0
D,DISPATCH,PRICE,5,\"2026/06/01 00:10:00\",NSW1,17500.00,0
D,DISPATCH,PRICE,5,\"2026/06/01 00:15:00\",NSW1,125.25,0
D,DISPATCH,PRICE,5,\"2026/06/01 00:10:00\",NSW1,999.00,1
D,DISPATCH,PRICE,5,\"2026/06/01 00:05:00\",VIC1,80.00,0
F,DISPATCH,PRICE,5,5
"""


def test_aemo_dispatch_loader_preserves_negative_and_spike_prices(tmp_path):
    source = tmp_path / "dispatch.csv"
    source.write_text(AEMO_FIXTURE, encoding="utf-8")

    series = load_aemo_nem_dispatch_prices(source, region_id="NSW1")

    assert series.price_unit == AEMO_NEM_PRICE_UNIT
    assert series.prices == (-25.5, 17500.0, 125.25)
    assert series.start_utc == "2026-05-31T14:05:00Z"
    assert series.end_utc == "2026-05-31T14:15:00Z"
    assert series.source_hash == hashlib.sha256(source.read_bytes()).hexdigest()
    assert [item.intervention for item in series.observations] == ["0", "0", "0"]


def test_aemo_dispatch_loader_filters_region(tmp_path):
    source = tmp_path / "dispatch.csv"
    source.write_text(AEMO_FIXTURE, encoding="utf-8")

    with pytest.raises(AEMONEMError, match="need at least two observations"):
        load_aemo_nem_dispatch_prices(source, region_id="VIC1")


def test_aemo_dispatch_loader_fails_on_ambiguous_intervention_runs(tmp_path):
    source = tmp_path / "dispatch.csv"
    source.write_text(AEMO_FIXTURE, encoding="utf-8")

    with pytest.raises(AEMONEMError, match="duplicate settlement timestamps"):
        load_aemo_nem_dispatch_prices(source, region_id="NSW1", intervention=None)


def test_aemo_zip_source_is_supported_and_hashes_container(tmp_path):
    source = tmp_path / "dispatch.zip"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("PUBLIC_DISPATCHPRICE.csv", AEMO_FIXTURE)

    series = load_aemo_nem_dispatch_prices(source, region_id="NSW1")

    assert series.prices == (-25.5, 17500.0, 125.25)
    assert series.source_hash == hashlib.sha256(source.read_bytes()).hexdigest()


def test_aemo_series_becomes_identity_bound_scenario_set(tmp_path):
    source = tmp_path / "dispatch.csv"
    source.write_text(AEMO_FIXTURE, encoding="utf-8")
    series = load_aemo_nem_dispatch_prices(source, region_id="NSW1")

    scenario = aemo_price_series_to_scenario_set(series)

    assert scenario.price_unit == "AUD/MWh"
    assert scenario.market_prices == series.prices
    assert scenario.source_hash == series.source_hash
    assert scenario.observed_at_utc == series.end_utc
    assert scenario.model_id == "aemo-dispatch-price-historical-replay"
    assert scenario.model_parameters["region_id"] == "NSW1"
    assert scenario.model_parameters["timestamp_convention"] == "period-ending"
    assert len(scenario.scenario_set_id) == 64


def test_aemo_loader_rejects_missing_information_row(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text(
        'D,DISPATCH,PRICE,5,"2026/06/01 00:05:00",NSW1,100,0\n'
        'D,DISPATCH,PRICE,5,"2026/06/01 00:10:00",NSW1,101,0\n',
        encoding="utf-8",
    )

    with pytest.raises(AEMONEMError, match="before its matching information row"):
        load_aemo_nem_dispatch_prices(source, region_id="NSW1")


def test_aemo_loader_rejects_nested_zip_without_csv(tmp_path):
    inner = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner, "w") as archive:
        archive.writestr("dispatch.csv", AEMO_FIXTURE)
    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as archive:
        archive.write(inner, arcname="inner.zip")

    with pytest.raises(AEMONEMError, match="Nested AEMO ZIP archives"):
        load_aemo_nem_dispatch_prices(outer, region_id="NSW1")
