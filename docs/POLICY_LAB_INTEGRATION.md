# Policy Lab Integration

SPK Derivatives v0.5 adds a deliberately narrow bridge from Policy Lab into the
pricing layer.

The design rule is:

> **Policy Lab decides what quantity is admissible under a policy; SPK
> Derivatives prices the consequences of that admitted quantity.**

SPK does not duplicate Policy Lab's evidence registry, constraint calculators,
governance rules, artifact canonicalization, or settlement authority.

## Upstream contract

The bridge targets the Policy Lab schema:

```text
policylab.claim_assessment_package.v0.1
```

Reference implementation/schema:

- Repository: `Spectating101/solarpunk-coin`
- Schema: `protocol/schema/claim-assessment-package.v0.1.schema.json`

The upstream artifact contains separate identities for the assessment and the
package content, the claim and evidence, one or more policy evaluations, and
optional settlement information.

## What SPK consumes

`extract_admitted_exposure()` reads the following information downstream:

| Area | Fields retained/used |
| --- | --- |
| Artifact | `schema`, `assessment_id`, `package_content_id` |
| Claim | `claim_id`, `case_id`, `subject`, request mode/quantity, canonical UTC period |
| Evidence | assurance level, `evidence_hash`, eligible quantity/unit, warnings |
| Policy evaluation | policy id/version/name, `decision_id`, `external_reading`, `supported_quantity`, binding calculators, rule warnings |
| Settlement | `scenario_only` when present |

The bridge performs lightweight structural/semantic checks needed for safe
downstream use. It is **not a replacement for full JSON Schema validation**.
Canonical artifact production and complete schema validation remain upstream
responsibilities.

## Admission semantics

Only these Policy Lab external readings are priceable:

```text
ADMITTED_WITH_LIMIT_UNDER_POLICY
ADMITTED_UNDER_POLICY
```

`BLOCKED_UNDER_POLICY` is rejected.

An evaluation with no `supported_quantity` is also rejected.

If a package contains multiple admitted policy evaluations, SPK refuses to pick
one implicitly. Supply `policy_id`:

```python
from spk_derivatives import extract_admitted_exposure

exposure = extract_admitted_exposure(
    "claim-assessment.json",
    policy_id="policy-id-here",
)
```

This matters because two governance policies can lawfully admit different
quantities from the same evidence. Picking one silently would turn a governance
choice into an accidental software default.

## Pricing an admitted exposure

```python
from spk_derivatives import (
    extract_admitted_exposure,
    price_admitted_exposure,
)

exposure = extract_admitted_exposure("claim-assessment.json")

result = price_admitted_exposure(
    exposure,
    S0=0.035,
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    method="binomial",
    steps=200,
)
```

The model first produces a **per-unit** derivative value. SPK then multiplies
that result by the exact `supported_quantity` emitted by Policy Lab.

SPK does not:

- change the admitted quantity,
- infer a different policy,
- convert units implicitly,
- infer a market price from evidence,
- increase an evidence assurance level,
- reinterpret a blocked decision as a scenario.

Therefore `S0` and `K` must be denominated per unit of
`exposure.unit`.

## Provenance carried into pricing

`PolicyPricedExposure` retains:

```text
assessment_id
package_content_id
claim_id
policy_id
decision_id
evidence_hash
evidence_assurance
```

The intended downstream invariant is:

> A valuation can be reproduced together with the exact evidence/policy decision
> that authorized the quantity being valued.

This is especially useful when the same physical evidence is evaluated under
multiple policy regimes or when a policy version changes.

## CLI

Inspect an admitted quantity:

```bash
spk-derivatives policy-check claim-assessment.json --json
```

Select a policy explicitly:

```bash
spk-derivatives policy-check claim-assessment.json \
  --policy conservative-energy-policy \
  --json
```

Price the admitted exposure:

```bash
spk-derivatives policy-price claim-assessment.json \
  --policy conservative-energy-policy \
  --spot 0.035 \
  --strike 0.040 \
  --maturity 1 \
  --rate 0.025 \
  --volatility 0.42 \
  --method monte-carlo \
  --simulations 50000 \
  --seed 7 \
  --json
```

## Failure modes are part of the interface

The bridge fails closed on the most important boundary cases:

| Condition | Behavior |
| --- | --- |
| Unsupported schema | error |
| Missing artifact/claim/evidence identities | error |
| No policy evaluations | error |
| Only blocked evaluations | error |
| Missing supported quantity | error |
| Multiple admitted policies without selector | error |
| Non-finite or negative supported quantity | error |
| Unknown pricing method | error |

This is intentional. Policy/evidence ambiguity should be made visible before
quantitative modeling begins.

## Extension direction

The current bridge is intentionally small. Natural next integrations include:

1. attaching Policy Lab decision identities to stress/scenario exports,
2. batch-pricing several explicitly selected policy regimes side by side,
3. comparing policy-induced quantity caps before/after market-risk effects,
4. emitting a combined machine-readable research package containing both
   constraint provenance and pricing assumptions/results.

Those should remain downstream extensions rather than copies of Policy Lab's
authority logic.
