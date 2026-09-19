#!/usr/bin/env python3
"""Analyze symbol-pair failures for a decoded Latin square."""

from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any


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


def load_table(path: Path) -> tuple[tuple[tuple[int, ...], ...], dict[str, Any]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        for key in ("table", "latin_square", "square_table", "square", "compact_square"):
            if key in payload:
                return normalize_table(payload[key]), {"input_path": str(path), "source_kind": key}
    return normalize_table(payload), {"input_path": str(path), "source_kind": "json_root"}


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


def scan_view(lines: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    odd_witness_count = 0
    first_odd_witness = None
    for first, second in combinations(range(len(lines)), 2):
        lengths = cycle_lengths(induced_permutation(lines, first, second))
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
        "has_odd_cycle_witness": odd_witness_count > 0,
        "odd_witness_pair_count": odd_witness_count,
        "first_odd_witness": first_odd_witness,
    }


def analyze_symbol_pairs(table: tuple[tuple[int, ...], ...]) -> list[dict[str, Any]]:
    lines = symbol_lines(table)
    profiles = []
    for u, v in combinations(range(len(lines)), 2):
        perm = induced_permutation(lines, u, v)
        lengths = cycle_lengths(perm)
        odd_lengths = [length for length in lengths if length > 1 and length % 2 == 1]
        profiles.append(
            {
                "pair": [u, v],
                "permutation": list(perm),
                "cycle_lengths": lengths,
                "cycle_type": sorted(lengths, reverse=True),
                "odd_cycle_lengths": odd_lengths,
                "odd_cycle_count": len(odd_lengths),
                "min_odd_cycle_length": min(odd_lengths) if odd_lengths else None,
                "has_odd_cycle_witness": bool(odd_lengths),
            }
        )
    return profiles


def rank_failures(profile: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failing = [item for item in profile if item["has_odd_cycle_witness"]]
    return sorted(
        failing,
        key=lambda item: (
            item["min_odd_cycle_length"],
            -item["odd_cycle_count"],
            item["pair"][0],
            item["pair"][1],
        ),
    )


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "Symbol-pair failure analysis",
        "",
        f"Input: {result['input']['input_path']}",
        f"Order: {result['order']}",
        f"Latin: {result['latin']['latin']}",
        f"Reduced: {result['reduced']}",
        f"Pattern: {result['pattern_name']}",
        f"FFF: {result['fff']}",
        f"Failing symbol pairs: {result['failing_symbol_pair_count']}",
        "",
        "Top failing symbol pairs:",
    ]
    top = result["ranked_failing_symbol_pairs"][:10]
    if not top:
        lines.append("- none")
    else:
        for item in top:
            lines.append(
                "- {pair}: odd_cycle_count={count}, min_odd_cycle_length={min_len}, cycle_type={cycle_type}".format(
                    pair=tuple(item["pair"]),
                    count=item["odd_cycle_count"],
                    min_len=item["min_odd_cycle_length"],
                    cycle_type=item["cycle_type"],
                )
            )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    table, metadata = load_table(args.input)
    latin = validate_latin_square(table)
    reduced = is_reduced(table) if latin["latin"] else False
    row_scan = scan_view(table)
    col_scan = scan_view(column_lines(table))
    sym_scan = scan_view(symbol_lines(table))
    pattern_bits = {
        "row": row_scan["has_odd_cycle_witness"],
        "col": col_scan["has_odd_cycle_witness"],
        "sym": sym_scan["has_odd_cycle_witness"],
    }
    pattern_tuple = (pattern_bits["row"], pattern_bits["col"], pattern_bits["sym"])
    symbol_profile = analyze_symbol_pairs(table) if latin["latin"] else []
    ranked_failures = rank_failures(symbol_profile)
    result = {
        "input": metadata,
        "order": len(table),
        "latin": latin,
        "reduced": reduced,
        "views": {"row": row_scan, "col": col_scan, "sym": sym_scan},
        "pattern_has_odd_cycle": pattern_bits,
        "pattern_name": PATTERN_NAMES[pattern_tuple] if latin["latin"] else None,
        "fff": bool(latin["latin"] and pattern_tuple == (False, False, False)),
        "symbol_pair_profile": symbol_profile,
        "failing_symbol_pair_count": len(ranked_failures),
        "ranked_failing_symbol_pairs": ranked_failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(result))
    return 0 if latin["latin"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
