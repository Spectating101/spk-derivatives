# Supported Quantitative Surface

SPK Derivatives 0.5 is intentionally narrower than the historical repository tree.

The repository contains legacy research utilities, plotting helpers, early data loaders, SolarPunkCoin reference material, and demonstration scripts. Their presence does not mean every historical module is part of the same support contract as the current evidence-bound quantitative spine.

## Canonical 0.5 spine

The following modules define the supported research/beta architecture:

- `policy_lab` — fail-closed Policy Lab interoperability;
- `policy_market_bridge` — explicit, deterministic claim-unit to market-quantity binding without semantic-unit laundering;
- `artifacts` — deterministic pricing result packages;
- `policy_analysis` — explicit governance-policy sensitivity;
- `market_models` — Black-76, Bachelier, and Gaussian OU market models;
- `spike_models` — mean-reverting compound-Poisson electricity spike scenarios;
- `market_calibration` — forward curves and transparent calibration diagnostics;
- `forward_pricing` — provenance-bound forward-curve option values;
- `units` — explicit quantity conversions;
- `energy_contracts` — merchant/fixed/floor/cap/collar settlement arithmetic;
- `scenario_set` — deterministic scenario-set manifests;
- `scenario_risk` — fixed-quantity market-risk distributions and model sensitivity;
- `joint_risk` — authority-bounded joint realized-volume/price scenarios;
- `model_validation` — analytic/Monte-Carlo consistency and generic replay diagnostics;
- `market_artifacts` — deterministic market-risk packages with scenario-set binding;
- `aemo_nem` — source-hashed public AEMO NEM `DISPATCH.PRICE` ingestion for the first real-market case;
- `empirical_validation` — chronological AEMO OU holdout validation against persistence;
- `cli` — canonical command-line verification and policy/market workflows.

These modules are the focus of current validation and API design.

## Policy Lab consumer / market bridge policy

SPK 0.5 pins the Policy Lab consumer contract in `POLICY_LAB_COMPATIBILITY.json`. The pin identifies the upstream repository revision and exact claim-assessment schema blob that this downstream consumer was reviewed against. A future Policy Lab schema/profile/blob is incompatible until deliberately reviewed.

The bridge deliberately has two boundaries:

1. `policy_lab` consumes an admitted Policy Lab claim quantity and preserves the upstream authority identities.
2. `policy_market_bridge` determines whether that claim quantity can be represented in a market quantity unit for downstream risk work.

No implicit semantic conversion is allowed. Literal physical `Wh/kWh/MWh/GWh/TWh` quantities can use the exact SI conversion path. Semantic units such as `kWh-claim`, `ENERGY_CLAIM_UNIT`, certificates, credits, or other claims cannot use that shortcut. They require a `declared-semantic-mapping` with an explicit factor, named mapping authority, reference, and explanation.

The mapping receives its own deterministic `binding_id`. That identity proves which mapping was declared; it does not establish that the mapping is legally, empirically, or commercially authoritative.

See `docs/POLICY_LAB_SPK_BRIDGE.md` and `protocol/schema/policy-market-binding.v0.1.schema.json`.

## Empirical adapter policy

A market adapter can enter the canonical research/beta spine only if it keeps market data separate from Policy Lab authority and makes its transformations inspectable.

The first adapter, `aemo_nem`, follows these rules:

1. consumes a local public AEMO CSV or single-layer ZIP rather than performing hidden network access;
2. hashes the exact source file bytes with SHA-256;
3. selects one declared NEM region;
4. uses native `DISPATCH.PRICE` RRP observations in `AUD/MWh`;
5. filters to `INTERVENTION = 0` by default when that field exists;
6. converts AEMO's fixed-AEST period-ending timestamps to UTC;
7. preserves negative and spike prices without clipping or winsorization;
8. fails on ambiguous duplicate settlement timestamps;
9. emits a deterministic SPK scenario set carrying the source hash.

The first empirical model gate then keeps the source identity attached while using a chronological prefix/holdout split. OU parameters are fitted only on the prefix and frozen before the held-out suffix is scored. Persistence is reported beside OU so serial persistence cannot be mistaken for evidence of model value.

The adapter and validation gate therefore establish a reproducible market-input and evaluation boundary. They do not establish that AEMO data is Policy Lab evidence, that a scenario has a particular probability, that OU is the correct pricing model, or that a forecast improvement would translate into a profitable hedge.

See `docs/AEMO_NEM_EMPIRICAL_CASE.md`.

## Compatibility / historical surface

The following areas remain importable or present because they contain useful research history or preserve compatibility, but they are not the canonical 0.5 support boundary:

- broad `analysis` helpers;
- plotting utilities;
- `context_translator`;
- early generic/live/location data helpers;
- solar/wind/hydro loader experiments;
- `results_manager`;
- standalone demos and report-generation helpers;
- legacy SolarPunkCoin/Solidity deployment material.

They should not be cited as evidence that the current package has production-grade coverage across the entire historical repository.

## Coverage interpretation

Repository-wide coverage is diluted by the retained historical surface. The relevant release question is coverage and invariant testing on the canonical quantitative spine, not an artificially inflated global percentage obtained by deleting useful research history or writing low-value tests for dormant display/demo code.

The intended 1.0 gate is:

1. canonical spine modules are individually tested around their public contracts and failure modes;
2. deterministic artifact validators have tamper and cross-field tests;
3. model benchmarks have numerical identity/convergence tests;
4. market-specific empirical cases identify source, sample, transformation, intervention/filtering, timestamp, and calibration assumptions;
5. empirical scenario inputs are source-hashed and bound into downstream deterministic artifacts;
6. empirical model claims are scored on chronological holdouts against simple benchmarks before they can be promoted;
7. Policy Lab consumer compatibility is pinned, and semantic claim-to-market mappings are identity-bound rather than implicit;
8. compatibility modules are either promoted with equivalent validation or explicitly remain non-canonical.

This document is a scope statement, not a production-readiness claim. SPK Derivatives remains research/beta software.
