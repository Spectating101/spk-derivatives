# Pricing Artifact Protocol

SPK Derivatives v0.5 adds a machine-readable result package for the part of the
workflow that happens **after** Policy Lab has admitted an exposure.

The protocol is intentionally modeled after Policy Lab's separation between a
human explanation and a canonical artifact: pricing output should not become an
untraceable number copied into a report, spreadsheet, or downstream agent.

## Schema

```text
spk_derivatives.pricing_result_package.v0.1
```

JSON Schema:

```text
protocol/schema/pricing-result-package.v0.1.schema.json
```

## Authority chain

```text
observed evidence
      |
      v
Policy Lab claim assessment
      |  assessment_id
      |  evidence_hash
      |  policy_id / decision_id
      |  supported_quantity
      v
SPK admitted exposure
      |
      v
pricing engine + declared assumptions
      |
      v
SPK pricing result package
      |  artifact_id
      |  package_content_id
      v
report / comparison / agent / external evaluation
```

The package never promotes SPK into the authority role. It retains Policy Lab's
identities and records what SPK did downstream.

## Two identities

SPK follows the same useful distinction that Policy Lab established between the
identity of a conclusion and the identity of the whole package.

### `artifact_id`

SHA-256 over the semantic pricing body:

- schema,
- authority/provenance,
- admitted exposure,
- model engine, inputs, reproducibility controls and assumptions,
- valuation.

Changing volatility, the selected policy decision, admitted quantity, random
seed, engine configuration, or price changes the artifact identity.

### `package_content_id`

SHA-256 over all fields except `package_content_id` itself.

This also reacts to explanatory material such as warnings and non-claims. A new
warning can therefore change the package content identity without pretending
that the underlying quantitative conclusion changed.

## Canonicalization

SPK-owned artifacts use:

```text
python-json-sort-keys-compact-utf8-v0.1
```

The implementation is deterministic sorted-key compact JSON with UTF-8 and
non-finite JSON numbers forbidden.

This canonicalization is **not** presented as a reimplementation of Policy Lab's
JavaScript identity algorithm. Policy Lab identities are retained verbatim and
validated for shape; SPK does not recompute them.

## Package shape

The top-level sections are:

```json
{
  "schema": "spk_derivatives.pricing_result_package.v0.1",
  "artifact_id": "...sha256...",
  "package_content_id": "...sha256...",
  "authority": {},
  "exposure": {},
  "model": {},
  "valuation": {},
  "warnings": [],
  "non_claims": [],
  "verification": {}
}
```

### Authority

Retains:

- Policy Lab source schema and profile,
- `assessment_id`,
- upstream `package_content_id`,
- claim/case identity,
- policy identity/version,
- `decision_id`,
- external reading,
- evidence hash and assurance level.

### Exposure

Retains the admitted quantity and unit, evidence quantity/unit, assessment
period, binding calculators, and available settlement-scenario signal.

### Model

Records the pricing engine and exact quantitative inputs. Reproducibility fields
include the SPK package version plus the engine-specific controls:

- binomial: tree steps,
- Monte Carlo: simulation count and seed.

Model assumptions can be declared explicitly rather than left implicit in prose.

### Valuation

Contains per-unit price, admitted quantity, quantity unit, and total modeled
value. Validation independently checks that:

```text
total_value == unit_price * admitted_quantity
```

within floating-point tolerance.

## CLI workflow

Create a package while pricing:

```bash
spk-derivatives policy-price claim-assessment.json \
  --policy conservative-energy-policy \
  --spot 0.035 \
  --strike 0.040 \
  --maturity 1 \
  --rate 0.025 \
  --volatility 0.42 \
  --steps 200 \
  --assumption "Risk-neutral valuation" \
  --package-out pricing-result.json \
  --json
```

Verify it later:

```bash
spk-derivatives verify-result pricing-result.json --json
```

Run boundary preflight on both artifacts:

```bash
spk-derivatives preflight \
  --policy-package claim-assessment.json \
  --policy conservative-energy-policy \
  --result-package pricing-result.json \
  --json
```

## Failure semantics

Validation fails closed on:

- unsupported schemas or profiles,
- malformed upstream cryptographic identities,
- invalid evidence assurance levels,
- negative/non-finite quantities,
- unsupported engines,
- invalid engine reproducibility controls,
- exposure/valuation quantity mismatch,
- inconsistent total value,
- mutated `artifact_id`,
- mutated `package_content_id`.

This does not make the model correct. It makes the boundary between **what was
admitted**, **what was assumed**, **what was computed**, and **what was later
changed** substantially harder to blur.
