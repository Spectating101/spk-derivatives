"""Command-line interface for SPK Derivatives."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from .artifacts import (
    PricingArtifactError,
    SPK_PRICING_PACKAGE_SCHEMA,
    build_policy_pricing_package,
    load_pricing_result_package,
    validate_pricing_result_package,
    write_pricing_result_package,
)
from .energy_contracts import EnergyContract
from .market_artifacts import (
    MarketRiskArtifactError,
    SPK_MARKET_RISK_SCHEMA,
    build_market_risk_package,
    load_market_risk_package,
    validate_market_risk_package,
    write_market_risk_package,
)
from .policy_analysis import (
    PolicyComparisonError,
    SPK_POLICY_COMPARISON_SCHEMA,
    build_policy_comparison_package,
    compare_policy_outcomes,
    validate_policy_comparison_package,
)
from .policy_lab import (
    POLICY_LAB_PROFILE,
    POLICY_LAB_SCHEMA,
    PolicyLabPackageError,
    extract_admitted_exposure,
    price_admitted_exposure,
)
from .scenario_risk import summarize_policy_contract_distribution
from .scenario_set import (
    SCENARIO_SET_SCHEMA,
    ScenarioSet,
    ScenarioSetError,
    build_market_price_scenarios,
    load_scenario_set,
    validate_scenario_set,
    write_scenario_set,
)


def _emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for item in payload:
            print(json.dumps(item, sort_keys=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _write_json(payload: Dict[str, Any], path: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_json_array(path: str, context: str) -> Sequence[float]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{context} must contain a JSON array")
    return payload


def _read_json_object(path: Optional[str], context: str) -> Dict[str, Any]:
    if path is None:
        return {}
    payload = _read_json(path)
    if not isinstance(payload, Mapping):
        raise ValueError(f"{context} must contain a JSON object")
    return dict(payload)


def _add_policy_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--policy", dest="policy_id")


def _add_pricing_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--spot", type=float, required=True, dest="S0")
    parser.add_argument("--strike", type=float, required=True, dest="K")
    parser.add_argument("--maturity", type=float, required=True, dest="T")
    parser.add_argument("--rate", type=float, required=True, dest="r")
    parser.add_argument("--volatility", type=float, required=True, dest="sigma")
    parser.add_argument(
        "--method",
        choices=("binomial", "monte-carlo"),
        default="binomial",
    )
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--simulations", type=int, default=10000)
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--payoff",
        choices=("call", "redeemable"),
        default="call",
        dest="payoff_type",
    )
    parser.add_argument(
        "--assumption",
        action="append",
        default=[],
        help="Declare a model assumption in the emitted artifact (repeatable)",
    )


def _add_contract_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--contract-type",
        choices=("merchant", "fixed-price", "floor", "cap", "collar"),
        required=True,
    )
    parser.add_argument("--currency", required=True)
    parser.add_argument("--fixed-price", type=float)
    parser.add_argument("--floor-price", type=float)
    parser.add_argument("--cap-price", type=float)


def _add_scenario_provenance_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--market-source", default="user-supplied-json")
    parser.add_argument("--observed-at")
    parser.add_argument("--model-id", default="empirical-scenarios")
    parser.add_argument("--model-parameters", help="Path to a JSON object of model parameters")
    parser.add_argument("--source-hash")
    parser.add_argument("--seed", type=int)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spk-derivatives",
        description="Renewable-energy derivatives pricing, provenance, and Policy Lab bridge",
    )
    subparsers = parser.add_subparsers(dest="command")

    info = subparsers.add_parser("info", help="Show package capabilities")
    info.add_argument("--json", action="store_true", dest="as_json")

    preflight = subparsers.add_parser(
        "preflight",
        help="Verify SPK runtime contracts and optional Policy Lab/SPK artifacts",
    )
    preflight.add_argument("--policy-package")
    _add_policy_selector(preflight)
    preflight.add_argument("--result-package")
    preflight.add_argument("--comparison-package")
    preflight.add_argument("--market-risk-package")
    preflight.add_argument("--scenario-set")
    preflight.add_argument("--json", action="store_true", dest="as_json")

    scenario_build = subparsers.add_parser(
        "scenario-build",
        help="Build a deterministic market-price scenario-set manifest",
    )
    scenario_build.add_argument("--prices", required=True, help="Path to a JSON array of prices")
    scenario_build.add_argument("--price-unit", required=True)
    scenario_build.add_argument("--source", required=True)
    scenario_build.add_argument("--observed-at", required=True)
    scenario_build.add_argument("--model-id", required=True)
    scenario_build.add_argument("--model-parameters", help="Path to a JSON object")
    scenario_build.add_argument("--source-hash")
    scenario_build.add_argument("--seed", type=int)
    scenario_build.add_argument("--out", required=True)
    scenario_build.add_argument("--json", action="store_true", dest="as_json")

    check = subparsers.add_parser(
        "policy-check",
        help="Read a Policy Lab claim-assessment package and expose one admitted quantity",
    )
    check.add_argument("package", help="Path to claim-assessment JSON")
    _add_policy_selector(check)
    check.add_argument("--json", action="store_true", dest="as_json")

    compare = subparsers.add_parser(
        "policy-compare",
        help="Show every Policy Lab policy outcome without silently choosing one",
    )
    compare.add_argument("package", help="Path to claim-assessment JSON")
    compare.add_argument("--json", action="store_true", dest="as_json")

    price = subparsers.add_parser(
        "policy-price",
        help="Price one Policy Lab-admitted exposure",
    )
    price.add_argument("package", help="Path to claim-assessment JSON")
    _add_policy_selector(price)
    _add_pricing_arguments(price)
    price.add_argument(
        "--package-out",
        help="Write a deterministic provenance-preserving pricing result package",
    )
    price.add_argument("--json", action="store_true", dest="as_json")

    sweep = subparsers.add_parser(
        "policy-sweep",
        help="Price all admitted policies under one common market/model assumption set",
    )
    sweep.add_argument("package", help="Path to claim-assessment JSON")
    _add_pricing_arguments(sweep)
    sweep.add_argument(
        "--package-out",
        help="Write a deterministic policy-comparison package",
    )
    sweep.add_argument("--json", action="store_true", dest="as_json")

    market_risk = subparsers.add_parser(
        "market-risk",
        help="Apply an identity-bound market scenario set and contract to one admitted quantity",
    )
    market_risk.add_argument("package", help="Path to Policy Lab claim-assessment JSON")
    _add_policy_selector(market_risk)
    scenario_source = market_risk.add_mutually_exclusive_group(required=True)
    scenario_source.add_argument(
        "--scenario-set",
        help="Path to a deterministic SPK scenario-set manifest",
    )
    scenario_source.add_argument(
        "--prices",
        help="Path to a raw JSON array; SPK will bind it into a scenario-set manifest",
    )
    _add_contract_arguments(market_risk)
    _add_scenario_provenance_arguments(market_risk)
    market_risk.add_argument("--scenario-out", help="Write the normalized scenario manifest")
    market_risk.add_argument("--package-out")
    market_risk.add_argument("--json", action="store_true", dest="as_json")

    verify = subparsers.add_parser(
        "verify-result",
        help="Verify a deterministic SPK pricing result package and its identities",
    )
    verify.add_argument("package")
    verify.add_argument("--json", action="store_true", dest="as_json")

    verify_comparison = subparsers.add_parser(
        "verify-comparison",
        help="Verify a deterministic SPK policy-comparison package and its identities",
    )
    verify_comparison.add_argument("package")
    verify_comparison.add_argument("--json", action="store_true", dest="as_json")

    verify_market = subparsers.add_parser(
        "verify-market-risk",
        help="Verify a deterministic SPK market-risk package and its identities",
    )
    verify_market.add_argument("package")
    verify_market.add_argument("--json", action="store_true", dest="as_json")

    verify_scenario = subparsers.add_parser(
        "verify-scenario-set",
        help="Verify a deterministic SPK scenario-set manifest and identity",
    )
    verify_scenario.add_argument("package")
    verify_scenario.add_argument("--json", action="store_true", dest="as_json")

    return parser


def _runtime_info() -> Dict[str, Any]:
    from . import __version__

    return {
        "name": "spk-derivatives",
        "version": __version__,
        "software_status": "research-beta",
        "pricing": "binomial, monte-carlo, Black-76, Bachelier, OU/spike scenarios, Greeks",
        "energy": "solar, wind, hydro",
        "policy_lab_schema": POLICY_LAB_SCHEMA,
        "policy_lab_profile": POLICY_LAB_PROFILE,
        "pricing_result_schema": SPK_PRICING_PACKAGE_SCHEMA,
        "policy_comparison_schema": SPK_POLICY_COMPARISON_SCHEMA,
        "market_risk_schema": SPK_MARKET_RISK_SCHEMA,
        "scenario_set_schema": SCENARIO_SET_SCHEMA,
        "policy_sensitivity": "compare and price admitted governance outcomes under common assumptions",
        "market_model_sensitivity": "compare price-model consequences under fixed admitted quantity and contract terms",
    }


def _pricing_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "S0": args.S0,
        "K": args.K,
        "T": args.T,
        "r": args.r,
        "sigma": args.sigma,
        "method": args.method,
        "steps": args.steps,
        "num_simulations": args.simulations,
        "seed": args.seed,
        "payoff_type": args.payoff_type,
    }


def _scenario_from_market_args(args: argparse.Namespace, contract: EnergyContract) -> ScenarioSet:
    if args.scenario_set:
        scenario_set = load_scenario_set(args.scenario_set)
        if scenario_set.normalized_kind != "market-price":
            raise ScenarioSetError("market-risk requires a market-price scenario set")
    else:
        if not args.observed_at:
            raise ScenarioSetError(
                "raw --prices require --observed-at so scenario provenance is explicit"
            )
        prices = _read_json_array(args.prices, "market-risk --prices")
        scenario_set = build_market_price_scenarios(
            prices,
            price_unit=contract.price_unit,
            source=args.market_source,
            source_hash=args.source_hash,
            observed_at_utc=args.observed_at,
            model_id=args.model_id,
            model_parameters=_read_json_object(
                args.model_parameters, "market-risk --model-parameters"
            ),
            seed=args.seed,
        )

    if scenario_set.price_unit != contract.price_unit:
        raise ScenarioSetError(
            f"scenario price_unit {scenario_set.price_unit!r} does not match "
            f"contract price_unit {contract.price_unit!r}"
        )
    return scenario_set


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "info"):
        _emit(_runtime_info(), bool(getattr(args, "as_json", False)))
        return 0

    try:
        if args.command == "scenario-build":
            prices = _read_json_array(args.prices, "scenario-build --prices")
            scenario_set = build_market_price_scenarios(
                prices,
                price_unit=args.price_unit,
                source=args.source,
                source_hash=args.source_hash,
                observed_at_utc=args.observed_at,
                model_id=args.model_id,
                model_parameters=_read_json_object(
                    args.model_parameters, "scenario-build --model-parameters"
                ),
                seed=args.seed,
            )
            target = write_scenario_set(scenario_set, args.out)
            output = scenario_set.to_dict()
            output["written_to"] = str(target)
            _emit(output, args.as_json)
            return 0

        if args.command == "verify-scenario-set":
            scenario_set = load_scenario_set(args.package)
            validate_scenario_set(scenario_set)
            _emit(
                {
                    "status": "ok",
                    "schema": SCENARIO_SET_SCHEMA,
                    "scenario_set_id": scenario_set.scenario_set_id,
                    "kind": scenario_set.normalized_kind,
                    "scenario_count": len(scenario_set.market_prices),
                    "price_unit": scenario_set.price_unit,
                    "model_id": scenario_set.model_id,
                },
                args.as_json,
            )
            return 0

        if args.command == "verify-result":
            package = load_pricing_result_package(args.package)
            validate_pricing_result_package(package)
            _emit(
                {
                    "status": "ok",
                    "schema": package["schema"],
                    "artifact_id": package["artifact_id"],
                    "package_content_id": package["package_content_id"],
                    "policy_id": package["authority"]["policy_id"],
                    "decision_id": package["authority"]["decision_id"],
                },
                args.as_json,
            )
            return 0

        if args.command == "verify-comparison":
            package = json.loads(Path(args.package).read_text(encoding="utf-8"))
            validate_policy_comparison_package(package)
            _emit(
                {
                    "status": "ok",
                    "schema": package["schema"],
                    "comparison_id": package["comparison_id"],
                    "package_content_id": package["package_content_id"],
                    "admitted_policy_count": package["comparison"]["admitted_policy_count"],
                    "blocked_policy_count": package["comparison"]["blocked_policy_count"],
                },
                args.as_json,
            )
            return 0

        if args.command == "verify-market-risk":
            package = load_market_risk_package(args.package)
            validate_market_risk_package(package)
            _emit(
                {
                    "status": "ok",
                    "schema": package["schema"],
                    "artifact_id": package["artifact_id"],
                    "package_content_id": package["package_content_id"],
                    "policy_id": package["authority"]["policy_id"],
                    "decision_id": package["authority"]["decision_id"],
                    "contract_type": package["contract"]["contract_type"],
                    "scenarios": package["risk"]["scenarios"],
                    "scenario_set_id": package["market"]["input"].get("scenario_set_id"),
                },
                args.as_json,
            )
            return 0

        if args.command == "preflight":
            payload = {**_runtime_info(), "status": "ok"}
            if args.policy_package:
                exposure = extract_admitted_exposure(
                    args.policy_package, policy_id=args.policy_id
                )
                payload["policy_package"] = {
                    "status": "admitted",
                    "assessment_id": exposure.assessment_id,
                    "policy_id": exposure.policy_id,
                    "decision_id": exposure.decision_id,
                    "quantity": exposure.quantity,
                    "unit": exposure.unit,
                }
            if args.result_package:
                result_package = load_pricing_result_package(args.result_package)
                validate_pricing_result_package(result_package)
                payload["result_package"] = {
                    "status": "verified",
                    "artifact_id": result_package["artifact_id"],
                    "package_content_id": result_package["package_content_id"],
                }
            if args.comparison_package:
                comparison_package = json.loads(
                    Path(args.comparison_package).read_text(encoding="utf-8")
                )
                validate_policy_comparison_package(comparison_package)
                payload["comparison_package"] = {
                    "status": "verified",
                    "comparison_id": comparison_package["comparison_id"],
                    "package_content_id": comparison_package["package_content_id"],
                }
            if args.market_risk_package:
                market_package = load_market_risk_package(args.market_risk_package)
                validate_market_risk_package(market_package)
                payload["market_risk_package"] = {
                    "status": "verified",
                    "artifact_id": market_package["artifact_id"],
                    "package_content_id": market_package["package_content_id"],
                    "scenario_set_id": market_package["market"]["input"].get(
                        "scenario_set_id"
                    ),
                }
            if args.scenario_set:
                scenario_set = load_scenario_set(args.scenario_set)
                payload["scenario_set"] = {
                    "status": "verified",
                    "scenario_set_id": scenario_set.scenario_set_id,
                    "kind": scenario_set.normalized_kind,
                    "scenario_count": len(scenario_set.market_prices),
                }
            _emit(payload, args.as_json)
            return 0

        if args.command == "policy-compare":
            outcomes = [item.to_dict() for item in compare_policy_outcomes(args.package)]
            _emit(outcomes, args.as_json)
            return 0

        if args.command == "policy-sweep":
            package = build_policy_comparison_package(
                args.package,
                **_pricing_kwargs(args),
                assumptions=args.assumption,
            )
            if args.package_out:
                target = _write_json(package, args.package_out)
                output = dict(package)
                output["written_to"] = str(target)
            else:
                output = package
            _emit(output, args.as_json)
            return 0

        exposure = extract_admitted_exposure(args.package, policy_id=args.policy_id)
        if args.command == "policy-check":
            _emit(exposure.to_dict(), args.as_json)
            return 0

        if args.command == "market-risk":
            contract = EnergyContract(
                args.contract_type,
                currency=args.currency,
                quantity_unit=exposure.unit,
                fixed_price=args.fixed_price,
                floor_price=args.floor_price,
                cap_price=args.cap_price,
            )
            scenario_set = _scenario_from_market_args(args, contract)
            if args.scenario_out:
                write_scenario_set(scenario_set, args.scenario_out)

            distribution = summarize_policy_contract_distribution(
                exposure,
                scenario_set.market_prices,
                contract,
            )
            output = distribution.to_dict()
            output["scenario_set_id"] = scenario_set.scenario_set_id

            if args.package_out:
                market_package = build_market_risk_package(
                    exposure,
                    distribution,
                    contract,
                    market_input={
                        "kind": "scenario-set",
                        "schema": SCENARIO_SET_SCHEMA,
                        "scenario_set_id": scenario_set.scenario_set_id,
                        "source": scenario_set.source,
                        "source_hash": scenario_set.source_hash,
                        "observed_at_utc": scenario_set.observed_at_utc,
                        "price_unit": scenario_set.price_unit,
                    },
                    scenario_model={
                        "id": scenario_set.model_id,
                        "parameters": dict(scenario_set.model_parameters),
                        "seed": scenario_set.seed,
                        "scenario_count": len(scenario_set.market_prices),
                    },
                )
                target = write_market_risk_package(market_package, args.package_out)
                output["market_risk_package"] = str(target)
                output["artifact_id"] = market_package["artifact_id"]
                output["market_risk_package_content_id"] = market_package[
                    "package_content_id"
                ]
            _emit(output, args.as_json)
            return 0

        result = price_admitted_exposure(exposure, **_pricing_kwargs(args))
        output = result.to_dict()

        if args.package_out:
            package = build_policy_pricing_package(
                exposure,
                result,
                S0=args.S0,
                K=args.K,
                T=args.T,
                r=args.r,
                sigma=args.sigma,
                payoff_type=args.payoff_type,
                steps=args.steps,
                num_simulations=args.simulations,
                seed=args.seed,
                assumptions=args.assumption,
            )
            target = write_pricing_result_package(package, args.package_out)
            output.update(
                {
                    "result_package": str(target),
                    "artifact_id": package["artifact_id"],
                    "result_package_content_id": package["package_content_id"],
                }
            )

        _emit(output, args.as_json)
        return 0
    except (
        PolicyLabPackageError,
        PricingArtifactError,
        PolicyComparisonError,
        MarketRiskArtifactError,
        ScenarioSetError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        parser.exit(2, f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
