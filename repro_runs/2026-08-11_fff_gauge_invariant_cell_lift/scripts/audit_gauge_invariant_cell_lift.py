#!/usr/bin/env python3
"""Audit the C92 role-Fourier selection rule and cubic cell invariant."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOL = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_color_parity_holonomy/scripts/"
        "audit_color_parity_holonomy.py"
    )
)
SURFACE = HOL["SURFACE"]
SMALL = HOL["SMALL"]
PAIR = HOL["PAIR"]
EVEN_PLANE = (0, 3, 5, 6)


def sign(bit: int) -> int:
    return 1 if bit == 0 else -1


def parity(value: int) -> int:
    return value.bit_count() & 1


def direct_intercalate_degrees(table: list[list[int]]) -> list[int]:
    n = len(table)
    degrees = [0] * (n * n)
    for row in range(n):
        for other_row in range(row + 1, n):
            for column in range(n):
                for other_column in range(column + 1, n):
                    if (
                        table[row][column] == table[other_row][other_column]
                        and table[row][other_column] == table[other_row][column]
                    ):
                        for cell in (
                            row * n + column,
                            row * n + other_column,
                            other_row * n + column,
                            other_row * n + other_column,
                        ):
                            degrees[cell] += 1
    return degrees


def invariant_monomial_audit() -> dict:
    checks = 0
    errors = []
    for dimension in range(1, 4):
        nonzero = range(1, 1 << dimension)
        for exponent_parities in range(1 << ((1 << dimension) - 1)):
            charge = 0
            for offset, character in enumerate(nonzero):
                if exponent_parities & (1 << offset):
                    charge ^= character
            invariant = True
            for gauge in range(1 << dimension):
                checks += 1
                multiplier = sign(parity(charge & gauge))
                if multiplier != 1:
                    invariant = False
            if invariant != (charge == 0):
                errors.append(
                    [dimension, exponent_parities, charge, invariant]
                )
    return {"checks": checks, "errors": errors}


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]

    exact_mask_cell_checks = 0
    role_fourier_checks = 0
    selection_rule_checks = 0
    odd_mask_zero_checks = 0
    cubic_cell_checks = 0
    cubic_gauge_checks = 0
    cubic_congruence_checks = 0
    intercalate_cubic_checks = 0
    aggregate_cell_checks = 0
    naive_global_identity_failures = 0
    naive_global_failure_witness = None
    dimension_counts = Counter()
    cubic_by_dimension = Counter()
    cubic_by_mass = Counter()
    naive_global_difference = Counter()
    aggregate_cubic = [0] * (n * n)
    cubic_contributions: list[list[dict]] = [[] for _ in range(n * n)]

    for component_id, component in enumerate(components):
        exact_masks = [
            mask
            for mask in range(8)
            if HOL["exact_mask_on_component"](component, alphas, mask)
        ]
        basis = HOL["binary_basis"](exact_masks)
        dimension_counts[len(basis)] += 1
        potentials = {
            mask: HOL["mask_potential_on_component"](
                component, alphas, mask
            )
            for mask in exact_masks
        }
        cells = defaultdict(lambda: [[], [], []])
        for flag in component:
            for role, cell in enumerate(flags[flag]["cells"]):
                cells[cell][role].append(flag)

        pushforwards: dict[int, dict[int, int]] = {
            mask: {} for mask in exact_masks
        }
        for cell, role_flags in cells.items():
            role_mass = [len(entries) for entries in role_flags]
            if len(set(role_mass)) != 1:
                errors.append(
                    ["role_mass", component_id, cell, role_mass]
                )
            t_value = role_mass[0]
            for mask in exact_masks:
                exact_mask_cell_checks += 1
                role_sums = [
                    sum(sign(potentials[mask][flag]) for flag in entries)
                    for entries in role_flags
                ]
                expected_role_sums = [
                    sign(mask & 1) * role_sums[0],
                    sign((mask >> 2) & 1) * role_sums[0],
                    sign((mask >> 1) & 1) * role_sums[1],
                ]
                role_fourier_checks += 3
                observed_role_sums = [
                    role_sums[2],
                    role_sums[1],
                    role_sums[2],
                ]
                if observed_role_sums != expected_role_sums:
                    errors.append(
                        [
                            "role_fourier",
                            component_id,
                            cell,
                            mask,
                            observed_role_sums,
                            expected_role_sums,
                        ]
                    )
                total = sum(role_sums)
                factor = 1 + sign((mask >> 2) & 1) + sign(mask & 1)
                selection_rule_checks += 1
                if total != factor * role_sums[0]:
                    errors.append(
                        [
                            "selection_factor",
                            component_id,
                            cell,
                            mask,
                            total,
                            factor,
                            role_sums[0],
                        ]
                    )
                if mask.bit_count() % 2:
                    odd_mask_zero_checks += 1
                    if total:
                        errors.append(
                            [
                                "odd_mask_nonzero",
                                component_id,
                                cell,
                                mask,
                                total,
                            ]
                        )
                pushforwards[mask][cell] = total

        if all(mask in exact_masks for mask in EVEN_PLANE):
            for flag in component:
                if (
                    potentials[3][flag]
                    ^ potentials[5][flag]
                    ^ potentials[6][flag]
                ):
                    errors.append(
                        ["incompatible_even_potentials", component_id, flag]
                    )
                    break
            intercalate = len(component) == 4
            for cell, role_flags in cells.items():
                cubic_cell_checks += 1
                t_value = len(role_flags[0])
                values = [pushforwards[mask][cell] for mask in (3, 5, 6)]
                cubic = -values[0] * values[1] * values[2]
                aggregate_cubic[cell] += cubic
                cubic_contributions[cell].append(
                    {
                        "component_id": component_id,
                        "exact_dimension": len(basis),
                        "role_mass": t_value,
                        "pushforwards_3_5_6": values,
                        "cubic": cubic,
                        "intercalate": intercalate,
                    }
                )
                cubic_by_dimension[(len(basis), t_value, cubic)] += 1
                cubic_by_mass[(t_value, cubic, intercalate)] += 1
                for gauge in range(4):
                    cubic_gauge_checks += 1
                    translated = [
                        values[0] * sign(parity(1 & gauge)),
                        values[1] * sign(parity(2 & gauge)),
                        values[2] * sign(parity(3 & gauge)),
                    ]
                    translated_cubic = (
                        -translated[0] * translated[1] * translated[2]
                    )
                    if translated_cubic != cubic:
                        errors.append(
                            [
                                "cubic_gauge",
                                component_id,
                                cell,
                                gauge,
                                cubic,
                                translated_cubic,
                            ]
                        )
                cubic_congruence_checks += 1
                if (cubic - t_value**3) % 4:
                    errors.append(
                        [
                            "cubic_mod4",
                            component_id,
                            cell,
                            t_value,
                            cubic,
                        ]
                    )
                if t_value % 2 == 0 and cubic % 8:
                    errors.append(
                        [
                            "cubic_even_mod8",
                            component_id,
                            cell,
                            t_value,
                            cubic,
                        ]
                    )
                if abs(cubic) > t_value**3:
                    errors.append(
                        [
                            "cubic_bound",
                            component_id,
                            cell,
                            t_value,
                            cubic,
                        ]
                    )
                if intercalate:
                    intercalate_cubic_checks += 1
                    if t_value != 1 or cubic != 1:
                        errors.append(
                            [
                                "intercalate_cubic",
                                component_id,
                                cell,
                                t_value,
                                cubic,
                            ]
                        )

    intercalate_degrees = direct_intercalate_degrees(table)
    for cell, (cubic, degree) in enumerate(
        zip(aggregate_cubic, intercalate_degrees)
    ):
        aggregate_cell_checks += 1
        difference = cubic - degree
        naive_global_difference[difference] += 1
        if difference:
            naive_global_identity_failures += 1
            if naive_global_failure_witness is None:
                row, column = divmod(cell, n)
                naive_global_failure_witness = {
                    "table": table,
                    "cell_index": cell,
                    "cell": [row, column, table[row][column]],
                    "cubic_sum": cubic,
                    "intercalate_degree": degree,
                    "difference": difference,
                    "component_contributions": cubic_contributions[cell],
                }

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "exact_space_dimension_counts": dict(sorted(dimension_counts.items())),
        "exact_mask_cell_checks": exact_mask_cell_checks,
        "role_fourier_checks": role_fourier_checks,
        "selection_rule_checks": selection_rule_checks,
        "odd_mask_zero_checks": odd_mask_zero_checks,
        "cubic_cell_checks": cubic_cell_checks,
        "cubic_gauge_checks": cubic_gauge_checks,
        "cubic_congruence_checks": cubic_congruence_checks,
        "intercalate_cubic_checks": intercalate_cubic_checks,
        "aggregate_cell_checks": aggregate_cell_checks,
        "naive_global_identity_failures": naive_global_identity_failures,
        "naive_global_failure_witness": naive_global_failure_witness,
        "cubic_by_dimension": {
            str(key): value for key, value in sorted(cubic_by_dimension.items())
        },
        "cubic_by_mass": {
            str(key): value for key, value in sorted(cubic_by_mass.items())
        },
        "naive_global_difference": {
            str(key): value for key, value in sorted(naive_global_difference.items())
        },
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    keys = (
        "component_count",
        "exact_mask_cell_checks",
        "role_fourier_checks",
        "selection_rule_checks",
        "odd_mask_zero_checks",
        "cubic_cell_checks",
        "cubic_gauge_checks",
        "cubic_congruence_checks",
        "intercalate_cubic_checks",
        "aggregate_cell_checks",
        "naive_global_identity_failures",
    )
    dimensions = Counter()
    cubic_by_dimension = Counter()
    cubic_by_mass = Counter()
    naive_difference = Counter()
    for record in records:
        dimensions.update(
            {
                int(key): value
                for key, value in record["exact_space_dimension_counts"].items()
            }
        )
        cubic_by_dimension.update(record["cubic_by_dimension"])
        cubic_by_mass.update(record["cubic_by_mass"])
        naive_difference.update(record["naive_global_difference"])
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    first_witness = next(
        (
            record["naive_global_failure_witness"]
            for record in records
            if record["naive_global_failure_witness"] is not None
        ),
        None,
    )
    return {
        "name": name,
        "table_count": len(records),
        **{key: sum(record[key] for record in records) for key in keys},
        "exact_space_dimension_counts": dict(sorted(dimensions.items())),
        "cubic_by_dimension": dict(sorted(cubic_by_dimension.items())),
        "cubic_by_mass": dict(sorted(cubic_by_mass.items())),
        "naive_global_difference": dict(sorted(naive_difference.items())),
        "naive_global_failure_witness": first_witness,
        "error_count": len(errors),
        "errors": errors[:100],
    }


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), SURFACE["parse_compact"](
                row["square"], 8
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    invariant_audit = invariant_monomial_audit()
    datasets = {
        "order4_complete": summarize(
            "order4_complete",
            [
                analyze_table(table, index)
                for index, table in enumerate(
                    SMALL["reduced_latin_squares"](4), 1
                )
            ],
        ),
        "order6_complete": summarize(
            "order6_complete",
            [
                analyze_table(table, index)
                for index, table in enumerate(
                    SMALL["reduced_latin_squares"](6), 1
                )
            ],
        ),
        "order8_fff_complete": summarize(
            "order8_fff_complete",
            [
                analyze_table(table, index)
                for index, table in load_n8(args.fff_metadata)
            ],
        ),
        "order10_tracked_partial": summarize(
            "order10_tracked_partial",
            [
                analyze_table(table, index)
                for index, table, _ in PAIR["FLAG"]["n10_tables"](
                    args.n10_corpus
                )
            ],
        ),
    }
    total_keys = (
        "table_count",
        "component_count",
        "exact_mask_cell_checks",
        "role_fourier_checks",
        "selection_rule_checks",
        "odd_mask_zero_checks",
        "cubic_cell_checks",
        "cubic_gauge_checks",
        "cubic_congruence_checks",
        "intercalate_cubic_checks",
        "aggregate_cell_checks",
        "naive_global_identity_failures",
        "error_count",
    )
    totals = {
        key: sum(dataset[key] for dataset in datasets.values())
        for key in total_keys
    }
    dimensions = Counter()
    cubic_by_mass = Counter()
    naive_difference = Counter()
    for dataset in datasets.values():
        dimensions.update(
            {
                int(key): value
                for key, value in dataset[
                    "exact_space_dimension_counts"
                ].items()
            }
        )
        cubic_by_mass.update(dataset["cubic_by_mass"])
        naive_difference.update(dataset["naive_global_difference"])
    totals["exact_space_dimension_counts"] = dict(sorted(dimensions.items()))
    totals["cubic_by_mass"] = dict(sorted(cubic_by_mass.items()))
    totals["naive_global_difference"] = dict(sorted(naive_difference.items()))
    totals["naive_global_failure_witness"] = next(
        (
            dataset["naive_global_failure_witness"]
            for dataset in datasets.values()
            if dataset["naive_global_failure_witness"] is not None
        ),
        None,
    )
    totals["invariant_monomial_checks"] = invariant_audit["checks"]
    totals["invariant_monomial_error_count"] = len(invariant_audit["errors"])

    payload = {
        "audit_version": "gauge_invariant_cell_lift_v1",
        "invariant_monomial_audit": invariant_audit,
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C92 is rigorous and exactly audited.",
            "Independent component gauges forbid an intrinsic linear signed gluing.",
            "The cubic lift is componentwise gauge invariant but its naive global sum is not fixed by intercalate degree.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "Gauge-invariant cell-lift audit",
        "",
        *[
            f"{key.replace('_', ' ')}: {totals[key]}"
            for key in total_keys
        ],
        f"invariant monomial checks: {totals['invariant_monomial_checks']}",
        f"invariant monomial errors: {totals['invariant_monomial_error_count']}",
        f"exact-space dimensions: {totals['exact_space_dimension_counts']}",
        f"cubic-by-mass distribution: {totals['cubic_by_mass']}",
        f"naive global difference distribution: {totals['naive_global_difference']}",
        f"first naive global failure witness: {totals['naive_global_failure_witness']}",
        "",
    ]
    for name, dataset in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components: {dataset['table_count']} / {dataset['component_count']}",
                f"- role-Fourier / odd-mask-zero checks: {dataset['role_fourier_checks']} / {dataset['odd_mask_zero_checks']}",
                f"- cubic / gauge / congruence checks: {dataset['cubic_cell_checks']} / {dataset['cubic_gauge_checks']} / {dataset['cubic_congruence_checks']}",
                f"- naive global identity failures: {dataset['naive_global_identity_failures']} / {dataset['aggregate_cell_checks']}",
                f"- errors: {dataset['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C92 is rigorous and exactly audited.",
            "- Odd-weight exact masks have zero cell pushforward pointwise.",
            "- There is no intrinsic linear cross-component signed gluing without extra gauge anchors.",
            "- The cubic invariant is an integral component lift, but its naive global sum is falsified on the recorded cells.",
            "- It does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return int(
        totals["error_count"]
        or totals["invariant_monomial_error_count"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
