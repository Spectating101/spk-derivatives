import json
from pathlib import Path

import spk_derivatives
from spk_derivatives.artifacts import SPK_CANONICALIZATION, SPK_PRICING_PACKAGE_SCHEMA
from spk_derivatives.market_artifacts import SPK_MARKET_RISK_SCHEMA
from spk_derivatives.policy_analysis import SPK_POLICY_COMPARISON_SCHEMA
from spk_derivatives.policy_lab import POLICY_LAB_PROFILE, POLICY_LAB_SCHEMA
from spk_derivatives.scenario_set import SCENARIO_SET_SCHEMA


def test_current_surface_matches_runtime_contracts():
    root = Path(__file__).resolve().parents[2]
    surface = json.loads((root / "CURRENT_SURFACE.json").read_text(encoding="utf-8"))

    assert surface["schema"] == "spk_derivatives.current_surface.v0.1"
    assert surface["package"]["name"] == "spk-derivatives"
    assert surface["package"]["version"] == spk_derivatives.__version__
    assert surface["authority_boundary"]["claim_assessment_schema"] == POLICY_LAB_SCHEMA
    assert surface["authority_boundary"]["profile_id"] == POLICY_LAB_PROFILE
    assert surface["artifact_protocol"]["pricing_result_schema"] == SPK_PRICING_PACKAGE_SCHEMA
    assert surface["artifact_protocol"]["policy_comparison_schema"] == SPK_POLICY_COMPARISON_SCHEMA
    assert surface["artifact_protocol"]["market_risk_schema"] == SPK_MARKET_RISK_SCHEMA
    assert surface["artifact_protocol"]["scenario_set_schema"] == SCENARIO_SET_SCHEMA
    assert surface["artifact_protocol"]["canonicalization"] == SPK_CANONICALIZATION
    assert "scenario_set_id" in surface["artifact_protocol"]["scenario_binding"]
    assert "black-76-forward-option" in surface["market_model_boundary"]["market_models"]
    assert "bachelier-normal-forward-option" in surface["market_model_boundary"]["market_models"]
    assert (
        "mean-reverting-compound-poisson-spike-scenarios"
        in surface["market_model_boundary"]["market_models"]
    )
    assert (
        "provenance-bearing-forward-curves"
        in surface["market_model_boundary"]["market_inputs"]
    )
    assert "identity-bound-scenario-sets" in surface["market_model_boundary"]["market_inputs"]
    assert (
        "source-hashed-aemo-nem-dispatch-prices"
        in surface["market_model_boundary"]["market_inputs"]
    )
    assert "fixed-price" in surface["market_model_boundary"]["contract_settlement"]
    assert "explicit conversion objects" in surface["market_model_boundary"]["unit_conversion"]
    assert "curve source" in surface["market_model_boundary"]["forward_pricing_provenance"]
    assert "comparison" in surface["model_sensitivity"]
    assert "authority_cap" in surface["joint_volume_price_risk"]
    assert "scenario_sets" in surface["reproducibility"]
    assert "analytic_monte_carlo" in surface["reproducibility"]
    assert "aemo_nem" in surface["empirical_market_adapters"]
    assert surface["empirical_market_adapters"]["aemo_nem"]["price_unit"] == "AUD/MWh"
    assert "scope_document" in surface["supported_surface"]
    assert "spk-derivatives scenario-build" in surface["canonical_commands"]
    assert "spk-derivatives verify-scenario-set" in surface["canonical_commands"]
    assert "spk-derivatives market-risk" in surface["canonical_commands"]
    assert "spk-derivatives verify-market-risk" in surface["canonical_commands"]


def test_current_surface_paths_exist():
    root = Path(__file__).resolve().parents[2]
    surface = json.loads((root / "CURRENT_SURFACE.json").read_text(encoding="utf-8"))

    assert (root / surface["artifact_protocol"]["schema_path"]).is_file()
    assert (root / surface["artifact_protocol"]["comparison_schema_path"]).is_file()
    assert (root / surface["artifact_protocol"]["market_risk_schema_path"]).is_file()
    assert (root / surface["artifact_protocol"]["scenario_set_schema_path"]).is_file()
    assert (root / surface["supported_surface"]["scope_document"]).is_file()
    assert (
        root / surface["empirical_market_adapters"]["aemo_nem"]["case_document"]
    ).is_file()
    assert (root / surface["validation"]["python_tests"]).is_dir()
    assert (root / surface["validation"]["solidity_tests"]).is_file()
    assert (root / surface["validation"]["solidity_security"]).is_file()
    assert (root / surface["validation"]["trust_boundary"]).is_file()
    assert (root / surface["validation"]["market_model_architecture"]).is_file()
    assert (root / surface["validation"]["market_calibration_and_risk"]).is_file()
    assert (
        root / surface["validation"]["scenario_identity_and_model_validation"]
    ).is_file()
    assert (root / surface["validation"]["supported_quantitative_surface"]).is_file()
    assert (root / surface["validation"]["aemo_nem_empirical_case"]).is_file()
