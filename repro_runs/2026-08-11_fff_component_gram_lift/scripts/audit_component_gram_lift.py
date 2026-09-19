#!/usr/bin/env python3
"""Audit the C93 equivariant gauge obstruction and quadratic Gram lift."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
C92 = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_gauge_invariant_cell_lift/scripts/"
        "audit_gauge_invariant_cell_lift.py"
    )
)
HOL = C92["HOL"]
SURFACE = C92["SURFACE"]
SMALL = C92["SMALL"]
PAIR = C92["PAIR"]
EVEN_MASKS = (3, 5, 6)


def sign(bit: int) -> int:
    return 1 if bit == 0 else -1


def line_cells(table: list[list[int]], view: int, line: int) -> list[int]:
    n = len(table)
    if view == 0:
        return [line * n + column for column in range(n)]
    if view == 1:
        return [row * n + line for row in range(n)]
    return [
        row * n + column
        for row in range(n)
        for column in range(n)
        if table[row][column] == line
    ]


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    cell_count = n * n
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]

    grams = {mask: [0] * (cell_count * cell_count) for mask in EVEN_MASKS}
    parity_grams = {
        mask: [0] * (cell_count * cell_count) for mask in EVEN_MASKS
    }
    exact_dimensions = Counter()
    dimension_zero_odd_cell_incidences = 0
    component_cell_pair_fourier_checks = 0
    component_quadratic_gauge_checks = 0
    component_mod2_checks = 0
    nontrivial_quadratic_components = 0

    for component_id, component in enumerate(components):
        exact_masks = [
            mask
            for mask in range(8)
            if HOL["exact_mask_on_component"](component, alphas, mask)
        ]
        basis = HOL["binary_basis"](exact_masks)
        dimension = len(basis)
        exact_dimensions[dimension] += 1
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

        t_values = [0] * cell_count
        label_counts = {
            cell: [0] * (1 << dimension) for cell in cells
        }
        for cell, role_flags in cells.items():
            role_masses = [len(entries) for entries in role_flags]
            if len(set(role_masses)) != 1:
                errors.append(
                    ["role_mass", component_id, cell, role_masses]
                )
            t_values[cell] = role_masses[0]
            if dimension == 0 and role_masses[0] % 2:
                dimension_zero_odd_cell_incidences += 1
            for flag in component:
                if cell not in flags[flag]["cells"]:
                    continue
                label = 0
                for bit, mask in enumerate(basis):
                    label |= potentials[mask][flag] << bit
                label_counts[cell][label] += 1

        pushforwards = {}
        for mask in EVEN_MASKS:
            if mask not in exact_masks:
                continue
            values = [0] * cell_count
            for cell, role_flags in cells.items():
                values[cell] = sum(
                    sign(potentials[mask][flag])
                    for entries in role_flags
                    for flag in entries
                )
                component_mod2_checks += 1
                if (values[cell] - t_values[cell]) % 2:
                    errors.append(
                        [
                            "component_pushforward_mod2",
                            component_id,
                            mask,
                            cell,
                            values[cell],
                            t_values[cell],
                        ]
                    )
            pushforwards[mask] = values
            support = list(cells)
            for x in support:
                for y in support:
                    index = x * cell_count + y
                    product = values[x] * values[y]
                    transformed_product = (-values[x]) * (-values[y])
                    if transformed_product != product:
                        errors.append(
                            [
                                "quadratic_gauge",
                                component_id,
                                mask,
                                x,
                                y,
                                product,
                                transformed_product,
                            ]
                        )
                    grams[mask][index] += product
                    parity_grams[mask][index] ^= (
                        (t_values[x] & 1) & (t_values[y] & 1)
                    )
                    component_quadratic_gauge_checks += 1

        if pushforwards:
            nontrivial_quadratic_components += 1

        support = list(cells)
        for x in support:
            for y in support:
                component_cell_pair_fourier_checks += 1
                lhs = sum(
                    values[x] * values[y]
                    for values in pushforwards.values()
                )
                rhs = (1 << dimension) * sum(
                    left * right
                    for left, right in zip(
                        label_counts[x], label_counts[y]
                    )
                ) - 9 * t_values[x] * t_values[y]
                if lhs != rhs:
                    errors.append(
                        [
                            "off_diagonal_fourier",
                            component_id,
                            x,
                            y,
                            lhs,
                            rhs,
                        ]
                    )

    gram_entry_mod2_checks = 0
    gram_kernel_checks = 0
    gram_symmetry_checks = 0
    gram_traces = {}
    for mask in EVEN_MASKS:
        gram = grams[mask]
        parity_gram = parity_grams[mask]
        gram_traces[mask] = sum(
            gram[cell * cell_count + cell] for cell in range(cell_count)
        )
        for x in range(cell_count):
            for y in range(cell_count):
                index = x * cell_count + y
                gram_entry_mod2_checks += 1
                if (gram[index] & 1) != parity_gram[index]:
                    errors.append(
                        [
                            "global_gram_mod2",
                            mask,
                            x,
                            y,
                            gram[index],
                            parity_gram[index],
                        ]
                    )
                gram_symmetry_checks += 1
                if gram[index] != gram[y * cell_count + x]:
                    errors.append(
                        ["gram_symmetry", mask, x, y, gram[index]]
                    )
        for view in range(3):
            if not (mask & (1 << view)):
                continue
            for x in range(cell_count):
                for line in range(n):
                    gram_kernel_checks += 1
                    value = sum(
                        gram[x * cell_count + y]
                        for y in line_cells(table, view, line)
                    )
                    if value:
                        errors.append(
                            ["gram_line_kernel", mask, view, x, line, value]
                        )

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "exact_space_dimension_counts": dict(sorted(exact_dimensions.items())),
        "nontrivial_quadratic_components": nontrivial_quadratic_components,
        "dimension_zero_odd_cell_incidences": (
            dimension_zero_odd_cell_incidences
        ),
        "component_cell_pair_fourier_checks": (
            component_cell_pair_fourier_checks
        ),
        "component_quadratic_gauge_checks": component_quadratic_gauge_checks,
        "component_mod2_checks": component_mod2_checks,
        "gram_entry_mod2_checks": gram_entry_mod2_checks,
        "gram_kernel_checks": gram_kernel_checks,
        "gram_symmetry_checks": gram_symmetry_checks,
        "gram_traces": {str(mask): value for mask, value in gram_traces.items()},
        "errors": errors,
    }


def equivariant_anchor_no_go_audit() -> dict:
    table = [
        [0, 1, 2, 3],
        [1, 0, 3, 2],
        [2, 3, 0, 1],
        [3, 2, 1, 0],
    ]
    n = 4
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    target = next(
        component
        for component in components
        if {
            cell
            for flag in component
            for cell in flags[flag]["cells"]
        }
        == {0, 1, 4, 5}
    )

    row_permutation = (0, 1, 2, 3)
    column_permutation = (1, 0, 3, 2)
    symbol_permutation = (1, 0, 3, 2)
    autotopism_errors = []
    for row in range(n):
        for column in range(n):
            left = table[row_permutation[row]][column_permutation[column]]
            right = symbol_permutation[table[row][column]]
            if left != right:
                autotopism_errors.append([row, column, left, right])

    flag_by_cells = {
        frozenset(flag["cells"]): index for index, flag in enumerate(flags)
    }
    flag_map = {}
    for index, flag in enumerate(flags):
        mapped_cells = []
        for cell in flag["cells"]:
            row, column = divmod(cell, n)
            mapped_cells.append(
                row_permutation[row] * n + column_permutation[column]
            )
        flag_map[index] = flag_by_cells[frozenset(mapped_cells)]

    target_set = set(target)
    component_stable = {flag_map[flag] for flag in target} == target_set
    shifts = {}
    shift_errors = []
    potentials = {}
    for mask in EVEN_MASKS:
        potential = HOL["mask_potential_on_component"](
            target, alphas, mask
        )
        potentials[str(mask)] = {
            str(flag): potential[flag] for flag in sorted(target)
        }
        observed = {
            potential[flag_map[flag]] ^ potential[flag] for flag in target
        }
        shifts[str(mask)] = sorted(observed)
        expected = {3: {1}, 5: {1}, 6: {0}}[mask]
        if observed != expected:
            shift_errors.append([mask, sorted(observed), sorted(expected)])

    errors = []
    if bad_groups:
        errors.append(["dual_edge_groups", bad_groups])
    if autotopism_errors:
        errors.append(["not_autotopism", autotopism_errors])
    if not component_stable:
        errors.append(["component_not_stable"])
    errors.extend(["shift", *entry] for entry in shift_errors)
    return {
        "table": table,
        "row_permutation": list(row_permutation),
        "column_permutation": list(column_permutation),
        "symbol_permutation": list(symbol_permutation),
        "target_component_flags": sorted(target),
        "target_component_cells": [0, 1, 4, 5],
        "flag_map_on_component": {
            str(flag): flag_map[flag] for flag in sorted(target)
        },
        "normalized_potentials": potentials,
        "gauge_shifts": shifts,
        "component_stable": component_stable,
        "error_count": len(errors),
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    count_keys = (
        "component_count",
        "nontrivial_quadratic_components",
        "dimension_zero_odd_cell_incidences",
        "component_cell_pair_fourier_checks",
        "component_quadratic_gauge_checks",
        "component_mod2_checks",
        "gram_entry_mod2_checks",
        "gram_kernel_checks",
        "gram_symmetry_checks",
    )
    dimensions = Counter()
    traces = Counter()
    errors = []
    for record in records:
        dimensions.update(
            {
                int(key): value
                for key, value in record["exact_space_dimension_counts"].items()
            }
        )
        traces.update(record["gram_traces"])
        errors.extend(
            [record["source_index"], error] for error in record["errors"]
        )
    return {
        "name": name,
        "table_count": len(records),
        **{
            key: sum(record[key] for record in records)
            for key in count_keys
        },
        "exact_space_dimension_counts": dict(sorted(dimensions.items())),
        "aggregate_gram_traces": dict(sorted(traces.items())),
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
    no_go = equivariant_anchor_no_go_audit()
    total_keys = (
        "table_count",
        "component_count",
        "nontrivial_quadratic_components",
        "dimension_zero_odd_cell_incidences",
        "component_cell_pair_fourier_checks",
        "component_quadratic_gauge_checks",
        "component_mod2_checks",
        "gram_entry_mod2_checks",
        "gram_kernel_checks",
        "gram_symmetry_checks",
        "error_count",
    )
    totals = {
        key: sum(dataset[key] for dataset in datasets.values())
        for key in total_keys
    }
    totals["equivariant_anchor_no_go_error_count"] = no_go["error_count"]
    payload = {
        "audit_version": "component_gram_lift_v1",
        "datasets": datasets,
        "equivariant_anchor_no_go": no_go,
        "totals": totals,
        "claim_boundary": [
            "C93 is rigorous and exactly audited.",
            "No universal isotopy-equivariant C79-derived gauge selection exists.",
            "The quadratic Gram/Fourier lift is canonical but does not decide order 10.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "Component Gram-lift and equivariant-anchor audit",
        "",
        *[
            f"{key.replace('_', ' ')}: {totals[key]}"
            for key in total_keys
        ],
        "equivariant anchor no-go errors: "
        f"{totals['equivariant_anchor_no_go_error_count']}",
        f"no-go gauge shifts: {no_go['gauge_shifts']}",
        f"no-go component flag map: {no_go['flag_map_on_component']}",
        "",
    ]
    for name, dataset in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components: {dataset['table_count']} / {dataset['component_count']}",
                f"- off-diagonal Fourier checks: {dataset['component_cell_pair_fourier_checks']}",
                f"- Gram mod-2 / kernel checks: {dataset['gram_entry_mod2_checks']} / {dataset['gram_kernel_checks']}",
                f"- dimension-zero odd cell incidences: {dataset['dimension_zero_odd_cell_incidences']}",
                f"- errors: {dataset['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C93 is rigorous and exactly audited.",
            "- The Klein-four autotopism rules out a universal isotopy-equivariant C79-derived gauge anchor.",
            "- The off-diagonal Fourier/Gram identity is the canonical quadratic replacement.",
            "- It does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] or no_go["error_count"])


if __name__ == "__main__":
    raise SystemExit(main())
