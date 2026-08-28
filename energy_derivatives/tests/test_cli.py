import copy
import json

from spk_derivatives.cli import main


def _write_policy_package(policy_package, tmp_path):
    path = tmp_path / "claim-assessment.json"
    path.write_text(json.dumps(policy_package), encoding="utf-8")
    return path


def _with_second_policy(policy_package):
    package = copy.deepcopy(policy_package)
    second = copy.deepcopy(package["evaluations"][0])
    second["policy"] = {"id": "policy-b", "version": "2", "name": "Pilot policy"}
    second["decision_id"] = "f" * 64
    second["supported_quantity"]["value"] = 700.0
    second["binding_calculators"] = ["POLICY_HAIRCUT"]
    second["blocking_calculators"] = []
    second["rule_evaluations"] = [
        {
            "calculator_id": "POLICY_HAIRCUT",
            "status": "LIMIT",
            "explanation": "Policy haircut applies.",
            "boundary": "30% haircut.",
            "warnings": [],
        }
    ]
    package["evaluations"].append(second)
    return package


def test_preflight_reports_runtime_contracts(capsys):
    assert main(["preflight", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "ok"
    assert payload["version"] == "0.5.0"
    assert payload["policy_lab_profile"] == "policylab.energy_linked_claim.v0"
    assert payload["pricing_result_schema"] == "spk_derivatives.pricing_result_package.v0.1"
    assert payload["policy_comparison_schema"] == "spk_derivatives.policy_comparison_package.v0.1"
    assert payload["market_risk_schema"] == "spk_derivatives.market_risk_package.v0.1"


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


def test_cli_policy_compare_does_not_choose_between_policies(policy_package, tmp_path, capsys):
    source = _write_policy_package(_with_second_policy(policy_package), tmp_path)

    assert main(["policy-compare", str(source), "--json"]) == 0
    outcomes = json.loads(capsys.readouterr().out)

    assert [item["policy_id"] for item in outcomes] == ["policy-a", "policy-b"]
    assert [item["supported_quantity"] for item in outcomes] == [1000.0, 700.0]


def test_cli_policy_sweep_emits_and_verifies_comparison_package(policy_package, tmp_path, capsys):
    source = _write_policy_package(_with_second_policy(policy_package), tmp_path)
    target = tmp_path / "policy-comparison.json"

    assert main([
        "policy-sweep",
        str(source),
        "--spot", "100",
        "--strike", "100",
        "--maturity", "1",
        "--rate", "0.05",
        "--volatility", "0.2",
        "--package-out", str(target),
        "--json",
    ]) == 0
    package = json.loads(capsys.readouterr().out)

    assert target.exists()
    assert len(package["comparison_id"]) == 64
    assert package["comparison"]["admitted_policy_count"] == 2

    assert main(["verify-comparison", str(target), "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["status"] == "ok"
    assert verified["comparison_id"] == package["comparison_id"]


def test_preflight_can_validate_comparison_package(policy_package, tmp_path, capsys):
    source = _write_policy_package(_with_second_policy(policy_package), tmp_path)
    target = tmp_path / "policy-comparison.json"

    assert main([
        "policy-sweep", str(source),
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
        "--comparison-package", str(target),
        "--json",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["comparison_package"]["status"] == "verified"


def test_cli_market_risk_emits_and_verifies_artifact(policy_package, tmp_path, capsys):
    source = _write_policy_package(policy_package, tmp_path)
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps([0.05, 0.08, 0.12, 0.15]), encoding="utf-8")
    target = tmp_path / "market-risk.json"

    assert main([
        "market-risk",
        str(source),
        "--prices", str(prices),
        "--contract-type", "floor",
        "--currency", "USD",
        "--floor-price", "0.10",
        "--market-source", "unit-test",
        "--model-id", "historical-replay",
        "--package-out", str(target),
        "--json",
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert target.exists()
    assert len(output["artifact_id"]) == 64
    assert output["distribution"]["quantity"] == 1000.0

    assert main(["verify-market-risk", str(target), "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["status"] == "ok"
    assert verified["artifact_id"] == output["artifact_id"]

    assert main([
        "preflight",
        "--market-risk-package", str(target),
        "--json",
    ]) == 0
    preflight = json.loads(capsys.readouterr().out)
    assert preflight["market_risk_package"]["status"] == "verified"
