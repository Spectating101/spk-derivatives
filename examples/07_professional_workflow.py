#!/usr/bin/env python3
"""
Professional Workflow Example

Shows the COMPLETE sophisticated user experience:
- Save/load results
- Compare scenarios
- Validate pricing
- Export reports
- Batch operations
- Comparative context
- Break-even analysis

This is what users reasonably expect from a professional library.
"""

import sys
sys.path.insert(0, '../energy_derivatives/src')

from data_loader_nasa import load_solar_parameters
from binomial import BinomialTree
from sensitivities import calculate_greeks
from results_manager import (
    PricingResult,
    ResultsComparator,
    PricingValidator,
    batch_price,
    comparative_context,
    break_even_analysis
)


def example_1_save_load():
    """
    Example 1: Save and Load Results

    User expectation: "I priced this yesterday, let me load it back."
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: SAVE & LOAD RESULTS")
    print("="*70)

    # Price option
    print("\n1. Pricing Taiwan 10kW system...")
    params = load_solar_parameters(lat=24.99, lon=121.30, volatility_cap=2.0)
    tree = BinomialTree(**params, N=500, payoff_type='call')
    price = tree.price()
    greeks = calculate_greeks(**params)

    # Create result object
    result = PricingResult(
        option_price=price,
        greeks=greeks,
        params=params,
        metadata={
            'location': 'Taiwan',
            'system_size_kw': 10.0,
            'description': 'Residential rooftop system'
        }
    )

    print(f"   Option price: ${price:.6f}")

    # Save it
    print("\n2. Saving to file...")
    filepath = result.save('results/taiwan_10kw.json')
    print(f"   ✓ Saved to: {filepath}")

    # Load it back
    print("\n3. Loading from file...")
    loaded = PricingResult.load('results/taiwan_10kw.json')
    print(f"   ✓ Loaded: ${loaded.option_price:.6f}")
    print(f"   Timestamp: {loaded.timestamp}")

    # Show summary
    print("\n4. Result summary:")
    print(loaded.summary())


def example_2_compare_scenarios():
    """
    Example 2: Compare Multiple Scenarios

    User expectation: "I want to compare Taiwan vs Arizona vs Spain."
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: COMPARE MULTIPLE SCENARIOS")
    print("="*70)

    scenarios = [
        {'location': 'Taiwan', 'lat': 24.99, 'lon': 121.30},
        {'location': 'Arizona', 'lat': 33.45, 'lon': -112.07},
        {'location': 'Spain', 'lat': 40.42, 'lon': -3.70},
    ]

    results = []
    labels = []

    print("\nPricing each location...")
    for scenario in scenarios:
        print(f"  - {scenario['location']}...", end=' ')
        params = load_solar_parameters(
            lat=scenario['lat'],
            lon=scenario['lon'],
            volatility_cap=2.0
        )
        tree = BinomialTree(**params, N=300, payoff_type='call')
        price = tree.price()
        greeks = calculate_greeks(**params)

        result = PricingResult(price, greeks, params, metadata=scenario)
        results.append(result)
        labels.append(scenario['location'])
        print(f"${price:.6f}")

    # Compare
    print("\nComparison table:")
    comparator = ResultsComparator(results, labels)
    print(comparator.comparison_table())

    # Best value
    idx, label, best = comparator.best_value()
    print(f"\n✓ Best value: {label} at ${best.option_price:.6f}")

    # Export comparison
    print("\nExporting comparison to CSV...")
    filepath = comparator.export_comparison('results/location_comparison.csv')
    print(f"✓ Saved to: {filepath}")


def example_3_validation():
    """
    Example 3: Validate Pricing

    User expectation: "Is this price reasonable or did something break?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: VALIDATE PRICING")
    print("="*70)

    # Price with normal parameters
    print("\n1. Normal pricing (Taiwan, 200% vol)...")
    params = load_solar_parameters(volatility_cap=2.0)
    tree = BinomialTree(**params, N=300, payoff_type='call')
    price = tree.price()
    greeks = calculate_greeks(**params)

    result = PricingResult(price, greeks, params)

    # Validate
    print(PricingValidator.validation_report(result))

    # Price with extreme parameters (uncapped volatility)
    print("\n2. Extreme pricing (Taiwan, uncapped vol)...")
    params_extreme = load_solar_parameters(volatility_cap=None)
    tree_extreme = BinomialTree(**params_extreme, N=300, payoff_type='call')
    price_extreme = tree_extreme.price()
    greeks_extreme = calculate_greeks(**params_extreme)

    result_extreme = PricingResult(price_extreme, greeks_extreme, params_extreme)

    # Validate extreme
    print(PricingValidator.validation_report(result_extreme))


def example_4_comparative_context():
    """
    Example 4: Comparative Context

    User expectation: "Is this a good deal compared to normal investments?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: COMPARATIVE CONTEXT")
    print("="*70)

    params = load_solar_parameters(volatility_cap=2.0)
    tree = BinomialTree(**params, N=300, payoff_type='call')
    price = tree.price()
    greeks = calculate_greeks(**params)

    result = PricingResult(price, greeks, params)

    # Get comparative context
    context = comparative_context(result)

    print("\nHow does this compare to other investments?")
    print("-" * 70)
    for key, comparison in context.items():
        print(f"\n{key.replace('_', ' ').title()}:")
        print(f"  {comparison}")


def example_5_breakeven():
    """
    Example 5: Break-Even Analysis

    User expectation: "When does this hedge actually pay off?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: BREAK-EVEN ANALYSIS")
    print("="*70)

    params = load_solar_parameters(volatility_cap=2.0)
    tree = BinomialTree(**params, N=300, payoff_type='call')
    price = tree.price()
    greeks = calculate_greeks(**params)

    result = PricingResult(price, greeks, params)

    # Calculate break-even
    breakeven = break_even_analysis(result, system_size_kw=10.0)

    print("\nBreak-Even Analysis:")
    print("-" * 70)
    print(f"Current Spot Price:    ${breakeven['current_spot']:.4f}")
    print(f"Strike Price:          ${breakeven['strike']:.4f}")
    print(f"Premium Paid:          ${breakeven['premium_paid']:.6f}")
    print(f"\nBreak-Even Price:      ${breakeven['breakeven_price']:.4f}")
    print(f"Required Change:       {breakeven['breakeven_change_pct']:+.2f}%")
    print(f"\n{breakeven['interpretation']}")


def example_6_batch_operations():
    """
    Example 6: Batch Pricing

    User expectation: "I have 5 solar farms, price them all at once."
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: BATCH OPERATIONS")
    print("="*70)

    # Define solar farm portfolio
    portfolio = [
        {'name': 'Farm A', 'lat': 33.45, 'lon': -112.07, 'size_kw': 1000},  # AZ
        {'name': 'Farm B', 'lat': 40.42, 'lon': -3.70, 'size_kw': 500},     # Spain
        {'name': 'Farm C', 'lat': 34.05, 'lon': -118.24, 'size_kw': 750},   # CA
    ]

    print(f"\nPricing portfolio of {len(portfolio)} solar farms...")

    def price_farm(scenario):
        """Price a single farm"""
        params = load_solar_parameters(
            lat=scenario['lat'],
            lon=scenario['lon'],
            volatility_cap=2.0
        )
        tree = BinomialTree(**params, N=200, payoff_type='call')
        price = tree.price()
        greeks = calculate_greeks(**params)
        return price, greeks, params

    # Batch price
    labels = [f"{farm['name']} ({farm['size_kw']}kW)" for farm in portfolio]
    comparator = batch_price(portfolio, price_farm, labels)

    # Show comparison
    print(comparator.comparison_table())

    # Export
    print("\nExporting portfolio pricing...")
    filepath = comparator.export_comparison('results/portfolio_pricing.csv')
    print(f"✓ Saved to: {filepath}")


def example_7_complete_workflow():
    """
    Example 7: Complete Professional Workflow

    Shows everything together: the full sophisticated experience.
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: COMPLETE PROFESSIONAL WORKFLOW")
    print("="*70)

    print("\n1. Price the option...")
    params = load_solar_parameters(lat=33.45, lon=-112.07, volatility_cap=2.0)
    tree = BinomialTree(**params, N=500, payoff_type='call')
    price = tree.price()
    greeks = calculate_greeks(**params)

    result = PricingResult(
        price, greeks, params,
        metadata={'location': 'Phoenix, AZ', 'system_size_kw': 50}
    )

    print(f"   ✓ Priced: ${price:.6f}")

    print("\n2. Validate the result...")
    validation = PricingValidator.validate(result)
    print(f"   ✓ Status: {validation['status']}")
    if validation['warnings']:
        for w in validation['warnings']:
            print(f"   ⚠️  {w}")

    print("\n3. Add comparative context...")
    context = comparative_context(result)
    print(f"   ✓ {context['volatility_vs_stocks']}")

    print("\n4. Calculate break-even...")
    breakeven = break_even_analysis(result)
    print(f"   ✓ {breakeven['interpretation']}")

    print("\n5. Save results...")
    filepath = result.save('results/phoenix_50kw_complete.json')
    print(f"   ✓ Saved to: {filepath}")

    print("\n6. Export to CSV...")
    csv_path = result.to_csv('results/phoenix_50kw_complete.csv')
    print(f"   ✓ Exported to: {csv_path}")

    print("\n" + "="*70)
    print("COMPLETE WORKFLOW FINISHED")
    print("="*70)
    print("""
What we just did:
✓ Priced an option
✓ Validated it (sanity checks)
✓ Added context (vs stocks, insurance)
✓ Calculated break-even
✓ Saved to JSON
✓ Exported to CSV

This is what users expect from a professional library.
    """)


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("PROFESSIONAL WORKFLOW DEMONSTRATIONS")
    print("Complete sophisticated user experience")
    print("="*70)

    try:
        example_1_save_load()
        input("\nPress Enter for next example...")

        example_2_compare_scenarios()
        input("\nPress Enter for next example...")

        example_3_validation()
        input("\nPress Enter for next example...")

        example_4_comparative_context()
        input("\nPress Enter for next example...")

        example_5_breakeven()
        input("\nPress Enter for next example...")

        example_6_batch_operations()
        input("\nPress Enter for complete workflow...")

        example_7_complete_workflow()

        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETE")
        print("="*70)
        print("""
This library now provides:

✅ Save/load results
✅ Compare scenarios
✅ Validate pricing
✅ Export to CSV/JSON
✅ Batch operations
✅ Comparative context
✅ Break-even analysis

Everything a user would reasonably expect from a professional pricing library.
        """)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted.")


if __name__ == "__main__":
    main()
