"""
SPK Derivatives: Energy Derivatives Pricing Framework
======================================================

A quantitative framework for pricing energy derivatives (solar, wind, hydro)
using binomial trees, Monte-Carlo simulation, forward-market models,
policy-admitted exposure quantities, deterministic research artifacts, explicit
contract settlement, joint volume-price risk, market/model sensitivity, and
policy-sensitivity analysis.
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
from . import policy_analysis
from . import market_models
from . import market_calibration
from . import energy_contracts
from . import scenario_risk
from . import market_artifacts
from . import units
from . import joint_risk

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

# Forward-market and mean-reversion models
from .market_models import (
    ForwardOptionValue,
    MarketModelError,
    bachelier_option_price,
    black76_option_price,
    ou_terminal_moments,
    simulate_ou_terminal_prices,
)

# Forward curves and market calibration
from .market_calibration import (
    ForwardCurve,
    ForwardCurveNode,
    MarketCalibrationError,
    OUCalibration,
    VolatilityEstimate,
    build_forward_curve,
    calibrate_ou_from_series,
    estimate_lognormal_volatility,
    estimate_normal_volatility,
)

# Explicit unit conversions
from .units import (
    ConvertedQuantity,
    QuantityConversion,
    UnitConversionError,
    convert_quantity,
    si_energy_conversion,
)

# Explicit energy-contract settlement
from .energy_contracts import (
    ContractSettlement,
    EnergyContract,
    EnergyContractError,
    PolicyContractSettlement,
    settle_energy_contract,
    settle_policy_exposure,
    settled_unit_price,
)

# Scenario distributions and market-model sensitivity
from .scenario_risk import (
    MarketModelComparison,
    MarketModelOutcome,
    PolicySettlementDistribution,
    ScenarioRiskError,
    SettlementDistribution,
    compare_market_model_scenarios,
    summarize_contract_distribution,
    summarize_policy_contract_distribution,
)

# Joint physical-volume and market-price scenarios
from .joint_risk import (
    JointExposureDistribution,
    JointRiskError,
    PolicyJointExposureDistribution,
    summarize_joint_exposure,
    summarize_policy_joint_exposure,
)

# Deterministic market-risk artifacts
from .market_artifacts import (
    MARKET_RISK_NON_CLAIMS,
    SPK_MARKET_RISK_SCHEMA,
    MarketRiskArtifactError,
    build_market_risk_package,
    compute_market_risk_artifact_id,
    compute_market_risk_content_id,
    load_market_risk_package,
    market_risk_identity_body,
    validate_market_risk_package,
    write_market_risk_package,
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

# Policy sensitivity and governance-comparison artifacts
from .policy_analysis import (
    SPK_POLICY_COMPARISON_SCHEMA,
    PolicyComparisonError,
    PolicyOutcome,
    PolicyPricedOutcome,
    build_policy_comparison_package,
    compare_policy_outcomes,
    price_admitted_policies,
    validate_policy_comparison_package,
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
    "policy_analysis",
    "market_models",
    "market_calibration",
    "units",
    "energy_contracts",
    "scenario_risk",
    "joint_risk",
    "market_artifacts",

    # Convenience functions
    "load_solar_parameters",
    "fetch_nasa_data",
    "load_parameters",
    "BinomialTree",
    "MonteCarloSimulator",
    "price_energy_derivative_mc",
    "GreeksCalculator",
    "calculate_greeks",

    # Forward-market and mean-reversion models
    "MarketModelError",
    "ForwardOptionValue",
    "black76_option_price",
    "bachelier_option_price",
    "ou_terminal_moments",
    "simulate_ou_terminal_prices",

    # Forward curves and market calibration
    "MarketCalibrationError",
    "ForwardCurveNode",
    "ForwardCurve",
    "VolatilityEstimate",
    "OUCalibration",
    "build_forward_curve",
    "estimate_normal_volatility",
    "estimate_lognormal_volatility",
    "calibrate_ou_from_series",

    # Explicit unit conversions
    "UnitConversionError",
    "QuantityConversion",
    "ConvertedQuantity",
    "convert_quantity",
    "si_energy_conversion",

    # Explicit contract settlement
    "EnergyContractError",
    "EnergyContract",
    "ContractSettlement",
    "PolicyContractSettlement",
    "settled_unit_price",
    "settle_energy_contract",
    "settle_policy_exposure",

    # Scenario distributions / model sensitivity
    "ScenarioRiskError",
    "SettlementDistribution",
    "PolicySettlementDistribution",
    "MarketModelOutcome",
    "MarketModelComparison",
    "summarize_contract_distribution",
    "summarize_policy_contract_distribution",
    "compare_market_model_scenarios",

    # Joint physical-volume / market-price risk
    "JointRiskError",
    "JointExposureDistribution",
    "PolicyJointExposureDistribution",
    "summarize_joint_exposure",
    "summarize_policy_joint_exposure",

    # Market-risk artifacts
    "SPK_MARKET_RISK_SCHEMA",
    "MARKET_RISK_NON_CLAIMS",
    "MarketRiskArtifactError",
    "market_risk_identity_body",
    "compute_market_risk_artifact_id",
    "compute_market_risk_content_id",
    "build_market_risk_package",
    "load_market_risk_package",
    "validate_market_risk_package",
    "write_market_risk_package",

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

    # Policy sensitivity protocol
    "SPK_POLICY_COMPARISON_SCHEMA",
    "PolicyComparisonError",
    "PolicyOutcome",
    "PolicyPricedOutcome",
    "compare_policy_outcomes",
    "price_admitted_policies",
    "build_policy_comparison_package",
    "validate_policy_comparison_package",
]
