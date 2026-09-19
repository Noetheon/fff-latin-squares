#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
import math
from pathlib import Path

from sympy import Matrix, ZZ
from sympy.matrices.normalforms import hermite_normal_form, smith_normal_form
from sympy.polys.matrices import DomainMatrix
from sympy.polys.matrices.normalforms import smith_normal_decomp


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


PRIMARY = load_module("primary_trade_lattice_saturation", PRIMARY_PATH)
SMALL = PRIMARY.SMALL


def saturated_column_basis(matrix: Matrix) -> tuple[Matrix, list[int]]:
    domain = DomainMatrix.from_Matrix(matrix, fmt="dense").convert_to(ZZ)
    diagonal, left, _ = smith_normal_decomp(domain)
    diagonal_matrix = diagonal.to_Matrix()
    rank = sum(
        diagonal_matrix[index, index] != 0
        for index in range(min(diagonal_matrix.shape))
    )
    left_inverse = left.to_Matrix().inv()
    basis = left_inverse[:, :rank]
    if any(value.q != 1 for value in basis):
        raise ValueError("nonintegral saturated basis")
    certificate_snf = [
        abs(int(diagonal_matrix[index, index]))
        for index in range(rank)
    ]
    return basis, certificate_snf


def analyze_task(task):
    source_index, table, c99_record, primary_record = task
    incidence = PRIMARY.line_incidence(table)
    rank, inverse_right, _ = PRIMARY.kernel_coordinates(incidence)
    # If y=T^{-1}x, the final 20 coordinates parametrize the saturated kernel.
    right = inverse_right.inv()
    kernel_basis = right[:, rank:]

    exchanges4 = PRIMARY.balanced_exchange_vectors(table, 4)
    exchange_matrix = Matrix.hstack(*(Matrix(vector) for vector in exchanges4))
    exchange_coordinates = (inverse_right * exchange_matrix)[rank:, :]
    exchange_hnf = hermite_normal_form(exchange_coordinates)

    modes = [
        Matrix(PRIMARY.primitive_centered(witness, 6))
        for witness in c99_record["integer_witnesses"]
    ]
    mode_coordinates = Matrix.hstack(
        *((inverse_right * mode)[rank:, :] for mode in modes)
    )
    saturated_coordinates, certificate_snf = saturated_column_basis(mode_coordinates)
    saturated_cells = kernel_basis * saturated_coordinates
    if incidence * saturated_cells != Matrix.zeros(incidence.rows, saturated_cells.cols):
        raise ValueError("saturated cell mode is not line-balanced")

    combined_hnf = hermite_normal_form(
        exchange_coordinates.row_join(saturated_coordinates)
    )
    combined_index = (
        abs(int(combined_hnf.det()))
        if combined_hnf.rows == combined_hnf.cols
        else None
    )
    errors = []
    expected_rank = primary_record["elementary_rank"]
    if exchange_hnf.cols != expected_rank:
        errors.append(["elementary_rank_disagreement", exchange_hnf.cols, expected_rank])
    if saturated_coordinates.cols != c99_record["r_Q"] - 1:
        errors.append(
            ["saturated_mode_rank", saturated_coordinates.cols, c99_record["r_Q"] - 1]
        )
    if expected_rank == 19 and c99_record["r_Q"] == 3 and combined_index != 2:
        errors.append(["rank19_common_mode_index", combined_index, 2])
    if expected_rank == 20 and combined_index != 1:
        errors.append(["full_elementary_lattice_index", combined_index, 1])

    return {
        "source_index": source_index,
        "r_Q": c99_record["r_Q"],
        "elementary_rank": expected_rank,
        "stored_certificate_lattice_snf": certificate_snf,
        "saturated_common_mode_rank": saturated_coordinates.cols,
        "saturated_common_mode_cell_basis": [
            [int(saturated_cells[row, col]) for row in range(saturated_cells.rows)]
            for col in range(saturated_cells.cols)
        ],
        "elementary_plus_saturated_common_mode_index": combined_index,
        "error_count": len(errors),
        "errors": errors,
    }


def write_summary(path: Path, payload: dict) -> None:
    totals = payload["totals"]
    lines = [
        "Centered common-mode saturation audit",
        "",
        f"exceptional tables: {totals['table_count']}",
        f"stored certificate lattice SNF: {totals['certificate_snf_distribution']}",
        f"E4 plus saturated mode index: {totals['combined_index_distribution']}",
        f"rank-19 r_Q=3 index-two count: {totals['rank19_r3_index_two_count']}",
        f"errors: {totals['error_count']}",
        "",
        "The index-two statement uses the saturated integral lattice of the full rational centered common-mode space, not a chosen certificate basis.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--c99-audit", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    primary_by_index = {
        record["source_index"]: record for record in primary["records"]
    }
    c99 = json.loads(args.c99_audit.read_text())
    exceptional = {
        record["source_index"]: record
        for record in c99["datasets"]["order6_complete"]["exceptional_tables"]
    }
    tasks = [
        (source_index, table, exceptional[source_index], primary_by_index[source_index])
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
        if source_index in exceptional
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=2))
    records.sort(key=lambda record: record["source_index"])

    snf_distribution = Counter(
        tuple(record["stored_certificate_lattice_snf"]) for record in records
    )
    index_distribution = Counter(
        record["elementary_plus_saturated_common_mode_index"] for record in records
    )
    payload = {
        "audit_version": "common_mode_saturation_v1",
        "totals": {
            "table_count": len(records),
            "certificate_snf_distribution": {
                str(key): value for key, value in sorted(snf_distribution.items())
            },
            "combined_index_distribution": {
                str(key): value for key, value in sorted(index_distribution.items())
            },
            "rank19_r3_index_two_count": sum(
                record["r_Q"] == 3
                and record["elementary_rank"] == 19
                and record["elementary_plus_saturated_common_mode_index"] == 2
                for record in records
            ),
            "error_count": sum(record["error_count"] for record in records),
        },
        "records": records,
        "claim_boundary": [
            "The saturation removes dependence on the stored C99 certificate basis.",
            "The result is a complete order-6 corpus fact, not an order-10 theorem.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
