#!/usr/bin/env python3
"""Validate Latin-square FFF patterns by direct cycle scanning."""

from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any


VIEWS = ("row", "col", "sym")
PATTERN_NAMES = {
    (False, False, False): "FFF",
    (False, False, True): "FFT",
    (False, True, False): "FTF",
    (False, True, True): "FTT",
    (True, False, False): "TFF",
    (True, False, True): "TFT",
    (True, True, False): "TTF",
    (True, True, True): "TTT",
}


def parse_compact_square(compact: str) -> tuple[tuple[int, ...], ...]:
    order = int(math.isqrt(len(compact)))
    if order * order != len(compact):
        raise ValueError(f"compact square length is not a square: {len(compact)}")
    return tuple(
        tuple(int(ch) for ch in compact[row * order : (row + 1) * order])
        for row in range(order)
    )


def normalize_table(raw: Any) -> tuple[tuple[int, ...], ...]:
    if isinstance(raw, str):
        return parse_compact_square(raw.strip())
    if isinstance(raw, list):
        return tuple(tuple(int(value) for value in row) for row in raw)
    raise ValueError(f"cannot parse table from object of type {type(raw).__name__}")


def load_table(path: Path, counterexample_index: int | None) -> tuple[tuple[tuple[int, ...], ...], dict[str, Any]]:
    text = path.read_text().strip()
    metadata: dict[str, Any] = {"input_path": str(path)}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "\t" in line:
                rows.append([int(x) for x in line.split("\t")])
            elif "," in line:
                rows.append([int(x) for x in line.split(",")])
            else:
                rows.append([int(x) for x in line.split()])
        return normalize_table(rows), metadata

    if isinstance(obj, dict) and "counterexamples" in obj:
        index = 0 if counterexample_index is None else counterexample_index
        entry = obj["counterexamples"][index]
        metadata.update(
            {
                "source_kind": "order8_core_counterexamples",
                "counterexample_index": index,
                "source_index": entry.get("index"),
                "source_line_number": entry.get("line_number"),
                "source_group_isotopic": entry.get("group_isotopic"),
            }
        )
        return normalize_table(entry["square"]), metadata

    if isinstance(obj, dict):
        for key in ("table", "latin_square", "square_table"):
            if key in obj:
                metadata["source_kind"] = key
                return normalize_table(obj[key]), metadata
        for key in ("square", "compact_square"):
            if key in obj:
                metadata["source_kind"] = key
                return normalize_table(obj[key]), metadata
    return normalize_table(obj), metadata


def validate_latin_square(table: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    order = len(table)
    expected = list(range(order))
    row_failures = []
    col_failures = []
    if any(len(row) != order for row in table):
        return {"latin": False, "reason": "non_square_rows", "order": order}
    for row_index, row in enumerate(table):
        if sorted(row) != expected:
            row_failures.append(row_index)
    for col in range(order):
        if sorted(table[row][col] for row in range(order)) != expected:
            col_failures.append(col)
    return {
        "latin": not row_failures and not col_failures,
        "order": order,
        "row_failures": row_failures,
        "column_failures": col_failures,
    }


def is_reduced(table: tuple[tuple[int, ...], ...]) -> bool:
    order = len(table)
    return list(table[0]) == list(range(order)) and [table[i][0] for i in range(order)] == list(range(order))


def positions_for_lines(lines: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(lines[0])
    maps = []
    for line in lines:
        pos = [None] * order
        for idx, value in enumerate(line):
            pos[value] = idx
        maps.append(tuple(int(v) for v in pos))
    return tuple(maps)


def induced_permutation(lines: tuple[tuple[int, ...], ...], first: int, second: int) -> tuple[int, ...]:
    positions = positions_for_lines(lines)
    return tuple(positions[second][value] for value in lines[first])


def cycle_lengths(perm: tuple[int, ...]) -> list[int]:
    seen = [False] * len(perm)
    lengths = []
    for start in range(len(perm)):
        if seen[start]:
            continue
        cursor = start
        length = 0
        while not seen[cursor]:
            seen[cursor] = True
            cursor = perm[cursor]
            length += 1
        lengths.append(length)
    return lengths


def column_lines(table: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(table)
    return tuple(tuple(table[row][col] for row in range(order)) for col in range(order))


def symbol_lines(table: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(table)
    lines = [[None] * order for _ in range(order)]
    for row_index, row in enumerate(table):
        for col_index, symbol in enumerate(row):
            lines[symbol][col_index] = row_index
    return tuple(tuple(int(value) for value in line) for line in lines)


def view_lines(table: tuple[tuple[int, ...], ...], view: str) -> tuple[tuple[int, ...], ...]:
    if view == "row":
        return table
    if view == "col":
        return column_lines(table)
    if view == "sym":
        return symbol_lines(table)
    raise ValueError(f"unknown view: {view}")


def scan_view(table: tuple[tuple[int, ...], ...], view: str) -> dict[str, Any]:
    lines = view_lines(table, view)
    pair_count = 0
    odd_witness_count = 0
    first_odd_witness = None
    all_cycle_lengths: dict[str, int] = {}
    for first, second in combinations(range(len(lines)), 2):
        pair_count += 1
        lengths = cycle_lengths(induced_permutation(lines, first, second))
        for length in lengths:
            all_cycle_lengths[str(length)] = all_cycle_lengths.get(str(length), 0) + 1
        odd_lengths = [length for length in lengths if length > 1 and length % 2 == 1]
        if odd_lengths:
            odd_witness_count += 1
            if first_odd_witness is None:
                first_odd_witness = {
                    "line_pair": [first, second],
                    "cycle_lengths": lengths,
                    "odd_cycle_lengths": odd_lengths,
                }
    return {
        "line_pair_count": pair_count,
        "has_odd_cycle_witness": odd_witness_count > 0,
        "odd_witness_pair_count": odd_witness_count,
        "first_odd_witness": first_odd_witness,
        "cycle_length_histogram": all_cycle_lengths,
        "all_induced_permutations_even_or_fixed": odd_witness_count == 0,
    }


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "FFF table validation summary",
        "",
        f"Input: {result['input']['input_path']}",
        f"Order: {result['order']}",
        f"Latin: {result['latin']['latin']}",
        f"Reduced: {result['reduced']}",
        f"Pattern: {result['pattern_name']}",
        f"FFF: {result['fff']}",
        "",
        "Views:",
    ]
    for view in VIEWS:
        item = result["views"][view]
        lines.append(
            "- {view}: has_odd_cycle={odd}, odd_pair_count={count}, all_even_or_fixed={even}".format(
                view=view,
                odd=item["has_odd_cycle_witness"],
                count=item["odd_witness_pair_count"],
                even=item["all_induced_permutations_even_or_fixed"],
            )
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--counterexample-index", type=int)
    parser.add_argument("--expect-reduced", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    table, metadata = load_table(args.input, args.counterexample_index)
    latin = validate_latin_square(table)
    if not latin["latin"]:
        views = {view: {"skipped": "not_latin"} for view in VIEWS}
        pattern_bits = {view: None for view in VIEWS}
    else:
        views = {view: scan_view(table, view) for view in VIEWS}
        pattern_bits = {view: views[view]["has_odd_cycle_witness"] for view in VIEWS}
    pattern_tuple = tuple(bool(pattern_bits[view]) for view in VIEWS) if latin["latin"] else None
    reduced = is_reduced(table) if latin["latin"] else False
    result = {
        "input": metadata,
        "order": len(table),
        "latin": latin,
        "reduced": reduced,
        "expect_reduced": args.expect_reduced,
        "reduced_expectation_met": (not args.expect_reduced) or reduced,
        "views": views,
        "pattern_has_odd_cycle": pattern_bits,
        "pattern_name": PATTERN_NAMES[pattern_tuple] if pattern_tuple is not None else None,
        "fff": bool(latin["latin"] and pattern_tuple == (False, False, False)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(result))
    if args.expect_reduced and not reduced:
        return 2
    return 0 if latin["latin"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
