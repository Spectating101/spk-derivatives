#!/usr/bin/env python3
"""
Custom Data Integration Example

This shows how to use the library with your own solar irradiance data
instead of NASA data.
"""

import pandas as pd
import numpy as np
from solar_quant import BinomialTree, calculate_greeks

def load_custom_solar_data():
    """
    Simulate loading solar irradiance data from your own source.
    In practice, this would load from your CSV, database, or API.
    """
    print("Loading custom solar data from local sensors...")

    # Simulate 2 years of daily solar irradiance data
    # In practice: df = pd.read_csv('my_solar_data.csv')
    dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')

    # Simulate realistic solar data (kWh/m²/day)
    # Mean around 5, with seasonal variation
    np.random.seed(42)
    seasonal = 5 + 2 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
    noise = np.random.normal(0, 1, len(dates))
    irradiance = seasonal + noise
    irradiance = np.maximum(irradiance, 0.5)  # Floor at 0.5

    df = pd.DataFrame({
        'date': dates,
        'irradiance_kwh_m2': irradiance
    })

    print(f"  Loaded {len(df)} days of data")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

    return df

def calculate_volatility(df, method='log', deseason=True):
    """
    Calculate annualized volatility from solar data.
    """
    print(f"\nCalculating volatility (method={method}, deseason={deseason})...")

    irr = df['irradiance_kwh_m2'].copy()

    # Deseasonalize if requested
    if deseason:
        rolling_mean = irr.rolling(window=30, center=True).mean()
        irr_deseason = irr - rolling_mean
        irr_deseason = irr_deseason.dropna()
        source = irr_deseason
    else:
        source = irr

    # Calculate returns
    if method == 'log':
        returns = np.log(source / source.shift(1))
    elif method == 'pct_change':
        returns = source.pct_change()
    else:
        raise ValueError(f"Unknown method: {method}")

    returns = returns.dropna()

    # Annualized volatility
    daily_vol = returns.std()
    annual_vol = daily_vol * np.sqrt(365)

    print(f"  Daily volatility:  {daily_vol:.4f}")
    print(f"  Annual volatility: {annual_vol:.2%}")

    return annual_vol

def main():
    print("\n" + "="*70)
    print("CUSTOM SOLAR DATA INTEGRATION")
    print("="*70 + "\n")

    # Step 1: Load your custom data
    df = load_custom_solar_data()

    print(f"\nData summary:")
    print(f"  Mean irradiance: {df['irradiance_kwh_m2'].mean():.2f} kWh/m²/day")
    print(f"  Min irradiance:  {df['irradiance_kwh_m2'].min():.2f} kWh/m²/day")
    print(f"  Max irradiance:  {df['irradiance_kwh_m2'].max():.2f} kWh/m²/day")

    # Step 2: Calculate volatility from your data
    volatility = calculate_volatility(df, method='log', deseason=True)

    # Optional: cap volatility for numerical stability
    if volatility > 2.0:
        print(f"\n⚠️  Volatility ({volatility:.2%}) exceeds 200%, capping for stability")
        volatility = 2.0

    # Step 3: Set up pricing parameters
    current_irradiance = df['irradiance_kwh_m2'].iloc[-1]
    energy_price = 0.10  # $/kWh

    params = {
        'S0': current_irradiance * energy_price,  # Spot price
        'K': current_irradiance * energy_price,   # Strike (at-the-money)
        'T': 1.0,                                  # 1 year maturity
        'r': 0.05,                                 # 5% risk-free rate
        'sigma': volatility                        # Calculated volatility
    }

    print("\n" + "="*70)
    print("PRICING PARAMETERS")
    print("="*70)
    print(f"Current Irradiance:  {current_irradiance:.2f} kWh/m²/day")
    print(f"Energy Value:        ${energy_price:.2f}/kWh")
    print(f"Spot Price (S₀):     ${params['S0']:.4f}")
    print(f"Strike Price (K):    ${params['K']:.4f} (at-the-money)")
    print(f"Maturity (T):        {params['T']:.1f} year")
    print(f"Risk-Free Rate (r):  {params['r']:.2%}")
    print(f"Volatility (σ):      {params['sigma']:.2%}")

    # Step 4: Price the option
    print("\n" + "="*70)
    print("PRICING OPTION WITH CUSTOM DATA")
    print("="*70)

    tree = BinomialTree(**params, N=1000, payoff_type='call')
    call_price = tree.price()

    print(f"\nCall Option Price: ${call_price:.6f}")
    print(f"Premium: {(call_price/params['S0']):.2%} of spot price")

    # Step 5: Calculate Greeks
    print("\n" + "="*70)
    print("RISK METRICS")
    print("="*70)

    greeks = calculate_greeks(**params)
    print(f"\nDelta:  {greeks['delta']:.4f} (hedge ratio)")
    print(f"Gamma:  {greeks['gamma']:.4f} (curvature)")
    print(f"Theta:  {greeks['theta']:.8f} (daily decay)")
    print(f"Vega:   {greeks['vega']:.6f} (vol sensitivity)")
    print(f"Rho:    {greeks['rho']:.6f} (rate sensitivity)")

    # Step 6: Practical application
    print("\n" + "="*70)
    print("PRACTICAL APPLICATION")
    print("="*70)
    print(f"""
Your solar farm produces at {current_irradiance:.2f} kWh/m²/day

Revenue Risk Protection:
- Buy this call option for ${call_price:.6f} per kWh/m²/day
- If irradiance drops below {params['K']:.4f}, option pays off
- Hedge ratio (Delta): {greeks['delta']:.2%} means hedge {greeks['delta']:.2%} of production

Cost Analysis:
- Daily time decay: ${abs(greeks['theta']):.6f}
- Monthly cost: ${abs(greeks['theta']) * 30:.4f}
- Annual cost: ${abs(greeks['theta']) * 365:.4f}

Volatility Impact:
- If volatility increases 10%, option value increases ${greeks['vega'] * 10:.4f}
- Useful for trading weather risk
    """)

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
