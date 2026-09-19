#!/usr/bin/env python3
"""Audit the orientable cell-companion surface of every flag component."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
C94 = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_component_edge_partition/scripts/"
        "audit_component_edge_partition.py"
    )
)
SURFACE = C94["SURFACE"]
SMALL = C94["SMALL"]
PAIR = C94["PAIR"]


def boundary_direction(cells: tuple[int, int, int], edge: tuple[int, int]):
    directed = ((cells[0], cells[1]), (cells[1], cells[2]), (cells[2], cells[0]))
    target = set(edge)
    for left, right in directed:
        if {left, right} == target:
            return left, right
    return None


def link_cycles(adjacency: dict[tuple, set[tuple]]) -> list[list[tuple]]:
    unseen = set(adjacency)
    cycles = []
    while unseen:
        start = min(unseen)
        previous = None
        current = start
        cycle = []
        while current not in cycle:
            cycle.append(current)
            unseen.discard(current)
            neighbors = sorted(adjacency[current])
            choices = [neighbor for neighbor in neighbors if neighbor != previous]
            if not choices:
                break
            previous, current = current, choices[0]
        cycles.append(cycle)
    return cycles


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    dual_adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            dual_adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](dual_adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]

    orientation_edge_checks = 0
    cell_edge_face_checks = 0
    link_vertex_degree_checks = 0
    link_colour_neighbor_checks = 0
    link_cycle_checks = 0
    link_cycle_length_sum = 0
    normalized_surface_checks = 0
    intercalate_sphere_checks = 0
    total_link_cycles = 0
    total_normalized_genus = 0
    genus_distribution = Counter()
    dimension_zero_genus_distribution = Counter()
    dimension_zero_link_cycle_distribution = Counter()

    for component_id, component in enumerate(components):
        component_set = set(component)
        atom_ids = {atom for flag in component for atom in flags[flag]["atoms"]}
        intercalate = (
            len(component) == 4
            and len(atom_ids) == 3
            and all(atoms[atom]["length"] == 2 for atom in atom_ids)
        )
        exact_masks = [
            mask
            for mask in range(8)
            if C94["HOL"]["exact_mask_on_component"](component, alphas, mask)
        ]
        dimension_zero = exact_masks == [0]

        edge_faces = [defaultdict(list) for _ in range(3)]
        for colour, alpha in enumerate(alphas):
            for flag in component:
                neighbor = alpha[flag]
                if neighbor not in component_set or flag > neighbor:
                    continue
                common = tuple(
                    sorted(
                        set(flags[flag]["cells"])
                        & set(flags[neighbor]["cells"])
                    )
                )
                if len(common) != 2:
                    errors.append(
                        ["dual_common_edge", component_id, colour, flag, neighbor]
                    )
                    continue
                edge_faces[colour][common].extend((flag, neighbor))
                left = boundary_direction(flags[flag]["cells"], common)
                right = boundary_direction(flags[neighbor]["cells"], common)
                orientation_edge_checks += 1
                if left is None or right != tuple(reversed(left)):
                    errors.append(
                        [
                            "face_orientation",
                            component_id,
                            colour,
                            flag,
                            neighbor,
                            left,
                            right,
                        ]
                    )

        for colour in range(3):
            for edge, owners in edge_faces[colour].items():
                cell_edge_face_checks += 1
                if len(owners) != 2 or len(set(owners)) != 2:
                    errors.append(
                        ["cell_edge_faces", component_id, colour, edge, owners]
                    )

        cell_links = defaultdict(lambda: defaultdict(set))
        role_counts = defaultdict(lambda: [0, 0, 0])
        for flag in component:
            cells = flags[flag]["cells"]
            for role, cell in enumerate(cells):
                role_counts[cell][role] += 1
                incident = []
                for other in cells:
                    if other == cell:
                        continue
                    view = C94["shared_view"](table, cell, other)
                    incident.append((view, min(cell, other), max(cell, other)))
                if len(incident) != 2 or None in [item[0] for item in incident]:
                    errors.append(["flag_link_edge", component_id, flag, cell])
                    continue
                left, right = incident
                if right in cell_links[cell][left]:
                    errors.append(
                        ["duplicate_link_edge", component_id, cell, left, right]
                    )
                cell_links[cell][left].add(right)
                cell_links[cell][right].add(left)

        component_link_cycles = 0
        component_link_vertices = 0
        for cell, adjacency in cell_links.items():
            counts = role_counts[cell]
            if len(set(counts)) != 1:
                errors.append(["role_mass", component_id, cell, counts])
            t_value = counts[0]
            component_link_vertices += len(adjacency)
            if len(adjacency) != 3 * t_value:
                errors.append(
                    [
                        "link_vertex_count",
                        component_id,
                        cell,
                        len(adjacency),
                        3 * t_value,
                    ]
                )
            for vertex, neighbors in adjacency.items():
                link_vertex_degree_checks += 1
                if len(neighbors) != 2:
                    errors.append(
                        ["link_degree", component_id, cell, vertex, len(neighbors)]
                    )
                    continue
                neighbor_colours = {neighbor[0] for neighbor in neighbors}
                expected = {0, 1, 2} - {vertex[0]}
                link_colour_neighbor_checks += 1
                if neighbor_colours != expected:
                    errors.append(
                        [
                            "link_colour_neighbors",
                            component_id,
                            cell,
                            vertex,
                            sorted(neighbor_colours),
                            sorted(expected),
                        ]
                    )
            cycles = link_cycles(adjacency)
            component_link_cycles += len(cycles)
            for cycle in cycles:
                link_cycle_checks += 1
                link_cycle_length_sum += len(cycle)
                colours = [vertex[0] for vertex in cycle]
                if len(cycle) % 3 or set(colours) != {0, 1, 2}:
                    errors.append(
                        ["link_cycle_colour", component_id, cell, colours]
                    )
                for index, colour in enumerate(colours):
                    if colour == colours[index - 1] or colour == colours[(index + 1) % len(colours)]:
                        errors.append(
                            ["link_cycle_repeat", component_id, cell, colours]
                        )
                        break
            if not (1 <= len(cycles) <= t_value):
                errors.append(
                    ["link_cycle_bound", component_id, cell, len(cycles), t_value]
                )

        face_count = len(component)
        if component_link_vertices != 3 * face_count:
            errors.append(
                [
                    "component_link_vertex_total",
                    component_id,
                    component_link_vertices,
                    3 * face_count,
                ]
            )
        numerator = face_count // 2 - component_link_cycles
        normalized_surface_checks += 1
        if face_count % 2 or numerator % 2:
            errors.append(
                ["normalized_euler_parity", component_id, face_count, component_link_cycles]
            )
            genus = -1
        else:
            genus = 1 + numerator // 2
            if genus < 0:
                errors.append(
                    ["normalized_negative_genus", component_id, genus]
                )
        total_link_cycles += component_link_cycles
        total_normalized_genus += genus
        genus_distribution[genus] += 1
        if dimension_zero:
            dimension_zero_genus_distribution[genus] += 1
            dimension_zero_link_cycle_distribution[component_link_cycles] += 1
        if intercalate:
            intercalate_sphere_checks += 1
            if component_link_cycles != 4 or genus != 0:
                errors.append(
                    [
                        "intercalate_companion_sphere",
                        component_id,
                        component_link_cycles,
                        genus,
                    ]
                )

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "flag_count": len(flags),
        "orientation_edge_checks": orientation_edge_checks,
        "cell_edge_face_checks": cell_edge_face_checks,
        "link_vertex_degree_checks": link_vertex_degree_checks,
        "link_colour_neighbor_checks": link_colour_neighbor_checks,
        "link_cycle_checks": link_cycle_checks,
        "link_cycle_length_sum": link_cycle_length_sum,
        "normalized_surface_checks": normalized_surface_checks,
        "intercalate_sphere_checks": intercalate_sphere_checks,
        "total_link_cycles": total_link_cycles,
        "total_normalized_genus": total_normalized_genus,
        "genus_distribution": dict(sorted(genus_distribution.items())),
        "dimension_zero_genus_distribution": dict(
            sorted(dimension_zero_genus_distribution.items())
        ),
        "dimension_zero_link_cycle_distribution": dict(
            sorted(dimension_zero_link_cycle_distribution.items())
        ),
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    count_keys = (
        "component_count",
        "flag_count",
        "orientation_edge_checks",
        "cell_edge_face_checks",
        "link_vertex_degree_checks",
        "link_colour_neighbor_checks",
        "link_cycle_checks",
        "link_cycle_length_sum",
        "normalized_surface_checks",
        "intercalate_sphere_checks",
        "total_link_cycles",
        "total_normalized_genus",
    )
    genus = Counter()
    dimension_zero_genus = Counter()
    dimension_zero_cycles = Counter()
    errors = []
    for record in records:
        genus.update(record["genus_distribution"])
        dimension_zero_genus.update(record["dimension_zero_genus_distribution"])
        dimension_zero_cycles.update(record["dimension_zero_link_cycle_distribution"])
        errors.extend([record["source_index"], error] for error in record["errors"])
    return {
        "name": name,
        "table_count": len(records),
        **{key: sum(record[key] for record in records) for key in count_keys},
        "genus_distribution": dict(sorted(genus.items())),
        "dimension_zero_genus_distribution": dict(sorted(dimension_zero_genus.items())),
        "dimension_zero_link_cycle_distribution": dict(sorted(dimension_zero_cycles.items())),
        "error_count": len(errors),
        "errors": errors[:100],
    }


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
            [analyze_table(table, index) for index, table in enumerate(SMALL["reduced_latin_squares"](4), 1)],
        ),
        "order6_complete": summarize(
            "order6_complete",
            [analyze_table(table, index) for index, table in enumerate(SMALL["reduced_latin_squares"](6), 1)],
        ),
        "order8_fff_complete": summarize(
            "order8_fff_complete",
            [analyze_table(table, index) for index, table in load_n8(args.fff_metadata)],
        ),
        "order10_tracked_partial": summarize(
            "order10_tracked_partial",
            [analyze_table(table, index) for index, table, _ in PAIR["FLAG"]["n10_tables"](args.n10_corpus)],
        ),
    }
    total_keys = (
        "table_count",
        "component_count",
        "flag_count",
        "orientation_edge_checks",
        "cell_edge_face_checks",
        "link_vertex_degree_checks",
        "link_colour_neighbor_checks",
        "link_cycle_checks",
        "link_cycle_length_sum",
        "normalized_surface_checks",
        "intercalate_sphere_checks",
        "total_link_cycles",
        "total_normalized_genus",
        "error_count",
    )
    totals = {key: sum(dataset[key] for dataset in datasets.values()) for key in total_keys}
    payload = {
        "audit_version": "cell_companion_surface_v1",
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C95 is rigorous and exactly audited.",
            "The normalized cell companion is a connected closed orientable surface.",
            "This is a joint cross-view condition but does not decide order 10.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = ["Cell-companion surface audit", ""]
    lines.extend(f"{key.replace('_', ' ')}: {totals[key]}" for key in total_keys)
    lines.append("")
    for name, dataset in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components/flags: {dataset['table_count']} / {dataset['component_count']} / {dataset['flag_count']}",
                f"- orientation / cell-edge checks: {dataset['orientation_edge_checks']} / {dataset['cell_edge_face_checks']}",
                f"- link degree / colour / cycle checks: {dataset['link_vertex_degree_checks']} / {dataset['link_colour_neighbor_checks']} / {dataset['link_cycle_checks']}",
                f"- normalized surfaces / intercalate spheres: {dataset['normalized_surface_checks']} / {dataset['intercalate_sphere_checks']}",
                f"- genus distribution: {dataset['genus_distribution']}",
                f"- dimension-zero genus distribution: {dataset['dimension_zero_genus_distribution']}",
                f"- errors: {dataset['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C95 is rigorous and exactly audited.",
            "- It is a joint rainbow-triangle realization constraint beyond C94 graphicality.",
            "- It does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"])


if __name__ == "__main__":
    raise SystemExit(main())
