#!/usr/bin/env python3
"""Build the projection-only forbidden-triangle classification CNF at p=5."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from pysat.card import CardEnc, EncType


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def relative(first: tuple[int, ...], second: tuple[int, ...]) -> tuple[int, ...]:
    inv = inverse(second)
    return tuple(inv[first[source]] for source in range(len(first)))


def cycles(permutation: tuple[int, ...]) -> list[tuple[int, ...]]:
    seen = set()
    result = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        current = start
        cycle = []
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = permutation[current]
        result.append(tuple(cycle))
    return result


def all_cycles_odd(permutation: tuple[int, ...]) -> bool:
    return all(len(cycle) % 2 for cycle in cycles(permutation))


def three_cycle_supports(permutation: tuple[int, ...]) -> set[tuple[int, ...]]:
    return {tuple(sorted(cycle)) for cycle in cycles(permutation) if len(cycle) == 3}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--classification", choices=("full", "three-class"), default="full")
    args = parser.parse_args()
    p = 5
    permutations = list(itertools.permutations(range(p)))
    selected = list(range(1, len(permutations) + 1))
    identity = permutations.index(tuple(range(p)))
    clauses: list[list[int]] = [[selected[identity]]]
    top = selected[-1]
    for source in range(p):
        for target in range(p):
            variables = [selected[index] for index, phi in enumerate(permutations) if phi[source] == target]
            encoded = CardEnc.equals(lits=variables, bound=2, top_id=top, encoding=EncType.seqcounter)
            clauses.extend([list(clause) for clause in encoded.clauses])
            top = encoded.nv
    base_clause_count = len(clauses)

    global_count = 0
    common_three_total = 0
    overlap_count = 0
    all_union_count = 0
    selected_count = 0
    selected_classes: dict[str, int] = {
        "all_5_cycles": 0,
        "two_5_cycles_and_one_3_1_1": 0,
        "common_3_support_mixed": 0,
    }
    for left, middle, right in itertools.combinations(range(len(permutations)), 3):
        relatives = [
            relative(permutations[left], permutations[middle]),
            relative(permutations[left], permutations[right]),
            relative(permutations[middle], permutations[right]),
        ]
        is_global = all(all_cycles_odd(item) for item in relatives)
        is_common_three = bool(set.intersection(*(three_cycle_supports(item) for item in relatives)))
        cycle_signature = tuple(sorted(tuple(sorted((len(cycle) for cycle in cycles(item)), reverse=True)) for item in relatives))
        if is_global:
            global_count += 1
        if is_common_three:
            common_three_total += 1
        if is_global and is_common_three:
            overlap_count += 1
        if is_global or is_common_three:
            all_union_count += 1
        class_name = None
        if cycle_signature == ((5,), (5,), (5,)):
            class_name = "all_5_cycles"
        elif cycle_signature == ((3, 1, 1), (5,), (5,)):
            class_name = "two_5_cycles_and_one_3_1_1"
        elif is_common_three and cycle_signature == ((3, 1, 1), (3, 2), (3, 2)):
            class_name = "common_3_support_mixed"
        include = is_global or is_common_three
        if args.classification == "three-class":
            include = class_name is not None
        if include:
            clauses.append([-selected[left], -selected[middle], -selected[right]])
            selected_count += 1
            if class_name is not None:
                selected_classes[class_name] += 1

    args.cnf.parent.mkdir(parents=True, exist_ok=True)
    with args.cnf.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {top} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
    payload = {
        "encoding_version": "p5_projection_forbidden_triangle_classification_v2",
        "classification_mode": args.classification,
        "projection_count": len(permutations),
        "selected_projection_count_implied": 10,
        "variables": top,
        "clauses": len(clauses),
        "base_cover_clauses": base_clause_count,
        "global_odd_cycle_forbidden_triangles": global_count,
        "common_three_cycle_forbidden_triangles_total": common_three_total,
        "forbidden_triangle_overlap": overlap_count,
        "all_forbidden_triangle_union": all_union_count,
        "selected_forbidden_triangle_union": selected_count,
        "selected_three_class_counts": selected_classes,
        "cnf_sha256": sha(args.cnf),
        "scope": "finite projection classification supporting the p=5 pair-block obstruction only",
    }
    args.metadata.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "p=5 projection forbidden-triangle CNF\n\n"
        f"variables: {top}\nclauses: {len(clauses)}\n"
        f"base cover clauses: {base_clause_count}\n"
        f"global odd-cycle triangles: {global_count}\n"
        f"common 3-cycle triangles total: {common_three_total}\n"
        f"overlap: {overlap_count}\nall-class union: {all_union_count}\n"
        f"classification mode: {args.classification}\n"
        f"selected forbidden triangles: {selected_count}\n"
        f"selected three-class counts: {json.dumps(selected_classes, sort_keys=True)}\n"
        f"CNF SHA-256: {payload['cnf_sha256']}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
