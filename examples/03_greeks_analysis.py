#!/usr/bin/env python3
"""
Greeks Analysis Example: Calculate and Interpret Risk Metrics

This shows how to calculate option Greeks (Delta, Gamma, Theta, Vega, Rho)
and interpret them for risk management.
"""

from spk_derivatives import load_solar_parameters, calculate_greeks, BinomialTree

def main():
    print("\n" + "="*70)
    print("SOLAR OPTION GREEKS (RISK METRICS)")
    print("="*70 + "\n")

    # Load solar data
    print("Loading NASA solar data for Taiwan...")
    params = load_solar_parameters(volatility_cap=2.0)

    # Calculate option price
    tree = BinomialTree(**params, N=1000, payoff_type='call')
    call_price = tree.price()

    # Calculate Greeks
    print("Calculating risk metrics...\n")
    greeks = calculate_greeks(
        S0=params['S0'],
        K=params['K'],
        T=params['T'],
        r=params['r'],
        sigma=params['sigma'],
        option_type='call'
    )

    # Display parameters
    print("="*70)
    print("OPTION PARAMETERS")
    print("="*70)
    print(f"Spot Price (S₀):   ${params['S0']:.4f}/kWh")
    print(f"Strike Price (K):  ${params['K']:.4f}/kWh")
    print(f"Time to Maturity:  {params['T']:.1f} year")
    print(f"Risk-Free Rate:    {params['r']:.2%}")
    print(f"Volatility (σ):    {params['sigma']:.2%}")
    print(f"\nCall Option Price: ${call_price:.6f}")

    # Display Greeks
    print("\n" + "="*70)
    print("GREEKS (RISK METRICS)")
    print("="*70)

    print(f"\n1. DELTA (Δ): {greeks['delta']:.4f}")
    print("   → Measures: Change in option price per $1 change in spot price")
    print(f"   → If spot price increases by $0.001, option price changes by ${greeks['delta'] * 0.001:.6f}")
    print(f"   → Hedge ratio: Need to hold {greeks['delta']:.1%} of underlying to hedge")

    print(f"\n2. GAMMA (Γ): {greeks['gamma']:.4f}")
    print("   → Measures: Rate of change of Delta")
    print("   → Shows how much Delta will change as spot price moves")
    print(f"   → High gamma = Delta is very sensitive to price changes")

    print(f"\n3. THETA (Θ): {greeks['theta']:.8f} per day")
    print("   → Measures: Time decay (option value lost per day)")
    print(f"   → Option loses ${abs(greeks['theta']):.8f} in value each day")
    print(f"   → Over 30 days: ${abs(greeks['theta']) * 30:.6f} lost to time decay")

    print(f"\n4. VEGA (ν): {greeks['vega']:.6f}")
    print("   → Measures: Sensitivity to volatility changes")
    print(f"   → If volatility increases by 1%, option price changes by ${greeks['vega']:.6f}")
    print("   → High vega = Option is very sensitive to volatility")

    print(f"\n5. RHO (ρ): {greeks['rho']:.6f}")
    print("   → Measures: Sensitivity to interest rate changes")
    print(f"   → If risk-free rate increases by 1%, option price changes by ${greeks['rho']:.6f}")

    # Practical interpretation
    print("\n" + "="*70)
    print("PRACTICAL INTERPRETATION FOR RISK MANAGEMENT")
    print("="*70)

    print(f"""
Scenario 1: HEDGING A SOLAR FARM
- You own a solar farm producing at the spot price (${params['S0']:.4f}/kWh)
- Delta = {greeks['delta']:.2%} means you need to sell {greeks['delta']:.2%} of production
  to hedge against price drops
- Gamma = {greeks['gamma']:.2f} means your hedge ratio changes rapidly with price

Scenario 2: TIME DECAY STRATEGY
- You sold this option and collected ${call_price:.6f} premium
- Time decay works in your favor: +${abs(greeks['theta']):.6f} per day
- After 30 days: +${abs(greeks['theta']) * 30:.4f} from time decay alone

Scenario 3: VOLATILITY TRADING
- If you expect volatility to increase, BUY this option
- Vega = {greeks['vega']:.4f} means +10% volatility → +${greeks['vega'] * 10:.4f} value
- If you expect volatility to decrease, SELL this option

Scenario 4: INTEREST RATE EXPOSURE
- Rho = {greeks['rho']:.4f} means small exposure to rate changes
- +1% rate change → +${greeks['rho']:.4f} option value
- Interest rate risk is minimal for this option
    """)

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
