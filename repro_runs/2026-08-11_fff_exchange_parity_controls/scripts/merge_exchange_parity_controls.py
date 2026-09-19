#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order8", type=Path, required=True)
    parser.add_argument("--order10", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    order8 = json.loads(args.order8.read_text())
    order10 = json.loads(args.order10.read_text())
    errors = []
    if order8["totals"]["table_count"] != 230:
        errors.append(["order8_table_count", order8["totals"]["table_count"], 230])
    if order10["totals"]["table_count"] != 135:
        errors.append(["order10_table_count", order10["totals"]["table_count"], 135])
    for payload in (order8, order10):
        if payload["totals"]["error_count"]:
            errors.append([payload["dataset"], "source_errors", payload["totals"]["error_count"]])

    payload = {
        "audit_version": "exchange_parity_controls_merge_v1",
        "order8_fff_complete": order8["totals"],
        "order10_tracked_partial": order10["totals"],
        "codimension_one_forced_by_fff": (
            order8["totals"]["exchange_quotient_dimension_mod2_distribution"] == {"1": 230}
        ),
        "error_count": len(errors),
        "errors": errors,
        "claim_boundary": [
            "Order-8 controls can falsify a universal implication FFF => q4=1.",
            "Order-10 controls are diagnostic only and cannot decide C38.",
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "Merged exchange-parity controls",
        "",
        f"order-8 FFF quotient dimensions: {order8['totals']['exchange_quotient_dimension_mod2_distribution']}",
        f"order-10 tracked quotient dimensions: {order10['totals']['exchange_quotient_dimension_mod2_distribution']}",
        f"FFF forces q4=1 on the complete order-8 controls: {payload['codimension_one_forced_by_fff']}",
        f"errors: {payload['error_count']}",
        "",
        "Boundary: no order-10 claim; C38 remains open and C40 is absent.",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
