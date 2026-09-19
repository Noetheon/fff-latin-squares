#!/usr/bin/env python3
"""Audit C91 cross-component cell parity and its intercalate refinement."""

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
        / "repro_runs/2026-08-11_fff_color_parity_holonomy/scripts/audit_color_parity_holonomy.py"
    )
)
SURFACE = HOL["SURFACE"]
SMALL = HOL["SMALL"]
PAIR = HOL["PAIR"]


def direct_intercalate_degrees(table: list[list[int]]) -> list[int]:
    n = len(table)
    degrees = [0] * (n * n)
    for r in range(n):
        for rr in range(r + 1, n):
            for c in range(n):
                for cc in range(c + 1, n):
                    if table[r][c] == table[rr][cc] and table[r][cc] == table[rr][c]:
                        for cell in (r * n + c, r * n + cc, rr * n + c, rr * n + cc):
                            degrees[cell] += 1
    return degrees


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
    cell_data = [
        {
            "roles": [0, 0, 0],
            "component_mass": 0,
            "delta_zero_mass": 0,
            "delta_zero_odd_count": 0,
            "intercalate_mass": 0,
            "nonintercalate_mass": 0,
            "nonintercalate_delta_zero_mass": 0,
            "nonintercalate_delta_zero_odd_count": 0,
        }
        for _ in range(n * n)
    ]
    global_edge_counts = {view: [0] * n for view in ("row", "col", "sym")}
    component_cell_checks = delta_even_checks = intercalate_component_cell_checks = 0
    component_line_parity_checks = component_line_incidence_checks = 0
    odd_zero_component_incidences = odd_nonintercalate_zero_incidences = 0
    exact_space_dimensions = Counter()

    for component_id, component in enumerate(components):
        exact_masks = [
            mask
            for mask in range(8)
            if HOL["exact_mask_on_component"](component, alphas, mask)
        ]
        basis = HOL["binary_basis"](exact_masks)
        exact_space_dimensions[len(basis)] += 1
        shifts = [
            sum(((mask >> view) & 1) << i for i, mask in enumerate(basis))
            for view in range(3)
        ]
        delta = shifts[0] ^ shifts[1] ^ shifts[2]
        atom_ids = {atom for flag in component for atom in flags[flag]["atoms"]}
        intercalate = (
            len(component) == 4
            and len(atom_ids) == 3
            and all(atoms[atom]["length"] == 2 for atom in atom_ids)
        )
        counts = defaultdict(lambda: [0, 0, 0])
        for flag in component:
            for role, cell in enumerate(flags[flag]["cells"]):
                counts[cell][role] += 1

        for cell, role_counts in counts.items():
            component_cell_checks += 1
            if len(set(role_counts)) != 1:
                errors.append(
                    ["component_role_mass", component_id, cell, role_counts]
                )
                continue
            mass = role_counts[0]
            data = cell_data[cell]
            for role in range(3):
                data["roles"][role] += role_counts[role]
            data["component_mass"] += mass
            if delta:
                delta_even_checks += 1
                if mass % 2:
                    errors.append(
                        ["nonzero_delta_odd_mass", component_id, cell, delta, mass]
                    )
            else:
                data["delta_zero_mass"] += mass
                if mass % 2:
                    data["delta_zero_odd_count"] += 1
                    odd_zero_component_incidences += 1
            if intercalate:
                intercalate_component_cell_checks += 1
                data["intercalate_mass"] += mass
                if delta or mass != 1 or exact_masks != [0, 3, 5, 6]:
                    errors.append(
                        [
                            "intercalate_component_mass",
                            component_id,
                            cell,
                            delta,
                            mass,
                            exact_masks,
                        ]
                    )
            else:
                data["nonintercalate_mass"] += mass
                if not delta:
                    data["nonintercalate_delta_zero_mass"] += mass
                    if mass % 2:
                        data["nonintercalate_delta_zero_odd_count"] += 1
                        odd_nonintercalate_zero_incidences += 1

        parity_support = [0] * (n * n)
        for cell, role_counts in counts.items():
            parity_support[cell] = role_counts[0] % 2
        line_parities = {
            "row": [
                sum(parity_support[r * n + c] for c in range(n)) % 2
                for r in range(n)
            ],
            "col": [
                sum(parity_support[r * n + c] for r in range(n)) % 2
                for c in range(n)
            ],
            "sym": [
                sum(
                    parity_support[r * n + c]
                    for r in range(n)
                    for c in range(n)
                    if table[r][c] == symbol
                )
                % 2
                for symbol in range(n)
            ],
        }
        line_masses = {
            "row": [
                sum(counts.get(r * n + c, [0, 0, 0])[0] for c in range(n))
                for r in range(n)
            ],
            "col": [
                sum(counts.get(r * n + c, [0, 0, 0])[2] for r in range(n))
                for c in range(n)
            ],
            "sym": [
                sum(
                    counts.get(r * n + c, [0, 0, 0])[0]
                    for r in range(n)
                    for c in range(n)
                    if table[r][c] == symbol
                )
                for symbol in range(n)
            ],
        }
        edge_counts = {view: [0] * n for view in ("row", "col", "sym")}
        for view, color in enumerate(("row", "col", "sym")):
            for flag in component:
                neighbor = alphas[view][flag]
                if flag < neighbor:
                    label = flags[flag]["edge_keys"][view][2]
                    edge_counts[color][label] += 1
        component_line_incidence_checks += 3 * n
        for view in ("row", "col", "sym"):
            expected_masses = [2 * value for value in edge_counts[view]]
            global_edge_counts[view] = [
                left + right
                for left, right in zip(global_edge_counts[view], edge_counts[view])
            ]
            if line_masses[view] != expected_masses:
                errors.append(
                    [
                        "component_line_incidence",
                        component_id,
                        view,
                        line_masses[view],
                        expected_masses,
                    ]
                )
        component_line_parity_checks += 3 * n
        for view, parities in line_parities.items():
            if any(parities):
                errors.append(
                    ["component_line_parity", component_id, view, parities]
                )

    direct_iota = direct_intercalate_degrees(table)
    global_edge_budget_checks = 0
    expected_edge_budget = n * (n - 1) // 2
    for view in ("row", "col", "sym"):
        global_edge_budget_checks += n
        if global_edge_counts[view] != [expected_edge_budget] * n:
            errors.append(
                [
                    "global_edge_budget",
                    view,
                    global_edge_counts[view],
                    expected_edge_budget,
                ]
            )

    cell_checks = cross_parity_checks = intercalate_refinement_checks = 0
    x_layer_parity_checks = 0
    even_iota_forced_cells = odd_iota_cells = 0
    iota_distribution = Counter()
    odd_zero_count_distribution = Counter()
    odd_nonintercalate_count_distribution = Counter()
    for cell, data in enumerate(cell_data):
        cell_checks += 1
        expected = n - 1
        if data["roles"] != [expected, expected, expected]:
            errors.append(["global_role_partition", cell, data["roles"], expected])
        if data["component_mass"] != expected:
            errors.append(
                ["component_mass_partition", cell, data["component_mass"], expected]
            )
        cross_parity_checks += 1
        if data["delta_zero_mass"] % 2 != expected % 2:
            errors.append(
                ["delta_zero_parity", cell, data["delta_zero_mass"], expected]
            )
        if data["delta_zero_odd_count"] % 2 != expected % 2:
            errors.append(
                [
                    "delta_zero_odd_component_parity",
                    cell,
                    data["delta_zero_odd_count"],
                    expected,
                ]
            )

        iota = direct_iota[cell]
        iota_distribution[iota] += 1
        odd_zero_count_distribution[data["delta_zero_odd_count"]] += 1
        odd_nonintercalate_count_distribution[
            data["nonintercalate_delta_zero_odd_count"]
        ] += 1
        intercalate_refinement_checks += 1
        if data["intercalate_mass"] != iota:
            errors.append(
                ["intercalate_mass", cell, data["intercalate_mass"], iota]
            )
        if data["nonintercalate_mass"] != expected - iota:
            errors.append(
                [
                    "nonintercalate_mass",
                    cell,
                    data["nonintercalate_mass"],
                    expected - iota,
                ]
            )
        if data["nonintercalate_delta_zero_mass"] % 2 != (expected - iota) % 2:
            errors.append(
                [
                    "nonintercalate_delta_zero_parity",
                    cell,
                    data["nonintercalate_delta_zero_mass"],
                    expected - iota,
                ]
            )
        if data["nonintercalate_delta_zero_odd_count"] % 2 != (expected - iota) % 2:
            errors.append(
                [
                    "nonintercalate_odd_component_parity",
                    cell,
                    data["nonintercalate_delta_zero_odd_count"],
                    expected - iota,
                ]
            )
        x_layer_parity_checks += 1
        x_endpoint_parity = (3 * (expected - iota)) % 2
        if data["nonintercalate_delta_zero_odd_count"] % 2 != x_endpoint_parity:
            errors.append(
                [
                    "x_endpoint_parity_decomposition",
                    cell,
                    data["nonintercalate_delta_zero_odd_count"],
                    x_endpoint_parity,
                ]
            )
        if n % 2 == 0 and iota % 2 == 0:
            even_iota_forced_cells += 1
            if data["nonintercalate_delta_zero_odd_count"] == 0:
                errors.append(["missing_forced_nonintercalate_component", cell, iota])
        elif n % 2 == 0:
            odd_iota_cells += 1

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "component_cell_checks": component_cell_checks,
        "component_line_parity_checks": component_line_parity_checks,
        "component_line_incidence_checks": component_line_incidence_checks,
        "global_edge_budget_checks": global_edge_budget_checks,
        "delta_even_checks": delta_even_checks,
        "intercalate_component_cell_checks": intercalate_component_cell_checks,
        "cell_checks": cell_checks,
        "cross_parity_checks": cross_parity_checks,
        "intercalate_refinement_checks": intercalate_refinement_checks,
        "x_layer_parity_checks": x_layer_parity_checks,
        "odd_zero_component_incidences": odd_zero_component_incidences,
        "odd_nonintercalate_zero_incidences": odd_nonintercalate_zero_incidences,
        "even_iota_forced_cells": even_iota_forced_cells,
        "odd_iota_cells": odd_iota_cells,
        "exact_space_dimensions": dict(sorted(exact_space_dimensions.items())),
        "iota_distribution": dict(sorted(iota_distribution.items())),
        "odd_zero_count_distribution": dict(sorted(odd_zero_count_distribution.items())),
        "odd_nonintercalate_count_distribution": dict(
            sorted(odd_nonintercalate_count_distribution.items())
        ),
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    scalar_keys = (
        "component_count",
        "component_cell_checks",
        "component_line_parity_checks",
        "component_line_incidence_checks",
        "global_edge_budget_checks",
        "delta_even_checks",
        "intercalate_component_cell_checks",
        "cell_checks",
        "cross_parity_checks",
        "intercalate_refinement_checks",
        "x_layer_parity_checks",
        "odd_zero_component_incidences",
        "odd_nonintercalate_zero_incidences",
        "even_iota_forced_cells",
        "odd_iota_cells",
    )
    result = {
        "name": name,
        "table_count": len(records),
        **{key: sum(record[key] for record in records) for key in scalar_keys},
    }
    for key in (
        "exact_space_dimensions",
        "iota_distribution",
        "odd_zero_count_distribution",
        "odd_nonintercalate_count_distribution",
    ):
        distribution = Counter()
        for record in records:
            distribution.update({int(k): v for k, v in record[key].items()})
        result[key] = dict(sorted(distribution.items()))
    result["error_count"] = len(errors)
    result["errors"] = errors[:100]
    return result


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), SURFACE["parse_compact"](row["square"], 8)


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
                for index, table in enumerate(SMALL["reduced_latin_squares"](4), 1)
            ],
        ),
        "order6_complete": summarize(
            "order6_complete",
            [
                analyze_table(table, index)
                for index, table in enumerate(SMALL["reduced_latin_squares"](6), 1)
            ],
        ),
        "order8_fff_complete": summarize(
            "order8_fff_complete",
            [analyze_table(table, index) for index, table in load_n8(args.fff_metadata)],
        ),
        "order10_tracked_partial": summarize(
            "order10_tracked_partial",
            [
                analyze_table(table, index)
                for index, table, _ in PAIR["FLAG"]["n10_tables"](args.n10_corpus)
            ],
        ),
    }
    scalar_keys = (
        "table_count",
        "component_count",
        "component_cell_checks",
        "component_line_parity_checks",
        "component_line_incidence_checks",
        "global_edge_budget_checks",
        "delta_even_checks",
        "intercalate_component_cell_checks",
        "cell_checks",
        "cross_parity_checks",
        "intercalate_refinement_checks",
        "x_layer_parity_checks",
        "odd_zero_component_incidences",
        "odd_nonintercalate_zero_incidences",
        "even_iota_forced_cells",
        "odd_iota_cells",
        "error_count",
    )
    totals = {key: sum(data[key] for data in datasets.values()) for key in scalar_keys}
    for key in (
        "exact_space_dimensions",
        "iota_distribution",
        "odd_zero_count_distribution",
        "odd_nonintercalate_count_distribution",
    ):
        distribution = Counter()
        for data in datasets.values():
            distribution.update({int(k): v for k, v in data[key].items()})
        totals[key] = dict(sorted(distribution.items()))
    payload = {
        "audit_version": "cross_component_cell_parity_v1",
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C91 is rigorous and exactly audited.",
            "The gluing law gives a binary decomposition of the C84 X endpoint layer.",
            "It does not identify component gauges and does not decide order 10.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "Cross-component cell-parity audit",
        "",
        *[f"{key.replace('_', ' ')}: {totals[key]}" for key in scalar_keys],
        f"exact-space dimensions: {totals['exact_space_dimensions']}",
        f"cell intercalate-degree distribution: {totals['iota_distribution']}",
        f"odd delta-zero component-count distribution: {totals['odd_zero_count_distribution']}",
        "odd nonintercalate delta-zero component-count distribution: "
        f"{totals['odd_nonintercalate_count_distribution']}",
        "",
    ]
    for name, data in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components: {data['table_count']} / {data['component_count']}",
                f"- component-cell / cell checks: {data['component_cell_checks']} / {data['cell_checks']}",
                f"- even-iota forced cells: {data['even_iota_forced_cells']}",
                f"- odd nonintercalate delta-zero incidences: {data['odd_nonintercalate_zero_incidences']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C91 is rigorous and exactly audited.",
            "- It is the first explicit cross-component cell gluing law after C90.",
            "- It decomposes the C84 X endpoint parity but not component gauges.",
            "- It does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
