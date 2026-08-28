"""Command-line interface for SPK Derivatives."""

import argparse
import json
from typing import Any, Dict, Optional, Sequence

from .policy_lab import (
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spk-derivatives",
        description="Renewable-energy derivatives pricing and Policy Lab bridge",
    )
    subparsers = parser.add_subparsers(dest="command")

    info = subparsers.add_parser("info", help="Show package capabilities")
    info.add_argument("--json", action="store_true", dest="as_json")

    check = subparsers.add_parser(
        "policy-check",
        help="Read a Policy Lab claim-assessment package and expose an admitted quantity",
    )
    check.add_argument("package", help="Path to claim-assessment JSON")
    check.add_argument("--policy", dest="policy_id")
    check.add_argument("--json", action="store_true", dest="as_json")

    price = subparsers.add_parser(
        "policy-price",
        help="Price one Policy Lab-admitted exposure",
    )
    price.add_argument("package", help="Path to claim-assessment JSON")
    price.add_argument("--policy", dest="policy_id")
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
    price.add_argument("--json", action="store_true", dest="as_json")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "info"):
        from . import __version__

        _emit(
            {
                "name": "spk-derivatives",
                "version": __version__,
                "pricing": "binomial, monte-carlo, Greeks, stress/scenario analysis",
                "energy": "solar, wind, hydro",
                "policy_lab": "policylab.claim_assessment_package.v0.1",
            },
            bool(getattr(args, "as_json", False)),
        )
        return 0

    try:
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
        _emit(result.to_dict(), args.as_json)
        return 0
    except (PolicyLabPackageError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
