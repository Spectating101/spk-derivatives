# SPK Derivatives

**Policy-aware quantitative pricing and risk tooling for renewable-energy derivatives.**

SPK Derivatives is a research/proof-of-concept Python framework for turning energy
data and policy-admitted exposure quantities into reproducible derivative pricing,
Greeks, stress tests, scenario analysis, and auditable outputs.

The project began as a solar-derivatives prototype and now supports **solar, wind,
and hydro**, multiple pricing engines, workflow/reporting utilities, and a direct
bridge from the **Policy Lab claim-assessment protocol**.

> **Status:** research/beta software. It is suitable for experimentation,
> education, model validation, and controlled prototyping; it is not a production
> trading, settlement, or compliance system.

## What it does

- **Pricing:** binomial-tree and Monte-Carlo valuation for call-style and
  redeemable energy claims.
- **Risk:** Delta, Gamma, Vega, Theta, Rho, sensitivity tables, stress tests,
  scenario comparison, portfolio Greeks, break-even and P&L analysis.
- **Energy data:** NASA POWER integration plus solar, wind, and hydro loaders.
- **Context:** translate raw energy observations into kWh and value-oriented
  analysis contexts.
- **Workflow:** result validation, comparison, batch pricing, exports and reports.
- **Policy Lab bridge:** consume a machine-readable claim-assessment package,
  refuse blocked/ambiguous exposures, and carry assessment/evidence/decision IDs
  into downstream pricing results.

## Architecture

```text
Observed evidence / source data
            |
            v
     Policy Lab protocol
  evidence + policy constraints
            |
            v
claim-assessment-package.v0.1
(admitted quantity + provenance)
            |
            v
      SPK Derivatives
 pricing | Greeks | stress | P&L
            |
            v
 auditable research / decision outputs
```

The boundary is intentional:

- **Policy Lab establishes admissibility.**
- **SPK Derivatives establishes quantitative consequences.**

SPK Derivatives does **not** upgrade evidence quality, choose governance policy,
or turn a blocked claim into a priceable exposure. If several policies admit
different quantities, the caller must select the policy explicitly.

The upstream Policy Lab implementation and protocol live in
[`Spectating101/solarpunk-coin`](https://github.com/Spectating101/solarpunk-coin).

## Install

Published package:

```bash
pip install spk-derivatives
```

Current repository development version:

```bash
git clone https://github.com/Spectating101/spk-derivatives.git
cd spk-derivatives
pip install -e ".[dev]"
```

## Quick start

### Price a derivative

```python
from spk_derivatives import BinomialTree, MonteCarloSimulator

tree = BinomialTree(
    S0=0.035,
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    N=200,
    payoff_type="call",
)

print(tree.price())
```

### Use a Policy Lab assessment

```python
from spk_derivatives import (
    extract_admitted_exposure,
    price_admitted_exposure,
)

exposure = extract_admitted_exposure(
    "claim-assessment.json",
    policy_id="your-policy-id",  # optional when only one policy is admitted
)

priced = price_admitted_exposure(
    exposure,
    S0=0.035,       # market value per admitted quantity unit
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    method="binomial",
)

print(priced.total_value)
print(priced.decision_id)
print(priced.evidence_hash)
```

No unit conversion is performed implicitly: `S0` and `K` must be expressed per
unit of the Policy Lab `supported_quantity`.

See [`docs/POLICY_LAB_INTEGRATION.md`](docs/POLICY_LAB_INTEGRATION.md) for the
integration contract and failure semantics.

## CLI

The package exposes a working `spk-derivatives` command:

```bash
spk-derivatives info

spk-derivatives policy-check claim-assessment.json --json

spk-derivatives policy-price claim-assessment.json \
  --spot 0.035 \
  --strike 0.040 \
  --maturity 1 \
  --rate 0.025 \
  --volatility 0.42 \
  --method binomial \
  --json
```

A blocked Policy Lab decision exits with an error rather than being priced.

## Package surface

```text
energy_derivatives/spk_derivatives/
├── binomial.py              # binomial pricing
├── monte_carlo.py           # Monte-Carlo pricing
├── sensitivities.py         # Greeks
├── analysis.py              # stress/scenario/P&L utilities
├── data_loader_*.py         # solar/wind/hydro + NASA
├── location_guide.py        # geographic presets
├── context_translator.py    # energy/value context
├── results_manager.py       # validation/comparison/batch workflows
├── policy_lab.py            # Policy Lab → admitted exposure bridge
└── cli.py                   # command-line interface
```

Additional examples and notebooks live under `examples/`.

## Policy-aware pricing contract

The bridge currently targets:

```text
policylab.claim_assessment_package.v0.1
```

It consumes, at minimum, the package identities, claim period, evidence
identity/assurance, policy evaluation, `supported_quantity`, and decision ID.

Downstream pricing results retain:

- `assessment_id`
- `package_content_id`
- `claim_id`
- `policy_id`
- `decision_id`
- `evidence_hash`
- `evidence_assurance`

That makes it possible to trace a valuation back to the exact policy/evidence
decision that admitted the quantity being valued.

## Adjacent SolarPunkCoin MVP

This repository also contains the earlier **SolarPunkCoin** smart-contract
proof-of-concept (`contracts/`, `test/`, `scripts/simulate_peg.py`) and associated
energy-anchoring research. It remains useful as an experimental application of
the broader research thesis, but the **PyPI/package surface is SPK Derivatives**.

Relevant material:

- `contracts/SolarPunkCoin.sol`
- `SOLIDITY_QUICKSTART.md`
- `MVP_SUMMARY.md`
- `POLYGON_ARCHITECTURE_EXPLAINED.md`
- `RESEARCH/`

## Validation

Run the Python test suite:

```bash
pytest energy_derivatives/tests
```

The core suite includes model sanity checks (including binomial convergence
against Black-Scholes), Monte-Carlo reproducibility, data-loader fallbacks, and
Policy Lab bridge guardrails.

## Research boundary

The pricing engines use conventional quantitative-finance assumptions (including
risk-neutral valuation and GBM-style dynamics in relevant paths). Renewable
energy, physical delivery, policy constraints, and market microstructure can
violate those assumptions. Treat model output as a testable analytical result,
not as self-authenticating market truth.

## License

MIT. See [`LICENSE`](LICENSE).
