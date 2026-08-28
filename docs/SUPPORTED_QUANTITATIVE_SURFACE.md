# Supported Quantitative Surface

SPK Derivatives 0.5 is intentionally narrower than the historical repository tree.

The repository contains legacy research utilities, plotting helpers, early data loaders, SolarPunkCoin reference material, and demonstration scripts. Their presence does not mean every historical module is part of the same support contract as the current evidence-bound quantitative spine.

## Canonical 0.5 spine

The following modules define the supported research/beta architecture:

- `policy_lab` — fail-closed Policy Lab interoperability;
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
- `model_validation` — analytic/Monte-Carlo consistency and replay diagnostics;
- `market_artifacts` — deterministic market-risk packages;
- `cli` — canonical command-line verification and policy/market workflows.

These modules are the focus of current validation and API design.

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
4. market-specific empirical cases identify source, sample, transformation, and calibration assumptions;
5. compatibility modules are either promoted with equivalent validation or explicitly remain non-canonical.

This document is a scope statement, not a production-readiness claim. SPK Derivatives remains research/beta software.
