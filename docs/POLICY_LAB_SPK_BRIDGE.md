# Policy Lab → SPK Derivatives Bridge

SPK Derivatives treats Policy Lab as an upstream authority boundary, not as an internal module to be copied or reimplemented.

The bridge has two separate contracts:

1. **Policy authority contract** — Policy Lab emits `policylab.claim_assessment_package.v0.1` under `policylab.energy_linked_claim.v0`. SPK consumes only explicitly admitted quantities and retains the upstream assessment, package, claim, policy, decision, evidence, assurance, period, and unit identities.
2. **Market quantity contract** — SPK refuses to assume that the admitted semantic claim unit is automatically a physical-energy or market-settlement unit. If downstream valuation requires a different quantity unit, the relationship must be represented explicitly as `spk_derivatives.policy_market_binding.v0.1`.

A third artifact now proves that the two contracts can compose without collapsing their semantics:

- `spk_derivatives.policy_bound_market_risk_package.v0.1` retains the original admitted claim, the exact mapping identity, the mapped market quantity, scenario-set identity, contract, and downstream risk output in one deterministic package.

This preserves the chain:

```text
real-world evidence
        ↓
Policy Lab
        ↓
evidence assurance + policy decision + admitted claim quantity
        ↓
policylab.claim_assessment_package.v0.1
        ↓
SPK Policy Lab consumer boundary
        ↓
explicit policy-market quantity binding, if required
        ↓
market data / scenario set / contract
        ↓
policy-bound market-risk package
```

The final package does **not** overwrite the Policy Lab claim quantity with the mapped market quantity. Both remain visible as separate fields.

## Pinned upstream contract

`POLICY_LAB_COMPATIBILITY.json` pins the Policy Lab schema/profile reference that SPK 0.5 was reviewed against:

- repository: `Spectating101/solarpunk-coin`;
- commit: `55fd6f2cf2eed25b589e91b5e3161e6ced68f5de`;
- schema path: `protocol/schema/claim-assessment-package.v0.1.schema.json`;
- Git blob: `5b1a312ee714abaf96453a3be5c628556becef36`;
- package schema: `policylab.claim_assessment_package.v0.1`;
- profile: `policylab.energy_linked_claim.v0`.

A future Policy Lab schema/profile/blob is not silently treated as compatible. It requires deliberate review and an update to the compatibility manifest.

This is a **consumer-driven compatibility pin**, not a fork of Policy Lab authority. Policy Lab remains responsible for its own canonicalization, evidence semantics, policy governance, and package production.

## Fail-closed authority boundary

SPK currently accepts only Policy Lab evaluations with external readings:

- `ADMITTED_WITH_LIMIT_UNDER_POLICY`;
- `ADMITTED_UNDER_POLICY`.

`BLOCKED_UNDER_POLICY` never becomes an SPK exposure. If more than one policy is admitted, the caller must choose the policy explicitly. SPK does not select a preferred governance policy.

The admitted quantity and claim unit are retained exactly. No market model is allowed to enlarge the Policy Lab quantity ceiling.

## Why the second binding exists

A Policy Lab package can legitimately say:

```text
admitted quantity = 33.066 ENERGY_CLAIM_UNIT
```

while a real electricity market can legitimately quote:

```text
price = 82.50 AUD/MWh
```

Those units are not interchangeable merely because both relate to energy.

The wrong implementation is:

```text
33.066 × 82.50
```

without first establishing what one `ENERGY_CLAIM_UNIT` means in market quantity.

SPK therefore requires an explicit bridge if the units differ semantically.

### Exact physical conversion

`exact-si-energy-conversion` is available only when the Policy Lab admitted unit is itself literal physical `Wh`, `kWh`, `MWh`, `GWh`, or `TWh`. The conversion factor is derived from exact SI decimal prefixes.

A semantic unit such as `kWh-claim` or `ENERGY_CLAIM_UNIT` is deliberately rejected by this path.

### Declared semantic mapping

`declared-semantic-mapping` can relate a semantic claim unit to a market quantity only when the caller supplies all of:

- an explicit positive conversion factor;
- the claimed authority for that mapping;
- a reference;
- a human-readable semantic explanation.

The resulting `binding_id` covers the Policy Lab decision identities, admitted quantity/unit, target market quantity/unit, factor, basis, authority, reference, semantics, period, and non-claims.

Hashing the declaration does **not** make the declaration true. It makes the exact declaration reproducible and mutation-evident.

## Downstream composition contract

`policy_bound_market_risk` uses the binding as a mandatory intermediate object when the market quantity differs from the Policy Lab claim quantity.

For example:

```text
Policy Lab
1000 kWh-claim admitted
        ↓
declared semantic mapping
factor = 0.001 MWh per kWh-claim
mapping authority/reference explicitly named
        ↓
market exposure
1.0 MWh
        ↓
AEMO-like scenario set
AUD/MWh
        ↓
AUD/MWh contract + risk distribution
```

The resulting package still contains:

```text
admitted_claim.quantity = 1000
admitted_claim.unit = kWh-claim
market_binding.binding_id = <sha256>
market_exposure.quantity = 1.0
market_exposure.unit = MWh
market.input.scenario_set_id = <sha256>
contract.price_unit = AUD/MWh
```

Changing the upstream Policy Lab decision, mapping factor/reference, mapped market quantity, scenario set, contract, or risk result changes the appropriate deterministic identity or fails validation.

## Research and Gauntlet significance

The bridge makes Policy Lab's portable package testable as a real interoperability boundary rather than merely an export format.

A downstream financial model cannot silently erase upstream governance distinctions:

- blocked policy → no downstream exposure;
- changed policy → changed decision identity;
- changed admitted quantity → changed downstream exposure;
- semantic-unit mismatch → hard failure until explicitly bridged;
- changed mapping basis → changed `binding_id`;
- changed market scenarios → changed scenario identity;
- changed model → model sensitivity, not evidence truth.

The bound market-risk package adds a particularly useful evaluator property: successful composition requires every semantic transition to be visible. A reviewer can inspect the original claim quantity, the separate mapping claim, and the downstream market consequence independently.

This is useful judge-facing evidence because the architecture demonstrates both **successful composition** and **refusal to compose when authority is insufficient**.

## Commercial significance

For external evaluation, including a market-entry assessment, the combined system should be described as an evidence-to-risk stack rather than as a generic option-pricing package:

```text
Policy Lab: what evidence and policy can justify
SPK Derivatives: what economic consequences follow under declared market assumptions
```

The systems remain independently usable. Policy Lab does not depend on SPK, and SPK can consume other authority surfaces in the future if they provide an explicit compatible contract.

For a market-specific pilot, the commercialization question is no longer "can this Python option package be sold?" It becomes "is there a buyer for a workflow that preserves evidence authority, makes claim-to-market assumptions explicit, and quantifies the resulting contract exposure?"

## Non-claims

The bridge does not establish that:

- a declared semantic mapping is legally valid;
- an admitted claim is a physical commodity;
- a claim unit is a certificate, credit, settlement unit, or money;
- a market price is applicable to the claim without a valid quantity/contract basis;
- deterministic identities establish empirical truth;
- downstream valuation establishes execution, liquidity, custody, issuance, redemption, or regulatory authority.
