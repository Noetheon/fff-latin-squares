#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
import math
from pathlib import Path

from flint import fmpz_mat


ROOT = Path(__file__).resolve().parents[3]
PRIMARY_PATH = (
    ROOT
    / "repro_runs/2026-08-11_fff_common_mode_trade_lattice/scripts/"
    "audit_common_mode_trade_lattice.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRIMARY = load_module("primary_trade_lattice", PRIMARY_PATH)
SMALL = PRIMARY.SMALL


def flint_matrix(rows: list[list[int]], columns: int) -> fmpz_mat:
    if not rows:
        return fmpz_mat(0, columns, [])
    return fmpz_mat(len(rows), columns, [value for row in rows for value in row])


def nonzero_snf(matrix: fmpz_mat) -> list[int]:
    smith = matrix.snf()
    return [
        abs(int(smith[index, index]))
        for index in range(min(smith.nrows(), smith.ncols()))
        if smith[index, index]
    ]


def nonzero_hnf_rows(matrix: fmpz_mat) -> list[tuple[int, ...]]:
    hnf = matrix.hnf()
    rows = []
    for row in range(hnf.nrows()):
        values = tuple(int(hnf[row, col]) for col in range(hnf.ncols()))
        if any(values):
            rows.append(values)
    return rows


def modular_rank(vectors: list[list[int]], prime: int) -> int:
    basis: dict[int, list[int]] = {}
    for vector in vectors:
        reduced = [value % prime for value in vector]
        while True:
            pivot = next((i for i, value in enumerate(reduced) if value), None)
            if pivot is None:
                break
            if pivot not in basis:
                inverse = pow(reduced[pivot], prime - 2, prime)
                basis[pivot] = [(value * inverse) % prime for value in reduced]
                break
            multiplier = reduced[pivot]
            reduced = [
                (value - multiplier * base) % prime
                for value, base in zip(reduced, basis[pivot])
            ]
    return len(basis)


def verify_record(
    table,
    expected: dict,
    c99_record: dict | None,
    saturation_record: dict | None,
) -> list:
    errors = []
    vectors3 = PRIMARY.balanced_exchange_vectors(table, 3)
    vectors4 = PRIMARY.balanced_exchange_vectors(table, 4)
    if len(vectors3) != expected["three_exchange_count"]:
        errors.append(["three_exchange_count", len(vectors3), expected["three_exchange_count"]])
    if len(vectors4) != expected["four_exchange_count"]:
        errors.append(["four_exchange_count", len(vectors4), expected["four_exchange_count"]])

    ambient4 = flint_matrix(vectors4, 36)
    rank = ambient4.rank()
    diagonal = nonzero_snf(ambient4)
    if rank != expected["elementary_rank"]:
        errors.append(["flint_rank", rank, expected["elementary_rank"]])
    if diagonal != expected["elementary_snf"]:
        errors.append(["flint_snf", diagonal, expected["elementary_snf"]])

    combined_rows = nonzero_hnf_rows(flint_matrix(vectors4 + vectors3, 36))
    four_rows = nonzero_hnf_rows(ambient4)
    containment = combined_rows == four_rows
    if containment != expected["three_exchange_lattice_contained_in_four"]:
        errors.append(["flint_three_exchange_containment", containment])

    for prime in (2, 3, 1_000_003):
        observed = modular_rank(vectors4, prime)
        if observed != expected["elementary_rank"]:
            errors.append(["modular_rank", prime, observed, expected["elementary_rank"]])

    mode_vectors = (
        [PRIMARY.primitive_centered(witness, 6) for witness in c99_record["integer_witnesses"]]
        if c99_record
        else []
    )
    for index, (vector, mode_expected) in enumerate(
        zip(mode_vectors, expected["common_modes"]), 1
    ):
        augmented = flint_matrix(vectors4 + [vector], 36)
        augmented_rank = augmented.rank()
        in_span = augmented_rank == rank
        in_lattice = nonzero_hnf_rows(augmented) == four_rows
        augmented_diagonal = nonzero_snf(augmented)
        augmented_index = (
            math.prod(augmented_diagonal) if augmented_rank == 20 else None
        )
        if in_span != mode_expected["in_rational_span"]:
            errors.append(["mode_span", index, in_span, mode_expected["in_rational_span"]])
        if in_lattice != mode_expected["in_lattice"]:
            errors.append(["mode_lattice", index, in_lattice, mode_expected["in_lattice"]])
        if augmented_index != mode_expected["augmented_full_index"]:
            errors.append(
                ["mode_augmented_index", index, augmented_index, mode_expected["augmented_full_index"]]
            )

    if mode_vectors:
        combined_modes = flint_matrix(vectors4 + mode_vectors, 36)
        combined_index = (
            math.prod(nonzero_snf(combined_modes))
            if combined_modes.rank() == 20
            else None
        )
        if combined_index != expected["common_mode_augmented_index"]:
            errors.append(
                ["combined_mode_index", combined_index, expected["common_mode_augmented_index"]]
            )

    if saturation_record is not None:
        saturated_basis = saturation_record["saturated_common_mode_cell_basis"]
        saturated_matrix = flint_matrix(saturated_basis, 36)
        saturated_rank = saturated_matrix.rank()
        saturated_diagonal = nonzero_snf(saturated_matrix)
        if saturated_rank != saturation_record["saturated_common_mode_rank"]:
            errors.append(
                ["saturated_mode_rank", saturated_rank, saturation_record["saturated_common_mode_rank"]]
            )
        if saturated_diagonal != [1] * saturated_rank:
            errors.append(["saturated_mode_not_primitive", saturated_diagonal])
        if nonzero_hnf_rows(flint_matrix(saturated_basis + mode_vectors, 36)) != nonzero_hnf_rows(
            saturated_matrix
        ):
            errors.append(["stored_modes_not_in_saturated_mode_lattice"])
        if flint_matrix(saturated_basis + mode_vectors, 36).rank() != saturated_rank:
            errors.append(["saturated_mode_rational_span_disagreement"])
        elementary_plus_saturated = flint_matrix(vectors4 + saturated_basis, 36)
        observed_index = (
            math.prod(nonzero_snf(elementary_plus_saturated))
            if elementary_plus_saturated.rank() == 20
            else None
        )
        if observed_index != saturation_record["elementary_plus_saturated_common_mode_index"]:
            errors.append(
                [
                    "elementary_plus_saturated_mode_index",
                    observed_index,
                    saturation_record["elementary_plus_saturated_common_mode_index"],
                ]
            )

    candidate = expected["six_exchange_completion"]
    if candidate is not None:
        vector = candidate["vector"]
        if sorted(vector).count(-1) != 6 or sorted(vector).count(1) != 6:
            errors.append(["six_exchange_shape"])
        incidence = PRIMARY.line_incidence(table)
        if incidence * PRIMARY.Matrix(vector) != PRIMARY.Matrix.zeros(18, 1):
            errors.append(["six_exchange_not_balanced"])
        completed = flint_matrix(vectors4 + [vector], 36)
        completed_diagonal = nonzero_snf(completed)
        if completed.rank() != 20 or completed_diagonal != [1] * 20:
            errors.append(["six_exchange_flint_completion", completed.rank(), completed_diagonal])

    return errors


def write_summary(path: Path, payload: dict) -> None:
    lines = [
        "Independent Python-FLINT verification",
        "",
        f"tables checked: {payload['table_count']}",
        f"exceptional C99 tables checked: {payload['exceptional_table_count']}",
        f"modular rank checks: {payload['modular_rank_check_count']}",
        f"mode checks: {payload['mode_check_count']}",
        f"saturated mode checks: {payload['saturated_mode_check_count']}",
        f"six-exchange completion checks: {payload['six_exchange_check_count']}",
        f"errors: {payload['error_count']}",
        f"overall_pass: {payload['overall_pass']}",
    ]
    path.write_text("\n".join(lines) + "\n")


def verify_task(task):
    source_index, table, expected, c99_record, saturation_record = task
    return source_index, verify_record(
        table,
        expected,
        c99_record,
        saturation_record,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--c99-audit", type=Path, required=True)
    parser.add_argument("--saturation", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    expected_by_index = {
        record["source_index"]: record for record in primary["records"]
    }
    c99 = json.loads(args.c99_audit.read_text())
    exceptional = {
        record["source_index"]: record
        for record in c99["datasets"]["order6_complete"]["exceptional_tables"]
    }
    saturation = json.loads(args.saturation.read_text())
    saturation_by_index = {
        record["source_index"]: record for record in saturation["records"]
    }
    tasks = [
        (
            source_index,
            table,
            expected_by_index[source_index],
            exceptional.get(source_index),
            saturation_by_index.get(source_index),
        )
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
    ]
    errors = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        verified = executor.map(verify_task, tasks, chunksize=2)
        for source_index, table_errors in verified:
            errors.extend([source_index, error] for error in table_errors)

    payload = {
        "verification_version": "common_mode_trade_lattice_flint_v1",
        "workers": args.workers,
        "table_count": len(tasks),
        "exceptional_table_count": len(exceptional),
        "modular_rank_check_count": 3 * len(tasks),
        "mode_check_count": sum(
            record["common_mode_count"] for record in primary["records"]
        ),
        "six_exchange_check_count": sum(
            record["six_exchange_completion"] is not None
            for record in primary["records"]
        ),
        "saturated_mode_check_count": len(saturation_by_index),
        "error_count": len(errors),
        "errors": errors[:100],
        "overall_pass": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
