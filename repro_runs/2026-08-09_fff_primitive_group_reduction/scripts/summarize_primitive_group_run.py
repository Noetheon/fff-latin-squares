#!/usr/bin/env python3
"""Combine group generation, clique solves, and proof checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKED_GROUPS = (
    "s5_on_2sets",
    "pgl2_9",
    "s6_psigmal2_9",
    "m10",
    "pgammal2_9",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    generation = load(args.results / "primitive_group_generation.json")
    groups = []
    for item in generation["small_primitive_groups"]:
        group_id = item["group_id"]
        if item["direct_exclusion"]:
            solve_result = "not_needed"
            proof_checked = "not_applicable"
            proof_sha256 = None
        else:
            solve = load(args.results / f"{group_id}_cadical.json")
            check = load(args.results / f"{group_id}_drat_check.json")
            solve_result = solve["result"]
            proof_checked = check["result"]
            proof_sha256 = check["proof"]["sha256"]
        groups.append(
            {
                **item,
                "upper_bound_solve_result": solve_result,
                "proof_checked": proof_checked,
                "proof_sha256": proof_sha256,
            }
        )

    checked_ok = all(
        item["direct_exclusion"]
        or (
            item["group_id"] in CHECKED_GROUPS
            and item["upper_bound_solve_result"] == "unsat"
            and item["proof_checked"] == "verified"
        )
        for item in groups
    )
    construction_ok = all(
        item["closure_ok"] and item["transitive"] and item["primitive"]
        for item in groups
    )
    excludes_required_ten_clique = all(
        item["maximum_f_clique_including_identity"] < 10 for item in groups
    )
    payload = {
        "degree": 10,
        "encoding_version": generation["encoding_version"],
        "classification_orders": generation["external_classification_boundary"][
            "primitive_group_orders_degree10"
        ],
        "classification_dependency": generation["external_classification_boundary"][
            "dependency"
        ],
        "group_constructions_valid": construction_ok,
        "all_nontrivial_upper_bounds_proof_checked": checked_ok,
        "all_seven_small_groups_exclude_required_ten_clique": excludes_required_ten_clique,
        "small_primitive_groups": groups,
        "remaining_generated_groups": ["A10", "S10"],
        "one_view_consequence": (
            "Assuming the complete standard degree-10 primitive-group classification, "
            "every normalized degree-10 F-view generates A10 or S10."
        ),
        "three_view_consequence": (
            "Combining the one-view result with C60, every hypothetical order-10 FFF "
            "square has A10/S10 generated groups in all views and at least one S10 view."
        ),
        "claim_boundary": "C38 open; C40 absent; no n=10 existence or nonexistence result",
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "Degree-10 primitive-group reduction",
        "",
        f"group constructions valid: {construction_ok}",
        f"all nontrivial upper bounds proof-checked: {checked_ok}",
        f"all seven small primitive groups exclude a 10-clique: {excludes_required_ten_clique}",
        "",
        "group\torder\tF candidates\tmax F clique including identity\tproof status",
    ]
    for item in groups:
        status = "direct enumeration" if item["direct_exclusion"] else item["proof_checked"]
        lines.append(
            f"{item['group_id']}\t{item['group_order']}\t{item['f_candidate_count']}\t"
            f"{item['maximum_f_clique_including_identity']}\t{status}"
        )
    lines.extend(
        [
            "",
            "Classification consequence: every normalized degree-10 F-view generates A10 or S10.",
            "Three-view consequence: at least one view of a hypothetical order-10 FFF square generates S10.",
            "External boundary: completeness of the standard primitive degree-10 group classification.",
            "Scope: C38 remains open; C40 remains absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
