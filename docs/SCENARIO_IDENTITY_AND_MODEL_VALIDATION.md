# Scenario Identity and Model Validation

SPK Derivatives treats reproducibility and model validation as separate from model choice.

## Deterministic scenario-set manifests

`spk_derivatives.scenario_set` defines `spk_derivatives.scenario_set.v0.1`.

A scenario set records the exact scenario values together with:

- scenario kind (`market-price` or `joint-volume-price`),
- price unit and, where applicable, quantity unit,
- source and optional SHA-256 source identity,
- observation timestamp,
- model identifier and declared parameters,
- optional random seed,
- deterministic `scenario_set_id`.

A joint scenario set preserves the pairing between realized quantity and market price. The package does not independently shuffle or decorrelate paired observations.

Scenario identity does not make a scenario authoritative or probable. It establishes only which quantitative input set was used.

### Scenario manifests are now operational inputs

Scenario identity is no longer only an in-memory research helper.

The CLI can:

```text
spk-derivatives scenario-build ...
spk-derivatives verify-scenario-set ...
spk-derivatives preflight --scenario-set ...
spk-derivatives market-risk --scenario-set ...
```

`scenario-build` turns a declared market-price array plus source, observation time, price unit, model identifier, optional model parameters/source hash, and optional seed into a portable manifest. `verify-scenario-set` recomputes the identity and rejects count or content mutation.

When `market-risk` consumes a scenario manifest, the resulting `spk_derivatives.market_risk_package.v0.1` binds the exact `scenario_set_id`, scenario schema, source metadata, observation time, price unit, model declaration, parameters, seed, and scenario count into its own deterministic identity.

Raw `market-risk --prices` input remains available as a convenience path, but it must declare an observation time and is normalized into a scenario manifest before risk analysis. This prevents an anonymous JSON array from becoming an untraceable market input.

The binding proves **which quantitative scenarios were used**. It does not prove that the scenarios are statistically representative, risk-neutral, forecast-quality, regulatory, or otherwise authoritative.

## Provenance-bound forward option values

`spk_derivatives.forward_pricing.price_forward_curve_option` prices Black-76 or Bachelier options from a `ForwardCurve` while retaining:

- exact maturity and interpolated/observed forward,
- option model and volatility convention,
- curve price unit,
- observation timestamp,
- curve source and optional source hash,
- interpolation rule.

The function inherits the forward curve's fail-closed tenor behavior: no implicit extrapolation is performed.

## Analytic versus Monte Carlo validation

`spk_derivatives.model_validation` provides seeded Monte Carlo checks against the analytic Black-76 and Bachelier formulas under matching assumptions.

The validation object reports:

- analytic value,
- Monte Carlo estimate,
- Monte Carlo standard error,
- absolute and relative error,
- error z-score,
- simulation count and seed.

This answers a narrow implementation question: *does the simulation converge toward the analytic benchmark under the same model?*

It does not answer whether Black-76 or Bachelier is empirically appropriate for a particular electricity, PPA, certificate, or other market.

## Historical replay diagnostics

`historical_replay_metrics` compares aligned modeled and observed series using:

- mean absolute error,
- root mean squared error,
- mean bias,
- correlation where defined.

These are diagnostics, not a forecast-performance certification. Market-specific evaluation must declare the data sample, sampling rule, out-of-sample design where relevant, transformations, and any model-selection process.

## Validation hierarchy

SPK's intended validation hierarchy is:

1. **formula identities and numerical bounds** — parity, intrinsic bounds, deterministic limiting cases;
2. **analytic/simulation consistency** — seeded Monte Carlo against known formula benchmarks;
3. **scenario reproducibility** — exact scenario-set identity and source/model declarations;
4. **artifact binding** — downstream market-risk artifacts name the exact scenario-set identity they consumed;
5. **historical replay** — transparent empirical diagnostics on declared data;
6. **market-specific model validation** — a future case-specific layer requiring real market data and documented calibration design.

Passing a lower layer does not imply passing a higher layer.

The repository remains research/beta software. None of these validation surfaces establish suitability for live trading, hedging advice, execution, legal settlement, or regulatory use.
