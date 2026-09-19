#!/usr/bin/env python3
"""Audit Smith/rank formulas for every C78 pair-label tensor slice."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PAIR = runpy.run_path(
    str(ROOT / "repro_runs/2026-08-09_fff_labelled_flag_incidence/scripts/audit_labelled_flag_incidence.py")
)
FLAG = PAIR["FLAG"]
SMALL = PAIR["SMALL"]
VIEWS = ("row", "col", "sym")
ODD_PRIME = 1_000_003


def rank_mod(matrix: list[list[int]], prime: int) -> int:
    """Return the exact row rank over GF(prime)."""
    data = [[value % prime for value in row] for row in matrix]
    rows = len(data)
    columns = len(data[0]) if data else 0
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if data[row][column]), None)
        if pivot is None:
            continue
        data[rank], data[pivot] = data[pivot], data[rank]
        inverse = pow(data[rank][column], prime - 2, prime)
        data[rank] = [(value * inverse) % prime for value in data[rank]]
        for row in range(rows):
            if row == rank or not data[row][column]:
                continue
            factor = data[row][column]
            data[row] = [
                (left - factor * right) % prime
                for left, right in zip(data[row], data[rank])
            ]
        rank += 1
        if rank == rows:
            break
    return rank


def rank_binary_vectors(vectors: list[int]) -> int:
    basis: dict[int, int] = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length() - 1
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return len(basis)


def compact_slice(
    tensor: Counter[tuple[int, int, int]], color: int, label: int
) -> tuple[list[list[int]], int]:
    other = [index for index in range(3) if index != color]
    entries = [
        (triple[other[0]], triple[other[1]], multiplicity)
        for triple, multiplicity in tensor.items()
        if triple[color] == label
    ]
    row_labels = sorted({row for row, _column, _value in entries})
    column_labels = sorted({column for _row, column, _value in entries})
    row_index = {value: index for index, value in enumerate(row_labels)}
    column_index = {value: index for index, value in enumerate(column_labels)}
    matrix = [[0] * len(column_labels) for _ in row_labels]
    four_count = 0
    for row, column, value in entries:
        matrix[row_index[row]][column_index[column]] = value
        four_count += value == 4
    if len(row_labels) != len(column_labels):
        raise AssertionError(["non_square_active_slice", color, label])
    return matrix, four_count


def flatten_rank_binary(
    tensor: Counter[tuple[int, int, int]], color: int, m: int
) -> int:
    other = [index for index in range(3) if index != color]
    rows = [0] * m
    for triple, multiplicity in tensor.items():
        if multiplicity % 2:
            position = triple[other[0]] * m + triple[other[1]]
            rows[triple[color]] ^= 1 << position
    return rank_binary_vectors(rows)


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    pairs, _pair_index = PAIR["pair_data"](n)
    m = len(pairs)
    tensor = Counter(PAIR["flag_label_triples"](table))
    profiles = PAIR["view_cycle_profiles"](table)
    direct_pattern = PAIR["pattern"](table)
    errors = []
    reconstructed_pattern = []
    rank_gap_histogram = Counter()
    odd_cycle_histogram = Counter()
    smith_histogram = Counter()

    for color, view in enumerate(VIEWS):
        view_has_odd = False
        for label, lengths in enumerate(profiles[view]):
            matrix, four_count = compact_slice(tensor, color, label)
            rank_odd = rank_mod(matrix, ODD_PRIME)
            rank_two = rank_mod(matrix, 2)
            t = sum(length == 2 for length in lengths)
            odd = sum(length % 2 for length in lengths)
            even_nonintercalate = sum(length > 2 and length % 2 == 0 for length in lengths)
            cycles = len(lengths)
            expected_active_dimension = n - t
            expected_unit_factors = n - cycles - t
            expected_rank_odd = expected_unit_factors + odd + t
            expected_rank_two = expected_unit_factors
            if len(matrix) != expected_active_dimension:
                errors.append(["active_dimension", view, label, len(matrix), expected_active_dimension])
            if four_count != t:
                errors.append(["intercalate_count", view, label, four_count, t])
            if rank_odd != expected_rank_odd:
                errors.append(["odd_rank", view, label, rank_odd, expected_rank_odd])
            if rank_two != expected_rank_two:
                errors.append(["binary_rank", view, label, rank_two, expected_rank_two])
            recovered_odd = rank_odd - rank_two - four_count
            if recovered_odd != odd:
                errors.append(["odd_cycle_recovery", view, label, recovered_odd, odd])
            if rank_odd - rank_two < four_count:
                errors.append(["rank_gap_nonnegative", view, label])
            view_has_odd |= recovered_odd > 0
            rank_gap_histogram[rank_odd - rank_two] += 1
            odd_cycle_histogram[odd] += 1
            smith_histogram["unit"] += expected_unit_factors
            smith_histogram["two"] += odd
            smith_histogram["four"] += t
            smith_histogram["zero"] += even_nonintercalate
        reconstructed_pattern.append("T" if view_has_odd else "F")

    reconstructed_pattern_text = "".join(reconstructed_pattern)
    if reconstructed_pattern_text != direct_pattern:
        errors.append(["pattern", reconstructed_pattern_text, direct_pattern])

    flatten_ranks = [flatten_rank_binary(tensor, color, m) for color in range(3)]
    if any(rank > m - 1 for rank in flatten_ranks):
        errors.append(["flatten_rank_bound", flatten_ranks, m - 1])

    return {
        "source_index": source_index,
        "pattern": direct_pattern,
        "slice_count": 3 * m,
        "rank_gap_histogram": dict(sorted(rank_gap_histogram.items())),
        "odd_cycle_histogram": dict(sorted(odd_cycle_histogram.items())),
        "smith_factor_totals": dict(sorted(smith_histogram.items())),
        "binary_flattening_ranks": flatten_ranks,
        "errors": errors,
    }


def dataset_summary(name: str, records: list[dict]) -> dict:
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    flatten_by_pattern: dict[str, Counter] = defaultdict(Counter)
    rank_gap_histogram = Counter()
    odd_cycle_histogram = Counter()
    smith_factor_totals = Counter()
    for record in records:
        flatten_by_pattern[record["pattern"]][tuple(record["binary_flattening_ranks"])] += 1
        rank_gap_histogram.update({int(key): value for key, value in record["rank_gap_histogram"].items()})
        odd_cycle_histogram.update({int(key): value for key, value in record["odd_cycle_histogram"].items()})
        smith_factor_totals.update(record["smith_factor_totals"])
    all_flatten = [rank for record in records for rank in record["binary_flattening_ranks"]]
    return {
        "name": name,
        "table_count": len(records),
        "pattern_counts": dict(sorted(Counter(record["pattern"] for record in records).items())),
        "slice_count": sum(record["slice_count"] for record in records),
        "rank_gap_histogram": {str(key): value for key, value in sorted(rank_gap_histogram.items())},
        "odd_cycle_histogram": {str(key): value for key, value in sorted(odd_cycle_histogram.items())},
        "smith_factor_totals": dict(sorted(smith_factor_totals.items())),
        "binary_flattening_rank_range": [min(all_flatten), max(all_flatten)],
        "binary_flattening_rank_triples_by_pattern": {
            pattern: {",".join(map(str, ranks)): count for ranks, count in sorted(values.items())}
            for pattern, values in sorted(flatten_by_pattern.items())
        },
        "error_count": len(errors),
        "errors": errors[:100],
    }


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), FLAG["parse_compact"](row["square"], 8)


def write_summary(payload: dict, path: Path) -> None:
    lines = [
        "Pair-tensor Smith obstruction audit",
        "",
        f"audit version: {payload['audit_version']}",
        f"odd rank field: GF({payload['odd_rank_prime']})",
        f"tables: {payload['totals']['tables']}",
        f"pair-label slices: {payload['totals']['slices']}",
        f"errors: {payload['totals']['errors']}",
        "",
        "Exact theorem audited:",
        "- coker(slice) = Z^q + (Z/2)^o + (Z/4)^t, up to unit factors.",
        "- rank_odd - rank_GF2 = intercalate cycles + odd cycles.",
        "- a square is FFF iff rank_odd-rank_GF2 equals the number of 4-entries in every slice.",
        "- equivalently, every normalized positive-support slice is totally unimodular/balanced.",
        "",
    ]
    for name, data in payload["datasets"].items():
        lines.extend(
            [
                name,
                f"- tables: {data['table_count']}",
                f"- patterns: {data['pattern_counts']}",
                f"- slices: {data['slice_count']}",
                f"- rank gaps: {data['rank_gap_histogram']}",
                f"- odd-cycle counts per slice: {data['odd_cycle_histogram']}",
                f"- Smith-factor totals: {data['smith_factor_totals']}",
                f"- binary flattening rank range: {data['binary_flattening_rank_range']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Evidence boundary:",
            "- The Smith/rank characterization is rigorous; this run is exact sanity evidence.",
            "- Global binary flattening ranks are exploratory and no corpus range is a theorem.",
            "- The order-10 corpus is tracked partial data, not an exhaustive census.",
            "- C38 remains open and C40 remains absent.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    datasets = {}
    n4 = [
        analyze_table(table, source)
        for source, table in enumerate(SMALL["reduced_latin_squares"](4), start=1)
    ]
    datasets["order4_complete"] = dataset_summary("order4_complete", n4)
    n6 = [
        analyze_table(table, source)
        for source, table in enumerate(SMALL["reduced_latin_squares"](6), start=1)
    ]
    datasets["order6_complete"] = dataset_summary("order6_complete", n6)
    n8 = [analyze_table(table, source) for source, table in load_n8(args.fff_metadata)]
    datasets["order8_fff_complete"] = dataset_summary("order8_fff_complete", n8)
    n10 = [
        analyze_table(table, source)
        for source, table, _metadata in FLAG["n10_tables"](args.n10_corpus)
    ]
    datasets["order10_tracked_partial"] = dataset_summary("order10_tracked_partial", n10)
    payload = {
        "audit_version": "pair_tensor_smith_v1",
        "odd_rank_prime": ODD_PRIME,
        "datasets": datasets,
        "totals": {
            "tables": sum(data["table_count"] for data in datasets.values()),
            "slices": sum(data["slice_count"] for data in datasets.values()),
            "errors": sum(data["error_count"] for data in datasets.values()),
        },
        "claim_boundary": [
            "The slice Smith theorem and rank-gap FFF equivalence are rigorous.",
            "The global flattening ranks are exploratory only.",
            "No order-10 existence or nonexistence result is claimed.",
            "C38 remains open and C40 remains absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(payload, args.summary)
    return int(payload["totals"]["errors"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
