#!/usr/bin/env python3
"""Build the exact projection-voltage CNF for pair-imprimitive row-F families."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Pool:
    def __init__(self) -> None:
        self.next_id = 1

    def one(self) -> int:
        value = self.next_id
        self.next_id += 1
        return value

    @property
    def count(self) -> int:
        return self.next_id - 1


def exactly_k(clauses: list[list[int]], variables: list[int], target: int) -> None:
    try:
        from pysat.card import CardEnc, EncType
    except ImportError as exc:
        raise RuntimeError("python-sat is required outside Git for cardinality encoding") from exc
    top = max(abs(lit) for clause in clauses for lit in clause) if clauses else 0
    top = max(top, max(variables, default=0))
    encoded = CardEnc.equals(lits=variables, bound=target, top_id=top, encoding=EncType.totalizer)
    clauses.extend([list(clause) for clause in encoded.clauses])
    return encoded.nv


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


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def relative(first: tuple[int, ...], second: tuple[int, ...]) -> tuple[int, ...]:
    """Return second^-1 composed with first."""
    inv = inverse(second)
    return tuple(inv[first[index]] for index in range(len(first)))


def add_xor_equals_one(
    clauses: list[list[int]], pool: Pool, variables: list[int], guards: tuple[int, int]
) -> int:
    if not variables:
        clauses.append([-guards[0], -guards[1]])
        return 0
    current = variables[0]
    auxiliaries = 0
    for variable in variables[1:]:
        out = pool.one()
        auxiliaries += 1
        # out <-> current XOR variable
        clauses.extend(
            [
                [-current, -variable, -out],
                [current, variable, -out],
                [current, -variable, out],
                [-current, variable, out],
            ]
        )
        current = out
    clauses.append([-guards[0], -guards[1], current])
    return auxiliaries


def write_dimacs(path: Path, variable_count: int, clauses: list[list[int]]) -> None:
    with path.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {variable_count} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", type=int, required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    p = args.p
    if p < 3 or p % 2 == 0:
        raise ValueError("p must be an odd integer at least 3")
    permutations = list(itertools.permutations(range(p)))
    identity_index = permutations.index(tuple(range(p)))
    pool = Pool()
    select = [pool.one() for _ in permutations]
    flips = [[pool.one() for _ in range(p)] for _ in permutations]
    clauses: list[list[int]] = []

    clauses.append([select[identity_index]])
    for bit in flips[identity_index]:
        clauses.append([-bit])
    for index in range(len(permutations)):
        for bit in flips[index]:
            clauses.append([-bit, select[index]])

    # Exactly two selected projections map every source block to every target block.
    cardinality_aux_start = pool.count + 1
    cardinality_top = pool.count
    for source in range(p):
        for target in range(p):
            variables = [select[index] for index, phi in enumerate(permutations) if phi[source] == target]
            try:
                from pysat.card import CardEnc, EncType
            except ImportError as exc:
                raise RuntimeError("python-sat is required outside Git") from exc
            encoded = CardEnc.equals(
                lits=variables,
                bound=2,
                top_id=max(pool.count, cardinality_top),
                encoding=EncType.totalizer,
            )
            clauses.extend([list(clause) for clause in encoded.clauses])
            cardinality_top = encoded.nv
            pool.next_id = max(pool.next_id, encoded.nv + 1)
            # Exactly one of the two selected maps has fiber bit one.
            bit_variables = [flips[index][source] for index, phi in enumerate(permutations) if phi[source] == target]
            encoded_bits = CardEnc.equals(
                lits=bit_variables,
                bound=1,
                top_id=max(pool.count, cardinality_top),
                encoding=EncType.totalizer,
            )
            clauses.extend([list(clause) for clause in encoded_bits.clauses])
            cardinality_top = encoded_bits.nv
            pool.next_id = max(pool.next_id, encoded_bits.nv + 1)

    odd_cycle_constraints = 0
    parity_auxiliaries = 0
    for left in range(len(permutations)):
        for right in range(left + 1, len(permutations)):
            quotient = relative(permutations[left], permutations[right])
            for cycle in cycles(quotient):
                if len(cycle) % 2 == 0:
                    continue
                variables = [flips[left][index] for index in cycle] + [
                    flips[right][index] for index in cycle
                ]
                parity_auxiliaries += add_xor_equals_one(
                    clauses, pool, variables, (select[left], select[right])
                )
                odd_cycle_constraints += 1

    args.cnf.parent.mkdir(parents=True, exist_ok=True)
    write_dimacs(args.cnf, pool.count, clauses)
    mapping = [
        {
            "index": index,
            "permutation": list(phi),
            "select_variable": select[index],
            "flip_variables": flips[index],
        }
        for index, phi in enumerate(permutations)
    ]
    metadata = {
        "encoding_version": "pairblock_projection_voltage_v1_exact",
        "p": p,
        "degree": 2 * p,
        "projection_count": len(permutations),
        "selected_projection_count_implied": 2 * p,
        "identity_projection_index": identity_index,
        "variables": pool.count,
        "clauses": len(clauses),
        "odd_cycle_voltage_constraints": odd_cycle_constraints,
        "parity_auxiliary_variables": parity_auxiliaries,
        "cardinality_auxiliary_variable_range": [cardinality_aux_start, cardinality_top],
        "projection_mapping": mapping,
        "cnf_path": str(args.cnf),
        "cnf_sha256": sha256_file(args.cnf),
        "scope": "pair-imprimitive row-F sharply transitive families only; not full FFF",
    }
    args.metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Pair-block projection-voltage CNF\n\n"
        f"p: {p}\ndegree: {2*p}\nprojections: {len(permutations)}\n"
        f"selected projections implied: {2*p}\nvariables: {pool.count}\n"
        f"clauses: {len(clauses)}\nodd-cycle voltage constraints: {odd_cycle_constraints}\n"
        f"CNF SHA-256: {metadata['cnf_sha256']}\n"
        "scope: pair-imprimitive row-F only; not full FFF\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
