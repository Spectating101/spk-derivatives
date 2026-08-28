# SPK Derivatives

**Policy-aware quantitative pricing, risk, and provenance tooling for renewable-energy derivatives.**

SPK Derivatives is a research/beta Python framework for turning energy data and
policy-admitted exposure quantities into reproducible derivative pricing,
Greeks, stress tests, scenario analysis, and machine-verifiable research
artifacts.

The project began as a solar-derivatives proof of concept and now supports
**solar, wind, and hydro**, multiple pricing engines, workflow/reporting
utilities, and a direct boundary with the **Policy Lab claim-assessment
protocol**.

> **Status:** research/beta software. It is suitable for experimentation,
> education, model validation, controlled prototyping, and external evaluation;
> it is not a production trading, settlement, compliance, or policy system.

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
  refuse blocked/ambiguous exposures, and preserve assessment/evidence/decision
  identities downstream.
- **Deterministic artifacts:** emit pricing-result packages with separate semantic
  and full-content SHA-256 identities so assumptions, provenance, valuation, and
  later mutation stay visible.
- **Preflight:** verify runtime contracts and Policy Lab/SPK artifact boundaries
  from the CLI.

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
pricing-result-package.v0.1
(model + assumptions + provenance)
            |
            v
 report | comparison | agent | evaluator
```

The boundary is intentional:

- **Policy Lab establishes admissibility and governance context.**
- **SPK Derivatives establishes quantitative consequences.**

SPK Derivatives does **not** upgrade evidence quality, choose governance policy,
recompute Policy Lab identities, or turn a blocked claim into a priceable
exposure. If several policies admit different quantities, the caller must select
the policy explicitly.

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
pip install -e ".[dev,api]"
```

## Quick start

### Price a derivative

```python
from spk_derivatives import BinomialTree

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
    policy_id="your-policy-id",  # optional only when one policy is admitted
)

priced = price_admitted_exposure(
    exposure,
    S0=0.035,       # market/model value per admitted quantity unit
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    method="binomial",
    steps=200,
)

print(priced.total_value)
print(priced.decision_id)
print(priced.evidence_hash)
```

No unit conversion is performed implicitly: `S0` and `K` must be expressed per
unit of the Policy Lab `supported_quantity`.

### Build a deterministic pricing artifact

```python
from spk_derivatives import build_policy_pricing_package

package = build_policy_pricing_package(
    exposure,
    priced,
    S0=0.035,
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    steps=200,
    assumptions=["Risk-neutral valuation"],
)

print(package["artifact_id"])
print(package["package_content_id"])
```

`artifact_id` represents the semantic pricing conclusion. `package_content_id`
represents the complete package, including warnings and explanatory non-claims.

## CLI

The package exposes a working `spk-derivatives` command:

```bash
spk-derivatives info --json
spk-derivatives preflight --json

spk-derivatives policy-check claim-assessment.json --json

spk-derivatives policy-price claim-assessment.json \
  --spot 0.035 \
  --strike 0.040 \
  --maturity 1 \
  --rate 0.025 \
  --volatility 0.42 \
  --method binomial \
  --steps 200 \
  --assumption "Risk-neutral valuation" \
  --package-out pricing-result.json \
  --json

spk-derivatives verify-result pricing-result.json --json

spk-derivatives preflight \
  --policy-package claim-assessment.json \
  --result-package pricing-result.json \
  --json
```

A blocked Policy Lab decision, malformed upstream identity, ambiguous admitted
policy, invalid model boundary, or mutated pricing package exits with an error
rather than being silently accepted.

## Canonical surfaces

The repository now declares its externally meaningful surfaces in
[`CURRENT_SURFACE.json`](CURRENT_SURFACE.json). This keeps package version,
Policy Lab contract, result-artifact protocol, CLI surface, and validation paths
explicit rather than relying on repository archaeology.

Current machine-readable contracts:

```text
Policy Lab input:
  policylab.claim_assessment_package.v0.1
  profile: policylab.energy_linked_claim.v0

SPK output:
  spk_derivatives.pricing_result_package.v0.1
  schema: protocol/schema/pricing-result-package.v0.1.schema.json
```

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
├── policy_lab.py            # Policy Lab → admitted exposure boundary
├── artifacts.py             # deterministic provenance-preserving result packages
└── cli.py                   # preflight, policy bridge, pricing, verification
```

Additional examples and notebooks live under `examples/`.

## Policy-aware pricing contract

The bridge validates the exact upstream contract SPK consumes:

- claim-assessment schema and energy-linked profile,
- lowercase SHA-256 assessment/package/evidence/decision identities,
- evidence assurance `L0`–`L4`,
- profile source/claim unit mapping,
- canonical claim period,
- admitted policy result and supported quantity,
- explicit policy selection when more than one policy admits an exposure.

This is intentionally narrower than reimplementing the entire Policy Lab
validator. Canonical Policy Lab package production, governance semantics,
constraint calculators, and Policy Lab identity recomputation remain upstream.

Downstream pricing retains:

- `assessment_id`
- upstream `package_content_id`
- `claim_id`
- `policy_id`
- `decision_id`
- `evidence_hash`
- `evidence_assurance`

See [`docs/POLICY_LAB_INTEGRATION.md`](docs/POLICY_LAB_INTEGRATION.md).

## Pricing artifact protocol

The v0.1 SPK result package records:

- authority/provenance,
- admitted exposure and its units,
- exact model inputs,
- engine-specific reproducibility controls,
- declared assumptions,
- per-unit and total valuation,
- warnings and non-claims,
- semantic `artifact_id`,
- whole-package `package_content_id`.

This makes a downstream valuation traceable to both the exact Policy Lab
decision that allowed the quantity and the exact quantitative configuration used
to value it.

See [`docs/PRICING_ARTIFACT_PROTOCOL.md`](docs/PRICING_ARTIFACT_PROTOCOL.md).

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

The suite covers model sanity checks, Monte-Carlo reproducibility, API behavior,
data-loader fallback, reporting, Policy Lab fail-closed boundaries, deterministic
artifact identities, mutation detection, CLI preflight, and repository surface
consistency.

The Solidity proof-of-concept also has Hardhat tests and a Slither security gate
in GitHub Actions.

## Research boundary

The pricing engines use conventional quantitative-finance assumptions (including
risk-neutral valuation and GBM-style dynamics in relevant paths). Renewable
energy, physical delivery, policy constraints, basis risk, liquidity, and market
microstructure can violate those assumptions. Treat model output as a testable
analytical result, not as self-authenticating market truth.

The artifact layer improves **traceability and falsifiability**; it does not turn
model assumptions into facts.

## License

MIT. See [`LICENSE`](LICENSE).
