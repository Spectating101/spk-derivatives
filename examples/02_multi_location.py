#!/usr/bin/env python3
"""
Multi-Location Example: Compare Option Prices Across Different Regions

This shows how to price solar derivatives for multiple geographic locations
and compare their characteristics.
"""

from solar_quant import load_solar_parameters, BinomialTree
import pandas as pd

def price_location(name, lat, lon):
    """Price solar call option for a specific location"""
    print(f"Pricing {name}...", end=' ')

    # Load data for this location
    params = load_solar_parameters(
        lat=lat,
        lon=lon,
        volatility_cap=2.0  # Cap at 200% for stability
    )

    # Price call option
    tree = BinomialTree(**params, N=500, payoff_type='call')
    call_price = tree.price()

    print("✓")

    return {
        'Location': name,
        'Latitude': lat,
        'Longitude': lon,
        'Spot ($/kWh)': params['S0'],
        'Volatility': f"{params['sigma']:.2%}",
        'Call Price': f"${call_price:.6f}",
        'Premium': f"{(call_price/params['S0']):.2%}"
    }

def main():
    print("\n" + "="*70)
    print("MULTI-LOCATION SOLAR DERIVATIVES PRICING")
    print("="*70 + "\n")

    # Define locations to price
    locations = [
        ('Taiwan (Taoyuan)', 24.99, 121.30),
        ('Arizona (Phoenix)', 33.45, -112.07),
        ('Spain (Madrid)', 40.42, -3.70),
        ('Germany (Berlin)', 52.52, 13.40),
        ('California (LA)', 34.05, -118.24),
    ]

    # Price each location
    results = []
    for name, lat, lon in locations:
        result = price_location(name, lat, lon)
        results.append(result)

    # Display results table
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70 + "\n")

    df = pd.DataFrame(results)
    print(df.to_string(index=False))

    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)
    print("""
The call option price reflects both:
1. Current irradiance levels (spot price)
2. Weather volatility (uncertainty premium)

Higher volatility → Higher option premium
More stable sun → Lower option premium

Premium % shows how much the option costs relative to spot price.
Locations with consistent sunshine (Arizona) typically have lower premiums.
    """)

if __name__ == "__main__":
    main()
