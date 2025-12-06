#!/usr/bin/env python3
"""
Contextual Pricing Example - The Sophistication Layer

This demonstrates the UX sophistication layer that translates technical
outputs into grounded, relatable context.

Not dumbing down - adding value through practical translation.
"""

from spk_derivatives import load_solar_parameters, BinomialTree, calculate_greeks
from spk_derivatives.context_translator import (
    SolarSystemContext,
    PriceTranslator,
    VolatilityTranslator,
    create_contextual_summary
)

def example_residential_system():
    """
    Example: 5kW residential solar system
    Translation: "What does this mean for MY house?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: RESIDENTIAL 5kW ROOFTOP SYSTEM")
    print("="*70)

    # Load pricing data
    params = load_solar_parameters(lat=33.45, lon=-112.07, volatility_cap=2.0)  # Phoenix, AZ
    tree = BinomialTree(**params, N=500, payoff_type='call')
    option_price = tree.price()
    greeks = calculate_greeks(**params)

    # Create contextual summary
    summary = create_contextual_summary(
        option_price=option_price,
        greeks=greeks,
        params=params,
        system_size_kw=5.0,           # Typical residential
        electricity_rate=0.13,         # Arizona average
        panel_efficiency=0.20          # Modern panels
    )

    print(summary)


def example_commercial_rooftop():
    """
    Example: 50kW commercial rooftop
    Translation: "What's the hedge cost for my business?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: COMMERCIAL 50kW ROOFTOP (WAREHOUSE/OFFICE)")
    print("="*70)

    # Load pricing data (California)
    params = load_solar_parameters(lat=34.05, lon=-118.24, volatility_cap=2.0)
    tree = BinomialTree(**params, N=500, payoff_type='call')
    option_price = tree.price()
    greeks = calculate_greeks(**params)

    summary = create_contextual_summary(
        option_price=option_price,
        greeks=greeks,
        params=params,
        system_size_kw=50.0,          # Commercial rooftop
        electricity_rate=0.18,         # California commercial rate
        panel_efficiency=0.22          # Premium panels
    )

    print(summary)


def example_solar_farm():
    """
    Example: 1MW (1000kW) solar farm
    Translation: "What's my monthly volatility exposure in dollars?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: 1MW SOLAR FARM (INVESTMENT)")
    print("="*70)

    # Load pricing data (Spain - good solar region)
    params = load_solar_parameters(lat=40.42, lon=-3.70, volatility_cap=2.0)
    tree = BinomialTree(**params, N=500, payoff_type='call')
    option_price = tree.price()
    greeks = calculate_greeks(**params)

    summary = create_contextual_summary(
        option_price=option_price,
        greeks=greeks,
        params=params,
        system_size_kw=1000.0,        # 1MW farm
        electricity_rate=0.10,         # European rate
        panel_efficiency=0.20          # Standard utility panels
    )

    print(summary)


def detailed_translation_example():
    """
    Show specific translations step-by-step
    """
    print("\n" + "="*70)
    print("DETAILED TRANSLATION WALKTHROUGH")
    print("="*70)

    # Load data
    params = load_solar_parameters(lat=24.99, lon=121.30, volatility_cap=2.0)  # Taiwan
    tree = BinomialTree(**params, N=500, payoff_type='call')
    option_price = tree.price()
    greeks = calculate_greeks(**params)

    # Set up translators for 10kW system
    solar_system = SolarSystemContext(
        system_size_kw=10.0,
        panel_efficiency=0.20
    )

    price_translator = PriceTranslator(
        solar_system=solar_system,
        electricity_rate=0.12
    )

    spot_ghi = params['S0'] / 0.10

    print("\nSTEP 1: Solar Irradiance → Actual Production")
    print("-" * 70)
    print(f"Technical:  GHI = {spot_ghi:.2f} kWh/m²/day")
    daily_kwh = solar_system.ghi_to_ac_output(spot_ghi)
    print(f"Grounded:   Your 10kW system produces {daily_kwh:.1f} kWh/day")
    print(f"            (accounting for {solar_system.panel_efficiency*100:.0f}% panel efficiency")
    print(f"             + {solar_system.SYSTEM_LOSSES*100:.0f}% system losses)")

    print("\nSTEP 2: Production → Revenue")
    print("-" * 70)
    print(f"Technical:  {daily_kwh:.1f} kWh/day output")
    daily_rev, monthly_rev, annual_rev = price_translator.revenue_at_ghi(spot_ghi)
    print(f"Grounded:   ${daily_rev:.2f}/day revenue")
    print(f"            ${monthly_rev:.2f}/month revenue")
    print(f"            ${annual_rev:,.2f}/year revenue")
    print(f"            (at $0.12/kWh net metering rate)")

    print("\nSTEP 3: Volatility % → Revenue Swings")
    print("-" * 70)
    print(f"Technical:  σ = {params['sigma']:.0%} (volatility)")
    vol_translator = VolatilityTranslator(price_translator, spot_ghi)
    daily_low, daily_exp, daily_high = vol_translator.volatility_to_revenue_range(params['sigma'])
    print(f"Grounded:   Daily revenue range: ${daily_low:.2f} to ${daily_high:.2f}")
    print(f"            Expected: ${daily_exp:.2f}")
    print(f"            Swing: ±${daily_high - daily_exp:.2f} per day")
    monthly_low, monthly_exp, monthly_high = vol_translator.volatility_to_monthly_range(params['sigma'])
    print(f"            Monthly swing: ±${monthly_high - monthly_exp:.2f}")
    print(f"            → Bad month could cost you ${monthly_exp - monthly_low:.0f}")

    print("\nSTEP 4: Option Price → Hedge Cost")
    print("-" * 70)
    print(f"Technical:  Call price = ${option_price:.6f} per unit")
    monthly_cost = price_translator.option_price_to_monthly_cost(option_price, spot_ghi)
    annual_cost = price_translator.option_price_to_annual_cost(option_price, spot_ghi)
    print(f"Grounded:   ${monthly_cost:.2f}/month to hedge your 10kW system")
    print(f"            ${annual_cost:.2f}/year")
    print(f"            = {(monthly_cost/monthly_rev)*100:.1f}% of your expected revenue")

    print("\nSTEP 5: Delta → Hedge Amount")
    print("-" * 70)
    print(f"Technical:  Δ = {greeks['delta']:.3f}")
    hedge_kwh = daily_kwh * greeks['delta']
    print(f"Grounded:   Hedge {hedge_kwh:.1f} kWh/day")
    print(f"            = {greeks['delta']*100:.1f}% of your {daily_kwh:.1f} kWh/day production")
    print(f"            → For every $1 the price moves, your option moves ${greeks['delta']:.2f}")

    print("\nSTEP 6: Theta → Time Decay Cost")
    print("-" * 70)
    print(f"Technical:  Θ = {greeks['theta']:.8f} per day")
    daily_decay = abs(greeks['theta']) * solar_system.system_size_kw
    monthly_decay = daily_decay * 30
    print(f"Grounded:   You lose ${daily_decay:.2f}/day to time decay")
    print(f"            = ${monthly_decay:.2f}/month")
    print(f"            If you SELL the option, you EARN this decay")

    print("\nSTEP 7: Vega → Volatility Impact")
    print("-" * 70)
    print(f"Technical:  ν = {greeks['vega']:.6f}")
    vega_scaled = greeks['vega'] * solar_system.system_size_kw
    print(f"Grounded:   +10% volatility = +${vega_scaled * 10:.2f} option value")
    print(f"            -10% volatility = -${vega_scaled * 10:.2f} option value")
    print(f"            Useful if you expect storm season or climate changes")

    print("\n" + "="*70)
    print("WHY THIS MATTERS: THE SOPHISTICATION LAYER")
    print("="*70)
    print("""
Most pricing tools give you:
  "Call price: $0.035645"
  "Volatility: 200%"
  "Delta: 0.634"

You think: "Okay... what does that MEAN for MY solar panels?"

This sophistication layer does the extra math to answer:
  ✓ How much electricity will MY panels actually produce?
  ✓ How much revenue is that worth in DOLLARS?
  ✓ What does "200% volatility" mean for MY monthly income?
  ✓ What does it COST to hedge MY system size?
  ✓ How much of MY production should I hedge?

Not dumbing down - grounding abstract finance in YOUR reality.

This is the difference between:
  "Here's a Greek letter" ← Useless
  "Here's what it costs you per month" ← Actionable
    """)


def main():
    """Run all contextual examples"""

    print("\n" + "="*70)
    print("SOLAR DERIVATIVES - CONTEXTUAL PRICING EXAMPLES")
    print("Demonstration of the Sophistication Layer")
    print("="*70)

    # Run examples
    example_residential_system()
    input("\nPress Enter to see commercial example...")

    example_commercial_rooftop()
    input("\nPress Enter to see solar farm example...")

    example_solar_farm()
    input("\nPress Enter to see detailed translation walkthrough...")

    detailed_translation_example()

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("""
The sophistication layer translates:
- Technical jargon → Real-world context
- Percentages → Dollars
- Greek letters → Actionable decisions
- "Per unit per day" → "Per month for your system"

This isn't dumbing down. It's:
✓ Adding value through practical translation
✓ Meeting users where they are
✓ Doing the extra math they'd have to do anyway
✓ Grounding abstract finance in physical reality

Result: Users understand not just WHAT they're buying,
but WHY it matters for THEIR specific situation.
    """)


if __name__ == "__main__":
    main()
