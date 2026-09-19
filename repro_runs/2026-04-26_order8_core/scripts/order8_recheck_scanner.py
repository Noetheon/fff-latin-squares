#!/usr/bin/env python3

import argparse
import gzip
import hashlib
import json
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path


ORDER = 8
VALID_SYMBOLS = tuple(range(ORDER))
PAIR_INDICES = tuple(combinations(range(ORDER), 2))
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
PATTERN_DETAILS = {
    name: {"row": pattern[0], "col": pattern[1], "sym": pattern[2]}
    for pattern, name in PATTERN_NAMES.items()
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_text_input(path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="ascii", newline="")
    return path.open("rt", encoding="ascii", newline="")


def iter_compact_squares(path):
    with open_text_input(path) as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            compact = raw_line.rstrip("\n")
            if compact:
                yield line_number, compact


def parse_compact_square(compact):
    if len(compact) != ORDER * ORDER:
        raise ValueError(f"expected {ORDER * ORDER} symbols, found {len(compact)}")

    rows = []
    for row_index in range(ORDER):
        chunk = compact[row_index * ORDER : (row_index + 1) * ORDER]
        row = []
        for char in chunk:
            value = ord(char) - ord("0")
            if value not in VALID_SYMBOLS:
                raise ValueError(f"invalid symbol {char!r}")
            row.append(value)
        rows.append(tuple(row))

    validate_latin_square(rows)
    return tuple(rows)


def validate_latin_square(rows):
    expected = list(VALID_SYMBOLS)
    for row_index, row in enumerate(rows):
        if sorted(row) != expected:
            raise ValueError(f"row {row_index} is not a permutation of 0..7")

    for column_index in range(ORDER):
        column = [rows[row_index][column_index] for row_index in range(ORDER)]
        if sorted(column) != expected:
            raise ValueError(f"column {column_index} is not a permutation of 0..7")


def positions_for_lines(lines):
    position_maps = []
    for line in lines:
        positions = [None] * ORDER
        for index, value in enumerate(line):
            if positions[value] is not None:
                raise ValueError(f"line is not a permutation: {line!r}")
            positions[value] = index
        if any(position is None for position in positions):
            raise ValueError(f"line is not a permutation: {line!r}")
        position_maps.append(tuple(positions))
    return tuple(position_maps)


def has_nontrivial_odd_cycle(perm):
    seen = [False] * len(perm)
    for start in range(len(perm)):
        if seen[start]:
            continue
        cursor = start
        cycle_length = 0
        while not seen[cursor]:
            seen[cursor] = True
            cursor = perm[cursor]
            cycle_length += 1
        if cycle_length > 1 and cycle_length % 2 == 1:
            return True
    return False


def view_has_odd_cycle(lines):
    position_maps = positions_for_lines(lines)
    for first, second in PAIR_INDICES:
        permutation = [position_maps[second][value] for value in lines[first]]
        if has_nontrivial_odd_cycle(permutation):
            return True
    return False


def column_lines(rows):
    return tuple(tuple(rows[row_index][column_index] for row_index in range(ORDER)) for column_index in range(ORDER))


def symbol_lines(rows):
    lines = [[None] * ORDER for _ in range(ORDER)]
    for row_index, row in enumerate(rows):
        for column_index, symbol in enumerate(row):
            if lines[symbol][column_index] is not None:
                raise ValueError("symbol view contains a duplicate occurrence in a column")
            lines[symbol][column_index] = row_index
    return tuple(tuple(line) for line in lines)


def square_pattern(rows):
    pattern = (
        view_has_odd_cycle(rows),
        view_has_odd_cycle(column_lines(rows)),
        view_has_odd_cycle(symbol_lines(rows)),
    )
    return pattern, PATTERN_NAMES[pattern]


def row_positions(rows):
    return positions_for_lines(rows)


def column_positions(rows):
    return positions_for_lines(column_lines(rows))


def build_principal_isotope(rows, left_identity_row, right_identity_column):
    row_pos = row_positions(rows)
    col_pos = column_positions(rows)
    left_division = row_pos[left_identity_row]
    right_division = col_pos[right_identity_column]

    loop_table = []
    for x in VALID_SYMBOLS:
        source_row = rows[right_division[x]]
        loop_row = []
        for y in VALID_SYMBOLS:
            loop_row.append(source_row[left_division[y]])
        loop_table.append(tuple(loop_row))
    return tuple(loop_table), rows[left_identity_row][right_identity_column]


def is_associative(table):
    for x in VALID_SYMBOLS:
        row_x = table[x]
        for y in VALID_SYMBOLS:
            xy = row_x[y]
            row_y = table[y]
            left_row = table[xy]
            right_row = table[x]
            for z in VALID_SYMBOLS:
                if left_row[z] != right_row[row_y[z]]:
                    return False
    return True


def has_identity(table, identity):
    return all(table[identity][x] == x and table[x][identity] == x for x in VALID_SYMBOLS)


def classify_group_isotopy(rows):
    for left_identity_row in VALID_SYMBOLS:
        for right_identity_column in VALID_SYMBOLS:
            loop_table, identity = build_principal_isotope(rows, left_identity_row, right_identity_column)
            if not has_identity(loop_table, identity):
                raise AssertionError("principal isotope construction failed to produce a loop")
            if is_associative(loop_table):
                return {
                    "group_isotopic": True,
                    "witness": {
                        "left_identity_row": left_identity_row,
                        "right_identity_column": right_identity_column,
                        "loop_identity": identity,
                    },
                }

    return {"group_isotopic": False, "witness": None}


def scan_main_classes(path, store_counterexamples=True, log_every=25000):
    started = time.time()
    pattern_counts = Counter()
    counterexamples = []
    group_counts = Counter()
    total = 0

    for line_number, compact in iter_compact_squares(path):
        total += 1
        rows = parse_compact_square(compact)
        pattern_tuple, pattern_name = square_pattern(rows)
        pattern_counts[pattern_name] += 1

        if pattern_tuple == (False, False, False):
            group_result = classify_group_isotopy(rows)
            group_counts[group_result["group_isotopic"]] += 1
            if store_counterexamples:
                counterexamples.append(
                    {
                        "index": total,
                        "line_number": line_number,
                        "square": compact,
                        "group_isotopic": group_result["group_isotopic"],
                        "group_isotopy_witness": group_result["witness"],
                    }
                )

        if log_every and total % log_every == 0:
            elapsed = time.time() - started
            print(
                f"[recheck-progress] scanned {total} main classes in {elapsed:.2f}s",
                file=sys.stderr,
                flush=True,
            )

    elapsed = time.time() - started
    ordered_pattern_counts = {name: pattern_counts.get(name, 0) for name in PATTERN_NAMES.values()}
    return {
        "input": {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        },
        "scan": {
            "order": ORDER,
            "total_main_classes": total,
            "elapsed_seconds": round(elapsed, 6),
            "pattern_key_legend": PATTERN_DETAILS,
            "pattern_counts": ordered_pattern_counts,
            "counterexample_pattern": "FFF",
            "counterexamples_count": ordered_pattern_counts["FFF"],
            "counterexample_group_isotopy": {
                "group_isotopic": group_counts.get(True, 0),
                "non_group_isotopic": group_counts.get(False, 0),
            },
            "validation": {
                "checked_row_permutations": True,
                "checked_column_permutations": True,
                "checked_symbol_permutations_on_demand": True,
            },
        },
        "counterexamples": counterexamples if store_counterexamples else None,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Independently recheck odd-cycle two-line trade patterns on order-8 main classes."
    )
    parser.add_argument("input", type=Path, help="Path to the order-8 main-class file (plain text or .gz).")
    parser.add_argument("--output", type=Path, required=True, help="Path to the JSON output file.")
    parser.add_argument(
        "--no-counterexamples",
        action="store_true",
        help="Skip embedding the FFF counterexample list in the JSON output.",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=25000,
        help="Emit a progress line to stderr every N scanned main classes (0 disables logging).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"input file not found: {args.input}")

    result = scan_main_classes(
        args.input,
        store_counterexamples=not args.no_counterexamples,
        log_every=args.log_every,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
