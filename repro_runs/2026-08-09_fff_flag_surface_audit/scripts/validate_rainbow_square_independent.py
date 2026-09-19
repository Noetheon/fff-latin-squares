#!/usr/bin/env python3
"""Independent direct validation of the rainbow-square trace on 230 tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def inv(permutation: list[int]) -> list[int]:
    result = [0] * len(permutation)
    for index, value in enumerate(permutation):
        result[value] = index
    return result


def cycle_partition(permutation: list[int]) -> list[tuple[int, ...]]:
    unseen = set(range(len(permutation)))
    result = []
    while unseen:
        start = min(unseen)
        orbit = []
        point = start
        while point in unseen:
            unseen.remove(point)
            orbit.append(point)
            point = permutation[point]
        result.append(tuple(sorted(orbit)))
    return result


def parse_square(compact: str) -> list[list[int]]:
    return [[int(value) for value in compact[8 * row : 8 * row + 8]] for row in range(8)]


def line_families(table: list[list[int]]) -> dict[str, list[list[int]]]:
    n = len(table)
    symbol = [[0] * n for _ in range(n)]
    for row in range(n):
        for column in range(n):
            symbol[table[row][column]][column] = row
    return {
        "R": table,
        "C": [[table[row][column] for row in range(n)] for column in range(n)],
        "S": symbol,
    }


def atom_lookup(table: list[list[int]]) -> tuple[dict, int]:
    lookup = {}
    intercalates = 0
    for view, lines in line_families(table).items():
        inverses = [inv(line) for line in lines]
        for high in range(len(table)):
            for low in range(high):
                relative = [inverses[low][value] for value in lines[high]]
                for support in cycle_partition(relative):
                    key = (view, low, high, support)
                    for point in support:
                        lookup[view, low, high, point] = key
                    if view == "R" and len(support) == 2:
                        intercalates += 1
    return lookup, intercalates


def get_atom(lookup: dict, view: str, first: int, second: int, point: int):
    low, high = sorted((first, second))
    return lookup[view, low, high, point]


def direct_trace(table: list[list[int]]) -> tuple[int, int, int]:
    n = len(table)
    row_inverses = [inv(row) for row in table]
    lookup, intercalates = atom_lookup(table)
    flags = []
    edge_groups = [defaultdict(list) for _ in range(3)]
    for row in range(n):
        for other in range(n):
            if row == other:
                continue
            for column in range(n):
                symbol = table[row][column]
                other_column = row_inverses[other][symbol]
                other_symbol = table[row][other_column]
                row_atom = get_atom(lookup, "R", row, other, column)
                col_atom = get_atom(lookup, "C", column, other_column, row)
                sym_atom = get_atom(lookup, "S", symbol, other_symbol, column)
                flag_id = len(flags)
                flags.append((row_atom, col_atom, sym_atom))
                edge_groups[0][col_atom, sym_atom, row].append(flag_id)
                edge_groups[1][row_atom, sym_atom, other_column].append(flag_id)
                edge_groups[2][row_atom, col_atom, symbol].append(flag_id)
    alpha = [[-1] * len(flags) for _ in range(3)]
    for color in range(3):
        for members in edge_groups[color].values():
            if len(members) != 2:
                raise RuntimeError(f"edge group size {len(members)}")
            first, second = members
            alpha[color][first] = second
            alpha[color][second] = first

    def beta(point: int) -> int:
        for color in (0, 1, 2):
            point = alpha[color][point]
        return point

    beta_fixed = 0
    beta2_fixed = 0
    for flag_id in range(len(flags)):
        once = beta(flag_id)
        beta_fixed += once == flag_id
        beta2_fixed += beta(once) == flag_id
    return intercalates, beta_fixed, beta2_fixed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--classifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    classifier = json.loads(args.classifier.read_text())
    expected = {record["source_index"]: record for record in classifier["records"]}
    records = []
    mismatches = []
    beta_identity_errors = []
    with args.fff_metadata.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            source = int(row["line_number"])
            intercalates, beta_fixed, beta2_fixed = direct_trace(parse_square(row["square"]))
            target = expected[source]
            if beta_fixed != 4 * intercalates:
                beta_identity_errors.append([source, beta_fixed, 4 * intercalates])
            if beta2_fixed != target["rainbow_square_trace_beta2_fixed"]:
                mismatches.append(
                    [source, beta2_fixed, target["rainbow_square_trace_beta2_fixed"]]
                )
            records.append(
                {
                    "source_index": source,
                    "intercalates": intercalates,
                    "beta_fixed": beta_fixed,
                    "beta2_fixed": beta2_fixed,
                }
            )
    payload = {
        "validation_version": "rainbow_square_independent_v1",
        "table_count": len(records),
        "metadata_sha256": sha256(args.fff_metadata),
        "classifier_sha256": sha256(args.classifier),
        "beta_identity_error_count": len(beta_identity_errors),
        "beta_identity_errors": beta_identity_errors,
        "beta2_mismatch_count": len(mismatches),
        "beta2_mismatches": mismatches,
        "records": records,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(
            [
                "Independent rainbow-square trace validation",
                "",
                f"tables: {len(records)}",
                f"Fix(beta)=4I errors: {len(beta_identity_errors)}",
                f"Fix(beta^2) mismatches: {len(mismatches)}",
                "",
                "Result: PASS" if not beta_identity_errors and not mismatches else "Result: FAIL",
            ]
        )
        + "\n"
    )
    return 0 if len(records) == 230 and not beta_identity_errors and not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
