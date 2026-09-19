#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import itertools
import json
import math
from pathlib import Path

from sympy import Matrix, ZZ
from sympy.matrices.normalforms import hermite_normal_form, smith_normal_form
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.normalforms import smith_normal_decomp


ROOT = Path(__file__).resolve().parents[3]
SMALL_PATH = (
    ROOT
    / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SMALL = load_module("small_order_trade_lattice", SMALL_PATH)


def line_profile(table: tuple[tuple[int, ...], ...], cells: tuple[int, ...]):
    n = len(table)
    profile = [0] * (3 * n)
    mask = 0
    for cell in cells:
        row, col = divmod(cell, n)
        symbol = table[row][col]
        profile[row] += 1
        profile[n + col] += 1
        profile[2 * n + symbol] += 1
        mask |= 1 << cell
    return tuple(profile), mask


def balanced_exchange_vectors(table, half_size: int) -> list[list[int]]:
    n = len(table)
    groups: dict[tuple[int, ...], list[tuple[int, tuple[int, ...]]]] = {}
    for cells in itertools.combinations(range(n * n), half_size):
        profile, mask = line_profile(table, cells)
        groups.setdefault(profile, []).append((mask, cells))

    vectors = []
    for group in groups.values():
        for left_index in range(len(group)):
            left_mask, left_cells = group[left_index]
            for right_index in range(left_index + 1, len(group)):
                right_mask, right_cells = group[right_index]
                if left_mask & right_mask:
                    continue
                vector = [0] * (n * n)
                for cell in left_cells:
                    vector[cell] = 1
                for cell in right_cells:
                    vector[cell] = -1
                if next(value for value in vector if value) < 0:
                    vector = [-value for value in vector]
                vectors.append(vector)
    vectors.sort()
    return vectors


def line_incidence(table) -> Matrix:
    n = len(table)
    rows = []
    for kind in range(3):
        for line in range(n):
            row = []
            for cell in range(n * n):
                r, c = divmod(cell, n)
                row.append(int((r, c, table[r][c])[kind] == line))
            rows.append(row)
    return Matrix(rows)


def primitive_centered(witness: dict, n: int) -> list[int]:
    vector = [
        n * value - witness["common_line_sum"]
        for value in witness["cell_vector"]
    ]
    divisor = 0
    for value in vector:
        divisor = math.gcd(divisor, abs(value))
    if divisor == 0:
        raise ValueError("constant witness supplied as nonconstant")
    if next(value for value in vector if value) < 0:
        divisor = -divisor
    return [value // divisor for value in vector]


def nonzero_smith_diagonal(matrix: Matrix) -> list[int]:
    smith = smith_normal_form(matrix, domain=ZZ)
    return [
        abs(int(smith[index, index]))
        for index in range(min(smith.shape))
        if smith[index, index]
    ]


def kernel_coordinates(incidence: Matrix):
    domain_matrix = DomainMatrix.from_Matrix(incidence, fmt="dense").convert_to(ZZ)
    diagonal, _, right = smith_normal_decomp(domain_matrix)
    diagonal_matrix = diagonal.to_Matrix()
    right_matrix = right.to_Matrix()
    rank = sum(
        diagonal_matrix[index, index] != 0
        for index in range(min(diagonal_matrix.shape))
    )
    kernel_basis = right_matrix[:, rank:]
    if incidence * kernel_basis != Matrix.zeros(incidence.rows, kernel_basis.cols):
        raise ValueError("Smith kernel basis does not annihilate incidence")
    return rank, right_matrix.inv(), nonzero_smith_diagonal(diagonal_matrix)


def lattice_status(coordinates: Matrix, basis_hnf: Matrix, vector: Matrix) -> dict:
    augmented = hermite_normal_form(coordinates.row_join(vector))
    same_rank = augmented.cols == basis_hnf.cols
    in_lattice = augmented == basis_hnf
    quotient_order = None
    if same_rank:
        coefficients = basis_hnf.gauss_jordan_solve(vector)[0]
        quotient_order = 1
        for value in coefficients:
            quotient_order = math.lcm(quotient_order, int(value.q))
    full_index = (
        abs(int(augmented.det())) if augmented.rows == augmented.cols else None
    )
    return {
        "in_lattice": in_lattice,
        "in_rational_span": same_rank,
        "quotient_order": quotient_order,
        "augmented_full_index": full_index,
    }


def modular_basis(vectors: list[list[int]], prime: int = 1_000_003):
    basis: dict[int, list[int]] = {}

    def independent(vector: list[int], commit: bool) -> bool:
        reduced = [value % prime for value in vector]
        while True:
            pivot = next((i for i, value in enumerate(reduced) if value), None)
            if pivot is None:
                return False
            if pivot not in basis:
                if commit:
                    inverse = pow(reduced[pivot], prime - 2, prime)
                    basis[pivot] = [(value * inverse) % prime for value in reduced]
                return True
            multiplier = reduced[pivot]
            reduced = [
                (value - multiplier * base) % prime
                for value, base in zip(reduced, basis[pivot])
            ]

    for vector in vectors:
        independent(vector, True)
    return basis, independent


def find_six_exchange(table, four_vectors: list[list[int]]):
    n = len(table)
    _, independent = modular_basis(four_vectors)
    halves: dict[tuple[int, ...], list[tuple[int, tuple[int, ...]]]] = {}
    for rows in itertools.product(range(n), repeat=n):
        if len({table[rows[col]][col] for col in range(n)}) != n:
            continue
        profile = tuple(rows.count(row) for row in range(n))
        mask = sum(1 << (n * rows[col] + col) for col in range(n))
        halves.setdefault(profile, []).append((mask, rows))

    searched = 0
    for profile in sorted(halves):
        group = sorted(halves[profile])
        for left_index in range(len(group)):
            left_mask, left_rows = group[left_index]
            for right_index in range(left_index + 1, len(group)):
                right_mask, right_rows = group[right_index]
                if left_mask & right_mask:
                    continue
                searched += 1
                vector = [0] * (n * n)
                for col, row in enumerate(left_rows):
                    vector[n * row + col] = 1
                for col, row in enumerate(right_rows):
                    vector[n * row + col] = -1
                if independent(vector, False):
                    return vector, searched
    return None, searched


def analyze_task(task):
    source_index, table, c99_record = task
    n = len(table)
    errors = []
    incidence = line_incidence(table)
    incidence_rank, inverse_right, incidence_snf = kernel_coordinates(incidence)
    if incidence_rank != 3 * n - 2:
        errors.append(["line_incidence_rank", incidence_rank, 3 * n - 2])

    exchanges3 = balanced_exchange_vectors(table, 3)
    exchanges4 = balanced_exchange_vectors(table, 4)
    matrix4 = Matrix.hstack(*(Matrix(vector) for vector in exchanges4))
    coordinates4 = (inverse_right * matrix4)[incidence_rank:, :]
    hnf4 = hermite_normal_form(coordinates4)
    elementary_snf = nonzero_smith_diagonal(hnf4)
    elementary_rank = hnf4.cols
    saturation_index = math.prod(elementary_snf)

    matrix3 = Matrix.hstack(*(Matrix(vector) for vector in exchanges3))
    coordinates3 = (inverse_right * matrix3)[incidence_rank:, :]
    hnf34 = hermite_normal_form(coordinates4.row_join(coordinates3))
    all_three_in_four_lattice = hnf34 == hnf4
    if not all_three_in_four_lattice:
        errors.append(["three_exchange_not_in_four_lattice"])
    if saturation_index != 1:
        errors.append(["elementary_lattice_not_saturated", saturation_index])

    r_value = c99_record["r_Q"] if c99_record else 1
    mode_vectors = (
        [primitive_centered(witness, n) for witness in c99_record["integer_witnesses"]]
        if c99_record
        else []
    )
    mode_records = []
    mode_coordinates = []
    for vector in mode_vectors:
        column = Matrix(vector)
        if incidence * column != Matrix.zeros(incidence.rows, 1):
            errors.append(["centered_mode_not_in_trade_lattice"])
        coordinates = (inverse_right * column)[incidence_rank:, :]
        mode_coordinates.append(coordinates)
        mode_records.append(
            {
                "shape": {
                    str(value): vector.count(value) for value in sorted(set(vector))
                },
                **lattice_status(coordinates4, hnf4, coordinates),
            }
        )

    common_mode_augmented_index = None
    if mode_coordinates:
        combined = coordinates4.row_join(Matrix.hstack(*mode_coordinates))
        combined_hnf = hermite_normal_form(combined)
        if combined_hnf.rows == combined_hnf.cols:
            common_mode_augmented_index = abs(int(combined_hnf.det()))

    six_exchange = None
    if r_value == 3 and elementary_rank == 19:
        candidate, searched = find_six_exchange(table, exchanges4)
        if candidate is None:
            errors.append(["missing_six_exchange_completion"])
        else:
            candidate_column = Matrix(candidate)
            candidate_coordinates = (inverse_right * candidate_column)[
                incidence_rank:, :
            ]
            completed_hnf = hermite_normal_form(
                coordinates4.row_join(candidate_coordinates)
            )
            completed_index = (
                abs(int(completed_hnf.det()))
                if completed_hnf.rows == completed_hnf.cols
                else None
            )
            if completed_hnf.cols != (n - 1) * (n - 2) or completed_index != 1:
                errors.append(
                    ["six_exchange_does_not_complete", completed_hnf.cols, completed_index]
                )
            six_exchange = {
                "vector": candidate,
                "positive_cells": [i for i, value in enumerate(candidate) if value == 1],
                "negative_cells": [i for i, value in enumerate(candidate) if value == -1],
                "candidate_pairs_searched": searched,
                "completed_rank": completed_hnf.cols,
                "completed_index": completed_index,
            }

    return {
        "source_index": source_index,
        "order": n,
        "r_Q": r_value,
        "line_incidence_rank": incidence_rank,
        "line_incidence_snf": incidence_snf,
        "three_exchange_count": len(exchanges3),
        "four_exchange_count": len(exchanges4),
        "three_exchange_lattice_contained_in_four": all_three_in_four_lattice,
        "elementary_rank": elementary_rank,
        "elementary_snf": elementary_snf,
        "elementary_saturation_index": saturation_index,
        "common_mode_count": len(mode_records),
        "common_modes": mode_records,
        "common_mode_augmented_index": common_mode_augmented_index,
        "six_exchange_completion": six_exchange,
        "error_count": len(errors),
        "errors": errors,
    }


def count_map(counter: Counter) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items())}


def summarize(records: list[dict]) -> dict:
    rank_by_r = Counter((record["r_Q"], record["elementary_rank"]) for record in records)
    mode_status = Counter()
    quotient_pairs = Counter()
    for record in records:
        for mode in record["common_modes"]:
            mode_status[
                (
                    record["r_Q"],
                    record["elementary_rank"],
                    mode["in_lattice"],
                    mode["in_rational_span"],
                    mode["augmented_full_index"],
                )
            ] += 1
        if record["r_Q"] == 3 and record["elementary_rank"] == 19:
            quotient_pairs[
                tuple(
                    sorted(
                        mode["augmented_full_index"]
                        for mode in record["common_modes"]
                    )
                )
            ] += 1

    return {
        "table_count": len(records),
        "line_incidence_rank_distribution": count_map(
            Counter(record["line_incidence_rank"] for record in records)
        ),
        "three_exchange_count_distribution": count_map(
            Counter(record["three_exchange_count"] for record in records)
        ),
        "four_exchange_count_distribution": count_map(
            Counter(record["four_exchange_count"] for record in records)
        ),
        "elementary_rank_distribution": count_map(
            Counter(record["elementary_rank"] for record in records)
        ),
        "elementary_rank_by_r_Q": {
            f"r={r_value},rank={rank}": count
            for (r_value, rank), count in sorted(rank_by_r.items())
        },
        "saturated_table_count": sum(
            record["elementary_saturation_index"] == 1 for record in records
        ),
        "three_exchange_containment_count": sum(
            record["three_exchange_lattice_contained_in_four"] for record in records
        ),
        "common_mode_status_distribution": {
            str(key): value for key, value in sorted(mode_status.items())
        },
        "rank19_r3_mode_index_pair_distribution": {
            str(key): value for key, value in sorted(quotient_pairs.items())
        },
        "rank19_r3_table_count": sum(
            record["r_Q"] == 3 and record["elementary_rank"] == 19
            for record in records
        ),
        "six_exchange_completion_count": sum(
            record["six_exchange_completion"] is not None for record in records
        ),
        "common_mode_augmented_index_two_count": sum(
            record["common_mode_augmented_index"] == 2 for record in records
        ),
        "error_count": sum(record["error_count"] for record in records),
    }


def write_summary(path: Path, payload: dict) -> None:
    totals = payload["totals"]
    lines = [
        "Order-6 common-mode trade-lattice audit",
        "",
        f"tables: {totals['table_count']}",
        f"line-incidence ranks: {totals['line_incidence_rank_distribution']}",
        f"E4 ranks: {totals['elementary_rank_distribution']}",
        f"E4 rank by r_Q: {totals['elementary_rank_by_r_Q']}",
        f"E4 saturated: {totals['saturated_table_count']} / {totals['table_count']}",
        f"3+3 lattice contained in E4: {totals['three_exchange_containment_count']} / {totals['table_count']}",
        f"rank-19 r_Q=3 tables: {totals['rank19_r3_table_count']}",
        f"rank-19 r_Q=3 mode index pairs: {totals['rank19_r3_mode_index_pair_distribution']}",
        f"rank-19 r_Q=3 common-mode subgroup index 2: {totals['common_mode_augmented_index_two_count']}",
        f"6+6 primitive completions: {totals['six_exchange_completion_count']}",
        f"errors: {totals['error_count']}",
        "",
        "Boundary:",
        "- The balanced cell-dependency lattice is not the same object as a classical Latin bitrade.",
        "- The rank/index distributions are complete order-6 census facts.",
        "- No order-10 conclusion follows; C38 remains open and C40 is absent.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c99-audit", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    c99 = json.loads(args.c99_audit.read_text())
    exceptional = {
        record["source_index"]: record
        for record in c99["datasets"]["order6_complete"]["exceptional_tables"]
    }
    tasks = [
        (source_index, table, exceptional.get(source_index))
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=2))
    records.sort(key=lambda record: record["source_index"])
    payload = {
        "audit_version": "common_mode_trade_lattice_v1",
        "workers": args.workers,
        "definitions": {
            "T_L": "integer kernel of the occupied-cell row/column/symbol incidence",
            "E4_L": "lattice generated by disjoint balanced 4+4 occupied-cell exchanges",
        },
        "totals": summarize(records),
        "records": records,
        "claim_boundary": [
            "Rigorous general lemmas identify centered C99 modes as balanced occupied-cell dependencies.",
            "The exact lattice distributions are complete order-6 census facts.",
            "Balanced occupied-cell dependencies are not automatically classical Latin bitrades.",
            "C38 remains open and C40 is absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
