#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path

from order8_recheck_scanner import (
    ORDER,
    PAIR_INDICES,
    classify_group_isotopy,
    parse_compact_square,
    square_pattern,
)


LETTER_TO_DIGIT = {letter: str(index) for index, letter in enumerate("abcdefgh")}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def swap_rows(rows, first, second):
    mutable = [list(row) for row in rows]
    mutable[first], mutable[second] = mutable[second], mutable[first]
    return tuple(tuple(row) for row in mutable)


def swap_columns(rows, first, second):
    mutable = [list(row) for row in rows]
    for row in mutable:
        row[first], row[second] = row[second], row[first]
    return tuple(tuple(row) for row in mutable)


def parse_transitive_species(path):
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines:
        raise ValueError("transitive file is empty")

    header = lines[0].split()
    if len(header) < 3:
        raise ValueError(f"unexpected header: {lines[0]!r}")

    declared_order = int(header[0])
    declared_alphabet = int(header[1])
    declared_count = int(header[2])
    if declared_order != ORDER or declared_alphabet != ORDER:
        raise ValueError(f"unexpected header values: {lines[0]!r}")

    species = []
    current_block = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            if current_block:
                if len(current_block) != ORDER:
                    raise ValueError(f"incomplete species block of size {len(current_block)}")
                species.append(tuple(current_block))
                current_block = []
            continue
        if len(stripped) != ORDER:
            raise ValueError(f"unexpected row length in transitive file: {stripped!r}")
        current_block.append(stripped)

    if current_block:
        if len(current_block) != ORDER:
            raise ValueError(f"incomplete species block of size {len(current_block)}")
        species.append(tuple(current_block))

    if len(species) != declared_count:
        raise ValueError(f"header declares {declared_count} species but parsed {len(species)}")

    return {
        "header": {
            "declared_order": declared_order,
            "declared_alphabet_size": declared_alphabet,
            "declared_species_count": declared_count,
        },
        "species_rows": species,
    }


def block_to_numeric_rows(block):
    compact = "".join("".join(LETTER_TO_DIGIT[char] for char in row) for row in block)
    return parse_compact_square(compact), compact


def evaluate_swaps(rows, swap_kind):
    evaluations = []
    failures = []
    for first, second in PAIR_INDICES:
        if swap_kind == "row":
            swapped = swap_rows(rows, first, second)
        elif swap_kind == "column":
            swapped = swap_columns(rows, first, second)
        else:
            raise ValueError(f"unknown swap kind: {swap_kind}")

        pattern_tuple, pattern_name = square_pattern(swapped)
        has_any_odd_cycle = any(pattern_tuple)
        record = {
            "pair": [first, second],
            "pattern": pattern_name,
            "has_any_odd_cycle": has_any_odd_cycle,
        }
        evaluations.append(record)
        if has_any_odd_cycle:
            failures.append(record)
    return evaluations, failures


def evaluate_species(index, block):
    rows, compact = block_to_numeric_rows(block)
    pattern_tuple, pattern_name = square_pattern(rows)
    group_result = classify_group_isotopy(rows)
    row_swaps, row_failures = evaluate_swaps(rows, "row")
    column_swaps, column_failures = evaluate_swaps(rows, "column")
    return {
        "index": index,
        "original_rows_letters": list(block),
        "original_rows_numeric": ["".join(str(value) for value in row) for row in rows],
        "compact_numeric": compact,
        "pattern": pattern_name,
        "pattern_detail": {"row": pattern_tuple[0], "col": pattern_tuple[1], "sym": pattern_tuple[2]},
        "group_isotopic": group_result["group_isotopic"],
        "group_isotopy_witness": group_result["witness"],
        "row_swaps": row_swaps,
        "column_swaps": column_swaps,
        "row_swap_failures": row_failures,
        "column_swap_failures": column_failures,
    }


def evaluate_transitive_file(path):
    parsed = parse_transitive_species(path)
    species_results = [
        evaluate_species(index, block)
        for index, block in enumerate(parsed["species_rows"], start=1)
    ]

    group_isotopic = sum(result["group_isotopic"] for result in species_results)
    row_swap_failures = sum(len(result["row_swap_failures"]) for result in species_results)
    column_swap_failures = sum(len(result["column_swap_failures"]) for result in species_results)

    return {
        "input": {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        },
        "transitive_file": parsed["header"],
        "summary": {
            "species_count": len(species_results),
            "all_patterns_are_fff": all(result["pattern"] == "FFF" for result in species_results),
            "group_isotopic": group_isotopic,
            "non_group_isotopic": len(species_results) - group_isotopic,
            "all_row_swaps_preserve_fff": row_swap_failures == 0,
            "all_column_swaps_preserve_fff": column_swap_failures == 0,
            "row_swap_failure_count": row_swap_failures,
            "column_swap_failure_count": column_swap_failures,
        },
        "species": species_results,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Independently recheck the 11 transitive order-8 species and all row/column swaps."
    )
    parser.add_argument("input", type=Path, help="Path to transitive8.txt.")
    parser.add_argument("--output", type=Path, required=True, help="Path to the JSON output file.")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"input file not found: {args.input}")

    result = evaluate_transitive_file(args.input)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
