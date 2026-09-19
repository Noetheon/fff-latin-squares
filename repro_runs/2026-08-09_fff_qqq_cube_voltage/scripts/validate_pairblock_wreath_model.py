#!/usr/bin/env python3
"""Decode and independently validate a selected wreath-family SAT model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def inverse(perm: list[int]) -> list[int]:
    result = [0] * len(perm)
    for source, target in enumerate(perm):
        result[target] = source
    return result


def compose(left: list[int], right: list[int]) -> list[int]:
    return [left[right[index]] for index in range(len(left))]


def cycle_lengths(perm: list[int]) -> list[int]:
    seen: set[int] = set()
    result = []
    for start in range(len(perm)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            current = perm[current]
            length += 1
        result.append(length)
    return sorted(result, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text())
    positive = {
        int(token)
        for line in args.model.read_text().splitlines()
        if line.startswith("v")
        for token in line[1:].split()
        if int(token) > 0
    }
    selected = [entry for entry in mapping["elements"] if entry["variable"] in positive]
    n = mapping["n"]
    sharp_counts = [[0] * n for _ in range(n)]
    for entry in selected:
        for source, target in enumerate(entry["permutation"]):
            sharp_counts[source][target] += 1
    bad_relatives = []
    for left_index, left in enumerate(selected):
        for right_index, right in enumerate(selected):
            if left_index == right_index:
                continue
            quotient = compose(inverse(right["permutation"]), left["permutation"])
            lengths = cycle_lengths(quotient)
            if any(length == 1 or length % 2 for length in lengths):
                bad_relatives.append({"left": left["variable"], "right": right["variable"], "cycles": lengths})
    result = {
        "selected_count": len(selected),
        "selected_variables": [entry["variable"] for entry in selected],
        "identity_selected": mapping["identity_variable"] in positive,
        "sharply_transitive": all(value == 1 for row in sharp_counts for value in row),
        "all_relative_permutations_even_fixedpointfree": not bad_relatives,
        "bad_relatives": bad_relatives,
        "mapping_sha256": sha256(args.mapping),
        "model_sha256": sha256(args.model),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Pair-block wreath model validation\n\n"
        f"selected_count: {result['selected_count']}\n"
        f"identity_selected: {str(result['identity_selected']).lower()}\n"
        f"sharply_transitive: {str(result['sharply_transitive']).lower()}\n"
        "all_relative_permutations_even_fixedpointfree: "
        f"{str(result['all_relative_permutations_even_fixedpointfree']).lower()}\n"
    )


if __name__ == "__main__":
    main()
