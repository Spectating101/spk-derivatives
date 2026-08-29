#!/usr/bin/env python3
"""Build an identity-bound SPK scenario manifest from a local AEMO price file."""

from __future__ import annotations

import argparse
import json

from spk_derivatives.aemo_nem import (
    aemo_price_series_to_scenario_set,
    load_aemo_nem_dispatch_prices,
)
from spk_derivatives.scenario_set import write_scenario_set


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a local public AEMO DISPATCH.PRICE CSV/ZIP into an SPK scenario manifest"
    )
    parser.add_argument("source", help="Local AEMO .csv or single-layer .zip")
    parser.add_argument("--region", required=True, choices=["NSW1", "QLD1", "SA1", "TAS1", "VIC1"])
    parser.add_argument("--out", required=True, help="Output scenario-set JSON path")
    args = parser.parse_args()

    series = load_aemo_nem_dispatch_prices(args.source, region_id=args.region)
    scenario = aemo_price_series_to_scenario_set(series)
    target = write_scenario_set(scenario, args.out)
    print(
        json.dumps(
            {
                "status": "ok",
                "region_id": series.region_id,
                "source_hash": series.source_hash,
                "observations": len(series.observations),
                "start_utc": series.start_utc,
                "end_utc": series.end_utc,
                "scenario_set_id": scenario.scenario_set_id,
                "price_unit": scenario.price_unit,
                "written_to": str(target),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
