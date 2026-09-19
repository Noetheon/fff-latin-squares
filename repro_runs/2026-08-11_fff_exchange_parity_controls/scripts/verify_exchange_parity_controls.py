#!/usr/bin/env python3
"""Independent packed-profile verifier for the exchange-parity controls."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
import itertools
import json
from pathlib import Path


def parse_compact(compact: str, n: int):
    if len(compact) != n * n:
        raise ValueError((len(compact), n * n))
    return tuple(
        tuple(int(compact[n * row + column]) for column in range(n))
        for row in range(n)
    )


def table_sha256(table) -> str:
    payload = ";".join(",".join(map(str, row)) for row in table).encode()
    return hashlib.sha256(payload).hexdigest()


def insert_gf2(basis: dict[int, int], vector: int) -> None:
    while vector:
        pivot = vector.bit_length() - 1
        if pivot in basis:
            vector ^= basis[pivot]
        else:
            basis[pivot] = vector
            return


def independent_exchange_data(table):
    n = len(table)
    groups: dict[bytes, list[int]] = {}
    for cells in itertools.combinations(range(n * n), 4):
        profile = bytearray(3 * n)
        mask = 0
        for cell in cells:
            row, column = divmod(cell, n)
            profile[row] += 1
            profile[n + column] += 1
            profile[2 * n + table[row][column]] += 1
            mask |= 1 << cell
        groups.setdefault(bytes(profile), []).append(mask)

    basis: dict[int, int] = {}
    exchange_count = 0
    for masks in groups.values():
        for left_index, left in enumerate(masks):
            for right in masks[left_index + 1 :]:
                if left & right:
                    continue
                exchange_count += 1
                insert_gf2(basis, left ^ right)
    return exchange_count, len(basis)


def independent_line_rank(table) -> int:
    n = len(table)
    basis: dict[int, int] = {}
    for kind in range(3):
        for line in range(n):
            mask = 0
            for row in range(n):
                for column in range(n):
                    if (row, column, table[row][column])[kind] == line:
                        mask |= 1 << (n * row + column)
            insert_gf2(basis, mask)
    return len(basis)


def inverse(permutation):
    result = [None] * len(permutation)
    for index, value in enumerate(permutation):
        result[value] = index
    return tuple(result)


def compose(first, second):
    return tuple(first[second[index]] for index in range(len(first)))


def has_odd_cycle(permutation) -> bool:
    seen = [False] * len(permutation)
    for start in range(len(permutation)):
        if seen[start]:
            continue
        cursor = start
        length = 0
        while not seen[cursor]:
            seen[cursor] = True
            cursor = permutation[cursor]
            length += 1
        if length > 1 and length % 2:
            return True
    return False


def view_lines(table, view: str):
    n = len(table)
    if view == "row":
        return table
    if view == "col":
        return tuple(tuple(table[row][column] for row in range(n)) for column in range(n))
    lines = [[None] * n for _ in range(n)]
    for row in range(n):
        for column in range(n):
            lines[table[row][column]][column] = row
    return tuple(tuple(line) for line in lines)


def independent_pattern(table) -> str:
    bits = []
    for view in ("row", "col", "sym"):
        lines = view_lines(table, view)
        inverses = [inverse(line) for line in lines]
        witness = any(
            has_odd_cycle(compose(inverses[second], lines[first]))
            for first, second in itertools.combinations(range(len(lines)), 2)
        )
        bits.append("T" if witness else "F")
    return "".join(bits)


def analyze(task):
    dataset, source_index, table, expected = task
    exchange_count, exchange_rank = independent_exchange_data(table)
    line_rank = independent_line_rank(table)
    quotient_dimension = len(table) ** 2 - line_rank - exchange_rank
    actual = {
        "table_sha256": table_sha256(table),
        "pattern": independent_pattern(table),
        "balanced_4plus4_exchange_count": exchange_count,
        "line_rank_mod2": line_rank,
        "exchange_rank_mod2": exchange_rank,
        "exchange_quotient_dimension_mod2": quotient_dimension,
    }
    errors = []
    for key, value in actual.items():
        if value != expected[key]:
            errors.append([key, value, expected[key]])
    return {
        "dataset": dataset,
        "source_index": source_index,
        **actual,
        "error_count": len(errors),
        "errors": errors,
    }


def load_order8(path: Path):
    with path.open() as handle:
        return {
            int(row["line_number"]): parse_compact(row["square"], 8)
            for row in csv.DictReader(handle, delimiter="\t")
        }


def load_order10(path: Path):
    payload = json.loads(path.read_text())
    return {
        index: parse_compact(compact, 10)
        for index, compact in enumerate(sorted(payload["tracked_order10_source_paths"]), 1)
    }


def record_map(payload: dict) -> dict[int, dict]:
    return {record["source_index"]: record for record in payload["records"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--order8-results", type=Path, required=True)
    parser.add_argument("--order10-results", type=Path, required=True)
    parser.add_argument("--order8-workers", type=int, default=8)
    parser.add_argument("--order10-workers", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    tables8 = load_order8(args.fff_metadata)
    tables10 = load_order10(args.n10_corpus)
    results8 = json.loads(args.order8_results.read_text())
    results10 = json.loads(args.order10_results.read_text())
    expected8 = record_map(results8)
    expected10 = record_map(results10)

    tasks8 = [
        ("order8_fff_complete", source, table, expected8[source])
        for source, table in sorted(tables8.items())
    ]
    with ProcessPoolExecutor(max_workers=args.order8_workers) as executor:
        verified8 = list(executor.map(analyze, tasks8, chunksize=1))

    representative_sources = []
    seen_patterns = set()
    for record in results10["records"]:
        if record["pattern"] not in seen_patterns:
            seen_patterns.add(record["pattern"])
            representative_sources.append(record["source_index"])
    if results10["records"][-1]["source_index"] not in representative_sources:
        representative_sources.append(results10["records"][-1]["source_index"])
    tasks10 = [
        ("order10_tracked_representatives", source, tables10[source], expected10[source])
        for source in representative_sources
    ]
    with ProcessPoolExecutor(max_workers=args.order10_workers) as executor:
        verified10 = list(executor.map(analyze, tasks10, chunksize=1))

    q0_record = next(
        record
        for record in results8["records"]
        if record["exchange_quotient_dimension_mod2"] == 0
    )
    q0_table = tables8[q0_record["source_index"]]
    all_records = verified8 + verified10
    payload = {
        "verification_version": "exchange_parity_controls_independent_v1",
        "method": "independent packed line profiles and direct GF(2) pivot dictionary",
        "order8_verified_table_count": len(verified8),
        "order10_verified_representative_count": len(verified10),
        "order10_verified_patterns": sorted(seen_patterns),
        "order10_verified_sources": representative_sources,
        "verified_quotient_distribution_order8": {
            str(key): value
            for key, value in sorted(
                Counter(
                    record["exchange_quotient_dimension_mod2"] for record in verified8
                ).items()
            )
        },
        "explicit_fff_counterexample_to_forced_q4_equals_1": {
            "source_index": q0_record["source_index"],
            "table_sha256": q0_record["table_sha256"],
            "table": [list(row) for row in q0_table],
            "pattern": q0_record["pattern"],
            "independently_computed_pattern": independent_pattern(q0_table),
            "group_isotopic": q0_record["group_isotopic"],
            "line_rank_mod2": q0_record["line_rank_mod2"],
            "exchange_rank_mod2": q0_record["exchange_rank_mod2"],
            "exchange_quotient_dimension_mod2": 0,
        },
        "error_count": sum(record["error_count"] for record in all_records),
        "records": all_records,
        "claim_boundary": [
            "The explicit order-8 FFF table disproves only the proposed implication FFF => q4=1.",
            "The checked order-10 representatives belong to a partial non-FFF diagnostic corpus.",
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "Independent exchange-parity control verification",
        "",
        f"order-8 tables verified: {len(verified8)}",
        f"order-10 representatives verified: {len(verified10)}",
        f"order-10 patterns represented: {sorted(seen_patterns)}",
        f"order-8 q4 distribution: {payload['verified_quotient_distribution_order8']}",
        f"explicit FFF q4=0 source: {q0_record['source_index']}",
        f"errors: {payload['error_count']}",
        "",
        "Boundary: FFF does not force q4=1; no order-10 existence conclusion.",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    return 1 if payload["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
