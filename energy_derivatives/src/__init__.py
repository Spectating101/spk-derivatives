"""
Energy Derivatives Pricing Framework
=====================================

A quantitative framework for pricing energy-backed digital assets using
binomial trees, Monte-Carlo simulation, and risk-neutral valuation.

Modules:
--------
- binomial: Binomial Option Pricing Model (BOPM)
- monte_carlo: Monte-Carlo simulation for derivative pricing
- sensitivities: Greeks calculation (Delta, Vega, Theta, Rho)
- plots: Visualization and results plotting
- data_loader: Data loading and preprocessing for CEIR integration
- data_loader_nasa: NASA POWER API integration for solar data
- live_data: Live data fetching utilities

Author: Energy Finance Research Group
Year: 2025
"""

__version__ = "0.2.0"
__author__ = "Solarpunk Bitcoin Team"

# Import modules
from . import binomial
from . import monte_carlo
from . import sensitivities
from . import plots
from . import data_loader
from . import data_loader_nasa
from . import live_data
from . import context_translator

# Import commonly used functions for convenience
from .data_loader_nasa import load_solar_parameters, fetch_nasa_data
from .data_loader import load_parameters
from .binomial import BinomialTree
from .monte_carlo import monte_carlo_option_price
from .sensitivities import calculate_greeks

# Import context translator (sophistication layer)
from .context_translator import (
    SolarSystemContext,
    PriceTranslator,
    VolatilityTranslator,
    GreeksTranslator,
    create_contextual_summary
)

__all__ = [
    # Modules
    'binomial',
    'monte_carlo',
    'sensitivities',
    'plots',
    'data_loader',
    'data_loader_nasa',
    'live_data',
    'context_translator',

    # Convenience functions
    'load_solar_parameters',
    'fetch_nasa_data',
    'load_parameters',
    'BinomialTree',
    'monte_carlo_option_price',
    'calculate_greeks',

    # Context translation (sophistication layer)
    'SolarSystemContext',
    'PriceTranslator',
    'VolatilityTranslator',
    'GreeksTranslator',
    'create_contextual_summary',
]
