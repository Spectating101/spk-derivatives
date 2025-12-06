#!/usr/bin/env python3
"""
Quick Start Example: Price a Solar Call Option in 5 Lines

This is the absolute simplest way to use the library.
"""

from solar_quant import load_solar_parameters, BinomialTree

# Load Taiwan solar data from NASA (automatic)
params = load_solar_parameters()

# Price an at-the-money call option
tree = BinomialTree(**params, N=100, payoff_type='call')
price = tree.price()

# Display result
print(f"\n{'='*50}")
print(f"SOLAR CALL OPTION PRICE")
print(f"{'='*50}")
print(f"Location:     Taiwan (24.99°N, 121.30°E)")
print(f"Spot Price:   ${params['S0']:.4f}/kWh")
print(f"Strike:       ${params['K']:.4f}/kWh (at-the-money)")
print(f"Maturity:     {params['T']:.1f} year")
print(f"Volatility:   {params['sigma']:.2%}")
print(f"\nCALL PRICE:   ${price:.6f}")
print(f"{'='*50}\n")
