# Market Calibration and Risk Surface

SPK Derivatives treats renewable quantity, market price, contract structure, unit conversion, and model choice as separate analytical objects.

## Quantity does not imply price

Policy Lab remains the upstream authority for evidence, provenance, policy evaluation, and admitted quantity. SPK consumes that admitted quantity as `Q`. Market observations and calibrated price processes are a separate input `P`. No weather, irradiance, wind, hydro, or Policy Lab quantity is silently converted into a market price.

## Explicit quantity conversions

Core contract and risk functions reject unit mismatches. `spk_derivatives.units` provides a first-class `QuantityConversion` object when a conversion is genuinely required. The conversion records source unit, target unit, factor, method, reference, and a deterministic conversion identity.

The built-in SI helper is deliberately narrow: it supports only exact decimal conversions among `Wh`, `kWh`, `MWh`, `GWh`, and `TWh`. Semantic units such as `kWh-claim`, certificates, credits, or settlement entitlements are not assumed equivalent to physical energy.

## Forward curves

`spk_derivatives.market_calibration.ForwardCurve` records:

- currency and quantity unit,
- observation timestamp,
- source and optional SHA-256 source identity,
- ordered maturity/forward nodes,
- interpolation method.

Only interpolation inside the observed tenor range is supported. Extrapolation is rejected instead of being silently manufactured.

Forward prices may be negative. Model selection remains explicit: Black-76 rejects non-positive forwards, while Bachelier can represent negative forwards.

## Transparent calibration diagnostics

The package exposes three small calibration helpers:

- historical normal price-change volatility for Bachelier-style benchmarks,
- historical log-return volatility for positive-price lognormal benchmarks,
- an Ornstein-Uhlenbeck diagnostic fitted through the exact AR(1) discretization.

The OU mapping is accepted only when the fitted autoregressive coefficient lies strictly between zero and one. A non-mean-reverting historical fit is rejected rather than coerced into an OU process.

Historical calibration is descriptive. It does not establish a risk-neutral measure, prove model adequacy, or imply that the fitted process should be used for a live hedge.

## Contract scenario distributions

`spk_derivatives.scenario_risk` applies explicit market-price scenarios to one fixed quantity and contract. It reports:

- mean and standard deviation of market price,
- mean and standard deviation of contract value,
- 5th/50th/95th percentile contract values,
- mean merchant-market value,
- mean protection value relative to merchant exposure,
- probability of negative contract value.

For Policy Lab exposures, the distribution retains the original assessment, source-package, claim, policy, decision, evidence-hash, and assurance identities.

## Joint volume-price risk

Fixed quantity is useful for isolating market-model sensitivity, but renewable exposure also contains realized-volume risk. `spk_derivatives.joint_risk` accepts paired quantity and market-price scenarios so physical volume and market price remain separate while preserving any empirical dependence between them.

For Policy Lab exposures, realized quantity scenarios are capped at the selected policy's admitted quantity. Any scenario above that cap is rejected rather than silently expanding upstream authority. The joint summary reports realized quantity statistics, price statistics, quantity-price correlation, cap utilization, merchant and contract values, downside quantiles, and protection value.

This makes three different sensitivity questions explicit:

1. **policy sensitivity** — change governance policy while holding market/model assumptions fixed;
2. **market-model sensitivity** — change price-model scenarios while holding admitted quantity and contract fixed;
3. **joint physical/market risk** — vary realized quantity and price together inside the admitted authority envelope.

## Model sensitivity

`compare_market_model_scenarios` compares two or more named market-price scenario sets under the same quantity and contract terms. The resulting expected-value and downside ranges are explicitly labeled **model sensitivity**.

They are not:

- evidence uncertainty,
- governance-policy sensitivity,
- market truth,
- execution or liquidity guarantees.

This is deliberately complementary to `policy-sweep`, which holds market/model assumptions constant while varying governance policy. Together, the two surfaces let a researcher separate policy sensitivity from market-model sensitivity.

## Deterministic market-risk artifacts

`spk_derivatives.market_risk_package.v0.1` binds:

1. exact Policy Lab authority identifiers,
2. admitted quantity and unit,
3. declared market input provenance,
4. scenario-model declaration,
5. explicit contract terms,
6. summarized risk distribution,
7. SHA-256 semantic and full-package identities.

The JSON Schema is published at `protocol/schema/market-risk-package.v0.1.schema.json`. The Python validator adds cross-field checks that JSON Schema alone cannot express, including quantity/unit consistency, authority identity shape, ordered quantiles, protection-value consistency, and deterministic identity verification.

## CLI surface

`spk-derivatives market-risk` accepts a Policy Lab assessment, an explicit JSON array of price scenarios, and declared contract terms. It can emit `market_risk_package.v0.1`. `verify-market-risk` and `preflight --market-risk-package` verify the resulting deterministic identities and cross-field invariants.

## Intended next empirical layer

A future market-specific case can add real power/forward/GEC/PPA observations and record their source identity in the forward curve or market-risk package. The framework should then compare transparent benchmark models against historical replay and calibrated mean-reverting scenarios without changing the Policy Lab authority result.

The package remains research/beta software. No market-risk artifact is settlement, legal, regulatory, reserve, liquidity, or execution authority.
