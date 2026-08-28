"""
SPK Derivatives: Energy Derivatives Pricing Framework
======================================================

A quantitative framework for pricing energy derivatives (solar, wind, hydro)
using binomial trees, Monte-Carlo simulation, risk-neutral valuation,
policy-admitted exposure quantities, and deterministic research artifacts.
"""

__version__ = "0.5.0"
__author__ = "SPK Derivatives Team"

# Core modules
from . import binomial
from . import monte_carlo
from . import sensitivities
from . import data_loader
from . import data_loader_nasa
from . import data_loader_base
from . import data_loader_wind
from . import data_loader_hydro
from . import location_guide
from . import live_data
from . import context_translator
from . import results_manager
from . import policy_lab
from . import artifacts

# Optional: plots (requires matplotlib)
try:
    from . import plots
except ImportError:
    plots = None

# Optional: analysis (openpyxl is only needed for Excel export)
try:
    from . import analysis
    from .analysis import (
        sensitivity_table,
        stress_test_volatility,
        stress_test_rates,
        combined_stress_test,
        export_to_excel,
        run_full_analysis,
        scenario_comparison,
        portfolio_greeks,
        pnl_calculator,
    )
except ImportError:
    analysis = None

# Common pricing/data functions
from .data_loader_nasa import load_solar_parameters, fetch_nasa_data
from .data_loader import load_parameters
from .binomial import BinomialTree
from .monte_carlo import MonteCarloSimulator, price_energy_derivative_mc
from .sensitivities import (
    GreeksCalculator,
    compute_energy_derivatives_greeks as calculate_greeks,
)

# Multi-energy data loaders
from .data_loader_base import EnergyDataLoader
from .data_loader_wind import WindDataLoader
from .data_loader_hydro import HydroDataLoader

# Geographic location guide
from .location_guide import (
    get_location,
    list_locations,
    search_by_country,
    get_best_location_for_energy,
    format_location_table,
)

# Context translation
from .context_translator import (
    SolarSystemContext,
    PriceTranslator,
    VolatilityTranslator,
    GreeksTranslator,
    create_contextual_summary,
)

# Results management
from .results_manager import (
    PricingResult,
    ResultsComparator,
    PricingValidator,
    batch_price,
    comparative_context,
    break_even_analysis,
)

# Policy Lab interoperability
from .policy_lab import (
    ADMITTED_READINGS,
    POLICY_LAB_PROFILE,
    POLICY_LAB_SCHEMA,
    PolicyLabExposure,
    PolicyLabPackageError,
    PolicyPricedExposure,
    extract_admitted_exposure,
    load_claim_assessment,
    price_admitted_exposure,
)

# Deterministic pricing artifacts
from .artifacts import (
    DEFAULT_NON_CLAIMS,
    SPK_CANONICALIZATION,
    SPK_PRICING_PACKAGE_SCHEMA,
    PricingArtifactError,
    build_policy_pricing_package,
    compute_artifact_id,
    compute_package_content_id,
    load_pricing_result_package,
    pricing_identity_body,
    sha256_hex,
    stable_json_dumps,
    validate_pricing_result_package,
    write_pricing_result_package,
)

__all__ = [
    # Modules
    "binomial",
    "monte_carlo",
    "sensitivities",
    "plots",
    "data_loader",
    "data_loader_nasa",
    "data_loader_base",
    "data_loader_wind",
    "data_loader_hydro",
    "location_guide",
    "live_data",
    "context_translator",
    "results_manager",
    "analysis",
    "policy_lab",
    "artifacts",

    # Convenience functions
    "load_solar_parameters",
    "fetch_nasa_data",
    "load_parameters",
    "BinomialTree",
    "MonteCarloSimulator",
    "price_energy_derivative_mc",
    "GreeksCalculator",
    "calculate_greeks",

    # Multi-energy data loaders
    "EnergyDataLoader",
    "WindDataLoader",
    "HydroDataLoader",

    # Geographic location guide
    "get_location",
    "list_locations",
    "search_by_country",
    "get_best_location_for_energy",
    "format_location_table",

    # Context translation
    "SolarSystemContext",
    "PriceTranslator",
    "VolatilityTranslator",
    "GreeksTranslator",
    "create_contextual_summary",

    # Results management
    "PricingResult",
    "ResultsComparator",
    "PricingValidator",
    "batch_price",
    "comparative_context",
    "break_even_analysis",

    # Analysis utilities
    "sensitivity_table",
    "stress_test_volatility",
    "stress_test_rates",
    "combined_stress_test",
    "export_to_excel",
    "run_full_analysis",
    "scenario_comparison",
    "portfolio_greeks",
    "pnl_calculator",

    # Policy Lab bridge
    "POLICY_LAB_SCHEMA",
    "POLICY_LAB_PROFILE",
    "ADMITTED_READINGS",
    "PolicyLabExposure",
    "PolicyPricedExposure",
    "PolicyLabPackageError",
    "load_claim_assessment",
    "extract_admitted_exposure",
    "price_admitted_exposure",

    # Pricing artifact protocol
    "SPK_PRICING_PACKAGE_SCHEMA",
    "SPK_CANONICALIZATION",
    "DEFAULT_NON_CLAIMS",
    "PricingArtifactError",
    "stable_json_dumps",
    "sha256_hex",
    "pricing_identity_body",
    "compute_artifact_id",
    "compute_package_content_id",
    "build_policy_pricing_package",
    "load_pricing_result_package",
    "validate_pricing_result_package",
    "write_pricing_result_package",
]
