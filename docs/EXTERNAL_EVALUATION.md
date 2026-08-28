# External Evaluation Guide

This page gives an outside researcher, educator, consultant, or market-validation
partner a short path to understand SPK Derivatives without reverse-engineering
the repository history.

## One-sentence description

**SPK Derivatives is a research-grade proof of concept that combines renewable
energy data, conventional derivative-pricing models, risk analytics,
policy-admitted exposure quantities, and deterministic provenance artifacts in
one Python workflow.**

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

SPK consumes the Policy Lab
`policylab.claim_assessment_package.v0.1` / `policylab.energy_linked_claim.v0`
contract and converts an already-admitted quantity into a priceable exposure.
Malformed identity/assurance/unit boundaries, blocked decisions, and ambiguous
multi-policy admission fail closed.

The Policy Lab protocol itself is maintained separately in
`Spectating101/solarpunk-coin`; SPK deliberately does not duplicate its authority
or evidence logic.

### Reproducible result artifacts

A valuation can be exported as
`spk_derivatives.pricing_result_package.v0.1`, containing:

- exact Policy Lab provenance,
- admitted quantity and unit semantics,
- model engine and inputs,
- reproducibility controls,
- explicit assumptions,
- valuation,
- warnings/non-claims,
- semantic `artifact_id`,
- full `package_content_id`.

The package can be revalidated later with `spk-derivatives verify-result`.

## Ten-minute technical evaluation

```bash
git clone https://github.com/Spectating101/spk-derivatives.git
cd spk-derivatives
python -m venv .venv
# activate .venv
pip install -e ".[dev,api]"
pytest energy_derivatives/tests
spk-derivatives preflight --json
```

Then inspect:

1. `CURRENT_SURFACE.json`
2. `energy_derivatives/spk_derivatives/binomial.py`
3. `energy_derivatives/spk_derivatives/monte_carlo.py`
4. `energy_derivatives/spk_derivatives/policy_lab.py`
5. `energy_derivatives/spk_derivatives/artifacts.py`
6. `protocol/schema/pricing-result-package.v0.1.schema.json`
7. `docs/POLICY_LAB_INTEGRATION.md`
8. `docs/PRICING_ARTIFACT_PROTOCOL.md`

## What to test rather than trust

Useful external evaluation questions include:

- Do binomial and Monte-Carlo values behave plausibly under controlled inputs?
- Are stress/scenario outputs stable and interpretable?
- Does the Policy Lab boundary reject blocked or ambiguous claims as documented?
- Does changing a model input change the semantic artifact identity?
- Can a result package be mutated without verification detecting it?
- Are the declared unit and risk assumptions appropriate for the proposed market?
- Does a candidate commercial use actually have liquidity, counterparties, and a
  decision problem that benefits from this modeling?

The last two are intentionally not answered by the repository itself.

## Potential offering surfaces

The repository is not packaged as a commercial product today, but its existing
surface can support validation of several directions without changing the core
research:

- professional/academic workshops on energy derivatives and risk modeling,
- reproducible teaching labs using renewable-energy data,
- consulting prototypes for scenario/stress analysis,
- policy-versus-market-risk comparison exercises,
- auditable custom research integrations around admitted energy-linked claims,
- localized documentation/examples for specific energy markets,
- machine-readable outputs for downstream research or agent workflows.

Any such offering should preserve the distinction between **model output**,
**evidence quality**, **policy authority**, and **commercial market reality**.

## What is not claimed

SPK Derivatives is not presently:

- a production trading platform,
- a broker/dealer or investment service,
- an exchange or settlement network,
- a substitute for legal/regulatory review,
- an audited production smart-contract system,
- proof that a modeled energy claim is commercially liquid,
- proof that deterministic provenance makes a quantitative model correct.

## Adjacent work

The repository also preserves an earlier SolarPunkCoin energy-backed stablecoin
MVP and the research that motivated it. That material is an experimental
application surface; the Python `spk-derivatives` package is the primary library
being evaluated here.

## Licensing and collaboration

Repository code is provided under the MIT license. Any separate commercial,
educational, localization, consulting, distribution, or operating arrangement
should be agreed independently rather than inferred from repository access.
