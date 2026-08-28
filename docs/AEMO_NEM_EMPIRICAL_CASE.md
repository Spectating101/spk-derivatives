# AEMO NEM Empirical Market Case

This case is the first explicit real-market adapter in the SPK 0.5 quantitative spine. It is deliberately narrow: public Australian National Electricity Market wholesale prices become a provenance-bearing **market input**, while Policy Lab remains the separate authority for evidence, policy admission, and bounded physical quantity.

The purpose is to test the architecture against a market where negative prices and extreme positive spikes are normal enough that a lognormal-only abstraction is visibly insufficient.

## Why AEMO NEM

AEMO publishes public National Electricity Market data through NEMWeb and the MMS data archive. Its public `DISPATCH.PRICE` table contains five-minute regional price observations, including regional reference price (`RRP`). AEMO documents RRP as the spot price at the regional reference node in dollars per MWh, exclusive of GST.

Official references:

- NEM data: <https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem>
- Dispatch data: <https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-management-system-mms-data/dispatch>
- NEMWeb: <https://www.nemweb.com.au/>
- Historical MMSDM archive: <https://www.nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/>

A concrete stable research source visible in the June 2026 MMSDM archive is:

```text
2026/MMSDM_2026_06/MMSDM_Historical_Data_SQLLoader/DATA/
PUBLIC_ARCHIVE#DISPATCHPRICE#FILE01#202606010000.zip
```

SPK does **not** redistribute that AEMO archive. The case consumes a locally downloaded copy and computes a SHA-256 identity over the exact file bytes.

## Market-clock and settlement conventions

The adapter treats AEMO market timestamps as fixed AEST (`UTC+10`) and converts them to UTC for SPK artifacts. AEMO interval timestamps are period-ending.

For the post-five-minute-settlement NEM, this case uses native `DISPATCH.PRICE` observations rather than silently constructing a 30-minute synthetic series. `INTERVENTION = 0` is retained by default when the field is available so market-pricing and physical intervention runs are not mixed.

If the source contains ambiguous duplicate timestamps after filtering, SPK fails closed rather than choosing a row.

## Ingestion boundary

`spk_derivatives.aemo_nem` provides:

```python
load_aemo_nem_dispatch_prices(...)
aemo_price_series_to_scenario_set(...)
```

The loader accepts a local CSV or a single-layer ZIP containing CSV files. Nested ZIP archives are rejected instead of recursively unpacked. This avoids silently traversing arbitrary archive structures and keeps the source identity obvious.

The resulting `AEMOPriceSeries` binds:

- NEM region (`NSW1`, `QLD1`, `SA1`, `TAS1`, `VIC1`),
- exact source path and SHA-256 file hash,
- `DISPATCH.PRICE` table identity,
- intervention filter,
- UTC interval range,
- native `AUD/MWh` unit,
- exact ordered RRP observations.

Negative prices and extreme positive prices are preserved. There is no winsorization, clipping, aggregation, or hidden unit conversion in the ingestion layer.

## Build a deterministic scenario manifest

After downloading an AEMO source file locally:

```bash
python case_studies/aemo_nem/build_scenario.py \
  ./PUBLIC_ARCHIVE#DISPATCHPRICE#FILE01#202606010000.zip \
  --region NSW1 \
  --out ./artifacts/aemo-nsw1-2026-06.scenario.json
```

The output scenario set records the exact source hash and receives its own deterministic `scenario_set_id`.

That scenario set can then be passed into the canonical Policy Lab → SPK risk chain:

```bash
spk-derivatives market-risk ./claim-assessment.json \
  --scenario-set ./artifacts/aemo-nsw1-2026-06.scenario.json \
  --contract-type floor \
  --currency AUD \
  --floor-price 80 \
  --package-out ./artifacts/aemo-nsw1-floor.market-risk.json \
  --json
```

The command will still reject the operation if the Policy Lab quantity unit and contract/scenario price unit do not form an exact declared unit pair. A physical `MWh` claim can naturally pair with `AUD/MWh`; a semantic unit such as `kWh-claim` cannot be silently treated as physical energy.

## What this case can test

The AEMO surface is suitable for the next empirical validation wave:

1. historical price replay with native negative prices and spikes;
2. Bachelier versus OU versus mean-reverting jump/spike scenario comparison;
3. calibration-window sensitivity;
4. floor/cap/collar/PPA-style contract consequences under one fixed admitted quantity;
5. model sensitivity versus Policy Lab governance-policy sensitivity;
6. later joint renewable-volume/price analysis once an explicitly aligned generation series is introduced.

The adapter does not yet claim an empirical winner among those models. It creates a reproducible input boundary on which such tests can be run.

## What this case does not establish

AEMO market data is not Policy Lab evidence authority. An AEMO file hash proves which local source file was consumed, not that the data is complete, final for every downstream purpose, or appropriate for a specific hedge.

Likewise:

- historical replay is not a risk-neutral measure;
- model fit is not hedge effectiveness;
- a scenario-set identity is not probability authority;
- a computed floor/cap/collar payoff is not a traded instrument or executed hedge;
- this adapter does not imply AEMO endorsement;
- third-party data rights and AEMO notices remain applicable to downstream use.

The repository remains research/beta software.
