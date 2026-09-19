#!/usr/bin/env python3
"""Independent semantic checks for the binary-homotopy audit output."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


EXPECTED = {
    "order2_reduced_complete": {
        "tables": 1,
        "pairs": {(1, 4): 1},
    },
    "order4_reduced_complete": {
        "tables": 4,
        "pairs": {(1, 4): 3, (2, 12): 1},
    },
    "order6_reduced_complete": {
        "tables": 9408,
        "pairs": {(0, 0): 8928, (1, 4): 480},
    },
    "order8_fff_complete": {
        "tables": 230,
        "pairs": {(0, 0): 63, (1, 4): 156, (2, 12): 10, (3, 28): 1},
    },
    "order10_tracked_partial": {
        "tables": 135,
        "pairs": {(0, 0): 135},
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--prior-subsquare-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text())
    prior = json.loads(args.prior_subsquare_audit.read_text())
    errors = []
    checks = 0
    grouped = {}
    for dataset, expectation in EXPECTED.items():
        records = [record for record in audit["records"] if record["dataset"] == dataset]
        observed = Counter(
            (record["delta_2"], record["direct_half_order_subsquare_count"])
            for record in records
        )
        grouped[dataset] = {
            "table_count": len(records),
            "delta_subsquare_pairs": {
                f"{delta},{count}": multiplicity
                for (delta, count), multiplicity in sorted(observed.items())
            },
        }
        checks += len(records) * 5 + 2
        if len(records) != expectation["tables"]:
            errors.append([dataset, "table_count", len(records), expectation["tables"]])
        if observed != Counter(expectation["pairs"]):
            errors.append([dataset, "distribution", dict(observed), expectation["pairs"]])
        for record in records:
            if record["formula_half_order_subsquare_count"] != 4 * ((1 << record["delta_2"]) - 1):
                errors.append([dataset, record["source_index"], "formula_recompute"])
            if record["direct_half_order_subsquare_count"] != record["predicted_half_order_subsquare_count"]:
                errors.append([dataset, record["source_index"], "count_match"])
            if not record["set_match"]:
                errors.append([dataset, record["source_index"], "set_match"])
            if record["left_kernel_dimension"] != record["delta_2"] + 2:
                errors.append([dataset, record["source_index"], "kernel_dimension"])
            if record["line_rank_mod2"] + record["left_kernel_dimension"] != 3 * record["order"]:
                errors.append([dataset, record["source_index"], "rank_nullity"])

    prior_distribution = {
        str(key): value
        for key, value in prior["order8_fff_subsquare_census"][
            "order4_subsquare_count_distribution"
        ].items()
    }
    current_distribution = audit["datasets"]["order8_fff_complete"][
        "half_order_subsquare_count_distribution"
    ]
    prior_match = current_distribution == prior_distribution
    checks += 1
    if not prior_match:
        errors.append(["order8_fff_complete", "prior_C44_distribution", current_distribution, prior_distribution])

    payload = {
        "verification_version": "binary_homotopy_subsquares_semantic_v1",
        "checks": checks,
        "datasets": grouped,
        "prior_C44_order8_distribution_match": prior_match,
        "error_count": len(errors),
        "errors": errors,
        "overall_ok": not errors,
        "boundary": "Semantic verification of exact outputs; theorem proof is in the proof note.",
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(
            [
                "Binary homotopy subsquare semantic verification",
                "",
                f"overall_ok: {payload['overall_ok']}",
                f"checks: {checks}",
                f"prior C44 distribution match: {prior_match}",
                f"errors: {len(errors)}",
                "",
                "C38 remains open; C40 is absent.",
            ]
        )
        + "\n"
    )
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
