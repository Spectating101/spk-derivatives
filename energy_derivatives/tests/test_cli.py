import json

from spk_derivatives.cli import main


def _write_policy_package(policy_package, tmp_path):
    path = tmp_path / "claim-assessment.json"
    path.write_text(json.dumps(policy_package), encoding="utf-8")
    return path


def test_preflight_reports_runtime_contracts(capsys):
    assert main(["preflight", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "ok"
    assert payload["version"] == "0.5.0"
    assert payload["policy_lab_profile"] == "policylab.energy_linked_claim.v0"
    assert payload["pricing_result_schema"] == "spk_derivatives.pricing_result_package.v0.1"


def test_cli_emits_and_verifies_pricing_package(policy_package, tmp_path, capsys):
    source = _write_policy_package(policy_package, tmp_path)
    target = tmp_path / "pricing-result.json"

    assert main([
        "policy-price",
        str(source),
        "--spot", "100",
        "--strike", "100",
        "--maturity", "1",
        "--rate", "0.05",
        "--volatility", "0.2",
        "--steps", "200",
        "--assumption", "Risk-neutral valuation",
        "--package-out", str(target),
        "--json",
    ]) == 0
    priced = json.loads(capsys.readouterr().out)

    assert target.exists()
    assert len(priced["artifact_id"]) == 64
    assert priced["result_package"] == str(target)

    assert main(["verify-result", str(target), "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["status"] == "ok"
    assert verified["artifact_id"] == priced["artifact_id"]


def test_preflight_can_validate_both_boundary_artifacts(policy_package, tmp_path, capsys):
    source = _write_policy_package(policy_package, tmp_path)
    target = tmp_path / "pricing-result.json"

    assert main([
        "policy-price",
        str(source),
        "--spot", "100",
        "--strike", "100",
        "--maturity", "1",
        "--rate", "0.05",
        "--volatility", "0.2",
        "--package-out", str(target),
        "--json",
    ]) == 0
    capsys.readouterr()

    assert main([
        "preflight",
        "--policy-package", str(source),
        "--result-package", str(target),
        "--json",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["policy_package"]["status"] == "admitted"
    assert payload["result_package"]["status"] == "verified"
