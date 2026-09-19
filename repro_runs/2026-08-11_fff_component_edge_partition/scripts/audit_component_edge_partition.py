#!/usr/bin/env python3
"""Audit the C94 component edge partition of the Latin cell graph."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict, deque
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


def shared_view(table: list[list[int]], x: int, y: int) -> int | None:
    n = len(table)
    row_x, column_x = divmod(x, n)
    row_y, column_y = divmod(y, n)
    tests = (
        row_x == row_y,
        column_x == column_y,
        table[row_x][column_x] == table[row_y][column_y],
    )
    return tests.index(True) if sum(tests) == 1 else None


def direct_intercalate_degrees(table: list[list[int]]) -> list[int]:
    n = len(table)
    degrees = [0] * (n * n)
    for row in range(n):
        for other_row in range(row + 1, n):
            for column in range(n):
                for other_column in range(column + 1, n):
                    if (
                        table[row][column]
                        == table[other_row][other_column]
                        and table[row][other_column]
                        == table[other_row][column]
                    ):
                        for cell in (
                            row * n + column,
                            row * n + other_column,
                            other_row * n + column,
                            other_row * n + other_column,
                        ):
                            degrees[cell] += 1
    return degrees


def erdos_gallai_checks(degrees: list[int]) -> tuple[int, list]:
    ordered = sorted(degrees, reverse=True)
    errors = []
    if sum(ordered) % 2:
        errors.append(["odd_degree_sum", ordered])
    for k in range(1, len(ordered) + 1):
        left = sum(ordered[:k])
        right = k * (k - 1) + sum(min(value, k) for value in ordered[k:])
        if left > right:
            errors.append(["erdos_gallai", k, left, right, ordered])
    return len(ordered), errors


def connected_on_support(edges: set[tuple[int, int]], support: set[int]) -> bool:
    if not support:
        return True
    adjacency = {cell: set() for cell in support}
    for x, y in edges:
        adjacency[x].add(y)
        adjacency[y].add(x)
    start = next(iter(support))
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == support


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

    global_edges = [defaultdict(list) for _ in range(3)]
    nonintercalate_degrees = [
        [0] * cell_count for _ in range(3)
    ]
    component_cell_degree_checks = 0
    component_cell_gram_checks = 0
    component_dual_edge_checks = 0
    component_flag_triangle_checks = 0
    component_connectedness_checks = 0
    component_line_graphical_checks = 0
    erdos_gallai_inequality_checks = 0
    intercalate_matching_checks = 0
    dimension_zero_components = 0
    dimension_zero_component_cells = 0
    dimension_zero_odd_cell_incidences = 0
    dimension_zero_support_weights = Counter()
    dimension_zero_cell_support_sizes = Counter()

    for component_id, component in enumerate(components):
        component_set = set(component)
        atom_ids = {
            atom for flag in component for atom in flags[flag]["atoms"]
        }
        intercalate = (
            len(component) == 4
            and len(atom_ids) == 3
            and all(atoms[atom]["length"] == 2 for atom in atom_ids)
        )
        exact_masks = [
            mask
            for mask in range(8)
            if HOL["exact_mask_on_component"](component, alphas, mask)
        ]
        dimension_zero = exact_masks == [0]
        if dimension_zero:
            dimension_zero_components += 1

        role_counts = defaultdict(lambda: [0, 0, 0])
        cell_flag_incidence = defaultdict(set)
        for flag in component:
            for role, cell in enumerate(flags[flag]["cells"]):
                role_counts[cell][role] += 1
                cell_flag_incidence[cell].add(flag)

        t_values = [0] * cell_count
        for cell, counts in role_counts.items():
            if len(set(counts)) != 1:
                errors.append(["role_mass", component_id, cell, counts])
            t_values[cell] = counts[0]
        support = set(role_counts)
        if dimension_zero:
            dimension_zero_component_cells += len(support)
            weight = sum(t_values[cell] & 1 for cell in support)
            dimension_zero_odd_cell_incidences += weight
            dimension_zero_support_weights[weight] += 1
            dimension_zero_cell_support_sizes[len(support)] += 1

        edges = [set() for _ in range(3)]
        for colour, alpha in enumerate(alphas):
            for flag in component:
                neighbor = alpha[flag]
                if neighbor not in component_set:
                    errors.append(
                        ["component_edge_escape", component_id, colour, flag]
                    )
                    continue
                if flag > neighbor:
                    continue
                common = set(flags[flag]["cells"]) & set(
                    flags[neighbor]["cells"]
                )
                component_dual_edge_checks += 1
                if len(common) != 2:
                    errors.append(
                        [
                            "dual_edge_cell_pair",
                            component_id,
                            colour,
                            flag,
                            neighbor,
                            sorted(common),
                        ]
                    )
                    continue
                x, y = sorted(common)
                view = shared_view(table, x, y)
                if view != colour:
                    errors.append(
                        [
                            "dual_edge_colour",
                            component_id,
                            colour,
                            view,
                            x,
                            y,
                        ]
                    )
                    continue
                edge = (x, y)
                if edge in edges[colour]:
                    errors.append(
                        ["duplicate_component_edge", component_id, colour, edge]
                    )
                edges[colour].add(edge)
                global_edges[colour][edge].append(component_id)

        all_edges = set().union(*edges)
        for flag in component:
            cells = flags[flag]["cells"]
            for left in range(3):
                for right in range(left + 1, 3):
                    x, y = sorted((cells[left], cells[right]))
                    view = shared_view(table, x, y)
                    component_flag_triangle_checks += 1
                    if view is None or (x, y) not in edges[view]:
                        errors.append(
                            [
                                "flag_triangle_edge",
                                component_id,
                                flag,
                                x,
                                y,
                                view,
                            ]
                        )

        component_connectedness_checks += 1
        if not connected_on_support(all_edges, support):
            errors.append(["component_cell_graph_disconnected", component_id])

        for cell in support:
            for view in range(3):
                degree = sum(cell in edge for edge in edges[view])
                component_cell_degree_checks += 1
                if degree != t_values[cell]:
                    errors.append(
                        [
                            "component_cell_degree",
                            component_id,
                            view,
                            cell,
                            degree,
                            t_values[cell],
                        ]
                    )
                if not intercalate:
                    nonintercalate_degrees[view][cell] += degree

        for view in range(3):
            if len(edges[view]) * 2 != len(component):
                errors.append(
                    [
                        "component_edge_count",
                        component_id,
                        view,
                        len(edges[view]),
                        len(component),
                    ]
                )
            if intercalate:
                intercalate_matching_checks += 1
                degrees = Counter(
                    cell for edge in edges[view] for cell in edge
                )
                if len(edges[view]) != 2 or set(degrees.values()) != {1}:
                    errors.append(
                        [
                            "intercalate_matching",
                            component_id,
                            view,
                            sorted(edges[view]),
                        ]
                    )
            for line in range(n):
                cells = line_cells(table, view, line)
                degrees = [t_values[cell] for cell in cells]
                component_line_graphical_checks += 1
                checks, graphical_errors = erdos_gallai_checks(degrees)
                erdos_gallai_inequality_checks += checks
                errors.extend(
                    [
                        "line_graphical",
                        component_id,
                        view,
                        line,
                        *entry,
                    ]
                    for entry in graphical_errors
                )

        for x in support:
            for y in support:
                observed = len(
                    cell_flag_incidence[x] & cell_flag_incidence[y]
                )
                expected = (
                    3 * t_values[x]
                    if x == y
                    else 2 if tuple(sorted((x, y))) in all_edges else 0
                )
                component_cell_gram_checks += 1
                if observed != expected:
                    errors.append(
                        [
                            "component_cell_gram",
                            component_id,
                            x,
                            y,
                            observed,
                            expected,
                        ]
                    )

    global_edge_partition_checks = 0
    for view in range(3):
        expected = set()
        for line in range(n):
            cells = line_cells(table, view, line)
            expected.update(
                (cells[left], cells[right])
                for left in range(n)
                for right in range(left + 1, n)
            )
        observed = set(global_edges[view])
        global_edge_partition_checks += len(expected)
        if observed != expected:
            errors.append(
                [
                    "global_edge_support",
                    view,
                    sorted(expected - observed)[:20],
                    sorted(observed - expected)[:20],
                ]
            )
        duplicates = [
            [edge, owners]
            for edge, owners in global_edges[view].items()
            if len(owners) != 1
        ]
        if duplicates:
            errors.append(["global_edge_partition", view, duplicates[:20]])

    intercalate_degrees = direct_intercalate_degrees(table)
    c84_residual_degree_checks = 0
    for view in range(3):
        for cell in range(cell_count):
            c84_residual_degree_checks += 1
            expected = n - 1 - intercalate_degrees[cell]
            if nonintercalate_degrees[view][cell] != expected:
                errors.append(
                    [
                        "c84_residual_degree",
                        view,
                        cell,
                        nonintercalate_degrees[view][cell],
                        expected,
                    ]
                )

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "flag_count": len(flags),
        "component_dual_edge_checks": component_dual_edge_checks,
        "component_flag_triangle_checks": component_flag_triangle_checks,
        "component_cell_degree_checks": component_cell_degree_checks,
        "component_cell_gram_checks": component_cell_gram_checks,
        "component_connectedness_checks": component_connectedness_checks,
        "component_line_graphical_checks": component_line_graphical_checks,
        "erdos_gallai_inequality_checks": erdos_gallai_inequality_checks,
        "global_edge_partition_checks": global_edge_partition_checks,
        "intercalate_matching_checks": intercalate_matching_checks,
        "c84_residual_degree_checks": c84_residual_degree_checks,
        "dimension_zero_components": dimension_zero_components,
        "dimension_zero_component_cells": dimension_zero_component_cells,
        "dimension_zero_odd_cell_incidences": (
            dimension_zero_odd_cell_incidences
        ),
        "dimension_zero_support_weights": dict(
            sorted(dimension_zero_support_weights.items())
        ),
        "dimension_zero_cell_support_sizes": dict(
            sorted(dimension_zero_cell_support_sizes.items())
        ),
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    count_keys = (
        "component_count",
        "flag_count",
        "component_dual_edge_checks",
        "component_flag_triangle_checks",
        "component_cell_degree_checks",
        "component_cell_gram_checks",
        "component_connectedness_checks",
        "component_line_graphical_checks",
        "erdos_gallai_inequality_checks",
        "global_edge_partition_checks",
        "intercalate_matching_checks",
        "c84_residual_degree_checks",
        "dimension_zero_components",
        "dimension_zero_component_cells",
        "dimension_zero_odd_cell_incidences",
    )
    weights = Counter()
    supports = Counter()
    errors = []
    for record in records:
        weights.update(record["dimension_zero_support_weights"])
        supports.update(record["dimension_zero_cell_support_sizes"])
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
        "dimension_zero_support_weights": dict(sorted(weights.items())),
        "dimension_zero_cell_support_sizes": dict(sorted(supports.items())),
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
    total_keys = (
        "table_count",
        "component_count",
        "flag_count",
        "component_dual_edge_checks",
        "component_flag_triangle_checks",
        "component_cell_degree_checks",
        "component_cell_gram_checks",
        "component_connectedness_checks",
        "component_line_graphical_checks",
        "erdos_gallai_inequality_checks",
        "global_edge_partition_checks",
        "intercalate_matching_checks",
        "c84_residual_degree_checks",
        "dimension_zero_components",
        "dimension_zero_component_cells",
        "dimension_zero_odd_cell_incidences",
        "error_count",
    )
    totals = {
        key: sum(dataset[key] for dataset in datasets.values())
        for key in total_keys
    }
    payload = {
        "audit_version": "component_edge_partition_v1",
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C94 is rigorous and exactly audited.",
            "The component edge partition is an integral lift of C91 and C84 degrees.",
            "It sees dimension-zero components but does not decide order 10.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "Component edge-partition audit",
        "",
        *[
            f"{key.replace('_', ' ')}: {totals[key]}"
            for key in total_keys
        ],
        "",
    ]
    for name, dataset in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components/flags: {dataset['table_count']} / {dataset['component_count']} / {dataset['flag_count']}",
                f"- dual-edge / degree / Gram checks: {dataset['component_dual_edge_checks']} / {dataset['component_cell_degree_checks']} / {dataset['component_cell_gram_checks']}",
                f"- graphical line / Erdos-Gallai checks: {dataset['component_line_graphical_checks']} / {dataset['erdos_gallai_inequality_checks']}",
                f"- global edge / C84 residual checks: {dataset['global_edge_partition_checks']} / {dataset['c84_residual_degree_checks']}",
                f"- dimension-zero components / odd incidences: {dataset['dimension_zero_components']} / {dataset['dimension_zero_odd_cell_incidences']}",
                f"- dimension-zero support weights: {dataset['dimension_zero_support_weights']}",
                f"- dimension-zero cell-support sizes: {dataset['dimension_zero_cell_support_sizes']}",
                f"- errors: {dataset['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C94 is rigorous and exactly audited.",
            "- The three simple component graphs have the same degree vector and partition all Latin-line clique edges.",
            "- This strictly strengthens isolated C91 parity and applies to exact-space dimension zero.",
            "- It does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"])


if __name__ == "__main__":
    raise SystemExit(main())
