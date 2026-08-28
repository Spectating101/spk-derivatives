#!/usr/bin/env python3
"""Run a chronological OU-versus-persistence holdout on local AEMO data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from spk_derivatives.aemo_nem import load_aemo_nem_dispatch_prices
from spk_derivatives.empirical_validation import validate_aemo_ou_holdout


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a source-bound AEMO NEM price series without in-sample leakage"
    )
    parser.add_argument("source", help="Local AEMO .csv or single-layer .zip")
    parser.add_argument(
        "--region", required=True, choices=["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]
    )
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--out", help="Optional JSON report output path")
    args = parser.parse_args()

    series = load_aemo_nem_dispatch_prices(args.source, region_id=args.region)
    report = validate_aemo_ou_holdout(series, train_fraction=args.train_fraction)
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
