# The Sophistication Layer

**Philosophy:** Don't dumb down - ground up.

---

## The Problem

Most financial tools give you technically correct but practically useless outputs:

```
Call option price: $0.035645
Volatility: 200%
Delta: 0.634
```

User thinks: *"Okay... what does that MEAN for my solar panels?"*

---

## The Solution: Context Translation

Add a **sophistication layer** that translates technical outputs into grounded, relatable context.

**Not dumbing down** - adding value through practical translation.

### Example Translations

| Technical Output | Grounded Context |
|------------------|------------------|
| "Volatility 200%" | "Your monthly revenue could swing ±$450" |
| "$0.035 per kWh/m²/day" | "$127/month hedge cost for your 50kW system" |
| "GHI 5.2 kWh/m²/day" | "Your panels produce 38 kWh/day (20% efficiency)" |
| "Delta = 0.634" | "Hedge 63% of your production (25 kWh/day)" |
| "Theta = -0.000131" | "Lose $4.78/month to time decay" |

---

## What Gets Translated

### 1. Solar Irradiance → Actual Production

**Technical:** GHI = 5.2 kWh/m²/day

**Sophisticated Translation:**
```python
from solar_quant.context_translator import SolarSystemContext

system = SolarSystemContext(system_size_kw=10.0, panel_efficiency=0.20)
daily_output = system.ghi_to_ac_output(5.2)  # 8.84 kWh/day

# Shows the user:
"Your 10kW system produces 8.84 kWh/day
(accounting for 20% panel efficiency + 15% system losses)"
```

**Why This Matters:**
- Users have PANELS, not "kWh/m²/day"
- Must account for efficiency, losses, system age
- Gives actionable production numbers

---

### 2. Production → Revenue

**Technical:** 8.84 kWh/day output

**Sophisticated Translation:**
```python
from solar_quant.context_translator import PriceTranslator

translator = PriceTranslator(system, electricity_rate=0.12)
daily_rev, monthly_rev, annual_rev = translator.revenue_at_ghi(5.2)

# Shows the user:
"$1.06/day = $31.85/month = $387/year
(at $0.12/kWh net metering rate)"
```

**Why This Matters:**
- Users care about DOLLARS, not kWh
- Must use their actual electricity rate
- Connect to monthly budget reality

---

### 3. Volatility % → Revenue Swings

**Technical:** σ = 200% volatility

**Sophisticated Translation:**
```python
from solar_quant.context_translator import VolatilityTranslator

vol_translator = VolatilityTranslator(translator, spot_ghi=5.2)
daily_low, daily_exp, daily_high = vol_translator.volatility_to_revenue_range(2.0)

# Shows the user:
"Daily revenue range: $0.28 to $2.14
Expected: $1.06
Swing: ±$1.08 per day

Monthly swing: ±$32.40
→ Bad month could cost you $97 vs average"
```

**Why This Matters:**
- "200%" means nothing to users
- "$32 monthly swing" is tangible
- Shows actual risk exposure in dollars

---

### 4. Option Price → Hedge Cost

**Technical:** Call price = $0.035645 per unit

**Sophisticated Translation:**
```python
monthly_cost = translator.option_price_to_monthly_cost(0.035645, 5.2)
annual_cost = translator.option_price_to_annual_cost(0.035645, 5.2)

# Shows the user:
"$10.69/month to hedge your 10kW system
$130.14/year
= 33.6% of your expected revenue"
```

**Why This Matters:**
- Users budget in months/years, not "per unit per day"
- Shows cost as % of revenue (is it worth it?)
- Enables real decision-making

---

### 5. Delta → Hedge Amount

**Technical:** Δ = 0.634

**Sophisticated Translation:**
```python
from solar_quant.context_translator import GreeksTranslator

delta_info = GreeksTranslator.delta_to_hedge_amount(
    delta=0.634,
    system_size_kw=10.0,
    ghi_kwh_m2_day=5.2,
    solar_system=system
)

# Shows the user:
"Hedge 5.61 kWh/day = 63.4% of your 8.84 kWh/day production
Monthly hedge: 168 kWh/month

Translation: For every $1 the price moves, your option moves $0.63"
```

**Why This Matters:**
- Users need kWh amounts to hedge, not abstract ratios
- Shows actual production volumes
- Connects to physical reality

---

### 6. Theta → Time Decay Cost

**Technical:** Θ = -0.000131 per day

**Sophisticated Translation:**
```python
theta_info = GreeksTranslator.theta_to_time_decay(
    theta=-0.000131,
    system_size_kw=10.0
)

# Shows the user:
"You lose $0.00131/day to time decay
= $0.039/month = $0.48/year

If you SELL this option, you EARN $0.00131/day from decay"
```

**Why This Matters:**
- Time decay is critical for option strategies
- Shows cost/revenue depending on position (buy vs sell)
- Monthly numbers are budgetable

---

### 7. Vega → Volatility Impact

**Technical:** ν = 0.0339

**Sophisticated Translation:**
```python
vega_info = GreeksTranslator.vega_to_volatility_impact(
    vega=0.0339,
    system_size_kw=10.0,
    current_volatility=2.0
)

# Shows the user:
"Current volatility: 200%

+10% volatility increase → +$3.39 option value
-10% volatility decrease → -$3.39 option value

Useful if you expect storm season or climate changes"
```

**Why This Matters:**
- Users understand "storm season" better than "vega"
- Shows dollar impact of volatility changes
- Enables volatility trading strategies

---

## The Full Sophistication Layer in Action

```python
from solar_quant import load_solar_parameters, BinomialTree, calculate_greeks
from solar_quant.context_translator import create_contextual_summary

# Price option (technical output)
params = load_solar_parameters()
tree = BinomialTree(**params, N=500, payoff_type='call')
option_price = tree.price()
greeks = calculate_greeks(**params)

# Add sophistication layer (contextual output)
summary = create_contextual_summary(
    option_price=option_price,
    greeks=greeks,
    params=params,
    system_size_kw=10.0,       # User's system
    electricity_rate=0.12,     # User's rate
    panel_efficiency=0.20      # User's panels
)

print(summary)
```

**Output:**
```
======================================================================
SOLAR DERIVATIVES PRICING - CONTEXTUAL SUMMARY
======================================================================

YOUR SOLAR SYSTEM
----------------------------------------------------------------------
System Type:       Residential
System Size:       10.0 kW
Panel Efficiency:  20.0%
Effective Output:  17.0% (after losses)

CURRENT PRODUCTION & REVENUE
----------------------------------------------------------------------
Solar Irradiance:  5.16 kWh/m²/day
Your AC Output:    8.8 kWh/day (263 kWh/month)
Daily Revenue:     $1.05/day
Monthly Revenue:   $31.56/month
Annual Revenue:    $383/year

(at $0.12/kWh electricity rate)

REVENUE VOLATILITY (What "σ = 200%" Actually Means)
----------------------------------------------------------------------
Your revenue is VOLATILE. Here's what that means in dollars:

Daily Revenue Range (68% confidence):
  Low Day:         $0.28  (bad weather)
  Expected:        $1.05  (average)
  High Day:        $2.11 (excellent sun)
  Daily Swing:     ±$1.06

Monthly Revenue Range (68% confidence):
  Low Month:       $8.37
  Expected:        $31.56
  High Month:      $63.42
  Monthly Swing:   ±$31.86

Translation: Your monthly revenue could vary by ±$32
due to weather unpredictability.

OPTION PRICING (What It Costs to Hedge This Risk)
----------------------------------------------------------------------
Call Option Price:     $0.035645 per unit
Your Monthly Cost:     $10.69/month
Your Annual Cost:      $130.14/year

Translation: It costs $11/month to protect against
revenue drops below $0.0516.

Cost as % of revenue:  33.9% of expected revenue

RISK MANAGEMENT METRICS (What the Greeks Mean for YOU)
----------------------------------------------------------------------

1. DELTA = 0.634 → HEDGE RATIO
   Your Daily Output:     8.8 kWh/day
   Amount to Hedge:       5.6 kWh/day (63.4%)
   Monthly Hedge:         168 kWh/month

   Translation: To properly hedge, you need to cover 63%
   of your production with this option.

2. THETA = -0.000131 → TIME DECAY
   Daily Value Loss:      $0.00/day
   Weekly Value Loss:     $0.01/week
   Monthly Value Loss:    $0.04/month
   Annual Value Loss:     $0.48/year

   Translation: If you BUY this option, you lose $0.00/day
   to time decay. If you SELL it, you earn $0.00/day.

3. VEGA = 0.033905 → VOLATILITY SENSITIVITY
   Current Volatility:    200%

   If volatility increases by 10%:  Option value +$3.39
   If volatility decreases by 10%:  Option value -$3.39

   Translation: If weather becomes MORE unpredictable (+10% vol), your option
   is worth $3 more. If weather stabilizes, it loses $3 in value.

PRACTICAL SCENARIOS
----------------------------------------------------------------------

Scenario A: You OWN the solar farm, WANT TO HEDGE revenue risk
  → BUY this call option
  → Cost: $10.69/month
  → Benefit: Protected if production drops below 0.0516
  → Trade-off: Pay $11/month for peace of mind

Scenario B: You're a SPECULATOR, think weather will be BETTER than expected
  → SELL this call option
  → Collect: $10.69/month premium
  → Risk: Pay out if production exceeds 0.0516
  → Profit: Earn $0.00/day from time decay

Scenario C: You think VOLATILITY WILL INCREASE (storm season)
  → BUY this option (vega = 0.0339 > 0)
  → Gain: $3 per +10% volatility
  → Strategy: Volatility trading (not directional)

COMPARISON TO OTHER INVESTMENTS
----------------------------------------------------------------------
Your annual revenue:           $383
Annual hedge cost:             $130 (33.9% of revenue)
Revenue volatility:            200%

For comparison:
- Stock market volatility:     ~20% (your risk is 10.0x higher)
- Insurance as % of value:     ~1-2% (you're paying 33.9%)
- This is weather derivatives, not insurance (different product)

======================================================================
```

---

## Why This Is Sophisticated (Not Simplified)

### It's Not Dumbing Down Because:

1. **Preserves all technical accuracy**
   - Still shows exact Greeks
   - Still shows technical values
   - Nothing is hidden or approximated

2. **Adds complexity, not removes it**
   - Panel efficiency calculations
   - System loss modeling
   - Degradation factors
   - Multiple time scales (day/month/year)

3. **Requires domain expertise**
   - Solar panel physics
   - System engineering
   - Revenue modeling
   - Risk management translation

4. **Enables sophisticated decisions**
   - Compare hedge cost to revenue volatility
   - Evaluate ROI of options
   - Choose appropriate delta hedge
   - Time option purchases to volatility cycles

### It IS Sophisticated Because:

- **Meets users where they are:** They have kW systems, not "kWh/m²/day exposure"
- **Does the extra math:** Panel efficiency, system losses, time scaling
- **Provides context:** Comparison to stock market, insurance costs
- **Shows scenarios:** Buy vs sell, hedge vs speculate
- **Grounds abstractions:** "200%" → "$32/month swing"

---

## Usage Patterns

### Pattern 1: Quick Contextual Summary

```python
from solar_quant import load_solar_parameters, BinomialTree, calculate_greeks
from solar_quant.context_translator import create_contextual_summary

params = load_solar_parameters()
price = BinomialTree(**params, N=500).price()
greeks = calculate_greeks(**params)

summary = create_contextual_summary(
    price, greeks, params,
    system_size_kw=5.0,  # Their system
    electricity_rate=0.13  # Their rate
)

print(summary)  # Full grounded report
```

### Pattern 2: Individual Translators

```python
from solar_quant.context_translator import (
    SolarSystemContext,
    PriceTranslator,
    VolatilityTranslator
)

# Set up system
system = SolarSystemContext(system_size_kw=50.0, panel_efficiency=0.22)

# Translate irradiance to production
daily_kwh = system.ghi_to_ac_output(5.2)

# Translate to revenue
translator = PriceTranslator(system, electricity_rate=0.18)
daily_rev, monthly_rev, annual_rev = translator.revenue_at_ghi(5.2)

# Translate volatility to revenue swings
vol_translator = VolatilityTranslator(translator, spot_ghi=5.2)
low, exp, high = vol_translator.volatility_to_monthly_range(2.0)
```

### Pattern 3: Greeks Translation

```python
from solar_quant.context_translator import GreeksTranslator

# Translate delta to hedge amount
delta_info = GreeksTranslator.delta_to_hedge_amount(
    delta=0.634,
    system_size_kw=10.0,
    ghi_kwh_m2_day=5.2,
    solar_system=system
)

print(f"Hedge {delta_info['hedge_kwh_daily']:.1f} kWh/day")
```

---

## Implementation Details

### Classes

1. **`SolarSystemContext`**
   - Converts GHI → AC output
   - Accounts for: efficiency, losses, degradation
   - Handles residential to utility scale

2. **`PriceTranslator`**
   - Converts prices → revenue
   - Converts option prices → hedge costs
   - Scales by system size

3. **`VolatilityTranslator`**
   - Converts volatility % → dollar swings
   - Shows revenue ranges (daily/monthly)
   - Confidence intervals (1σ, 2σ)

4. **`GreeksTranslator`**
   - Static methods for each Greek
   - Converts to actionable metrics
   - Provides interpretation strings

5. **`create_contextual_summary()`**
   - Orchestrates all translators
   - Generates comprehensive report
   - Formatted for readability

---

## Benefits

### For Users

- **Understand what they're buying:** Not just Greeks, but actual dollars
- **Make informed decisions:** Compare costs to revenue
- **Budget properly:** Monthly/annual costs shown
- **Act on insights:** "Hedge 63% of production" is actionable

### For Developers

- **Reusable translators:** Build custom UX on top
- **Composable:** Use individual translators as needed
- **Extensible:** Add new translation types easily
- **Well-documented:** Clear API and examples

### For the Library

- **Differentiation:** Most pricing tools don't have this
- **User satisfaction:** Users actually understand outputs
- **Reduced support:** Clear outputs = fewer questions
- **Professional polish:** Shows attention to UX

---

## Examples Included

See `examples/06_contextual_pricing.py` for:

1. **Residential 5kW system** (Phoenix, AZ)
2. **Commercial 50kW rooftop** (Los Angeles, CA)
3. **1MW solar farm** (Spain)
4. **Detailed translation walkthrough** (step-by-step)

Run it:
```bash
python examples/06_contextual_pricing.py
```

---

## Future Enhancements

### Potential Additions

1. **Comparison Tools**
   - "Your solar vs grid electricity savings"
   - "Option cost vs battery storage cost"
   - "Hedging vs overbuilding capacity"

2. **Scenario Modeling**
   - "If electricity rates increase 20%..."
   - "If your panels degrade 1%/year..."
   - "If you expand to 15kW..."

3. **Visual Translations**
   - Revenue distribution charts
   - Hedge cost vs revenue graphs
   - Volatility timeline plots

4. **Regional Contexts**
   - State-specific buyback rates
   - Regional weather patterns
   - Local utility comparisons

5. **Tax Implications**
   - Solar tax credits
   - Hedging expense deductions
   - Revenue recognition

---

## Philosophy Summary

**The sophistication layer is about:**

✓ **Translation, not simplification**
✓ **Grounding, not dumbing down**
✓ **Context, not reduction**
✓ **Value-add, not hand-holding**

**Result:** Users understand not just WHAT the numbers are, but WHY they matter for THEIR specific situation.

This is **sophisticated UX** - meeting users where they are while preserving all technical rigor.

---

**Version:** 0.2.0-research
**Created:** December 6, 2024
**Philosophy:** Don't dumb down - ground up
