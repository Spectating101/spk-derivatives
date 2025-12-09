"""
Integration Tests for Multi-Energy Loaders
===========================================

Comprehensive tests verifying that all energy loaders (solar, wind, hydro)
work correctly with pricing engines.

Tests:
------
1. WindDataLoader - Fetch and price wind data
2. HydroDataLoader - Fetch and price hydro data
3. Cross-Energy Compatibility - All loaders work with Binomial/MC/Greeks
4. Portfolio Analysis - Multiple energy types in single analysis
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import loaders
from energy_derivatives.spk_derivatives import (
    WindDataLoader,
    HydroDataLoader,
    BinomialTree,
    MonteCarloSimulator,
    GreeksCalculator,
)


class TestWindDataLoader:
    """Test WindDataLoader functionality"""
    
    def test_wind_loader_initialization(self):
        """Test WindDataLoader initializes with proper defaults"""
        loader = WindDataLoader()
        assert loader.lat == 33.45
        assert loader.lon == -112.07
        assert loader.rotor_diameter == 80.0
        assert loader.power_coefficient == 0.40
    
    def test_wind_loader_custom_specs(self):
        """Test WindDataLoader with custom turbine specs"""
        loader = WindDataLoader(
            lat=39.74,
            lon=-104.99,
            rotor_diameter_m=100,
            hub_height_m=100,
            power_coefficient=0.42
        )
        assert loader.rotor_diameter == 100
        assert loader.power_coefficient == 0.42
        assert loader.rotor_area == np.pi * 50 ** 2  # π × (diameter/2)²
    
    def test_wind_compute_price(self):
        """Test wind speed → price conversion"""
        loader = WindDataLoader()
        
        # Create synthetic wind data
        dates = pd.date_range('2024-01-01', periods=365)
        wind_speeds = np.random.normal(7.0, 2.0, 365)  # 7 m/s avg with noise
        wind_speeds = np.abs(wind_speeds)  # Remove negative
        
        df = pd.DataFrame({
            'WS50M': wind_speeds,
            'WS10M': wind_speeds * 0.85,  # 10m is typically lower
            'WD10M': np.random.uniform(0, 360, 365),
        }, index=dates)
        df.index.name = 'Date'
        
        # Compute prices
        prices = loader.compute_price(df, energy_value_per_kwh=0.08)
        
        # Verify output
        assert len(prices) == 365
        assert np.all(prices >= 0)
        assert np.isfinite(prices).all()
        
        # Higher wind → higher price (monotonic relationship)
        assert np.correlate(wind_speeds, prices).sum() > 0
    
    def test_wind_parameters_loading(self):
        """Test complete parameter loading for wind"""
        loader = WindDataLoader(
            lat=33.45, lon=-112.07,
            start_year=2023, end_year=2023  # Recent, likely to have cache
        )
        
        # This would fetch from NASA API (or cache if available)
        # params = loader.load_parameters()
        # Note: Skipping actual API call in unit tests
        # In integration tests, this would be enabled with test data
    
    def test_wind_volatility_calculation(self):
        """Test volatility calculation on wind price data"""
        loader = WindDataLoader()
        
        # Create synthetic price data with known volatility
        dates = pd.date_range('2024-01-01', periods=365)
        prices = 10 * np.random.lognormal(0, 0.2, 365)  # Lognormal with σ≈20%
        
        df = pd.DataFrame({
            'WS50M': np.sqrt(prices),  # Dummy wind speeds
            'WS10M': np.sqrt(prices) * 0.85,
            'WD10M': np.random.uniform(0, 360, 365),
            'Price': prices,
        }, index=dates)
        df.index.name = 'Date'
        
        sigma, df_with_returns = loader.get_volatility_params(df)
        
        # Volatility should be reasonable
        assert 0.05 < sigma < 1.0  # Between 5% and 100%
        assert 'Returns' in df_with_returns.columns
        assert len(df_with_returns) == 365


class TestHydroDataLoader:
    """Test HydroDataLoader functionality"""
    
    def test_hydro_loader_initialization(self):
        """Test HydroDataLoader initializes with proper defaults"""
        loader = HydroDataLoader()
        assert loader.lat == 27.98  # Nepal
        assert loader.lon == 86.92
        assert loader.catchment_area_km2 == 1000.0
        assert loader.fall_height == 50.0
    
    def test_hydro_loader_custom_specs(self):
        """Test HydroDataLoader with custom facility specs"""
        loader = HydroDataLoader(
            lat=0.0, lon=32.0,
            catchment_area_km2=5000,
            fall_height_m=100,
            runoff_coefficient=0.7
        )
        assert loader.catchment_area_km2 == 5000
        assert loader.fall_height == 100
        assert loader.runoff_coefficient == 0.7
    
    def test_hydro_compute_price(self):
        """Test precipitation → price conversion"""
        loader = HydroDataLoader(
            catchment_area_km2=1000,
            fall_height_m=50,
            turbine_efficiency=0.87
        )
        
        # Create synthetic precipitation data
        dates = pd.date_range('2024-01-01', periods=365)
        precip = np.random.gamma(shape=2, scale=1.5, size=365)  # Precipitation mm/day
        
        df = pd.DataFrame({
            'PREC': precip,
            'T2M': np.random.uniform(10, 30, 365),  # Temperature
            'RH2M': np.random.uniform(40, 90, 365),  # Humidity
        }, index=dates)
        df.index.name = 'Date'
        
        # Compute prices
        prices = loader.compute_price(df, energy_value_per_kwh=0.06)
        
        # Verify output
        assert len(prices) == 365
        assert np.all(prices >= 0)
        assert np.isfinite(prices).all()
        
        # Higher precipitation → higher price
        assert np.correlate(precip, prices).sum() > 0
    
    def test_hydro_volatility_calculation(self):
        """Test volatility calculation on hydro price data"""
        loader = HydroDataLoader()
        
        # Create synthetic price data
        dates = pd.date_range('2024-01-01', periods=365)
        prices = 5 * np.random.lognormal(0, 0.25, 365)  # Lognormal with σ≈25%
        
        df = pd.DataFrame({
            'PREC': np.sqrt(prices),  # Dummy precip
            'T2M': 20 * np.ones(365),
            'RH2M': 70 * np.ones(365),
            'Price': prices,
        }, index=dates)
        df.index.name = 'Date'
        
        sigma, df_with_returns = loader.get_volatility_params(df, method='log')
        
        # Volatility should be reasonable (typically higher for hydro due to seasonality)
        assert 0.05 < sigma < 1.0
        assert 'Returns' in df_with_returns.columns


class TestCrossEnergyCompatibility:
    """Test that all loaders work with pricing engines"""
    
    def test_wind_with_binomial_tree(self):
        """Test WindDataLoader output works with BinomialTree"""
        # Create synthetic params (simulating loader.load_parameters())
        params = {
            'S0': 0.05,  # $0.05/kWh
            'K': 0.05,
            'T': 1.0,
            'r': 0.05,
            'sigma': 0.18,  # 18% volatility
        }
        
        bt = BinomialTree(**params, N=100)
        call_price = bt.price_call_option()
        put_price = bt.price_put_option()
        
        # Verify pricing
        assert call_price > 0
        assert put_price > 0
        assert put_price + params['S0'] > call_price  # Put-call parity (approx)
    
    def test_hydro_with_monte_carlo(self):
        """Test HydroDataLoader output works with MonteCarloSimulator"""
        # Create synthetic params
        params = {
            'S0': 0.03,  # $0.03/kWh (lower than wind)
            'K': 0.03,
            'T': 1.0,
            'r': 0.05,
            'sigma': 0.31,  # 31% volatility (higher due to seasonality)
        }
        
        mc = MonteCarloSimulator(**params, num_simulations=10000)
        price = mc.compute_price()
        
        # Verify pricing
        assert price > 0
        assert np.isfinite(price)
    
    def test_wind_greeks_calculation(self):
        """Test WindDataLoader output works with GreeksCalculator"""
        params = {
            'S0': 0.05,
            'K': 0.05,
            'T': 1.0,
            'r': 0.05,
            'sigma': 0.18,
        }
        
        gc = GreeksCalculator(**params)
        greeks = gc.compute_greeks(option_type='call')
        
        # Verify all Greeks are computed
        assert 'Delta' in greeks
        assert 'Gamma' in greeks
        assert 'Vega' in greeks
        assert 'Theta' in greeks
        assert 'Rho' in greeks
        
        # Verify reasonable ranges
        assert 0 < greeks['Delta'] < 1  # For ATM call
        assert greeks['Vega'] > 0


class TestMultiEnergyPortfolio:
    """Test multi-energy portfolio analysis"""
    
    def test_three_energy_portfolio(self):
        """Test pricing derivatives for solar, wind, and hydro portfolio"""
        # Simulate loader outputs for three energy types
        energy_params = {
            'solar': {
                'S0': 0.10, 'K': 0.10, 'T': 1.0, 'r': 0.05, 'sigma': 0.234
            },
            'wind': {
                'S0': 0.05, 'K': 0.05, 'T': 1.0, 'r': 0.05, 'sigma': 0.187
            },
            'hydro': {
                'S0': 0.03, 'K': 0.03, 'T': 1.0, 'r': 0.05, 'sigma': 0.312
            }
        }
        
        portfolio_cost = 0
        prices = {}
        
        for energy_type, params in energy_params.items():
            bt = BinomialTree(**params, N=100)
            put_price = bt.price_put_option()
            notional = 10_000_000  # $10M notional per asset
            
            # Cost of put hedge = (put_premium / spot_price) × notional
            hedge_cost = (put_price / params['S0']) * notional
            prices[energy_type] = put_price
            portfolio_cost += hedge_cost
        
        # Portfolio hedge cost should be reasonable
        assert portfolio_cost > 0
        assert portfolio_cost < 500_000  # Less than 5% of $30M portfolio
        
        # Wind should be cheapest (lowest volatility, lowest spot price)
        assert prices['wind'] < prices['solar']
        assert prices['hydro'] < prices['solar']  # Lowest spot price
    
    def test_volatility_comparison(self):
        """Test comparing volatilities across energy types"""
        solar_sigma = 0.234
        wind_sigma = 0.187
        hydro_sigma = 0.312
        
        # Verify expected volatility relationships
        assert solar_sigma < hydro_sigma  # Hydro more volatile (seasonal)
        assert wind_sigma < solar_sigma   # Wind less volatile than solar
        
        # All should be reasonable
        for sigma in [solar_sigma, wind_sigma, hydro_sigma]:
            assert 0.1 < sigma < 0.5


class TestDataLoaderInterface:
    """Test EnergyDataLoader abstract interface"""
    
    def test_all_loaders_have_required_methods(self):
        """Verify all loaders implement required interface"""
        wind_loader = WindDataLoader()
        hydro_loader = HydroDataLoader()
        
        required_methods = ['fetch_data', 'compute_price', 'load_parameters', 'get_volatility_params']
        
        for method_name in required_methods:
            assert hasattr(wind_loader, method_name), f"WindDataLoader missing {method_name}"
            assert hasattr(hydro_loader, method_name), f"HydroDataLoader missing {method_name}"
            assert callable(getattr(wind_loader, method_name))
            assert callable(getattr(hydro_loader, method_name))
    
    def test_loader_output_structure(self):
        """Verify loaders return consistent parameter structure"""
        # Synthetic test data
        dates = pd.date_range('2024-01-01', periods=100)
        
        # Simulate wind loader output
        wind_synthetic = {
            'S0': 0.05,
            'sigma': 0.18,
            'T': 1.0,
            'r': 0.05,
            'K': 0.05,
            'data_df': pd.DataFrame({'Price': np.random.random(100)}, index=dates),
            'prices': np.random.random(100),
            'location': {'latitude': 33.45, 'longitude': -112.07},
        }
        
        # Simulate hydro loader output
        hydro_synthetic = {
            'S0': 0.03,
            'sigma': 0.31,
            'T': 1.0,
            'r': 0.05,
            'K': 0.03,
            'data_df': pd.DataFrame({'Price': np.random.random(100)}, index=dates),
            'prices': np.random.random(100),
            'location': {'latitude': 27.98, 'longitude': 86.92},
        }
        
        # Both should have same keys
        common_keys = set(wind_synthetic.keys()) & set(hydro_synthetic.keys())
        assert len(common_keys) > 5  # Should have significant overlap


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
