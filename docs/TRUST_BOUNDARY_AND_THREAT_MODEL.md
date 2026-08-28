# SPK Derivatives Trust Boundary and Threat Model

**Status:** research-beta architecture note. This is not a security audit, legal opinion, market-risk certification, or model-validation report.

SPK Derivatives inherits one central lesson from Policy Lab: a quantitative result is only useful if its authority boundaries are explicit. Pricing, evidence, governance, execution, and settlement are different domains and must not be silently collapsed into one claim of truth.

## Security and integrity objectives

SPK v0.5 is designed to preserve six properties:

1. **Upstream authority identity** — a valuation retains the exact Policy Lab assessment, evidence, policy, and decision identities that admitted the quantity.
2. **Quantity integrity** — SPK never increases, invents, or implicitly converts the Policy Lab-supported quantity.
3. **Policy sensitivity visibility** — if several policies produce different outcomes, SPK exposes the difference rather than selecting one by software default.
4. **Model reproducibility** — pricing artifacts retain method, assumptions, numerical controls, and deterministic identities.
5. **Mutation detection** — pricing and policy-comparison artifacts carry SHA-256 identities over semantic content and package content.
6. **Boundary honesty** — a model price is not evidence truth, legal authority, liquidity, execution, reserve custody, or settlement finality.

## Trust boundary

```text
POLICY LAB CLAIM-ASSESSMENT PACKAGE
  evidence identity
  provenance assurance
  policy identity
  admitted / blocked decision
  supported quantity
          |
          v
SPK POLICY BRIDGE
  schema/profile checks
  explicit policy selection
  blocked outcomes remain blocked
          |
          +--------------------+
          |                    |
          v                    v
SINGLE-POLICY PRICING      POLICY-SENSITIVITY ANALYSIS
  binomial / MC              all recorded policies
  unit valuation             common model assumptions
  total model value          blocked rows preserved
          |                    |
          v                    v
DETERMINISTIC RESULT      DETERMINISTIC COMPARISON
PACKAGE                   PACKAGE
```

Policy Lab remains authoritative for evidence normalization, provenance classification, governance policy evaluation, claim admissibility, and its own canonical identities. SPK is authoritative only for the quantitative transformations it explicitly performs.

## Threats and failure modes

### S1 — Blocked policy accidentally priced

**Failure:** downstream code treats every policy row as a numeric exposure.

**Control:** only Policy Lab readings explicitly recognized as admitted may become `PolicyLabExposure` objects. Policy comparison keeps blocked rows visible but never includes them in `priced_outcomes`.

### S2 — Governance choice hidden as software default

**Failure:** two admitted policies produce different quantities and software silently prices one.

**Control:** single-exposure extraction fails when more than one admitted policy exists unless `policy_id` is supplied. `policy-sweep` prices all admitted policies under a common assumption set.

### S3 — Policy sensitivity mistaken for market sensitivity

**Failure:** a quantity difference caused by governance rules is presented as price/volatility risk.

**Control:** policy-comparison artifacts separate `policy_outcomes`, common `model` assumptions, and `priced_outcomes`. Their interpretation explicitly labels cross-row differences as policy sensitivity.

### S4 — Evidence assurance inflation

**Failure:** a successful quantitative model run is interpreted as stronger evidence.

**Control:** evidence assurance and evidence hash are retained verbatim. SPK has no API that promotes L0–L4 assurance.

### S5 — Unit mismatch

**Failure:** model prices denominated per MWh are multiplied by a kWh-claim quantity without conversion.

**Control:** SPK performs no implicit unit conversion at the Policy Lab bridge. `S0` and `K` are explicitly defined per admitted quantity unit.

**Residual risk:** callers can still supply economically inconsistent units. Future work should support explicit, declared conversion transforms with their own identities rather than inference.

### S6 — Result mutation after computation

**Failure:** a JSON output is edited while preserving the apparent provenance labels.

**Control:** pricing artifacts and policy-comparison packages carry semantic and package-content SHA-256 identities. Validators recompute both and fail on mutation.

### S7 — Model specification drift

**Failure:** implementation changes but a historical result is interpreted as if produced by the same model version.

**Control:** single-pricing artifacts retain the SPK package version and reproducibility controls. Comparison packages retain numerical controls and common assumptions.

**Residual risk:** v0.5 does not yet bind a source commit or implementation hash into every result package. A future protocol revision should add optional immutable source/build identity.

### S8 — Monte-Carlo irreproducibility

**Failure:** stochastic results cannot be reproduced.

**Control:** result artifacts carry simulation count and seed. Users who require deterministic replay should always supply a seed.

### S9 — Model validity mistaken for market truth

**Failure:** a mathematically correct binomial/GBM-style valuation is treated as an executable market price for an illiquid energy-linked claim.

**Control:** documentation and machine-readable non-claims distinguish model value from liquidity, execution, counterparty, basis, and regulatory reality.

### S10 — Settlement semantics imported into pricing

**Failure:** a Policy Lab settlement scenario or capacity statement is treated as reserve proof or legal redemption.

**Control:** settlement fields are retained as context only. Pricing does not promote settlement scenario metadata into authority.

### S11 — Duplicate or replayed economic interpretation

**Failure:** the same Policy Lab decision is priced repeatedly under different market assumptions and consumers mistake them for distinct admissibility decisions.

**Control:** every pricing artifact retains the same upstream assessment/decision IDs while its own artifact identity changes with model assumptions and valuation. Consumers can distinguish authority identity from model-run identity.

### S12 — Comparison package cherry-picking

**Failure:** one favorable admitted policy is shown while stricter or blocked policies are omitted.

**Control:** `build_policy_comparison_package()` consumes the full Policy Lab evaluation set and the validator requires `priced_outcomes` to contain all and only admitted policy IDs. Blocked outcomes remain represented in `policy_outcomes`.

## Current appropriate uses

SPK v0.5 is appropriate for research, teaching, scenario analysis, policy-versus-market-risk comparison, model prototyping, and technical evaluation with explicit assumptions.

It is not appropriate by itself for production trading, regulated advice, reserve/custody claims, legal settlement, mainnet financial exposure, or claims that a modeled instrument has real liquidity.

## Next controls worth adding

The strongest next protocol improvements would be source/build identities for model implementations, explicit unit-conversion artifacts, model-validation reference vectors, deterministic scenario-set manifests, and a portfolio package that binds multiple Policy Lab decisions without losing per-claim authority identity.
