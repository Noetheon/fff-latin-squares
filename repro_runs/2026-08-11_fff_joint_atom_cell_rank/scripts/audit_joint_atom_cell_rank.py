#!/usr/bin/env python3
"""Audit the C97 joint atom/normalized-cell incidence rank."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
C96 = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-11_fff_normalized_cell_rank/scripts/"
        "audit_normalized_cell_rank.py"
    )
)
SURFACE = C96["SURFACE"]
SMALL = C96["SMALL"]
PAIR = C96["PAIR"]
UnionFind = C96["UnionFind"]
CORNER_IDENTIFICATIONS = C96["CORNER_IDENTIFICATIONS"]
OPPOSITE_ROLE = C96["OPPOSITE_ROLE"]
connected_labels = C96["connected_labels"]
PRIMES = (1_000_003, 1_000_033)


def rank_mod(rows: list[list[int]], prime: int) -> int:
    matrix = [[value % prime for value in row] for row in rows]
    row_count = len(matrix)
    column_count = len(matrix[0]) if matrix else 0
    rank = 0
    for column in range(column_count):
        pivot = next(
            (index for index in range(rank, row_count) if matrix[index][column]),
            None,
        )
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inverse = pow(matrix[rank][column], prime - 2, prime)
        matrix[rank] = [(value * inverse) % prime for value in matrix[rank]]
        for index in range(rank + 1, row_count):
            factor = matrix[index][column]
            if factor:
                matrix[index] = [
                    (left - factor * right) % prime
                    for left, right in zip(matrix[index], matrix[rank])
                ]
        rank += 1
        if rank == row_count:
            break
    return rank


def nullspace_mod(rows: list[list[int]], prime: int) -> list[list[int]]:
    matrix = [[value % prime for value in row] for row in rows]
    row_count = len(matrix)
    column_count = len(matrix[0]) if matrix else 0
    pivots = []
    rank = 0
    for column in range(column_count):
        pivot = next(
            (index for index in range(rank, row_count) if matrix[index][column]),
            None,
        )
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inverse = pow(matrix[rank][column], prime - 2, prime)
        matrix[rank] = [(value * inverse) % prime for value in matrix[rank]]
        for index in range(row_count):
            if index == rank:
                continue
            factor = matrix[index][column]
            if factor:
                matrix[index] = [
                    (left - factor * right) % prime
                    for left, right in zip(matrix[index], matrix[rank])
                ]
        pivots.append(column)
        rank += 1
        if rank == row_count:
            break
    pivot_set = set(pivots)
    basis = []
    for free in (column for column in range(column_count) if column not in pivot_set):
        vector = [0] * column_count
        vector[free] = 1
        for row, pivot in enumerate(pivots):
            vector[pivot] = (-matrix[row][free]) % prime
        basis.append(vector)
    return basis


def centered(vector: list[int], prime: int) -> list[int]:
    return [value if value <= prime // 2 else value - prime for value in vector]


def independent_rank_integer(vectors: list[list[int]]) -> int:
    if not vectors:
        return 0
    return rank_mod(vectors, PRIMES[0])


def normalized_vertices(component, flags, alphas):
    local = {flag: index for index, flag in enumerate(component)}
    union = UnionFind(3 * len(component))
    for colour, role_pairs in CORNER_IDENTIFICATIONS.items():
        for flag in component:
            neighbor = alphas[colour][flag]
            for left_role, right_role in role_pairs:
                union.union(
                    3 * local[flag] + left_role,
                    3 * local[neighbor] + right_role,
                )
    roots = sorted({union.find(index) for index in range(3 * len(component))})
    root_id = {root: index for index, root in enumerate(roots)}
    corner_vertex = [
        root_id[union.find(index)] for index in range(3 * len(component))
    ]
    return local, corner_vertex, len(roots)


def opposite_component_count(component, local, corner_vertex, vertex_count, alphas):
    adjacency = [set() for _ in range(vertex_count)]
    for colour, alpha in enumerate(alphas):
        role = OPPOSITE_ROLE[colour]
        for flag in component:
            neighbor = alpha[flag]
            if flag > neighbor:
                continue
            left = corner_vertex[3 * local[flag] + role]
            right = corner_vertex[3 * local[neighbor] + role]
            adjacency[left].add(right)
            adjacency[right].add(left)
    return connected_labels(adjacency)[1]


def exact_integer_intersection_witnesses(
    atom_rows: list[list[int]],
    cell_rows: list[list[int]],
    target_dimension: int,
) -> list[dict]:
    if target_dimension <= 1:
        return []
    atom_count = len(atom_rows[0])
    difference_rows = [
        atom + [-value for value in cell]
        for atom, cell in zip(atom_rows, cell_rows)
    ]
    basis = nullspace_mod(difference_rows, PRIMES[0])
    candidate_signals = []
    witnesses = []
    seen_vectors = set()

    def inspect(modular_vector: list[int]) -> None:
        vector = centered(modular_vector, PRIMES[0])
        key = tuple(vector)
        if key in seen_vectors:
            return
        seen_vectors.add(key)
        if max(map(abs, vector), default=0) > 100:
            return
        atom_vector = vector[:atom_count]
        cell_vector = vector[atom_count:]
        atom_signal = [
            sum(value * weight for value, weight in zip(row, atom_vector))
            for row in atom_rows
        ]
        cell_signal = [
            sum(value * weight for value, weight in zip(row, cell_vector))
            for row in cell_rows
        ]
        if atom_signal != cell_signal or not any(atom_signal):
            return
        if len(set(atom_signal)) == 1:
            return
        if independent_rank_integer([[1] * len(atom_signal), *candidate_signals, atom_signal]) == len(candidate_signals) + 2:
            candidate_signals.append(atom_signal)
            witnesses.append(
                {
                    "atom_vector": atom_vector,
                    "cell_vector": cell_vector,
                    "signal_distribution": dict(sorted(Counter(atom_signal).items())),
                }
            )

    for modular_vector in basis:
        inspect(modular_vector)
    for radius in (1, 2, 3):
        if len(candidate_signals) == target_dimension - 1:
            break
        for coefficients in product(range(-radius, radius + 1), repeat=len(basis)):
            if not any(coefficients):
                continue
            inspect(
                [
                    sum(
                        coefficient * basis_vector[index]
                        for coefficient, basis_vector in zip(coefficients, basis)
                    )
                    % PRIMES[0]
                    for index in range(len(basis[0]))
                ]
            )
            if len(candidate_signals) == target_dimension - 1:
                break
    return witnesses


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]
    records = []

    for component_id, component in enumerate(components):
        local, corner_vertex, vertex_count = normalized_vertices(
            component, flags, alphas
        )
        q_value = opposite_component_count(
            component, local, corner_vertex, vertex_count, alphas
        )
        atom_ids = sorted({atom for flag in component for atom in flags[flag]["atoms"]})
        atom_index = {atom: index for index, atom in enumerate(atom_ids)}
        atom_rows = []
        cell_rows = []
        joint_rows = []
        for flag in component:
            atom_row = [0] * len(atom_ids)
            cell_row = [0] * vertex_count
            for atom in flags[flag]["atoms"]:
                atom_row[atom_index[atom]] = 1
            for role in range(3):
                cell_row[corner_vertex[3 * local[flag] + role]] = 1
            atom_rows.append(atom_row)
            cell_rows.append(cell_row)
            joint_rows.append(atom_row + cell_row)

        ranks = {str(prime): rank_mod(joint_rows, prime) for prime in PRIMES}
        if len(set(ranks.values())) != 1:
            errors.append(["odd_prime_rank_disagreement", component_id, ranks])
        joint_rank = ranks[str(PRIMES[0])]
        rank_p = len(atom_ids) - 2
        rank_c = vertex_count - q_value + 1
        s_upper_bound = rank_p + rank_c - joint_rank
        if s_upper_bound < 1:
            errors.append(
                ["missing_constant_intersection_upper_bound", component_id, s_upper_bound]
            )
        witnesses = exact_integer_intersection_witnesses(
            atom_rows, cell_rows, s_upper_bound
        )
        rational_s_certified = (
            s_upper_bound == 1 or len(witnesses) == s_upper_bound - 1
        )
        if not rational_s_certified:
            errors.append(
                [
                    "rational_intersection_not_certified",
                    component_id,
                    s_upper_bound,
                    len(witnesses),
                ]
            )
        observed_nullity = len(atom_ids) + vertex_count - joint_rank
        records.append(
            {
                "component_id": component_id,
                "flag_count": len(component),
                "atom_count": len(atom_ids),
                "normalized_vertex_count": vertex_count,
                "q": q_value,
                "odd_prime_joint_ranks": ranks,
                "s_Q_upper_bound_from_modular_joint_rank": s_upper_bound,
                "s_Q": s_upper_bound if rational_s_certified else None,
                "epsilon_Q": s_upper_bound - 1 if rational_s_certified else None,
                "joint_nullity_Q": observed_nullity if rational_s_certified else None,
                "integer_witnesses": witnesses,
            }
        )
    return {
        "source_index": source_index,
        "order": len(table),
        "component_count": len(records),
        "flag_count": len(flags),
        "components": records,
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    s_distribution = Counter()
    q_s_distribution = Counter()
    shape_distribution = Counter()
    witness_count = 0
    errors = []
    exceptional = []
    for record in records:
        errors.extend([record["source_index"], error] for error in record["errors"])
        for component in record["components"]:
            s_value = component["s_Q"]
            s_key = "uncertified" if s_value is None else str(s_value)
            s_distribution[s_key] += 1
            q_s_distribution[f"{component['q']},{s_key}"] += 1
            shape_distribution[
                ",".join(
                    map(
                        str,
                        (
                            component["flag_count"],
                            component["atom_count"],
                            component["normalized_vertex_count"],
                            component["q"],
                            s_key,
                        ),
                    )
                )
            ] += 1
            witness_count += len(component["integer_witnesses"])
            if s_value and s_value > 1:
                exceptional.append(
                    {"source_index": record["source_index"], **component}
                )
    return {
        "name": name,
        "table_count": len(records),
        "component_count": sum(record["component_count"] for record in records),
        "flag_count": sum(record["flag_count"] for record in records),
        "s_Q_distribution": dict(sorted(s_distribution.items())),
        "q_s_Q_distribution": dict(sorted(q_s_distribution.items())),
        "shape_distribution": dict(sorted(shape_distribution.items())),
        "integer_witness_count": witness_count,
        "exceptional_component_count": len(exceptional),
        "exceptional_components": exceptional,
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
            [
                analyze_table(table, index)
                for index, table, _ in PAIR["FLAG"]["n10_tables"](args.n10_corpus)
            ],
        ),
    }
    totals = {
        "table_count": sum(item["table_count"] for item in datasets.values()),
        "component_count": sum(item["component_count"] for item in datasets.values()),
        "flag_count": sum(item["flag_count"] for item in datasets.values()),
        "integer_witness_count": sum(item["integer_witness_count"] for item in datasets.values()),
        "exceptional_component_count": sum(item["exceptional_component_count"] for item in datasets.values()),
        "error_count": sum(item["error_count"] for item in datasets.values()),
    }
    payload = {
        "audit_version": "joint_atom_cell_rank_v1",
        "prime_fields": list(PRIMES),
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C97 is a rigorous joint-rank identity with exact rational corpus certification.",
            "Finite s_Q distributions are corpus observations only.",
            "The tracked order-10 corpus is diagnostic only.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Joint atom/cell incidence rank audit", ""]
    lines.extend(f"{key.replace('_', ' ')}: {value}" for key, value in totals.items())
    lines.append("")
    for name, dataset in datasets.items():
        lines.extend(
            [
                name,
                f"- tables/components/flags: {dataset['table_count']} / {dataset['component_count']} / {dataset['flag_count']}",
                f"- s_Q distribution: {dataset['s_Q_distribution']}",
                f"- (q,s_Q) distribution: {dataset['q_s_Q_distribution']}",
                f"- integer witnesses / exceptional components: {dataset['integer_witness_count']} / {dataset['exceptional_component_count']}",
                f"- errors: {dataset['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- The joint-rank formula is rigorous; finite distributions are exactly certified corpus facts.",
            "- This does not decide order 10.",
            "- C38 remains open and C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return totals["error_count"]


if __name__ == "__main__":
    raise SystemExit(main())
