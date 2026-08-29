# SPK Derivatives

**Policy-aware quantitative pricing, market-risk, and scenario tooling for renewable-energy exposures.**

SPK Derivatives is a research/beta Python framework for separating and analyzing the distinct layers of an energy-linked financial conclusion:

**evidence → governance policy → admitted physical quantity → market data/model → contract payoff → quantitative value/risk**

The package began as a solar-energy derivatives research prototype. The current `0.5` line makes the boundaries explicit rather than treating renewable output, market price, policy authority, and settlement as one object.

## What SPK owns

SPK Derivatives owns downstream quantitative work:

- binomial and Monte-Carlo benchmark pricing;
- Black-76 and Bachelier forward-option benchmarks;
- Ornstein-Uhlenbeck mean-reverting market-price scenarios;
- provenance-bearing forward curves and transparent calibration diagnostics;
- explicit merchant, fixed-price, floor, cap, and collar settlement arithmetic;
- market-risk distributions and market-model sensitivity;
- joint realized-volume / market-price risk;
- deterministic result artifacts;
- Policy Lab interoperability and policy-sensitive valuation.

SPK does **not** decide whether evidence is true, whether a claim is legally valid, which governance policy should apply, whether a trade can execute, or whether a modeled result constitutes settlement.

## Policy Lab boundary

Policy Lab is the upstream authority layer. SPK consumes `policylab.claim_assessment_package.v0.1` packages using profile `policylab.energy_linked_claim.v0`.

SPK only prices quantities Policy Lab has already admitted. It fails closed on unsupported schemas/profiles, malformed identities, blocked decisions, missing supported quantities, unit mismatches, ambiguous multi-policy admission, and invalid assurance identifiers.

A Policy Lab quantity is an authority-bounded `Q`. It is **not** a market price.

## Quantity and market price are separate

The core market architecture separates:

- `Q(t)`: physical / admitted quantity;
- `P(t)`: market price;
- contract terms: how `Q` and `P` map to a payoff.

A weather or metering observation may support physical quantity without implying that electricity, a PPA, a green certificate, or another market instrument follows the same stochastic process.

### Forward and price models

```python
from spk_derivatives import (
    black76_option_price,
    bachelier_option_price,
    ou_terminal_moments,
    simulate_ou_terminal_prices,
)
```

- **Black-76** is available as a transparent positive-forward benchmark.
- **Bachelier** supports normal-forward pricing and can represent negative power prices.
- **Ornstein-Uhlenbeck** provides exact terminal moments and reproducible mean-reverting terminal scenarios. OU scenarios are not automatically a risk-neutral pricing measure.

## Forward curves and calibration

```python
from spk_derivatives import (
    build_forward_curve,
    estimate_normal_volatility,
    estimate_lognormal_volatility,
    calibrate_ou_from_series,
)

curve = build_forward_curve(
    [(0.25, 410.0), (0.5, 425.0), (1.0, 440.0)],
    currency="CNY",
    quantity_unit="MWh",
    observed_at_utc="2026-08-29T00:00:00Z",
    source="declared market-data source",
)

six_month_forward = curve.forward_at(0.5)
```

Forward-curve interpolation is allowed only inside observed maturities. Extrapolation is rejected rather than silently manufactured.

Calibration helpers expose:

- historical normal price-change volatility;
- historical positive-price log-return volatility;
- diagnostic OU calibration through the exact AR(1) discretization.

Historical calibration is descriptive evidence about a chosen sample, not proof of model adequacy or a risk-neutral measure.

## Explicit unit conversions

Core contract/risk functions reject unit mismatches. When conversion is required, it is a first-class object:

```python
from spk_derivatives import si_energy_conversion, convert_quantity

conversion = si_energy_conversion("kWh", "MWh")
converted = convert_quantity(1500.0, conversion)
assert converted.target_value == 1.5
```

The built-in helper only converts exact SI watt-hour prefixes (`Wh`, `kWh`, `MWh`, `GWh`, `TWh`). Semantic units such as `kWh-claim`, certificates, credits, or entitlements are not assumed equivalent to physical energy.

## Explicit contract layer

```python
from spk_derivatives import EnergyContract, settle_energy_contract

ppa = EnergyContract(
    "fixed-price",
    currency="CNY",
    quantity_unit="MWh",
    fixed_price=380.0,
)

result = settle_energy_contract(
    quantity=100.0,
    quantity_unit="MWh",
    market_price=420.0,
    contract=ppa,
)
```

Supported deterministic settlement rules:

- merchant;
- fixed-price;
- floor;
- cap;
- collar.

These functions perform scenario arithmetic. They do not create legal settlement authority or execute trades.

## Market-risk distributions

`spk_derivatives.scenario_risk` applies a market-price scenario set to one fixed quantity and contract and reports:

- market-price mean / standard deviation;
- contract-value mean / standard deviation;
- 5th / 50th / 95th percentile contract values;
- mean merchant-market value;
- mean protection value relative to merchant exposure;
- probability of negative contract value.

For Policy Lab exposures, upstream assessment, claim, policy, decision, evidence hash, assurance, and package identities remain attached.

## Joint volume-price risk

Renewable volume and power price can be correlated without being the same stochastic object. `spk_derivatives.joint_risk` accepts paired realized-quantity and price scenarios.

For Policy Lab-bound analysis, realized quantity scenarios may not exceed the selected policy's admitted quantity. The package refuses scenarios that silently expand upstream authority.

The joint surface reports quantity statistics, market-price statistics, quantity/price correlation where defined, cap utilization, merchant/contract value distributions, downside quantiles, and protection value.

## Policy sensitivity vs market-model sensitivity

SPK deliberately separates two different questions.

**Policy sensitivity:** hold market/model assumptions fixed and compare what different governance policies admit.

```bash
spk-derivatives policy-compare claim-assessment.json --json
spk-derivatives policy-sweep claim-assessment.json \
  --spot 100 --strike 100 --maturity 1 --rate 0.05 --volatility 0.20 \
  --package-out policy-comparison.json --json
```

**Market-model sensitivity:** hold admitted quantity and contract fixed and compare different market-price scenario models.

```python
from spk_derivatives import compare_market_model_scenarios
```

Neither is evidence truth. Policy sensitivity is not market sensitivity; model sensitivity is not governance authority.

## Deterministic artifacts

SPK publishes three machine-readable result protocols:

- `spk_derivatives.pricing_result_package.v0.1`;
- `spk_derivatives.policy_comparison_package.v0.1`;
- `spk_derivatives.market_risk_package.v0.1`.

SPK-owned artifacts use deterministic canonical JSON and SHA-256 identities. They retain upstream Policy Lab identifiers rather than pretending SPK can recompute Policy Lab's governance authority.

JSON Schemas are under `protocol/schema/`.

## CLI

```bash
spk-derivatives info --json
spk-derivatives preflight --json
spk-derivatives policy-check claim-assessment.json --json
spk-derivatives policy-compare claim-assessment.json --json
spk-derivatives policy-price claim-assessment.json \
  --spot 100 --strike 100 --maturity 1 --rate 0.05 --volatility 0.20 \
  --package-out pricing-result.json --json
spk-derivatives policy-sweep claim-assessment.json \
  --spot 100 --strike 100 --maturity 1 --rate 0.05 --volatility 0.20 \
  --package-out policy-comparison.json --json
spk-derivatives market-risk claim-assessment.json \
  --prices prices.json --contract-type floor --currency USD --floor-price 0.10 \
  --package-out market-risk.json --json
spk-derivatives verify-result pricing-result.json --json
spk-derivatives verify-comparison policy-comparison.json --json
spk-derivatives verify-market-risk market-risk.json --json
```

`market-risk --prices` expects a JSON array of market-price scenarios. The quantity unit comes from the selected admitted Policy Lab exposure; the command does not perform hidden unit conversion.

## Installation

From the repository:

```bash
pip install -e .
```

Optional API dependencies:

```bash
pip install -e ".[api]"
```

The package remains **research/beta**. The existing public PyPI release predates this `0.5` branch and should not be treated as equivalent to the current repository surface.

## Validation

The repository maintains Python tests across supported interpreter versions plus Solidity compile/test/security checks for the retained legacy reference contract surface.

The supported quantitative spine now has dedicated tests for:

- Policy Lab fail-closed interoperability;
- deterministic pricing and comparison artifacts;
- policy sensitivity and cherry-pick rejection;
- Black-76 / Bachelier parity and bounds;
- OU moments and reproducibility;
- forward curves and calibration diagnostics;
- explicit contract/unit boundaries;
- explicit quantity conversions;
- market-risk distributions;
- joint volume-price authority caps;
- market-risk artifact mutation detection;
- CLI and current-surface contracts.

## Research and use boundaries

Appropriate uses include:

- research and teaching;
- renewable-energy finance workshops;
- policy-vs-market scenario exercises;
- model-governance demonstrations;
- prototype consulting analyses;
- evaluation of evidence-bound quantitative workflows.

Not claimed:

- production trading readiness;
- investment or hedging advice;
- exchange or broker execution;
- legal settlement;
- reserve sufficiency;
- regulatory approval;
- liquidity or counterparty guarantees;
- market-model correctness from historical calibration alone.

See:

- `docs/POLICY_LAB_INTEGRATION.md`
- `docs/PRICING_ARTIFACT_PROTOCOL.md`
- `docs/TRUST_BOUNDARY_AND_THREAT_MODEL.md`
- `docs/MARKET_MODEL_ARCHITECTURE.md`
- `docs/MARKET_CALIBRATION_AND_RISK.md`
- `docs/EXTERNAL_EVALUATION.md`

## Legacy SolarPunkCoin material

The repository retains historical SolarPunkCoin/Solidity material as an adjacent reference application from the project's earlier research path. It is **not** the identity of the current SPK Derivatives quantitative package and is not required for the Python market-risk surface.

Legacy deployment is manual-only. Ordinary SPK development does not deploy the retained contract.

## License

MIT. See `LICENSE`.
