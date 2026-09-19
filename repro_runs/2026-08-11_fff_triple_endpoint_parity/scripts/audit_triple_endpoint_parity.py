#!/usr/bin/env python3
"""Audit the C84 triple endpoint contraction and common-cell parity law."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PAIR = runpy.run_path(
    str(ROOT / "repro_runs/2026-08-09_fff_labelled_flag_incidence/scripts/audit_labelled_flag_incidence.py")
)
FLAG = PAIR["FLAG"]
SMALL = PAIR["SMALL"]


def direct_flag_triples(table: list[list[int]]) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]]:
    """Enumerate ordered flags directly, retaining endpoint pairs."""
    n = len(table)
    inverse_rows = [FLAG["inverse"](row) for row in table]
    triples = []
    for row in range(n):
        for other_row in range(n):
            if row == other_row:
                continue
            for column in range(n):
                symbol = table[row][column]
                other_column = inverse_rows[other_row][symbol]
                other_symbol = table[row][other_column]
                triples.append(
                    (
                        tuple(sorted((row, other_row))),
                        tuple(sorted((column, other_column))),
                        tuple(sorted((symbol, other_symbol))),
                    )
                )
    return triples


def endpoint_tensor_from_direct_flags(table: list[list[int]]) -> list[list[list[int]]]:
    n = len(table)
    output = [[[0] * n for _ in range(n)] for _ in range(n)]
    for row_pair, column_pair, symbol_pair in direct_flag_triples(table):
        for row in row_pair:
            for column in column_pair:
                for symbol in symbol_pair:
                    output[row][column][symbol] += 1
    return output


def endpoint_tensor_from_aggregated_tensor(table: list[list[int]]) -> list[list[list[int]]]:
    n = len(table)
    pairs, _pair_index = PAIR["pair_data"](n)
    tensor = Counter(PAIR["flag_label_triples"](table))
    output = [[[0] * n for _ in range(n)] for _ in range(n)]
    for (row_edge, column_edge, symbol_edge), multiplicity in tensor.items():
        for row in pairs[row_edge]:
            for column in pairs[column_edge]:
                for symbol in pairs[symbol_edge]:
                    output[row][column][symbol] += multiplicity
    return output


def endpoint_tensors_by_multiplicity(
    table: list[list[int]],
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    """Contract the indicators of multiplicity-one and multiplicity-four entries."""
    n = len(table)
    pairs, _pair_index = PAIR["pair_data"](n)
    tensor = Counter(PAIR["flag_label_triples"](table))
    singleton = [[[0] * n for _ in range(n)] for _ in range(n)]
    intercalate = [[[0] * n for _ in range(n)] for _ in range(n)]
    for (row_edge, column_edge, symbol_edge), multiplicity in tensor.items():
        if multiplicity not in (1, 4):
            raise AssertionError(f"unexpected tensor multiplicity: {multiplicity}")
        target = singleton if multiplicity == 1 else intercalate
        for row in pairs[row_edge]:
            for column in pairs[column_edge]:
                for symbol in pairs[symbol_edge]:
                    target[row][column][symbol] += 1
    return singleton, intercalate


def cell_intercalate_degrees(table: list[list[int]]) -> list[list[int]]:
    n = len(table)
    degrees = [[0] * n for _ in range(n)]
    for row_high in range(n):
        for row_low in range(row_high):
            for column_high in range(n):
                for column_low in range(column_high):
                    if (
                        table[row_high][column_high] == table[row_low][column_low]
                        and table[row_high][column_low] == table[row_low][column_high]
                    ):
                        for row in (row_low, row_high):
                            for column in (column_low, column_high):
                                degrees[row][column] += 1
    return degrees


def rank_binary(vectors: list[int]) -> int:
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


def binary_flattening_ranks(endpoint: list[list[list[int]]]) -> list[int]:
    n = len(endpoint)
    support = [
        (row, column, symbol)
        for row in range(n)
        for column in range(n)
        for symbol in range(n)
        if endpoint[row][column][symbol] % 2
    ]
    ranks = []
    for mode in range(3):
        other = [index for index in range(3) if index != mode]
        vectors = [0] * n
        for triple in support:
            position = triple[other[0]] * n + triple[other[1]]
            vectors[triple[mode]] ^= 1 << position
        ranks.append(rank_binary(vectors))
    return ranks


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    expected_line_sum = 8 * (n - 1)
    direct = endpoint_tensor_from_direct_flags(table)
    aggregated = endpoint_tensor_from_aggregated_tensor(table)
    singleton_endpoint, intercalate_endpoint = endpoint_tensors_by_multiplicity(table)
    intercalates = cell_intercalate_degrees(table)
    errors = []

    if direct != aggregated:
        mismatches = sum(
            direct[row][column][symbol] != aggregated[row][column][symbol]
            for row in range(n)
            for column in range(n)
            for symbol in range(n)
        )
        errors.append(["independent_construction", mismatches])

    split_mismatches = sum(
        direct[row][column][symbol]
        != singleton_endpoint[row][column][symbol]
        + 4 * intercalate_endpoint[row][column][symbol]
        for row in range(n)
        for column in range(n)
        for symbol in range(n)
    )
    if split_mismatches:
        errors.append(["multiplicity_split", split_mismatches])

    line_checks = 0
    binary_line_checks = 0
    for mode in range(3):
        other = [index for index in range(3) if index != mode]
        for left in range(n):
            for right in range(n):
                values = []
                for coordinate in range(n):
                    triple = [0, 0, 0]
                    triple[other[0]] = left
                    triple[other[1]] = right
                    triple[mode] = coordinate
                    values.append(direct[triple[0]][triple[1]][triple[2]])
                if sum(values) != expected_line_sum:
                    errors.append(["line_sum", mode, left, right, sum(values), expected_line_sum])
                if sum(value % 2 for value in values) % 2:
                    errors.append(["binary_line_parity", mode, left, right])
                line_checks += 1
                binary_line_checks += 1

    latin_cell_checks = 0
    complementary_mass_checks = 0
    multiplicity_split_cell_checks = 0
    latin_parity_ones = 0
    for row in range(n):
        for column in range(n):
            symbol = table[row][column]
            expected_cell = 3 * (n - 1) + intercalates[row][column]
            observed_cell = direct[row][column][symbol]
            if observed_cell != expected_cell:
                errors.append(["latin_cell", row, column, observed_cell, expected_cell])
            expected_complement = 5 * (n - 1) - intercalates[row][column]
            observed_complement = sum(
                direct[row][column][other_symbol]
                for other_symbol in range(n)
                if other_symbol != symbol
            )
            if observed_complement != expected_complement:
                errors.append(
                    ["complementary_mass", row, column, observed_complement, expected_complement]
                )
            expected_parity = (n - 1 + intercalates[row][column]) % 2
            if observed_cell % 2 != expected_parity:
                errors.append(["latin_cell_parity", row, column])
            observed_intercalate_part = intercalate_endpoint[row][column][symbol]
            if observed_intercalate_part != intercalates[row][column]:
                errors.append(
                    [
                        "intercalate_endpoint_cell",
                        row,
                        column,
                        observed_intercalate_part,
                        intercalates[row][column],
                    ]
                )
            expected_singleton_part = 3 * (n - 1 - intercalates[row][column])
            observed_singleton_part = singleton_endpoint[row][column][symbol]
            if observed_singleton_part != expected_singleton_part:
                errors.append(
                    [
                        "singleton_endpoint_cell",
                        row,
                        column,
                        observed_singleton_part,
                        expected_singleton_part,
                    ]
                )
            if not 0 <= intercalates[row][column] <= n - 1:
                errors.append(["intercalate_degree_bound", row, column])
            latin_parity_ones += observed_cell % 2
            latin_cell_checks += 1
            complementary_mass_checks += 1
            multiplicity_split_cell_checks += 1

    flattening_ranks = binary_flattening_ranks(direct)
    if any(rank > n - 1 for rank in flattening_ranks):
        errors.append(["flattening_rank_bound", flattening_ranks, n - 1])

    support_size = sum(
        direct[row][column][symbol] % 2
        for row in range(n)
        for column in range(n)
        for symbol in range(n)
    )
    return {
        "source_index": source_index,
        "pattern": PAIR["pattern"](table),
        "group_isotopic": None,
        "endpoint_total_mass": sum(
            direct[row][column][symbol]
            for row in range(n)
            for column in range(n)
            for symbol in range(n)
        ),
        "binary_support_size": support_size,
        "binary_flattening_ranks": flattening_ranks,
        "latin_cell_parity_ones": latin_parity_ones,
        "line_checks": line_checks,
        "binary_line_checks": binary_line_checks,
        "latin_cell_checks": latin_cell_checks,
        "complementary_mass_checks": complementary_mass_checks,
        "multiplicity_split_cell_checks": multiplicity_split_cell_checks,
        "errors": errors,
    }


def dataset_summary(name: str, records: list[dict]) -> dict:
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    rank_triples = Counter(tuple(record["binary_flattening_ranks"]) for record in records)
    supports = [record["binary_support_size"] for record in records]
    latin_ones = [record["latin_cell_parity_ones"] for record in records]
    return {
        "name": name,
        "table_count": len(records),
        "pattern_counts": dict(sorted(Counter(record["pattern"] for record in records).items())),
        "endpoint_total_mass_values": sorted({record["endpoint_total_mass"] for record in records}),
        "binary_zero_tensor_count": sum(record["binary_support_size"] == 0 for record in records),
        "binary_support_range": [min(supports), max(supports)],
        "latin_cell_parity_one_range": [min(latin_ones), max(latin_ones)],
        "binary_flattening_rank_range": [
            min(rank for record in records for rank in record["binary_flattening_ranks"]),
            max(rank for record in records for rank in record["binary_flattening_ranks"]),
        ],
        "binary_flattening_rank_triples": {
            ",".join(map(str, ranks)): count for ranks, count in sorted(rank_triples.items())
        },
        "line_checks": sum(record["line_checks"] for record in records),
        "binary_line_checks": sum(record["binary_line_checks"] for record in records),
        "latin_cell_checks": sum(record["latin_cell_checks"] for record in records),
        "complementary_mass_checks": sum(
            record["complementary_mass_checks"] for record in records
        ),
        "multiplicity_split_cell_checks": sum(
            record["multiplicity_split_cell_checks"] for record in records
        ),
        "error_count": len(errors),
        "errors": errors[:100],
    }


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            table = FLAG["parse_compact"](row["square"], 8)
            yield int(row["line_number"]), row["group_isotopic"] == "true", table


def write_summary(payload: dict, path: Path) -> None:
    lines = [
        "Triple endpoint parity tensor audit",
        "",
        f"audit version: {payload['audit_version']}",
        f"tables: {payload['totals']['tables']}",
        f"endpoint lines checked: {payload['totals']['line_checks']}",
        f"Latin cells checked: {payload['totals']['latin_cell_checks']}",
        f"complementary masses checked: {payload['totals']['complementary_mass_checks']}",
        f"multiplicity-split cells checked: {payload['totals']['multiplicity_split_cell_checks']}",
        f"errors: {payload['totals']['errors']}",
        "",
        "Exact theorem audited:",
        "- every integer endpoint line has sum 8(n-1);",
        "- D(r,c,L(r,c)) = 3(n-1) + cell intercalate degree;",
        "- the complementary line mass is 5(n-1) minus that degree;",
        "- for T=X+4Y, the endpoint contractions on a Latin cell are",
        "  X: 3(n-1-iota) and Y: iota;",
        "- H=D mod 2 has even one-dimensional fibers and flattening rank at most n-1.",
        "",
    ]
    for name, data in payload["datasets"].items():
        lines.extend(
            [
                name,
                f"- tables: {data['table_count']}",
                f"- patterns: {data['pattern_counts']}",
                f"- total-mass values: {data['endpoint_total_mass_values']}",
                f"- zero binary tensors: {data['binary_zero_tensor_count']}",
                f"- binary support range: {data['binary_support_range']}",
                f"- Latin-cell parity-one range: {data['latin_cell_parity_one_range']}",
                f"- binary flattening rank range: {data['binary_flattening_rank_range']}",
                f"- line checks: {data['line_checks']}",
                f"- Latin-cell checks: {data['latin_cell_checks']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Evidence boundary:",
            "- C84 is rigorous; this run is exact sanity evidence.",
            "- H is a genuine common-cell contraction but its ambient line-parity condition is weak.",
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
    n8 = []
    for source, group_isotopic, table in load_n8(args.fff_metadata):
        record = analyze_table(table, source)
        record["group_isotopic"] = group_isotopic
        n8.append(record)
    datasets["order8_fff_complete"] = dataset_summary("order8_fff_complete", n8)
    n10 = [
        analyze_table(table, source)
        for source, table, _metadata in FLAG["n10_tables"](args.n10_corpus)
    ]
    datasets["order10_tracked_partial"] = dataset_summary("order10_tracked_partial", n10)

    payload = {
        "audit_version": "triple_endpoint_parity_v2",
        "datasets": datasets,
        "totals": {
            "tables": sum(data["table_count"] for data in datasets.values()),
            "line_checks": sum(data["line_checks"] for data in datasets.values()),
            "binary_line_checks": sum(
                data["binary_line_checks"] for data in datasets.values()
            ),
            "latin_cell_checks": sum(
                data["latin_cell_checks"] for data in datasets.values()
            ),
            "complementary_mass_checks": sum(
                data["complementary_mass_checks"] for data in datasets.values()
            ),
            "multiplicity_split_cell_checks": sum(
                data["multiplicity_split_cell_checks"] for data in datasets.values()
            ),
            "errors": sum(data["error_count"] for data in datasets.values()),
        },
        "claim_boundary": [
            "C84 is a rigorous multi-slice/common-cell consequence of C78.",
            "The endpoint line-parity space alone does not decide Latin realizability or FFF.",
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
