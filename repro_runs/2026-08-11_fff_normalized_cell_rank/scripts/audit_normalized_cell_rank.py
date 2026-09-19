#!/usr/bin/env python3
"""Audit the C96 normalized cell-incidence kernel and rank formula."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
C95 = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_cell_companion_surface/scripts/"
        "audit_cell_companion_surface.py"
    )
)
C94 = C95["C94"]
SURFACE = C95["SURFACE"]
SMALL = C95["SMALL"]
PAIR = C95["PAIR"]


class UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left = self.find(left)
        right = self.find(right)
        if left != right:
            self.parent[right] = left


CORNER_IDENTIFICATIONS = {
    0: ((0, 2), (2, 0)),
    1: ((1, 2), (2, 1)),
    2: ((0, 1), (1, 0)),
}
OPPOSITE_ROLE = (1, 0, 2)


def gf2_rank(rows: list[int]) -> int:
    pivots = {}
    for original in rows:
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def connected_labels(adjacency: list[set[int]]) -> tuple[list[int], int]:
    labels = [-1] * len(adjacency)
    count = 0
    for start in range(len(adjacency)):
        if labels[start] != -1:
            continue
        labels[start] = count
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if labels[neighbor] == -1:
                    labels[neighbor] = count
                    stack.append(neighbor)
        count += 1
    return labels, count


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

    normalized_vertex_checks = 0
    link_partition_checks = 0
    opposite_edge_checks = 0
    face_profile_checks = 0
    gf2_rank_checks = 0
    gram_entry_checks = 0
    coarse_factor_checks = 0
    gram_aggregation_checks = 0
    component_count_by_q = Counter()
    dimension_zero_count_by_q = Counter()
    normalized_vertex_distribution = Counter()
    opposite_component_distribution = Counter()
    rank_distribution = Counter()
    nontrivial_q_components = []

    for component_id, component in enumerate(components):
        local = {flag: index for index, flag in enumerate(component)}
        union = UnionFind(3 * len(component))
        for colour, role_pairs in CORNER_IDENTIFICATIONS.items():
            alpha = alphas[colour]
            for flag in component:
                neighbor = alpha[flag]
                for left_role, right_role in role_pairs:
                    left = 3 * local[flag] + left_role
                    right = 3 * local[neighbor] + right_role
                    if flags[flag]["cells"][left_role] != flags[neighbor]["cells"][right_role]:
                        errors.append(
                            [
                                "corner_cell_mismatch",
                                component_id,
                                colour,
                                flag,
                                neighbor,
                                left_role,
                                right_role,
                            ]
                        )
                    union.union(left, right)

        roots = sorted({union.find(index) for index in range(3 * len(component))})
        root_id = {root: index for index, root in enumerate(roots)}
        corner_vertex = [root_id[union.find(index)] for index in range(3 * len(component))]
        vertex_count = len(roots)
        vertex_cells = defaultdict(set)
        for flag in component:
            for role, cell in enumerate(flags[flag]["cells"]):
                vertex = corner_vertex[3 * local[flag] + role]
                vertex_cells[vertex].add(cell)
        for vertex in range(vertex_count):
            normalized_vertex_checks += 1
            if len(vertex_cells[vertex]) != 1:
                errors.append(
                    ["normalized_vertex_cell", component_id, vertex, sorted(vertex_cells[vertex])]
                )

        # Reconstruct the C95 link components independently from Latin-cell
        # edge labels and compare their complete corner partitions to the UF
        # corner orbits above.
        cell_links = defaultdict(lambda: defaultdict(set))
        corner_link_edges = {}
        for flag in component:
            cells = flags[flag]["cells"]
            for role, cell in enumerate(cells):
                incident = []
                for other in cells:
                    if other == cell:
                        continue
                    view = C94["shared_view"](table, cell, other)
                    incident.append((view, min(cell, other), max(cell, other)))
                left, right = incident
                cell_links[cell][left].add(right)
                cell_links[cell][right].add(left)
                corner_link_edges[(local[flag], role)] = (cell, left, right)

        link_component = {}
        for cell, link_adjacency in cell_links.items():
            tokens = sorted(link_adjacency)
            token_index = {token: index for index, token in enumerate(tokens)}
            labels, _ = connected_labels(
                [
                    {token_index[neighbor] for neighbor in link_adjacency[token]}
                    for token in tokens
                ]
            )
            for token, label in zip(tokens, labels):
                link_component[(cell, token)] = label

        uf_partition = defaultdict(set)
        link_partition = defaultdict(set)
        for flag in component:
            for role in range(3):
                corner = (local[flag], role)
                uf_partition[corner_vertex[3 * corner[0] + role]].add(corner)
                cell, left, right = corner_link_edges[corner]
                left_label = link_component[(cell, left)]
                right_label = link_component[(cell, right)]
                if left_label != right_label:
                    errors.append(
                        ["link_corner_component", component_id, corner, left_label, right_label]
                    )
                link_partition[(cell, left_label)].add(corner)
        link_partition_checks += 1
        if sorted(map(sorted, uf_partition.values())) != sorted(
            map(sorted, link_partition.values())
        ):
            errors.append(["normalized_link_partition", component_id])

        opposite = [set() for _ in range(vertex_count)]
        surface_edge_multiplicity = Counter()
        for colour, alpha in enumerate(alphas):
            role = OPPOSITE_ROLE[colour]
            edge_roles = tuple(sorted(set(range(3)) - {role}))
            for flag in component:
                neighbor = alpha[flag]
                if flag > neighbor:
                    continue
                left = corner_vertex[3 * local[flag] + role]
                right = corner_vertex[3 * local[neighbor] + role]
                opposite[left].add(right)
                opposite[right].add(left)
                edge_vertices = tuple(
                    sorted(
                        corner_vertex[3 * local[flag] + edge_role]
                        for edge_role in edge_roles
                    )
                )
                if len(set(edge_vertices)) != 2:
                    errors.append(
                        ["collapsed_surface_edge", component_id, colour, flag, edge_vertices]
                    )
                surface_edge_multiplicity[edge_vertices] += 1
                opposite_edge_checks += 1
        opposite_labels, q_value = connected_labels(opposite)

        reference_profile = None
        incidence_rows = []
        coarse_rows = []
        for flag in component:
            vertices = [corner_vertex[3 * local[flag] + role] for role in range(3)]
            if len(set(vertices)) != 3:
                errors.append(["repeated_face_vertex", component_id, flag, vertices])
            profile = tuple(sorted(opposite_labels[vertex] for vertex in vertices))
            if reference_profile is None:
                reference_profile = profile
            face_profile_checks += 1
            if profile != reference_profile:
                errors.append(
                    ["face_opposite_profile", component_id, flag, profile, reference_profile]
                )
            row = 0
            for vertex in vertices:
                row |= 1 << vertex
            incidence_rows.append(row)
            cells = flags[flag]["cells"]
            coarse_rows.append(tuple(sorted(cells)))

        observed_rank = gf2_rank(incidence_rows)
        expected_rank = vertex_count - q_value + 1
        gf2_rank_checks += 1
        if observed_rank != expected_rank:
            errors.append(
                ["gf2_rank", component_id, observed_rank, expected_rank, vertex_count, q_value]
            )

        vertex_face_degree = [0] * vertex_count
        for row in incidence_rows:
            value = row
            while value:
                bit = value & -value
                vertex_face_degree[bit.bit_length() - 1] += 1
                value ^= bit
        normalized_gram = {}
        for left in range(vertex_count):
            for right in range(left, vertex_count):
                observed = sum(
                    bool(row & (1 << left)) and bool(row & (1 << right))
                    for row in incidence_rows
                )
                expected = (
                    vertex_face_degree[left]
                    if left == right
                    else 2 * surface_edge_multiplicity.get((left, right), 0)
                )
                normalized_gram[(left, right)] = observed
                gram_entry_checks += 1
                if observed != expected:
                    errors.append(
                        ["normalized_gram", component_id, left, right, observed, expected]
                    )

        for flag, coarse in zip(component, coarse_rows):
            reconstructed = tuple(
                sorted(
                    next(iter(vertex_cells[corner_vertex[3 * local[flag] + role]]))
                    for role in range(3)
                )
            )
            coarse_factor_checks += 1
            if reconstructed != coarse:
                errors.append(
                    ["coarse_incidence_factor", component_id, flag, reconstructed, coarse]
                )

        support_cells = sorted({cell for cells in coarse_rows for cell in cells})
        vertex_cell = {vertex: next(iter(cells)) for vertex, cells in vertex_cells.items()}
        direct_coarse_gram = Counter()
        for cells in coarse_rows:
            for left_index, left_cell in enumerate(cells):
                for right_cell in cells[left_index:]:
                    direct_coarse_gram[(left_cell, right_cell)] += 1
        aggregated_coarse_gram = Counter()
        for (left_vertex, right_vertex), value in normalized_gram.items():
            left_cell = vertex_cell[left_vertex]
            right_cell = vertex_cell[right_vertex]
            cell_pair = tuple(sorted((left_cell, right_cell)))
            aggregated_coarse_gram[cell_pair] += (
                2 * value
                if left_vertex != right_vertex and left_cell == right_cell
                else value
            )
        for left_index, left_cell in enumerate(support_cells):
            for right_cell in support_cells[left_index:]:
                cell_pair = (left_cell, right_cell)
                direct = direct_coarse_gram[cell_pair]
                aggregated = aggregated_coarse_gram[cell_pair]
                gram_aggregation_checks += 1
                if direct != aggregated:
                    errors.append(
                        [
                            "gram_aggregation",
                            component_id,
                            left_cell,
                            right_cell,
                            direct,
                            aggregated,
                        ]
                    )

        exact_masks = [
            mask
            for mask in range(8)
            if C94["HOL"]["exact_mask_on_component"](component, alphas, mask)
        ]
        dimension_zero = exact_masks == [0]
        component_count_by_q[q_value] += 1
        if dimension_zero:
            dimension_zero_count_by_q[q_value] += 1
        normalized_vertex_distribution[vertex_count] += 1
        opposite_component_distribution[q_value] += 1
        rank_distribution[observed_rank] += 1
        if q_value > 1:
            nontrivial_q_components.append(
                {
                    "component_id": component_id,
                    "flag_count": len(component),
                    "normalized_vertex_count": vertex_count,
                    "q": q_value,
                    "rank": observed_rank,
                    "nullity": vertex_count - observed_rank,
                    "dimension_zero": dimension_zero,
                    "support_cell_count": len(support_cells),
                    "face_component_profile": list(reference_profile),
                }
            )

    return {
        "source_index": source_index,
        "order": n,
        "component_count": len(components),
        "flag_count": len(flags),
        "normalized_vertex_checks": normalized_vertex_checks,
        "link_partition_checks": link_partition_checks,
        "opposite_edge_checks": opposite_edge_checks,
        "face_profile_checks": face_profile_checks,
        "gf2_rank_checks": gf2_rank_checks,
        "gram_entry_checks": gram_entry_checks,
        "coarse_factor_checks": coarse_factor_checks,
        "gram_aggregation_checks": gram_aggregation_checks,
        "component_count_by_q": dict(sorted(component_count_by_q.items())),
        "dimension_zero_count_by_q": dict(sorted(dimension_zero_count_by_q.items())),
        "normalized_vertex_distribution": dict(sorted(normalized_vertex_distribution.items())),
        "opposite_component_distribution": dict(sorted(opposite_component_distribution.items())),
        "rank_distribution": dict(sorted(rank_distribution.items())),
        "nontrivial_q_components": nontrivial_q_components,
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    count_keys = (
        "component_count",
        "flag_count",
        "normalized_vertex_checks",
        "link_partition_checks",
        "opposite_edge_checks",
        "face_profile_checks",
        "gf2_rank_checks",
        "gram_entry_checks",
        "coarse_factor_checks",
        "gram_aggregation_checks",
    )
    counters = {key: Counter() for key in (
        "component_count_by_q",
        "dimension_zero_count_by_q",
        "normalized_vertex_distribution",
        "opposite_component_distribution",
        "rank_distribution",
    )}
    errors = []
    nontrivial_q_components = []
    for record in records:
        for key, counter in counters.items():
            counter.update(record[key])
        errors.extend([record["source_index"], error] for error in record["errors"])
        nontrivial_q_components.extend(
            {"source_index": record["source_index"], **component}
            for component in record["nontrivial_q_components"]
        )
    return {
        "name": name,
        "table_count": len(records),
        **{key: sum(record[key] for record in records) for key in count_keys},
        **{key: dict(sorted(counter.items())) for key, counter in counters.items()},
        "nontrivial_q_component_count": len(nontrivial_q_components),
        "nontrivial_q_components": nontrivial_q_components,
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
        "order4_complete": summarize("order4_complete", [analyze_table(table, index) for index, table in enumerate(SMALL["reduced_latin_squares"](4), 1)]),
        "order6_complete": summarize("order6_complete", [analyze_table(table, index) for index, table in enumerate(SMALL["reduced_latin_squares"](6), 1)]),
        "order8_fff_complete": summarize("order8_fff_complete", [analyze_table(table, index) for index, table in load_n8(args.fff_metadata)]),
        "order10_tracked_partial": summarize("order10_tracked_partial", [analyze_table(table, index) for index, table, _ in PAIR["FLAG"]["n10_tables"](args.n10_corpus)]),
    }
    total_keys = (
        "table_count", "component_count", "flag_count", "normalized_vertex_checks",
        "link_partition_checks", "opposite_edge_checks", "face_profile_checks",
        "gf2_rank_checks", "gram_entry_checks", "coarse_factor_checks",
        "gram_aggregation_checks", "error_count",
    )
    totals = {key: sum(dataset[key] for dataset in datasets.values()) for key in total_keys}
    payload = {
        "audit_version": "normalized_cell_rank_v1",
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C96 is rigorous and exactly audited.",
            "The rank formula is componentwise and does not decide order 10.",
            "The tracked order-10 corpus is diagnostic only.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Normalized cell-incidence rank audit", ""]
    lines.extend(f"{key.replace('_', ' ')}: {totals[key]}" for key in total_keys)
    lines.append("")
    for name, dataset in datasets.items():
        lines.extend([
            name,
            f"- tables/components/flags: {dataset['table_count']} / {dataset['component_count']} / {dataset['flag_count']}",
            f"- vertices/link partitions/opposite edges/face profiles: {dataset['normalized_vertex_checks']} / {dataset['link_partition_checks']} / {dataset['opposite_edge_checks']} / {dataset['face_profile_checks']}",
            f"- GF2 ranks / Gram / coarse-factor / Gram-aggregation checks: {dataset['gf2_rank_checks']} / {dataset['gram_entry_checks']} / {dataset['coarse_factor_checks']} / {dataset['gram_aggregation_checks']}",
            f"- q distribution: {dataset['component_count_by_q']}",
            f"- dimension-zero q distribution: {dataset['dimension_zero_count_by_q']}",
            f"- nontrivial-q components: {dataset['nontrivial_q_component_count']}",
            f"- errors: {dataset['error_count']}",
            "",
        ])
    lines.extend([
        "Boundary:",
        "- C96 is rigorous and exactly audited.",
        "- It is a normalized-cell Gram/rank lift, not an order-10 decision.",
        "- C38 remains open and C40 absent.",
    ])
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"])


if __name__ == "__main__":
    raise SystemExit(main())
