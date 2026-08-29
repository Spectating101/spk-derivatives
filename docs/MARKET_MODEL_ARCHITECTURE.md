# Market Model Architecture

SPK Derivatives treats physical renewable quantity and market price as separate analytical objects.

This separation is deliberate. A weather or metering observation can support a physical quantity without implying that electricity, a PPA, a green certificate, or another market instrument changes in value by the same percentage. The older solar proof of concept used irradiance-derived economic values as a convenient research bridge; the supported architecture now makes the physical and market sides explicit instead of treating them as one stochastic process.

## Boundary

```text
physical evidence / metering / generation
                  |
                  v
             Policy Lab
      evidence + policy + quantity
                  |
                  v
        admitted quantity Q
                  |
                  +--------------------+
                                       |
market data / forward curve            |
spot / contract / certificate          |
                  |                    |
                  v                    v
            market price P       explicit contract
                  \                    /
                   \                  /
                    v                v
                     SPK Derivatives
                 valuation / settlement
                 risk / stress / scenario
```

Policy Lab remains the authority layer. SPK does not infer evidence truth, upgrade assurance, or change the admitted quantity. SPK's market layer requires market/contract assumptions to be stated separately.

## Analytic forward-option benchmarks

### Black-76

`black76_option_price` prices European calls and puts on positive forwards/futures under the standard lognormal Black-76 assumptions. It rejects non-positive forwards and strikes rather than silently applying a lognormal model where it is mathematically invalid.

Use it as a transparent benchmark when a positive forward representation and lognormal volatility are defensible.

### Bachelier

`bachelier_option_price` uses the normal model. It permits negative forwards and strikes, which makes it useful for electricity-market research where negative prices can occur.

Its volatility parameter is a normal volatility in price units per square-root year, not a percentage/lognormal volatility. The package keeps that distinction explicit.

## Mean-reverting electricity scenarios

`ou_terminal_moments` and `simulate_ou_terminal_prices` implement exact terminal moments/sampling for an Ornstein-Uhlenbeck process:

```text
dP = kappa * (theta - P) dt + sigma dW
```

This allows mean reversion and negative prices. The OU surface is intentionally labeled as a scenario model. Supplying OU parameters does not, by itself, establish the correct risk-neutral pricing measure for a traded electricity derivative.

A later market-calibration layer can bind the model to an observed forward curve, historical estimation window, or contract-specific calibration dataset.

## Explicit contract settlement

`energy_contracts.py` keeps quantity and price units separate and provides deterministic scenario settlement for:

- merchant exposure;
- fixed-price contracts;
- floors;
- caps;
- collars.

For an admitted quantity `Q` and market price `P`, the contract chooses an explicit settled unit price and computes both merchant value and contract value. No unit conversion is implicit.

`settle_policy_exposure` carries the Policy Lab `assessment_id`, source package identity, claim, policy, decision, evidence hash, and assurance into the settlement result. It cannot create a quantity that Policy Lab did not admit.

These settlement functions are research/scenario arithmetic. They do not execute a trade, create legal settlement authority, or substitute for stochastic option valuation where one is required.

## Why this matters

The architecture now supports a clean decomposition:

```text
Evidence uncertainty     -> Policy Lab assurance/provenance
Governance uncertainty   -> policy comparison / admitted quantity
Physical uncertainty     -> generation or delivery quantity scenarios
Market uncertainty       -> price/forward scenarios and option models
Contract structure       -> PPA/floor/cap/collar settlement rule
Model uncertainty        -> comparison across justified market models
```

This is the intended direction for the research stack: evidence truth, governance policy, physical quantity, market price, contract payoff, model value, execution, and legal settlement remain distinguishable layers.

## Next validation work

Before claiming broader market-model maturity, SPK should add:

1. forward-curve inputs with calibration provenance;
2. deterministic analytic/Monte-Carlo golden vectors for Black-76 and Bachelier;
3. at least one calibrated mean-reverting electricity case;
4. explicit price/quantity correlation for volume-risk research;
5. contract-specific historical replay;
6. model-selection and calibration metadata in deterministic result artifacts.

Until those controls exist, this surface remains research/beta and should be used for education, controlled prototyping, scenario analysis, and model validation rather than production trading.
