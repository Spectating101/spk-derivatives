import json
from pathlib import Path

import spk_derivatives
from spk_derivatives.artifacts import SPK_CANONICALIZATION, SPK_PRICING_PACKAGE_SCHEMA
from spk_derivatives.policy_analysis import SPK_POLICY_COMPARISON_SCHEMA
from spk_derivatives.policy_lab import POLICY_LAB_PROFILE, POLICY_LAB_SCHEMA


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
    assert surface["artifact_protocol"]["canonicalization"] == SPK_CANONICALIZATION


def test_current_surface_paths_exist():
    root = Path(__file__).resolve().parents[2]
    surface = json.loads((root / "CURRENT_SURFACE.json").read_text(encoding="utf-8"))

    assert (root / surface["artifact_protocol"]["schema_path"]).is_file()
    assert (root / surface["artifact_protocol"]["comparison_schema_path"]).is_file()
    assert (root / surface["validation"]["python_tests"]).is_dir()
    assert (root / surface["validation"]["solidity_tests"]).is_file()
    assert (root / surface["validation"]["solidity_security"]).is_file()
    assert (root / surface["validation"]["trust_boundary"]).is_file()
