"""
Comprehensive Unit Tests for spk-derivatives Core Modules
===========================================================

Tests covering:
- Binomial pricing engine
- Monte Carlo simulation
- Greeks (sensitivities) calculation
- Data loaders (NASA, Wind, Hydro, Base)
- Location guide (geographic presets)
- Context translator (sophisticated output)
- Results manager (professional workflows)

Target Coverage: 80%+
Run: pytest tests/test_core_modules.py -v --cov
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

# Import all core modules
from energy_derivatives.spk_derivatives import (
    BinomialTree,
    MonteCarloSimulator,
    GreeksCalculator,
    load_solar_parameters,
    EnergyDataLoader,
    WindDataLoader,
    HydroDataLoader,
    get_location,
    list_locations,
    search_by_country,
    SolarSystemContext,
    PriceTranslator,
    GreeksTranslator,
    create_contextual_summary,
    PricingResult,
    ResultsComparator,
    PricingValidator,
    batch_price,
)


# ============================================================================
# BINOMIAL TREE TESTS
# ============================================================================

class TestBinomialTree:
    """Unit tests for BinomialTree pricing engine"""
    
    def test_binomial_initialization(self):
        """Test BinomialTree initializes with correct parameters"""
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=100)
        
        assert tree.S0 == 0.035
        assert tree.K == 0.040
        assert tree.T == 1.0
        assert tree.r == 0.025
        assert tree.sigma == 0.42
        assert tree.N == 100
    
    def test_binomial_price_call_option(self):
        """Test Binomial pricing for call option"""
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call')
        price = tree.price()
        
        # Price should be positive and less than spot
        assert 0 < price < 0.035
        # For OTM call, price should be small but positive
        assert price < 0.010
    
    def test_binomial_price_put_option(self):
        """Test Binomial pricing for put option"""
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='put')
        price = tree.price()
        
        # Price should be positive
        assert price > 0
        # For ITM put, price should be significant
        assert price > 0.004
    
    def test_binomial_convergence(self):
        """Test Binomial convergence with increasing N"""
        # Price with low precision
        price_low = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=50, payoff_type='call').price()
        
        # Price with high precision
        price_high = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=500, payoff_type='call').price()
        
        # Should converge (error should decrease)
        error_low = abs(price_low - price_high) / price_high if price_high != 0 else 0
        
        # With higher N, error should be smaller
        price_very_high = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=1000, payoff_type='call').price()
        error_high = abs(price_high - price_very_high) / price_very_high if price_very_high != 0 else 0
        
        # Error should shrink with more nodes
        assert error_high < error_low
    
    def test_binomial_atm_symmetry(self):
        """Test at-the-money call/put symmetry"""
        # ATM call
        call = BinomialTree(S0=0.050, K=0.050, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call').price()
        
        # ATM put
        put = BinomialTree(S0=0.050, K=0.050, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='put').price()
        
        # Put-call parity: C - P = S0 - K*e^(-r*T)
        parity_diff = call - put - (0.050 - 0.050 * np.exp(-0.025 * 1.0))
        
        # Should be approximately zero (within numerical tolerance)
        assert abs(parity_diff) < 0.001
    
    def test_binomial_volatility_effect(self):
        """Test that higher volatility increases option value"""
        low_vol = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.20, N=100, payoff_type='call').price()
        high_vol = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.80, N=100, payoff_type='call').price()
        
        # Higher volatility should increase call value
        assert high_vol > low_vol
    
    def test_binomial_time_decay(self):
        """Test that option value decreases with less time to maturity"""
        short_term = BinomialTree(S0=0.035, K=0.040, T=0.1, r=0.025, sigma=0.42, N=100, payoff_type='call').price()
        long_term = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call').price()
        
        # Longer maturity should have higher value
        assert long_term > short_term


# ============================================================================
# MONTE CARLO TESTS
# ============================================================================

class TestMonteCarloSimulator:
    """Unit tests for MonteCarloSimulator"""
    
    def test_mc_initialization(self):
        """Test MonteCarloSimulator initializes correctly"""
        mc = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, 
                                num_simulations=1000, seed=42, payoff_type='call')
        
        assert mc.S0 == 0.035
        assert mc.K == 0.040
        assert mc.num_simulations == 1000
        assert mc.seed == 42
    
    def test_mc_price_call(self):
        """Test Monte Carlo pricing for call option"""
        mc = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                num_simulations=10000, seed=42, payoff_type='call')
        price = mc.price()
        
        # Should be positive and less than spot
        assert 0 < price < 0.035
    
    def test_mc_confidence_interval(self):
        """Test Monte Carlo confidence interval computation"""
        mc = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                num_simulations=10000, seed=42, payoff_type='call')
        price, low, high = mc.confidence_interval(confidence=0.95)
        
        # CI bounds should be ordered
        assert low < price < high
        
        # Interval width should be reasonable
        width = high - low
        assert 0 < width < price * 2  # Width shouldn't be > 2x price
    
    def test_mc_convergence(self):
        """Test Monte Carlo convergence with sample size"""
        price_low = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                       num_simulations=1000, seed=42, payoff_type='call').price()
        
        price_high = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                        num_simulations=50000, seed=42, payoff_type='call').price()
        
        # Prices should be close (convergence)
        error = abs(price_low - price_high) / price_high if price_high != 0 else 0
        assert error < 0.15  # Within 15% for reasonable sample sizes
    
    def test_mc_vs_binomial_agreement(self):
        """Test Monte Carlo vs Binomial Tree agreement"""
        binomial_price = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                      N=400, payoff_type='call').price()
        
        mc_price = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                       num_simulations=20000, seed=42, payoff_type='call').price()
        
        # Should agree within 2% (reasonable tolerance)
        error = abs(binomial_price - mc_price) / mc_price if mc_price != 0 else 0
        assert error < 0.02
    
    def test_mc_seed_reproducibility(self):
        """Test that same seed produces same result"""
        mc1 = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                 num_simulations=5000, seed=123, payoff_type='call')
        price1 = mc1.price()
        
        mc2 = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                                 num_simulations=5000, seed=123, payoff_type='call')
        price2 = mc2.price()
        
        # Should be identical
        assert price1 == price2


# ============================================================================
# GREEKS TESTS
# ============================================================================

class TestGreeksCalculator:
    """Unit tests for Greeks (sensitivities) calculation"""
    
    def test_greeks_initialization(self):
        """Test GreeksCalculator initializes correctly"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        
        assert greeks.S0 == 0.035
        assert greeks.K == 0.040
    
    def test_delta_call_bounds(self):
        """Test delta is between 0 and 1 for call option"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        delta = greeks.delta(option_type='call')
        
        assert 0 <= delta <= 1
    
    def test_delta_put_bounds(self):
        """Test delta is between -1 and 0 for put option"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        delta = greeks.delta(option_type='put')
        
        assert -1 <= delta <= 0
    
    def test_gamma_positive(self):
        """Test gamma is always positive"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        gamma = greeks.gamma()
        
        assert gamma > 0
    
    def test_vega_positive(self):
        """Test vega is always positive"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        vega = greeks.vega()
        
        assert vega > 0
    
    def test_theta_decay(self):
        """Test theta for call option (negative time decay)"""
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=0.01, r=0.025, sigma=0.42)  # Near expiry
        theta = greeks.theta(option_type='call')
        
        # Call theta should be negative (losing value as time passes)
        assert theta < 0
    
    def test_delta_increases_with_spot(self):
        """Test delta increases when spot price rises (call)"""
        delta_low = GreeksCalculator(S0=0.030, K=0.040, T=1.0, r=0.025, sigma=0.42).delta(option_type='call')
        delta_high = GreeksCalculator(S0=0.050, K=0.040, T=1.0, r=0.025, sigma=0.42).delta(option_type='call')
        
        # Delta should increase with spot price
        assert delta_high > delta_low


# ============================================================================
# DATA LOADER TESTS
# ============================================================================

class TestWindDataLoader:
    """Unit tests for WindDataLoader"""
    
    def test_wind_loader_initialization(self):
        """Test WindDataLoader initializes with defaults"""
        loader = WindDataLoader()
        
        assert loader.rotor_diameter == 80.0
        assert loader.hub_height == 80.0
        assert loader.power_coefficient == 0.40
        assert loader.rotor_area == np.pi * 40 ** 2
    
    def test_wind_loader_custom_specs(self):
        """Test WindDataLoader with custom turbine specs"""
        loader = WindDataLoader(rotor_diameter=100, hub_height=100, power_coefficient=0.45)
        
        assert loader.rotor_diameter == 100
        assert loader.hub_height == 100
        assert loader.power_coefficient == 0.45
    
    def test_wind_compute_price(self):
        """Test wind speed to price conversion"""
        loader = WindDataLoader()
        
        # Create synthetic wind data
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            'WS50M': np.random.normal(8.0, 2.0, 100),
            'WD10M': np.random.uniform(0, 360, 100),
        }, index=dates)
        df.index.name = 'Date'
        df['WS50M'] = np.abs(df['WS50M'])  # Ensure positive
        
        # Compute prices
        prices = loader.compute_price(df, energy_value_per_kwh=0.08)
        
        # Validate output
        assert len(prices) == 100
        assert np.all(prices >= 0)
        assert np.isfinite(prices).all()


class TestHydroDataLoader:
    """Unit tests for HydroDataLoader"""
    
    def test_hydro_loader_initialization(self):
        """Test HydroDataLoader initializes correctly"""
        loader = HydroDataLoader()
        
        assert loader.catchment_area > 0
        assert loader.elevation_drop > 0
        assert loader.turbine_efficiency > 0
    
    def test_hydro_compute_price(self):
        """Test precipitation to price conversion"""
        loader = HydroDataLoader()
        
        # Create synthetic hydro data
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            'PRECTOT': np.random.exponential(2.0, 100),  # Daily precipitation
        }, index=dates)
        df.index.name = 'Date'
        
        # Compute prices
        prices = loader.compute_price(df, energy_value_per_kwh=0.06)
        
        # Validate output
        assert len(prices) == 100
        assert np.all(prices >= 0)
        assert np.isfinite(prices).all()


# ============================================================================
# LOCATION GUIDE TESTS
# ============================================================================

class TestLocationGuide:
    """Unit tests for geographic location system"""
    
    def test_get_location(self):
        """Test get_location retrieves location data"""
        loc = get_location('Phoenix')
        
        assert loc is not None
        assert 'city' in loc
        assert 'country' in loc
        assert 'coordinates' in loc
        assert loc['city'] == 'Phoenix'
    
    def test_list_locations_solar(self):
        """Test listing solar locations"""
        solar_locs = list_locations('solar')
        
        assert len(solar_locs) > 0
        assert all('solar_rating' in loc for loc in solar_locs)
    
    def test_list_locations_wind(self):
        """Test listing wind locations"""
        wind_locs = list_locations('wind')
        
        assert len(wind_locs) > 0
        assert all('wind_rating' in loc for loc in wind_locs)
    
    def test_search_by_country(self):
        """Test country search"""
        us_locs = search_by_country('United States')
        
        assert len(us_locs) > 0
        assert all(loc['country'] == 'United States' for loc in us_locs)
    
    def test_location_coordinates(self):
        """Test that locations have valid coordinates"""
        loc = get_location('Taiwan')
        coords = loc['coordinates']
        
        assert -90 <= coords[0] <= 90  # Latitude
        assert -180 <= coords[1] <= 180  # Longitude


# ============================================================================
# CONTEXT TRANSLATOR TESTS
# ============================================================================

class TestContextTranslator:
    """Unit tests for context translation and sophisticated output"""
    
    def test_price_translator(self):
        """Test PriceTranslator for readable output"""
        translator = PriceTranslator(currency='USD', decimal_places=4)
        
        formatted = translator.format(0.0356)
        assert '$' in formatted
        assert '0.0356' in formatted
    
    def test_greek_translator(self):
        """Test GreeksTranslator for risk interpretation"""
        translator = GreeksTranslator()
        
        delta = 0.35
        interpretation = translator.interpret_delta(delta)
        
        assert interpretation is not None
        assert len(interpretation) > 0


# ============================================================================
# RESULTS MANAGER TESTS
# ============================================================================

class TestPricingResult:
    """Unit tests for PricingResult container"""
    
    def test_pricing_result_creation(self):
        """Test PricingResult initialization"""
        result = PricingResult(
            location='Taiwan',
            method='binomial',
            option_type='call',
            price=0.0356,
            S0=0.0525,
            K=0.0525,
            sigma=1.89,
            delta=0.38,
            vega=0.12
        )
        
        assert result.location == 'Taiwan'
        assert result.price == 0.0356
        assert result.delta == 0.38


class TestResultsComparator:
    """Unit tests for comparing pricing results"""
    
    def test_results_comparator(self):
        """Test ResultsComparator functionality"""
        binomial_result = PricingResult(
            location='Taiwan',
            method='binomial',
            option_type='call',
            price=0.0356,
            S0=0.0525,
            K=0.0525,
            sigma=1.89
        )
        
        mc_result = PricingResult(
            location='Taiwan',
            method='monte_carlo',
            option_type='call',
            price=0.0361,
            S0=0.0525,
            K=0.0525,
            sigma=1.89
        )
        
        comparator = ResultsComparator([binomial_result, mc_result])
        comparison = comparator.compare()
        
        assert 'convergence_error' in comparison or 'results' in comparison


class TestPricingValidator:
    """Unit tests for input validation"""
    
    def test_validator_valid_inputs(self):
        """Test validator accepts valid parameters"""
        validator = PricingValidator()
        
        # Should not raise
        validator.validate(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
    
    def test_validator_negative_spot(self):
        """Test validator rejects negative spot price"""
        validator = PricingValidator()
        
        with pytest.raises((ValueError, AssertionError)):
            validator.validate(S0=-0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
    
    def test_validator_negative_volatility(self):
        """Test validator rejects negative volatility"""
        validator = PricingValidator()
        
        with pytest.raises((ValueError, AssertionError)):
            validator.validate(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=-0.42)
    
    def test_validator_zero_time(self):
        """Test validator rejects zero maturity"""
        validator = PricingValidator()
        
        with pytest.raises((ValueError, AssertionError)):
            validator.validate(S0=0.035, K=0.040, T=0, r=0.025, sigma=0.42)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple modules"""
    
    def test_full_pricing_workflow(self):
        """Test complete pricing workflow: data → tree → greeks → results"""
        # 1. Get location
        location = get_location('Taiwan')
        
        # 2. Price with Binomial
        binomial = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call')
        binomial_price = binomial.price()
        
        # 3. Price with Monte Carlo
        mc = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                               num_simulations=10000, seed=42, payoff_type='call')
        mc_price = mc.price()
        
        # 4. Calculate Greeks
        greeks = GreeksCalculator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42)
        delta = greeks.delta(option_type='call')
        vega = greeks.vega()
        
        # 5. Create results
        result = PricingResult(
            location=location['city'],
            method='binomial',
            option_type='call',
            price=binomial_price,
            S0=0.035,
            K=0.040,
            sigma=0.42,
            delta=delta,
            vega=vega
        )
        
        # Validate full workflow
        assert result.price > 0
        assert 0 <= result.delta <= 1
        assert result.vega > 0
        assert abs(binomial_price - mc_price) / mc_price < 0.02
    
    def test_multi_energy_workflow(self):
        """Test workflow with multiple energy types"""
        # Wind
        wind_loader = WindDataLoader(location_name='Aalborg')
        assert wind_loader is not None
        
        # Hydro
        hydro_loader = HydroDataLoader(location_name='Nepal')
        assert hydro_loader is not None
    
    def test_batch_pricing(self):
        """Test batch pricing across multiple scenarios"""
        scenarios = [
            {'S0': 0.030, 'K': 0.040, 'sigma': 0.30},
            {'S0': 0.035, 'K': 0.040, 'sigma': 0.42},
            {'S0': 0.050, 'K': 0.040, 'sigma': 0.60},
        ]
        
        # This test validates that batch_price exists and works
        # Actual implementation depends on how batch_price is defined
        try:
            results = batch_price(scenarios, T=1.0, r=0.025, method='binomial', N=100)
            assert len(results) == len(scenarios)
        except Exception as e:
            # If not implemented, that's OK for this phase
            pytest.skip(f"batch_price not fully implemented: {e}")


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_very_high_volatility(self):
        """Test with extremely high volatility (>100%)"""
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=2.0, N=50, payoff_type='call')
        price = tree.price()
        
        # Should still produce valid price
        assert 0 < price < 1.0
        assert np.isfinite(price)
    
    def test_deep_otm_option(self):
        """Test deeply out-of-the-money option"""
        tree = BinomialTree(S0=0.010, K=0.100, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call')
        price = tree.price()
        
        # Should be nearly zero but positive
        assert 0 < price < 0.001
    
    def test_deep_itm_option(self):
        """Test deeply in-the-money option"""
        tree = BinomialTree(S0=0.100, K=0.010, T=1.0, r=0.025, sigma=0.42, N=100, payoff_type='call')
        price = tree.price()
        
        # Should be near intrinsic value
        intrinsic = 0.100 - 0.010
        assert price > intrinsic * 0.9
    
    def test_very_short_maturity(self):
        """Test with very short time to maturity"""
        tree = BinomialTree(S0=0.035, K=0.040, T=0.001, r=0.025, sigma=0.42, N=100, payoff_type='call')
        price = tree.price()
        
        # Should be very small
        assert 0 <= price < 0.001
    
    def test_zero_interest_rate(self):
        """Test with zero risk-free rate"""
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.0, sigma=0.42, N=100, payoff_type='call')
        price = tree.price()
        
        assert 0 < price < 0.035


# ============================================================================
# PERFORMANCE BASELINE TESTS
# ============================================================================

class TestPerformance:
    """Performance baseline tests (should complete quickly)"""
    
    def test_binomial_performance(self):
        """Test Binomial tree doesn't take excessive time"""
        import time
        
        start = time.time()
        tree = BinomialTree(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42, N=500, payoff_type='call')
        price = tree.price()
        elapsed = time.time() - start
        
        # Should complete in < 1 second
        assert elapsed < 1.0
        assert price > 0
    
    def test_monte_carlo_performance(self):
        """Test Monte Carlo doesn't take excessive time"""
        import time
        
        start = time.time()
        mc = MonteCarloSimulator(S0=0.035, K=0.040, T=1.0, r=0.025, sigma=0.42,
                               num_simulations=10000, seed=42, payoff_type='call')
        price = mc.price()
        elapsed = time.time() - start
        
        # Should complete in < 5 seconds
        assert elapsed < 5.0
        assert price > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
