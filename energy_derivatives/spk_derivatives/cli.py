"""Command-line interface for SPK Derivatives."""

import argparse
import json
from typing import Any, Dict, Optional, Sequence

from .artifacts import (
    PricingArtifactError,
    SPK_PRICING_PACKAGE_SCHEMA,
    build_policy_pricing_package,
    load_pricing_result_package,
    validate_pricing_result_package,
    write_pricing_result_package,
)
from .policy_lab import (
    POLICY_LAB_PROFILE,
    POLICY_LAB_SCHEMA,
    PolicyLabPackageError,
    extract_admitted_exposure,
    price_admitted_exposure,
)


def _emit(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _add_policy_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--policy", dest="policy_id")


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
    preflight.add_argument("--json", action="store_true", dest="as_json")

    check = subparsers.add_parser(
        "policy-check",
        help="Read a Policy Lab claim-assessment package and expose an admitted quantity",
    )
    check.add_argument("package", help="Path to claim-assessment JSON")
    _add_policy_selector(check)
    check.add_argument("--json", action="store_true", dest="as_json")

    price = subparsers.add_parser(
        "policy-price",
        help="Price one Policy Lab-admitted exposure",
    )
    price.add_argument("package", help="Path to claim-assessment JSON")
    _add_policy_selector(price)
    price.add_argument("--spot", type=float, required=True, dest="S0")
    price.add_argument("--strike", type=float, required=True, dest="K")
    price.add_argument("--maturity", type=float, required=True, dest="T")
    price.add_argument("--rate", type=float, required=True, dest="r")
    price.add_argument("--volatility", type=float, required=True, dest="sigma")
    price.add_argument(
        "--method",
        choices=("binomial", "monte-carlo"),
        default="binomial",
    )
    price.add_argument("--steps", type=int, default=100)
    price.add_argument("--simulations", type=int, default=10000)
    price.add_argument("--seed", type=int)
    price.add_argument(
        "--payoff",
        choices=("call", "redeemable"),
        default="call",
        dest="payoff_type",
    )
    price.add_argument(
        "--assumption",
        action="append",
        default=[],
        help="Declare a model assumption in the emitted result package (repeatable)",
    )
    price.add_argument(
        "--package-out",
        help="Write a deterministic provenance-preserving pricing result package",
    )
    price.add_argument("--json", action="store_true", dest="as_json")

    verify = subparsers.add_parser(
        "verify-result",
        help="Verify a deterministic SPK pricing result package and its identities",
    )
    verify.add_argument("package")
    verify.add_argument("--json", action="store_true", dest="as_json")

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
            _emit(payload, args.as_json)
            return 0

        exposure = extract_admitted_exposure(args.package, policy_id=args.policy_id)
        if args.command == "policy-check":
            _emit(exposure.to_dict(), args.as_json)
            return 0

        result = price_admitted_exposure(
            exposure,
            S0=args.S0,
            K=args.K,
            T=args.T,
            r=args.r,
            sigma=args.sigma,
            method=args.method,
            steps=args.steps,
            num_simulations=args.simulations,
            seed=args.seed,
            payoff_type=args.payoff_type,
        )
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
    except (PolicyLabPackageError, PricingArtifactError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
