#!/usr/bin/env python3
"""Construct the seven small primitive degree-10 groups and F-clique CNFs."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical195


Permutation = tuple[int, ...]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compose(left: Permutation, right: Permutation) -> Permutation:
    return tuple(left[right[index]] for index in range(len(left)))


def inverse(permutation: Permutation) -> Permutation:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def relative(first: Permutation, second: Permutation) -> Permutation:
    return compose(inverse(second), first)


def cycle_type(permutation: Permutation) -> tuple[int, ...]:
    seen: set[int] = set()
    lengths: list[int] = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            length += 1
            current = permutation[current]
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def is_f(permutation: Permutation) -> bool:
    return all(length % 2 == 0 for length in cycle_type(permutation))


def sign(permutation: tuple[int, ...]) -> int:
    inversions = sum(
        permutation[left] > permutation[right]
        for left in range(len(permutation))
        for right in range(left + 1, len(permutation))
    )
    return -1 if inversions % 2 else 1


def pair_actions() -> dict[str, list[Permutation]]:
    points = list(itertools.combinations(range(5), 2))
    point_index = {point: index for index, point in enumerate(points)}

    def induced(permutation: tuple[int, ...]) -> Permutation:
        return tuple(
            point_index[tuple(sorted((permutation[left], permutation[right])))]
            for left, right in points
        )

    symmetric = list(itertools.permutations(range(5)))
    return {
        "a5_on_2sets": [induced(item) for item in symmetric if sign(item) == 1],
        "s5_on_2sets": [induced(item) for item in symmetric],
    }


# F_9 = F_3[t]/(t^2+1), encoded as a + 3b.
def f9_add(left: int, right: int) -> int:
    return ((left % 3 + right % 3) % 3) + 3 * ((left // 3 + right // 3) % 3)


def f9_neg(value: int) -> int:
    return ((-value % 3) % 3) + 3 * ((-(value // 3)) % 3)


def f9_mul(left: int, right: int) -> int:
    a, b = left % 3, left // 3
    c, d = right % 3, right // 3
    return ((a * c - b * d) % 3) + 3 * ((a * d + b * c) % 3)


def f9_power(value: int, exponent: int) -> int:
    result = 1
    while exponent:
        if exponent & 1:
            result = f9_mul(result, value)
        value = f9_mul(value, value)
        exponent >>= 1
    return result


def f9_inverse(value: int) -> int:
    if not value:
        raise ZeroDivisionError
    return f9_power(value, 7)


def f9_sub(left: int, right: int) -> int:
    return f9_add(left, f9_neg(right))


def f9_div(left: int, right: int) -> int:
    return f9_mul(left, f9_inverse(right))


def projective_actions() -> dict[str, list[Permutation]]:
    infinity = 9

    def canonical(matrix: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        first = next(value for value in matrix if value)
        scale = f9_inverse(first)
        return tuple(f9_mul(scale, value) for value in matrix)

    def determinant(matrix: tuple[int, int, int, int]) -> int:
        a, b, c, d = matrix
        return f9_sub(f9_mul(a, d), f9_mul(b, c))

    def matrix_action(matrix: tuple[int, int, int, int]) -> Permutation:
        a, b, c, d = matrix
        image = []
        for point in range(10):
            if point == infinity:
                image.append(infinity if c == 0 else f9_div(a, c))
                continue
            numerator = f9_add(f9_mul(a, point), b)
            denominator = f9_add(f9_mul(c, point), d)
            image.append(infinity if denominator == 0 else f9_div(numerator, denominator))
        return tuple(image)

    matrices = {
        canonical(matrix)
        for matrix in itertools.product(range(9), repeat=4)
        if determinant(matrix)
    }
    if len(matrices) != 720:
        raise AssertionError("PGL(2,9) matrix count")
    squares = {f9_mul(value, value) for value in range(1, 9)}
    linear = [(matrix_action(matrix), 0 if determinant(matrix) in squares else 1) for matrix in sorted(matrices)]
    frobenius = tuple(f9_power(point, 3) if point != infinity else infinity for point in range(10))
    psl = [action for action, determinant_class in linear if determinant_class == 0]
    pgl = [action for action, _ in linear]
    s6 = psl + [compose(action, frobenius) for action, determinant_class in linear if determinant_class == 0]
    m10 = psl + [compose(action, frobenius) for action, determinant_class in linear if determinant_class == 1]
    pgamma = pgl + [compose(action, frobenius) for action, _ in linear]
    return {
        "psl2_9": psl,
        "pgl2_9": pgl,
        "s6_psigmal2_9": s6,
        "m10": m10,
        "pgammal2_9": pgamma,
    }


def is_primitive(group: list[Permutation]) -> bool:
    universe = set(range(10))
    for size in (2, 5):
        for rest in itertools.combinations(range(1, 10), size - 1):
            block = {0, *rest}
            valid = True
            for permutation in group:
                image = {permutation[point] for point in block}
                if image != block and image & block:
                    valid = False
                    break
            if valid and block != universe:
                return False
    return True


def exact_max_candidate_clique(group: list[Permutation], candidates: list[int], nonedges: list[list[int]]) -> tuple[int, list[int]]:
    for bound in range(min(9, len(candidates)), 0, -1):
        encoded = CardEnc.atleast(
            lits=list(range(1, len(candidates) + 1)),
            bound=bound,
            top_id=len(candidates),
            encoding=EncType.seqcounter,
        )
        with Cadical195(bootstrap_with=nonedges + [list(clause) for clause in encoded.clauses]) as solver:
            if solver.solve():
                positive = {value for value in solver.get_model() if value > 0}
                witness = [candidates[index] for index in range(len(candidates)) if index + 1 in positive]
                return bound, witness
    return 0, []


def write_upper_cnf(path: Path, candidate_count: int, nonedges: list[list[int]], bound: int) -> tuple[int, int]:
    if candidate_count == 0:
        path.write_text("p cnf 0 1\n0\n")
        return 0, 1
    encoded = CardEnc.atleast(
        lits=list(range(1, candidate_count + 1)),
        bound=bound,
        top_id=candidate_count,
        encoding=EncType.seqcounter,
    )
    clauses = nonedges + [list(clause) for clause in encoded.clauses]
    with path.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {encoded.nv} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
    return encoded.nv, len(clauses)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cnf-dir", type=Path, required=True)
    parser.add_argument("--mapping-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    args.cnf_dir.mkdir(parents=True, exist_ok=True)
    args.mapping_dir.mkdir(parents=True, exist_ok=True)
    groups = pair_actions() | projective_actions()
    expected_orders = {
        "a5_on_2sets": 60,
        "s5_on_2sets": 120,
        "psl2_9": 360,
        "pgl2_9": 720,
        "s6_psigmal2_9": 720,
        "m10": 720,
        "pgammal2_9": 1440,
    }
    results = []
    started = time.time()
    for group_id, group in groups.items():
        group_set = set(group)
        if len(group) != expected_orders[group_id] or len(group_set) != len(group):
            raise AssertionError(f"bad order for {group_id}")
        identity = tuple(range(10))
        if identity not in group_set:
            raise AssertionError(f"identity missing for {group_id}")
        closure_ok = all(compose(left, right) in group_set for left in group for right in group)
        transitive = {permutation[0] for permutation in group} == set(range(10))
        primitive = is_primitive(group)
        identity_index = group.index(identity)
        candidates = [index for index, permutation in enumerate(group) if index != identity_index and is_f(permutation)]
        nonedges: list[list[int]] = []
        for left_position, left_index in enumerate(candidates):
            for right_position in range(left_position + 1, len(candidates)):
                right_index = candidates[right_position]
                if not is_f(relative(group[left_index], group[right_index])):
                    nonedges.append([-(left_position + 1), -(right_position + 1)])
        maximum, witness = exact_max_candidate_clique(group, candidates, nonedges)
        upper_bound = maximum + 1
        cnf = args.cnf_dir / f"{group_id}_f_clique_upper.cnf"
        variables, clauses = write_upper_cnf(cnf, len(candidates), nonedges, upper_bound)
        mapping = args.mapping_dir / f"{group_id}_mapping.json"
        mapping_payload = {
            "group_id": group_id,
            "group_order": len(group),
            "identity_index": identity_index,
            "candidate_group_indices": candidates,
            "candidate_permutations": [group[index] for index in candidates],
            "candidate_cycle_types": sorted({cycle_type(group[index]) for index in candidates}),
            "maximum_candidate_clique_witness_indices": witness,
            "maximum_candidate_clique_witness": [group[index] for index in witness],
        }
        mapping.write_text(json.dumps(mapping_payload, indent=2, sort_keys=True) + "\n")
        results.append(
            {
                "group_id": group_id,
                "group_order": len(group),
                "closure_ok": closure_ok,
                "transitive": transitive,
                "primitive": primitive,
                "f_candidate_count": len(candidates),
                "f_candidate_cycle_types": [list(item) for item in sorted({cycle_type(group[index]) for index in candidates})],
                "compatibility_nonedges": len(nonedges),
                "maximum_f_clique_including_identity": maximum + 1,
                "upper_bound_cnf_requires_candidate_clique": upper_bound,
                "upper_bound_cnf_variables": variables,
                "upper_bound_cnf_clauses": clauses,
                "upper_bound_cnf_path": str(cnf),
                "upper_bound_cnf_sha256": sha(cnf),
                "mapping_path": str(mapping),
                "mapping_sha256": sha(mapping),
                "direct_exclusion": len(candidates) == 0,
            }
        )
    payload = {
        "encoding_version": "degree10_primitive_group_f_clique_v1",
        "degree": 10,
        "small_primitive_groups": results,
        "external_classification_boundary": {
            "primitive_group_orders_degree10": [60, 120, 360, 720, 720, 720, 1440, 1814400, 3628800],
            "unexcluded_groups": ["A10", "S10"],
            "dependency": "completeness of the standard primitive permutation group classification/library",
        },
        "elapsed_seconds": time.time() - started,
        "claim_boundary": "small primitive closures excluded; no n=10 FFF existence or nonexistence result",
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Degree-10 primitive-group F-clique generation", ""]
    for item in results:
        lines.append(
            f"{item['group_id']}: order={item['group_order']}, F candidates={item['f_candidate_count']}, "
            f"max clique with identity={item['maximum_f_clique_including_identity']}, "
            f"upper CNF={item['upper_bound_cnf_variables']}/{item['upper_bound_cnf_clauses']}"
        )
    lines.extend(
        [
            "",
            "Classification consequence after proof checks: only A10 or S10 can remain as a primitive generated group.",
            "Scope: C38 open; C40 absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
