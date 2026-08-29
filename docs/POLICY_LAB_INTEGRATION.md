# Policy Lab Integration

SPK Derivatives v0.5 defines a deliberately strict boundary from Policy Lab into
the pricing layer.

The design rule is:

> **Policy Lab decides what quantity is admissible under a policy; SPK
> Derivatives prices the consequences of that admitted quantity and records its
> own assumptions/results downstream.**

SPK does not duplicate Policy Lab's evidence registry, constraint calculators,
governance rules, artifact canonicalization, or settlement authority.

## Upstream contract

The bridge targets exactly:

```text
schema:  policylab.claim_assessment_package.v0.1
profile: policylab.energy_linked_claim.v0
```

Reference implementation/schema:

- Repository: `Spectating101/solarpunk-coin`
- Schema: `protocol/schema/claim-assessment-package.v0.1.schema.json`

Policy Lab owns canonical package production and its SHA-256 identity rules. SPK
retains those identities verbatim rather than attempting to become a second
canonicalization authority.

## What SPK validates at the boundary

SPK validates the subset of the upstream protocol it actually consumes:

| Area | Downstream requirement |
| --- | --- |
| Schema/profile | exact claim-assessment schema + energy-linked profile |
| Artifact identity | lowercase SHA-256 `assessment_id` and `package_content_id` |
| Evidence identity | lowercase SHA-256 `evidence_hash` |
| Policy decision | lowercase SHA-256 `decision_id` |
| Assurance | `L0` through `L4` |
| Unit semantics | eligible evidence unit matches profile `source_unit`; admitted quantity unit matches profile `claim_unit` |
| Claim | claim/case/subject/request mode + canonical UTC period |
| Admission | admitted external reading + supported quantity |
| Ambiguity | explicit `policy_id` when several evaluations admit quantities |

This is a fail-closed interoperability contract, **not a replacement for Policy
Lab's complete validator**.

## Admission semantics

Only these Policy Lab external readings are priceable:

```text
ADMITTED_WITH_LIMIT_UNDER_POLICY
ADMITTED_UNDER_POLICY
```

`BLOCKED_UNDER_POLICY` is rejected. An evaluation with no `supported_quantity`
is rejected.

If a package contains multiple admitted policy evaluations, SPK refuses to pick
one implicitly:

```python
from spk_derivatives import extract_admitted_exposure

exposure = extract_admitted_exposure(
    "claim-assessment.json",
    policy_id="policy-id-here",
)
```

Two governance policies can legitimately admit different quantities from the
same evidence. Selecting one silently would turn a governance choice into a
software default.

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

The model produces a **per-unit** derivative value. SPK then multiplies that
value by the exact `supported_quantity` emitted by Policy Lab.

SPK does not:

- change the admitted quantity,
- infer a different policy,
- convert units implicitly,
- infer a market price from evidence,
- increase an evidence assurance level,
- reinterpret a blocked decision as an admitted scenario.

Therefore `S0` and `K` must be denominated per unit of `exposure.unit`.

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

The intended invariant is:

> A valuation must remain traceable to the exact Policy Lab evidence/policy
> decision that authorized the quantity being valued.

## From pricing result to auditable artifact

For durable downstream use, create an SPK result package rather than copying the
price alone:

```python
from spk_derivatives import build_policy_pricing_package

package = build_policy_pricing_package(
    exposure,
    result,
    S0=0.035,
    K=0.040,
    T=1.0,
    r=0.025,
    sigma=0.42,
    steps=200,
    assumptions=["Risk-neutral valuation"],
)
```

That package preserves Policy Lab provenance and adds SPK model inputs,
reproducibility controls, assumptions, valuation, warnings, non-claims, and two
SPK-owned deterministic identities.

See `docs/PRICING_ARTIFACT_PROTOCOL.md`.

## CLI

Inspect an admitted quantity:

```bash
spk-derivatives policy-check claim-assessment.json --json
```

Price and emit a result artifact:

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
  --package-out pricing-result.json \
  --json
```

Verify both sides of the boundary:

```bash
spk-derivatives preflight \
  --policy-package claim-assessment.json \
  --policy conservative-energy-policy \
  --result-package pricing-result.json \
  --json
```

## Failure modes are part of the interface

The bridge fails closed on the important boundary cases:

| Condition | Behavior |
| --- | --- |
| Unsupported schema/profile | error |
| Malformed upstream SHA-256 identity | error |
| Assurance outside `L0`–`L4` | error |
| Profile/evidence/claim unit mismatch | error |
| No policy evaluations | error |
| Only blocked evaluations | error |
| Missing supported quantity | error |
| Multiple admitted policies without selector | error |
| Non-finite or negative quantity | error |
| Invalid model bounds/reproducibility controls | error |
| Unknown pricing method | error |

Policy/evidence ambiguity is therefore surfaced **before** quantitative modeling
begins rather than disappearing inside a default.
