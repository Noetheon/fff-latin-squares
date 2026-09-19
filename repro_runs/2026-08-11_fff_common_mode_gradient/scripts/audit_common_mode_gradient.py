#!/usr/bin/env python3
"""Audit the C98 gradient characterization of C97 common face modes."""

from __future__ import annotations

import argparse
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
C97 = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_joint_atom_cell_rank/scripts/"
        "audit_joint_atom_cell_rank.py"
    )
)
SURFACE = C97["SURFACE"]
SMALL = C97["SMALL"]
PAIR = C97["PAIR"]
PRIMES = C97["PRIMES"]
OPPOSITE_ROLE = C97["OPPOSITE_ROLE"]
rank_mod = C97["rank_mod"]
normalized_vertices = C97["normalized_vertices"]
exact_integer_intersection_witnesses = C97[
    "exact_integer_intersection_witnesses"
]


def component_labels(adjacency: list[set[int]]) -> tuple[list[int], int]:
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


def exceptional_lookup(c97_payload: dict, dataset_name: str) -> dict:
    return {
        (entry["source_index"], entry["component_id"]): entry
        for entry in c97_payload["datasets"][dataset_name]["exceptional_components"]
    }


def table_streams(fff_metadata: Path, n10_corpus: Path):
    yield "order4_complete", (
        (index, table)
        for index, table in enumerate(SMALL["reduced_latin_squares"](4), 1)
    )
    yield "order6_complete", (
        (index, table)
        for index, table in enumerate(SMALL["reduced_latin_squares"](6), 1)
    )
    yield "order8_fff_complete", C97["load_n8"](fff_metadata)
    yield "order10_tracked_partial", (
        (index, table)
        for index, table, _ in PAIR["FLAG"]["n10_tables"](n10_corpus)
    )


def add_coefficient(row: list[int], index: int, value: int) -> None:
    row[index] += value


def matrix_rows(flags, component, atom_ids, potential_count, edge_records, mode):
    atom_index = {atom: index for index, atom in enumerate(atom_ids)}
    rows = []
    for edge in edge_records:
        row = [0] * (len(atom_ids) + potential_count)
        add_coefficient(row, atom_index[edge["atom_left"]], 1)
        add_coefficient(row, atom_index[edge["atom_right"]], -1)
        left = edge[f"{mode}_left"]
        right = edge[f"{mode}_right"]
        add_coefficient(row, len(atom_ids) + left, -1)
        add_coefficient(row, len(atom_ids) + right, 1)
        rows.append(row)
    return rows


def transition_component_count(atom_ids, edge_records) -> int:
    atom_index = {atom: index for index, atom in enumerate(atom_ids)}
    adjacency = [set() for _ in atom_ids]
    for edge in edge_records:
        left = atom_index[edge["atom_left"]]
        right = atom_index[edge["atom_right"]]
        adjacency[left].add(right)
        adjacency[right].add(left)
    return component_labels(adjacency)[1]


def verify_witness_gradients(witnesses, edge_records, atom_ids, mode) -> int:
    atom_index = {atom: index for index, atom in enumerate(atom_ids)}
    check_count = 0
    for witness in witnesses:
        atom_vector = witness["atom_vector"]
        potential = witness["cell_vector"]
        for edge in edge_records:
            left_atom = atom_vector[atom_index[edge["atom_left"]]]
            right_atom = atom_vector[atom_index[edge["atom_right"]]]
            left_potential = potential[edge[f"{mode}_left"]]
            right_potential = potential[edge[f"{mode}_right"]]
            if left_atom - right_atom != left_potential - right_potential:
                raise ValueError(
                    f"{mode} witness gradient failure on edge {edge['edge_id']}"
                )
            check_count += 1
    return check_count


def analyze_component(
    flags,
    alphas,
    component,
    component_id,
    source_index,
    c97_exception,
):
    local, corner_vertex, vertex_count = normalized_vertices(
        component, flags, alphas
    )
    vertex_cell = [-1] * vertex_count
    errors = []
    for flag in component:
        for role in range(3):
            vertex = corner_vertex[3 * local[flag] + role]
            cell = flags[flag]["cells"][role]
            if vertex_cell[vertex] not in (-1, cell):
                errors.append(
                    ["normalized_vertex_cell_conflict", component_id, vertex]
                )
            vertex_cell[vertex] = cell

    atom_ids = sorted({atom for flag in component for atom in flags[flag]["atoms"]})
    cell_ids = sorted({cell for flag in component for cell in flags[flag]["cells"]})
    cell_index = {cell: index for index, cell in enumerate(cell_ids)}
    normalized_adjacency = [set() for _ in range(vertex_count)]
    coarse_adjacency = [set() for _ in cell_ids]
    transition_adjacency = [set() for _ in atom_ids]
    atom_index = {atom: index for index, atom in enumerate(atom_ids)}
    edge_records = []

    for colour, alpha in enumerate(alphas):
        role = OPPOSITE_ROLE[colour]
        for flag in component:
            neighbor = alpha[flag]
            if flag > neighbor:
                continue
            atom_left = flags[flag]["atoms"][colour]
            atom_right = flags[neighbor]["atoms"][colour]
            norm_left = corner_vertex[3 * local[flag] + role]
            norm_right = corner_vertex[3 * local[neighbor] + role]
            coarse_left = cell_index[flags[flag]["cells"][role]]
            coarse_right = cell_index[flags[neighbor]["cells"][role]]
            normalized_adjacency[norm_left].add(norm_right)
            normalized_adjacency[norm_right].add(norm_left)
            coarse_adjacency[coarse_left].add(coarse_right)
            coarse_adjacency[coarse_right].add(coarse_left)
            transition_adjacency[atom_index[atom_left]].add(atom_index[atom_right])
            transition_adjacency[atom_index[atom_right]].add(atom_index[atom_left])
            edge_records.append(
                {
                    "edge_id": len(edge_records),
                    "colour": colour,
                    "atom_left": atom_left,
                    "atom_right": atom_right,
                    "norm_left": norm_left,
                    "norm_right": norm_right,
                    "coarse_left": coarse_left,
                    "coarse_right": coarse_right,
                }
            )

    normalized_labels, q_value = component_labels(normalized_adjacency)
    coarse_labels, p_value = component_labels(coarse_adjacency)
    if p_value > q_value:
        errors.append(["coarse_component_count_exceeds_normalized", p_value, q_value])
    projection = defaultdict(set)
    for vertex, cell in enumerate(vertex_cell):
        projection[normalized_labels[vertex]].add(coarse_labels[cell_index[cell]])
    if any(len(targets) != 1 for targets in projection.values()):
        errors.append(["opposite_graph_projection_not_componentwise", component_id])
    if set().union(*projection.values()) != set(range(p_value)):
        errors.append(["opposite_graph_projection_not_surjective", component_id])

    b_rows_bits = []
    for flag in component:
        bits = 0
        for cell in flags[flag]["cells"]:
            bits |= 1 << cell_index[cell]
        b_rows_bits.append(bits)
    observed_b_rank = C97["C96"]["gf2_rank"](b_rows_bits)
    expected_b_rank = len(cell_ids) - p_value + 1
    if observed_b_rank != expected_b_rank:
        errors.append(
            ["coarse_incidence_rank", component_id, observed_b_rank, expected_b_rank]
        )

    transition_count = component_labels(transition_adjacency)[1]
    if transition_count != 3:
        errors.append(
            ["atom_transition_component_count", component_id, transition_count, 3]
        )
    atom_gradient_rank = len(atom_ids) - transition_count
    normalized_rows = matrix_rows(
        flags, component, atom_ids, vertex_count, edge_records, "norm"
    )
    coarse_rows = matrix_rows(
        flags, component, atom_ids, len(cell_ids), edge_records, "coarse"
    )
    norm_s_by_prime = {}
    coarse_t_by_prime = {}
    for prime in PRIMES:
        norm_rank = rank_mod(normalized_rows, prime)
        coarse_rank = rank_mod(coarse_rows, prime)
        norm_solution_dimension = vertex_count - norm_rank + atom_gradient_rank
        coarse_solution_dimension = len(cell_ids) - coarse_rank + atom_gradient_rank
        norm_s_by_prime[str(prime)] = norm_solution_dimension - (q_value - 1)
        coarse_t_by_prime[str(prime)] = coarse_solution_dimension - (p_value - 1)

    s_value = c97_exception["s_Q"] if c97_exception else 1
    if any(value != s_value for value in norm_s_by_prime.values()):
        errors.append(
            ["normalized_gradient_dimension", component_id, norm_s_by_prime, s_value]
        )

    coarse_witnesses = []
    if s_value == 1:
        t_value = 1
    else:
        atom_rows = []
        cell_rows = []
        joint_rows = []
        for flag in component:
            atom_row = [0] * len(atom_ids)
            cell_row = [0] * len(cell_ids)
            for atom in flags[flag]["atoms"]:
                atom_row[atom_index[atom]] = 1
            for cell in flags[flag]["cells"]:
                cell_row[cell_index[cell]] = 1
            atom_rows.append(atom_row)
            cell_rows.append(cell_row)
            joint_rows.append(atom_row + cell_row)
        upper_bounds = {
            str(prime): (
                len(atom_ids)
                - 2
                + expected_b_rank
                - rank_mod(joint_rows, prime)
            )
            for prime in PRIMES
        }
        if len(set(upper_bounds.values())) != 1:
            errors.append(["coarse_upper_bound_prime_disagreement", upper_bounds])
        t_upper = upper_bounds[str(PRIMES[0])]
        coarse_witnesses = exact_integer_intersection_witnesses(
            atom_rows, cell_rows, t_upper
        )
        if t_upper != 1 and len(coarse_witnesses) != t_upper - 1:
            errors.append(
                [
                    "coarse_rational_intersection_not_certified",
                    component_id,
                    t_upper,
                    len(coarse_witnesses),
                ]
            )
        t_value = t_upper

    if any(value != t_value for value in coarse_t_by_prime.values()):
        errors.append(
            ["coarse_gradient_dimension", component_id, coarse_t_by_prime, t_value]
        )
    eta_value = s_value - t_value
    eta_bound = vertex_count - len(cell_ids) - q_value + p_value
    if eta_value < 0 or eta_value > eta_bound:
        errors.append(["sheet_excess_bound", component_id, eta_value, eta_bound])

    normalized_witness_checks = 0
    if c97_exception:
        try:
            normalized_witness_checks = verify_witness_gradients(
                c97_exception["integer_witnesses"],
                edge_records,
                atom_ids,
                "norm",
            )
        except ValueError as error:
            errors.append(["normalized_witness_gradient", component_id, str(error)])
    coarse_witness_checks = 0
    try:
        coarse_witness_checks = verify_witness_gradients(
            coarse_witnesses, edge_records, atom_ids, "coarse"
        )
    except ValueError as error:
        errors.append(["coarse_witness_gradient", component_id, str(error)])

    return {
        "component_id": component_id,
        "flag_count": len(component),
        "atom_count": len(atom_ids),
        "coarse_cell_count": len(cell_ids),
        "normalized_vertex_count": vertex_count,
        "transition_graph_component_count": transition_count,
        "dual_edge_count": len(edge_records),
        "p_coarse": p_value,
        "q_normalized": q_value,
        "coarse_incidence_rank_GF2": observed_b_rank,
        "normalized_gradient_s_by_prime": norm_s_by_prime,
        "coarse_gradient_t_by_prime": coarse_t_by_prime,
        "s_Q": s_value,
        "t_Q": t_value,
        "eta_Q": eta_value,
        "eta_upper_bound": eta_bound,
        "coarse_integer_witness_count": len(coarse_witnesses),
        "normalized_witness_gradient_check_count": normalized_witness_checks,
        "coarse_witness_gradient_check_count": coarse_witness_checks,
        "errors": errors,
    }


def summarize_dataset(name, table_stream, exceptions):
    records = []
    table_count = 0
    flag_count = 0
    for source_index, table in table_stream:
        table_count += 1
        atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
        flags = SURFACE["build_flags"](table, point_to_atom)
        alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
        adjacency = [set() for _ in flags]
        for alpha in alphas:
            for flag, neighbor in enumerate(alpha):
                adjacency[flag].add(neighbor)
        components = SURFACE["connected_components"](adjacency)
        flag_count += len(flags)
        if bad_groups:
            records.append(
                {
                    "source_index": source_index,
                    "component_id": None,
                    "errors": [["dual_edge_groups", bad_groups]],
                }
            )
        for component_id, component in enumerate(components):
            record = analyze_component(
                flags,
                alphas,
                component,
                component_id,
                source_index,
                exceptions.get((source_index, component_id)),
            )
            record["source_index"] = source_index
            records.append(record)

    valid = [record for record in records if record.get("component_id") is not None]
    errors = [
        [record["source_index"], record.get("component_id"), error]
        for record in records
        for error in record["errors"]
    ]
    s_distribution = Counter(record["s_Q"] for record in valid)
    t_distribution = Counter(record["t_Q"] for record in valid)
    eta_distribution = Counter(record["eta_Q"] for record in valid)
    pq_distribution = Counter(
        (record["p_coarse"], record["q_normalized"]) for record in valid
    )
    sheet_only = [record for record in valid if record["eta_Q"] > 0]
    return {
        "name": name,
        "table_count": table_count,
        "component_count": len(valid),
        "flag_count": flag_count,
        "dual_edge_count": sum(record["dual_edge_count"] for record in valid),
        "s_Q_distribution": {str(k): v for k, v in sorted(s_distribution.items())},
        "t_Q_distribution": {str(k): v for k, v in sorted(t_distribution.items())},
        "eta_Q_distribution": {str(k): v for k, v in sorted(eta_distribution.items())},
        "p_q_distribution": {
            f"{p},{q}": value for (p, q), value in sorted(pq_distribution.items())
        },
        "p_equals_q_count": sum(
            record["p_coarse"] == record["q_normalized"] for record in valid
        ),
        "coarse_integer_witness_count": sum(
            record["coarse_integer_witness_count"] for record in valid
        ),
        "normalized_witness_gradient_check_count": sum(
            record["normalized_witness_gradient_check_count"] for record in valid
        ),
        "coarse_witness_gradient_check_count": sum(
            record["coarse_witness_gradient_check_count"] for record in valid
        ),
        "sheet_only_component_count": len(sheet_only),
        "sheet_only_components": sheet_only,
        "error_count": len(errors),
        "errors": errors[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c97-audit", type=Path, required=True)
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    c97_payload = json.loads(args.c97_audit.read_text())
    if c97_payload["totals"]["error_count"]:
        raise ValueError("C97 input contains certification errors")
    datasets = {}
    for name, stream in table_streams(args.fff_metadata, args.n10_corpus):
        datasets[name] = summarize_dataset(
            name, stream, exceptional_lookup(c97_payload, name)
        )

    totals = {
        "table_count": sum(data["table_count"] for data in datasets.values()),
        "component_count": sum(data["component_count"] for data in datasets.values()),
        "flag_count": sum(data["flag_count"] for data in datasets.values()),
        "dual_edge_count": sum(data["dual_edge_count"] for data in datasets.values()),
        "coarse_integer_witness_count": sum(
            data["coarse_integer_witness_count"] for data in datasets.values()
        ),
        "normalized_witness_gradient_check_count": sum(
            data["normalized_witness_gradient_check_count"]
            for data in datasets.values()
        ),
        "coarse_witness_gradient_check_count": sum(
            data["coarse_witness_gradient_check_count"]
            for data in datasets.values()
        ),
        "sheet_only_component_count": sum(
            data["sheet_only_component_count"] for data in datasets.values()
        ),
        "error_count": sum(data["error_count"] for data in datasets.values()),
    }
    payload = {
        "audit_version": "common_mode_gradient_v1",
        "prime_fields": list(PRIMES),
        "c97_input": str(args.c97_audit),
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C98 is a rigorous gradient/cycle characterization with exact corpus sanity checks.",
            "The finite equality p_F=q_F is observed, not asserted universally.",
            (
                f"The observed {totals['sheet_only_component_count']} sheet-only "
                "component(s) are not a universal classification."
            ),
            "The tracked order-10 corpus is partial; C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = ["Common-mode gradient audit", ""]
    lines.extend(f"{key.replace('_', ' ')}: {value}" for key, value in totals.items())
    lines.append("")
    for name, data in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components/flags: {data['table_count']} / {data['component_count']} / {data['flag_count']}",
                f"- s_Q distribution: {data['s_Q_distribution']}",
                f"- coarse t_Q distribution: {data['t_Q_distribution']}",
                f"- sheet eta_Q distribution: {data['eta_Q_distribution']}",
                f"- (p,q) distribution: {data['p_q_distribution']}",
                f"- p=q components: {data['p_equals_q_count']} / {data['component_count']}",
                f"- coarse integer witnesses: {data['coarse_integer_witness_count']}",
                f"- sheet-only components: {data['sheet_only_component_count']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- Gradient characterization is rigorous; distributions are frozen-corpus facts.",
            (
                f"- p_F=q_F and the observed {totals['sheet_only_component_count']} "
                "sheet-only component(s) are not universal claims."
            ),
            "- This does not decide order 10; C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 1 if totals["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
