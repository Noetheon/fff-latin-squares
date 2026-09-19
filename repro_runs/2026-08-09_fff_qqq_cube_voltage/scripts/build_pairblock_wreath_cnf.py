#!/usr/bin/env python3
"""Build the exact pair-block wreath-product row-F selection CNF."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wreath_perm(phi: tuple[int, ...], flips: tuple[int, ...]) -> tuple[int, ...]:
    p = len(phi)
    return tuple(2 * phi[index // 2] + ((index % 2) ^ flips[index // 2]) for index in range(2 * p))


def inverse(perm: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(perm)
    for source, target in enumerate(perm):
        result[target] = source
    return tuple(result)


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[right[index]] for index in range(len(left)))


def cycle_lengths(perm: tuple[int, ...]) -> list[int]:
    seen: set[int] = set()
    lengths = []
    for start in range(len(perm)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            current = perm[current]
            length += 1
        lengths.append(length)
    return sorted(lengths, reverse=True)


def relative_is_even(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    quotient = compose(inverse(right), left)
    lengths = cycle_lengths(quotient)
    return all(length > 1 and length % 2 == 0 for length in lengths)


def add_exactly_one(clauses: list[list[int]], variables: list[int]) -> None:
    clauses.append(variables)
    clauses.extend([[-a, -b] for a, b in itertools.combinations(variables, 2)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", type=int, choices=(3, 5), required=True)
    parser.add_argument("--cnf-output", type=Path, required=True)
    parser.add_argument("--mapping-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    p = args.p
    n = 2 * p
    identity = tuple(range(n))

    elements = []
    for phi in itertools.permutations(range(p)):
        for flips in itertools.product((0, 1), repeat=p):
            perm = wreath_perm(phi, flips)
            if perm == identity or relative_is_even(perm, identity):
                elements.append({"phi": phi, "flips": flips, "perm": perm})
    elements.sort(key=lambda item: item["perm"])
    identity_index = next(index for index, item in enumerate(elements) if item["perm"] == identity)
    variable_ids = list(range(1, len(elements) + 1))
    clauses: list[list[int]] = [[variable_ids[identity_index]]]

    sharp_clause_count_before = len(clauses)
    for source in range(n):
        for target in range(n):
            candidates = [variable_ids[index] for index, item in enumerate(elements) if item["perm"][source] == target]
            if not candidates:
                clauses.append([])
            else:
                add_exactly_one(clauses, candidates)
    sharp_clause_count = len(clauses) - sharp_clause_count_before

    incompatible_count = 0
    for left_index in range(len(elements)):
        left = elements[left_index]["perm"]
        for right_index in range(left_index + 1, len(elements)):
            right = elements[right_index]["perm"]
            if not relative_is_even(left, right):
                clauses.append([-variable_ids[left_index], -variable_ids[right_index]])
                incompatible_count += 1
    compatible_count = len(elements) * (len(elements) - 1) // 2 - incompatible_count

    args.cnf_output.parent.mkdir(parents=True, exist_ok=True)
    with args.cnf_output.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {len(elements)} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")

    mapping = {
        "encoding_version": "pairblock_wreath_row_f_selection_v1",
        "p": p,
        "n": n,
        "identity_variable": variable_ids[identity_index],
        "elements": [
            {
                "variable": variable_ids[index],
                "phi": list(item["phi"]),
                "flips": list(item["flips"]),
                "permutation": list(item["perm"]),
                "cycle_lengths_vs_identity": cycle_lengths(item["perm"]),
            }
            for index, item in enumerate(elements)
        ],
    }
    args.mapping_output.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
    metadata = {
        "encoding_version": mapping["encoding_version"],
        "p": p,
        "n": n,
        "full_wreath_order": len(list(itertools.permutations(range(p)))) * (2**p),
        "candidate_count_including_identity": len(elements),
        "variables": len(elements),
        "clauses": len(clauses),
        "sharp_transitivity_clause_count": sharp_clause_count,
        "incompatible_pair_clause_count": incompatible_count,
        "compatible_pair_count": compatible_count,
        "cnf_sha256": sha256(args.cnf_output),
        "mapping_sha256": sha256(args.mapping_output),
        "elapsed_seconds": time.time() - started,
        "scope": "Common p-blocks-of-size-2 row-F sharply transitive families only.",
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary_output.write_text(
        "Pair-block wreath row-F CNF\n\n"
        f"p: {p}\nn: {n}\nfull_wreath_order: {metadata['full_wreath_order']}\n"
        f"candidates_including_identity: {len(elements)}\nvariables: {len(elements)}\n"
        f"clauses: {len(clauses)}\ncompatible_pairs: {compatible_count}\n"
        f"incompatible_pairs: {incompatible_count}\n"
        f"cnf_sha256: {metadata['cnf_sha256']}\nelapsed_seconds: {metadata['elapsed_seconds']:.6f}\n"
        "scope: common pair-block imprimitive row-F model; not a global FFF model.\n"
    )


if __name__ == "__main__":
    main()
