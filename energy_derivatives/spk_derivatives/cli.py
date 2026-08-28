"""Command-line interface for SPK Derivatives."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .artifacts import (
    PricingArtifactError,
    SPK_PRICING_PACKAGE_SCHEMA,
    build_policy_pricing_package,
    load_pricing_result_package,
    validate_pricing_result_package,
    write_pricing_result_package,
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
    preflight.add_argument("--json", action="store_true", dest="as_json")

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

    return parser


def _runtime_info() -> Dict[str, Any]:
    from . import __version__

    return {
        "name": "spk-derivatives",
        "version": __version__,
        "software_status": "research-beta",
        "pricing": "binomial, monte-carlo, Greeks, stress/scenario analysis",
        "energy": "solar, wind, hydro",
        "policy_lab_schema": POLICY_LAB_SCHEMA,
        "policy_lab_profile": POLICY_LAB_PROFILE,
        "pricing_result_schema": SPK_PRICING_PACKAGE_SCHEMA,
        "policy_comparison_schema": SPK_POLICY_COMPARISON_SCHEMA,
        "policy_sensitivity": "compare and price admitted governance outcomes under common assumptions",
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "info"):
        _emit(_runtime_info(), bool(getattr(args, "as_json", False)))
        return 0

    try:
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
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        parser.exit(2, f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
