# External Evaluation Guide

This page gives an outside researcher, educator, consultant, or market-validation
partner a short path to understand SPK Derivatives without reverse-engineering
the repository history.

## One-sentence description

**SPK Derivatives is a research-grade proof of concept that combines renewable
energy data, conventional derivative-pricing models, risk analytics, and
policy-admitted exposure quantities in one auditable Python workflow.**

## What is implemented

### Quantitative layer

- Binomial-tree derivative pricing
- Monte-Carlo valuation
- Greeks and sensitivity analysis
- Volatility/rate stress tests
- Scenario comparison
- Portfolio Greeks
- Break-even and P&L analysis
- Result validation/comparison and batch workflows

### Energy/data layer

- Solar, wind, and hydro support
- NASA POWER integration
- Geographic presets
- Raw-data-to-kWh/value context tooling

### Policy/evidence interoperability

SPK can consume a Policy Lab
`policylab.claim_assessment_package.v0.1` artifact and turn an already-admitted
quantity into a priceable exposure while retaining assessment, decision, and
evidence identities.

The Policy Lab protocol itself is maintained separately in
`Spectating101/solarpunk-coin`; SPK deliberately does not duplicate its authority
or evidence logic.

## Ten-minute technical evaluation

```bash
git clone https://github.com/Spectating101/spk-derivatives.git
cd spk-derivatives
python -m venv .venv
# activate .venv
pip install -e ".[dev]"
pytest energy_derivatives/tests
spk-derivatives info
```

Then inspect:

1. `energy_derivatives/spk_derivatives/binomial.py`
2. `energy_derivatives/spk_derivatives/monte_carlo.py`
3. `energy_derivatives/spk_derivatives/analysis.py`
4. `energy_derivatives/spk_derivatives/policy_lab.py`
5. `docs/POLICY_LAB_INTEGRATION.md`

## Potential offering surfaces

The repository is not packaged as a commercial product today, but its existing
surface can support validation of several directions without changing the core
research:

- professional/academic workshops on energy derivatives and risk modeling,
- reproducible teaching labs using real renewable-energy data,
- consulting prototypes for scenario/stress analysis,
- policy-versus-market-risk comparison exercises,
- custom research integrations around admitted energy-linked claims,
- localized documentation/examples for specific energy markets.

Any such offering should preserve the distinction between **model output**,
**evidence quality**, and **policy authority**.

## What is not claimed

SPK Derivatives is not presently:

- a production trading platform,
- a broker/dealer or investment service,
- an exchange or settlement network,
- a substitute for legal/regulatory review,
- an audited production smart-contract system,
- proof that a modeled energy claim is commercially liquid.

Those are market/institutional questions outside the pricing library.

## Adjacent work

The repository also preserves an earlier SolarPunkCoin energy-backed stablecoin
MVP and the research that motivated it. That material is an experimental
application surface; the Python `spk-derivatives` package is the primary library
being evaluated here.

## Licensing and collaboration

Repository code is provided under the MIT license. Any separate commercial,
educational, localization, consulting, distribution, or operating arrangement
should be agreed independently rather than inferred from repository access.
