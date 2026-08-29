"""AEMO NEM wholesale-price ingestion for empirical SPK market scenarios.

This adapter parses public AEMO MMS CSV blocks without turning AEMO market data
into Policy Lab authority. It binds one local source file to a SHA-256 identity,
filters a declared NEM region and market-pricing run, preserves negative/spike
prices, and can convert the resulting AUD/MWh series into a deterministic SPK
scenario-set manifest.

AEMO NEM timestamps are interpreted on the market clock (AEST, UTC+10 fixed),
and are period-ending timestamps. The adapter intentionally performs no network
downloads, no hidden price aggregation, and no unit conversion.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import io
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union
import zipfile

from .scenario_set import ScenarioSet, build_market_price_scenarios


AEMO_NEM_PRICE_UNIT = "AUD/MWh"
AEMO_MARKET_TIMEZONE = timezone(timedelta(hours=10), name="AEST")
AEMO_TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"
AEMO_NEM_REGIONS = frozenset({"NSW1", "QLD1", "SA1", "TAS1", "VIC1"})


class AEMONEMError(ValueError):
    """Raised when an AEMO public-price source is malformed or ambiguous."""


@dataclass(frozen=True)
class AEMOPriceObservation:
    settlement_utc: str
    region_id: str
    rrp_aud_per_mwh: float
    intervention: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AEMOPriceSeries:
    region_id: str
    price_unit: str
    observations: Tuple[AEMOPriceObservation, ...]
    source: str
    source_hash: str
    report_dataset: str
    report_table: str
    intervention_filter: Optional[str]

    def __post_init__(self) -> None:
        if self.region_id not in AEMO_NEM_REGIONS:
            raise AEMONEMError(f"Unsupported NEM region: {self.region_id!r}")
        if self.price_unit != AEMO_NEM_PRICE_UNIT:
            raise AEMONEMError(f"AEMO RRP unit must be {AEMO_NEM_PRICE_UNIT}")
        if len(self.observations) < 2:
            raise AEMONEMError("AEMO price series requires at least two observations")
        if len(self.source_hash) != 64 or any(ch not in "0123456789abcdef" for ch in self.source_hash):
            raise AEMONEMError("source_hash must be lowercase SHA-256 hex")

        timestamps = [item.settlement_utc for item in self.observations]
        if timestamps != sorted(timestamps):
            raise AEMONEMError("AEMO observations must be sorted by settlement time")
        if len(set(timestamps)) != len(timestamps):
            raise AEMONEMError("AEMO price series contains duplicate settlement timestamps")
        for item in self.observations:
            if item.region_id != self.region_id:
                raise AEMONEMError("AEMO observation region does not match series region")
            if not math.isfinite(item.rrp_aud_per_mwh):
                raise AEMONEMError("AEMO RRP values must be finite")

    @property
    def prices(self) -> Tuple[float, ...]:
        return tuple(item.rrp_aud_per_mwh for item in self.observations)

    @property
    def start_utc(self) -> str:
        return self.observations[0].settlement_utc

    @property
    def end_utc(self) -> str:
        return self.observations[-1].settlement_utc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "price_unit": self.price_unit,
            "observations": [item.to_dict() for item in self.observations],
            "source": self.source,
            "source_hash": self.source_hash,
            "report_dataset": self.report_dataset,
            "report_table": self.report_table,
            "intervention_filter": self.intervention_filter,
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _aemo_timestamp_to_utc(value: str) -> str:
    try:
        local = datetime.strptime(value.strip(), AEMO_TIMESTAMP_FORMAT).replace(
            tzinfo=AEMO_MARKET_TIMEZONE
        )
    except ValueError as exc:
        raise AEMONEMError(f"Invalid AEMO settlement timestamp: {value!r}") from exc
    return local.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _finite_price(value: str) -> float:
    try:
        price = float(value)
    except (TypeError, ValueError) as exc:
        raise AEMONEMError(f"Invalid AEMO RRP value: {value!r}") from exc
    if not math.isfinite(price):
        raise AEMONEMError("AEMO RRP values must be finite")
    return price


def _normal_region(region_id: str) -> str:
    region = region_id.strip().upper()
    if region not in AEMO_NEM_REGIONS:
        raise AEMONEMError(
            f"region_id must be one of {sorted(AEMO_NEM_REGIONS)}, got {region_id!r}"
        )
    return region


def _iter_csv_payloads(path: Path) -> Iterable[Tuple[str, bytes]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        yield path.name, path.read_bytes()
        return
    if suffix != ".zip":
        raise AEMONEMError("AEMO source must be a .csv or single-layer .zip archive")

    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                item
                for item in archive.namelist()
                if not item.endswith("/") and item.lower().endswith(".csv")
            ]
            nested = [
                item
                for item in archive.namelist()
                if not item.endswith("/") and item.lower().endswith(".zip")
            ]
            if nested and not names:
                raise AEMONEMError(
                    "Nested AEMO ZIP archives are not expanded implicitly; extract the target CSV first"
                )
            if not names:
                raise AEMONEMError("AEMO ZIP archive contains no CSV files")
            for name in sorted(names):
                yield name, archive.read(name)
    except zipfile.BadZipFile as exc:
        raise AEMONEMError(f"Invalid AEMO ZIP archive: {path}") from exc


def _parse_price_csv_bytes(
    payload: bytes,
    *,
    region_id: str,
    dataset: str,
    table: str,
    intervention: Optional[str],
) -> List[AEMOPriceObservation]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AEMONEMError("AEMO CSV must be UTF-8 compatible") from exc

    target_dataset = dataset.strip().upper()
    target_table = table.strip().upper()
    headers: Dict[Tuple[str, str, str], Sequence[str]] = {}
    observations: List[AEMOPriceObservation] = []

    for row_number, row in enumerate(csv.reader(io.StringIO(text)), start=1):
        if not row:
            continue
        record_type = row[0].strip().upper()
        if record_type not in {"I", "D"} or len(row) < 4:
            continue
        row_dataset = row[1].strip().upper()
        row_table = row[2].strip().upper()
        version = row[3].strip()
        key = (row_dataset, row_table, version)

        if record_type == "I":
            headers[key] = tuple(item.strip().upper() for item in row[4:])
            continue
        if row_dataset != target_dataset or row_table != target_table:
            continue
        columns = headers.get(key)
        if columns is None:
            raise AEMONEMError(
                f"AEMO data row {row_number} appeared before its matching information row"
            )
        values = list(row[4:])
        if len(values) < len(columns):
            values.extend([""] * (len(columns) - len(values)))
        record = dict(zip(columns, values[: len(columns)]))

        missing = [name for name in ("SETTLEMENTDATE", "REGIONID", "RRP") if name not in record]
        if missing:
            raise AEMONEMError(
                f"AEMO {row_dataset}.{row_table} header is missing required columns: {missing}"
            )
        if record["REGIONID"].strip().upper() != region_id:
            continue

        intervention_value = record.get("INTERVENTION")
        normalized_intervention = (
            intervention_value.strip() if intervention_value is not None else None
        )
        if intervention is not None and normalized_intervention is not None:
            if normalized_intervention != intervention:
                continue

        observations.append(
            AEMOPriceObservation(
                settlement_utc=_aemo_timestamp_to_utc(record["SETTLEMENTDATE"]),
                region_id=region_id,
                rrp_aud_per_mwh=_finite_price(record["RRP"]),
                intervention=normalized_intervention,
            )
        )

    return observations


def load_aemo_nem_dispatch_prices(
    source: Union[str, Path],
    *,
    region_id: str,
    intervention: Optional[str] = "0",
) -> AEMOPriceSeries:
    """Load public AEMO DISPATCH.PRICE observations from a local CSV or ZIP.

    The adapter uses native five-minute DISPATCH.PRICE RRP observations, which
    are the natural post-five-minute-settlement market input. If an INTERVENTION
    field is present, the default keeps the market-pricing run (`0`). Passing
    ``intervention=None`` retains all runs but duplicate timestamps then fail
    closed rather than being silently resolved.
    """
    path = Path(source)
    if not path.is_file():
        raise AEMONEMError(f"AEMO source file does not exist: {path}")
    region = _normal_region(region_id)
    source_bytes = path.read_bytes()
    source_hash = _sha256_bytes(source_bytes)

    observations: List[AEMOPriceObservation] = []
    for _, payload in _iter_csv_payloads(path):
        observations.extend(
            _parse_price_csv_bytes(
                payload,
                region_id=region,
                dataset="DISPATCH",
                table="PRICE",
                intervention=intervention,
            )
        )
    observations.sort(key=lambda item: item.settlement_utc)
    if len(observations) < 2:
        raise AEMONEMError(
            f"No usable AEMO DISPATCH.PRICE series for {region}; need at least two observations"
        )

    return AEMOPriceSeries(
        region_id=region,
        price_unit=AEMO_NEM_PRICE_UNIT,
        observations=tuple(observations),
        source=str(path),
        source_hash=source_hash,
        report_dataset="DISPATCH",
        report_table="PRICE",
        intervention_filter=intervention,
    )


def aemo_price_series_to_scenario_set(
    series: AEMOPriceSeries,
    *,
    model_id: str = "aemo-dispatch-price-historical-replay",
    model_parameters: Optional[Mapping[str, Any]] = None,
) -> ScenarioSet:
    """Bind one exact AEMO regional price series into an SPK scenario manifest."""
    parameters: Dict[str, Any] = {
        "region_id": series.region_id,
        "report_dataset": series.report_dataset,
        "report_table": series.report_table,
        "intervention_filter": series.intervention_filter,
        "market_clock": "AEST UTC+10 fixed",
        "timestamp_convention": "period-ending",
        "scenario_interpretation": "historical empirical replay",
    }
    if model_parameters:
        parameters.update(dict(model_parameters))
    return build_market_price_scenarios(
        series.prices,
        price_unit=series.price_unit,
        source=f"AEMO NEM {series.report_dataset}.{series.report_table} {series.region_id}: {series.source}",
        source_hash=series.source_hash,
        observed_at_utc=series.end_utc,
        model_id=model_id,
        model_parameters=parameters,
        seed=None,
    )
