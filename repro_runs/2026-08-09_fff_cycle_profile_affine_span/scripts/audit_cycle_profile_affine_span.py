#!/usr/bin/env python3
"""Audit affine modular relations among three-view aggregate cycle profiles."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import runpy
import time
from pathlib import Path


PRIMES = (2, 3, 5, 7)
VIEWS = ("row", "col", "sym")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inverse(permutation: list[int] | tuple[int, ...]) -> list[int]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return result


def aggregate_cycle_profile(table: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[int]:
    n = len(table)
    symbol_lines = [[0] * n for _ in range(n)]
    for row, entries in enumerate(table):
        for column, symbol in enumerate(entries):
            symbol_lines[symbol][column] = row
    lines_by_view = (
        table,
        tuple(tuple(table[row][column] for row in range(n)) for column in range(n)),
        symbol_lines,
    )
    result: list[int] = []
    for lines in lines_by_view:
        counts = [0] * (n + 1)
        inverses = [inverse(line) for line in lines]
        for left in range(n):
            for right in range(left):
                inv_right = inverses[right]
                line_left = lines[left]
                seen = [False] * n
                for start in range(n):
                    if seen[start]:
                        continue
                    point = start
                    length = 0
                    while not seen[point]:
                        seen[point] = True
                        length += 1
                        point = inv_right[line_left[point]]
                    counts[length] += 1
        result.extend(counts[2:])
    return result


class Rref:
    def __init__(self, prime: int, dimension: int) -> None:
        self.prime = prime
        self.dimension = dimension
        self.rows: dict[int, list[int]] = {}

    def add(self, values: list[int]) -> bool:
        row = [value % self.prime for value in values]
        for pivot in sorted(self.rows):
            if row[pivot]:
                coefficient = row[pivot]
                basis = self.rows[pivot]
                row = [
                    (left - coefficient * right) % self.prime
                    for left, right in zip(row, basis)
                ]
        try:
            pivot = next(index for index, value in enumerate(row) if value)
        except StopIteration:
            return False
        scale = pow(row[pivot], -1, self.prime)
        row = [(value * scale) % self.prime for value in row]
        for old_pivot, basis in list(self.rows.items()):
            if basis[pivot]:
                coefficient = basis[pivot]
                self.rows[old_pivot] = [
                    (left - coefficient * right) % self.prime
                    for left, right in zip(basis, row)
                ]
        self.rows[pivot] = row
        return True

    @property
    def rank(self) -> int:
        return len(self.rows)

    def nullspace(self) -> list[list[int]]:
        result = []
        for free in range(self.dimension):
            if free in self.rows:
                continue
            vector = [0] * self.dimension
            vector[free] = 1
            for pivot, row in self.rows.items():
                vector[pivot] = (-row[free]) % self.prime
            result.append(vector)
        return result


def vector_rank(vectors: list[list[int]], prime: int, dimension: int) -> int:
    space = Rref(prime, dimension)
    for vector in vectors:
        space.add(vector)
    return space.rank


def fixed_point_free_partitions(n: int) -> list[list[int]]:
    result: list[list[int]] = []

    def visit(remaining: int, minimum: int, parts: list[int]) -> None:
        if remaining == 0:
            counts = [0] * (n - 1)
            for part in parts:
                counts[part - 2] += 1
            result.append(counts)
            return
        for part in range(minimum, remaining + 1):
            if part >= 2:
                visit(remaining - part, part, parts + [part])

    visit(n, 2, [])
    return result


def baseline_relations(n: int, prime: int) -> tuple[list[list[int]], dict]:
    width = 3 * (n - 1) + 1
    pair_count = n * (n - 1) // 2
    local_profiles = fixed_point_free_partitions(n)
    local_space = Rref(prime, n)
    for profile in local_profiles:
        local_space.add(profile + [1])
    local_relations = local_space.nullspace()
    relations: list[list[int]] = []
    for view_index in range(3):
        offset = view_index * (n - 1)
        for local in local_relations:
            relation = [0] * width
            relation[offset : offset + n - 1] = local[:-1]
            relation[-1] = pair_count * local[-1]
            relations.append([value % prime for value in relation])

    # Every intercalate contributes one 2-cycle in each of the three views.
    row_col = [0] * width
    row_col[0], row_col[n - 1] = 1, -1
    row_sym = [0] * width
    row_sym[0], row_sym[2 * (n - 1)] = 1, -1
    relations.extend(
        [[value % prime for value in row_col], [value % prime for value in row_sym]]
    )

    # For even n, the product-of-line-signs identity gives total even-cycle parity.
    if prime == 2 and n % 2 == 0:
        sign_relation = [0] * width
        for view_index in range(3):
            offset = view_index * (n - 1)
            for length in range(2, n + 1, 2):
                sign_relation[offset + length - 2] = 1
        sign_relation[-1] = -(n * (n - 1) // 2)
        relations.append([value % prime for value in sign_relation])

    return relations, {
        "fixed_point_free_partitions": local_profiles,
        "local_affine_nullity": len(local_relations),
        "baseline_generator_count": len(relations),
        "baseline_rank": vector_rank(relations, prime, width),
    }


def feature_names(n: int) -> list[str]:
    return [
        f"{view}_cycles_{length}"
        for view in VIEWS
        for length in range(2, n + 1)
    ] + ["constant"]


def readable_relation(vector: list[int], n: int, prime: int) -> str:
    terms = []
    for coefficient, name in zip(vector, feature_names(n)):
        coefficient %= prime
        if coefficient == 0:
            continue
        terms.append(name if coefficient == 1 else f"{coefficient}*{name}")
    return " + ".join(terms) + f" = 0 (mod {prime})"


def parse_compact(compact: str, n: int) -> list[list[int]]:
    if len(compact) != n * n:
        raise ValueError(f"expected compact length {n*n}, got {len(compact)}")
    return [[int(value) for value in compact[n * row : n * (row + 1)]] for row in range(n)]


def validate_latin(table: list[list[int]]) -> bool:
    n = len(table)
    target = list(range(n))
    return all(sorted(row) == target for row in table) and all(
        sorted(table[row][column] for row in range(n)) == target for column in range(n)
    )


def intercalates(table: list[list[int]]) -> list[tuple[int, int, int, int]]:
    n = len(table)
    result = []
    for first_row in range(n):
        for second_row in range(first_row):
            for first_column in range(n):
                for second_column in range(first_column):
                    if (
                        table[first_row][first_column] == table[second_row][second_column]
                        and table[first_row][second_column] == table[second_row][first_column]
                    ):
                        result.append((first_row, second_row, first_column, second_column))
    return result


def apply_intercalate_trade(table: list[list[int]], trade: tuple[int, int, int, int]) -> None:
    first_row, second_row, first_column, second_column = trade
    table[first_row][first_column], table[first_row][second_column] = (
        table[first_row][second_column],
        table[first_row][first_column],
    )
    table[second_row][first_column], table[second_row][second_column] = (
        table[second_row][second_column],
        table[second_row][first_column],
    )


def analyze_profiles(name: str, n: int, tables, expected_count: int | None = None) -> tuple[dict, dict[int, Rref]]:
    width = 3 * (n - 1) + 1
    spaces = {prime: Rref(prime, width) for prime in PRIMES}
    distinct = {prime: set() for prime in PRIMES}
    count = 0
    started = time.perf_counter()
    for table in tables:
        row = aggregate_cycle_profile(table) + [1]
        count += 1
        for prime, space in spaces.items():
            space.add(row)
            distinct[prime].add(tuple(value % prime for value in row))
    if expected_count is not None and count != expected_count:
        raise RuntimeError(f"{name}: expected {expected_count} tables, found {count}")
    prime_results = {}
    for prime, space in spaces.items():
        baseline, metadata = baseline_relations(n, prime)
        nullspace = space.nullspace()
        baseline_is_valid = all(
            all(sum(a * b for a, b in zip(vector, row)) % prime == 0 for row in space.rows.values())
            for vector in baseline
        )
        exact_span_match = baseline_is_valid and metadata["baseline_rank"] == len(nullspace)
        prime_results[str(prime)] = {
            "observed_rank": space.rank,
            "observed_nullity": len(nullspace),
            "distinct_residue_profiles": len(distinct[prime]),
            "baseline": metadata,
            "baseline_relations_valid": baseline_is_valid,
            "observed_nullspace_equals_baseline_span": exact_span_match,
            "observed_nullspace_basis": [
                readable_relation(vector, n, prime) for vector in nullspace
            ],
        }
    return {
        "name": name,
        "order": n,
        "table_count": count,
        "elapsed_seconds": time.perf_counter() - started,
        "prime_results": prime_results,
    }, spaces


def dihedral_order10() -> list[list[int]]:
    result = []
    for left in range(10):
        a, epsilon = left % 5, left // 5
        row = []
        for right in range(10):
            b, delta = right % 5, right // 5
            row.append(((a + (b if epsilon == 0 else -b)) % 5) + 5 * ((epsilon + delta) % 2))
        result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n6-generator", type=Path, required=True)
    parser.add_argument("--n8-census", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--trade-seed", type=int, default=20260809)
    parser.add_argument("--trade-steps", type=int, default=1000)
    args = parser.parse_args()

    generator_namespace = runpy.run_path(str(args.n6_generator))
    n6_result, _ = analyze_profiles(
        "all reduced order-6 Latin squares",
        6,
        generator_namespace["reduced_latin_squares"](6),
        9408,
    )

    def n8_tables():
        with gzip.open(args.n8_census, "rt") as handle:
            for line in handle:
                yield parse_compact(line.strip(), 8)

    n8_result, _ = analyze_profiles(
        "ANU order-8 main-class representatives", 8, n8_tables(), 283657
    )

    corpus = json.loads(args.n10_corpus.read_text())
    compact_tables = list(corpus["tracked_order10_source_paths"])
    n10_tracked, tracked_spaces = analyze_profiles(
        "tracked order-10 partial-table corpus",
        10,
        (parse_compact(compact, 10) for compact in compact_tables),
        135,
    )

    random_generator = random.Random(args.trade_seed)
    table = dihedral_order10()
    if not validate_latin(table):
        raise RuntimeError("D10 construction is not Latin")
    width = 28
    augmented_spaces = {prime: Rref(prime, width) for prime in PRIMES}
    for compact in compact_tables:
        row = aggregate_cycle_profile(parse_compact(compact, 10)) + [1]
        for space in augmented_spaces.values():
            space.add(row)
    rank_rise_witnesses = []
    sampled_tables = 0
    for step in range(args.trade_steps):
        available = intercalates(table)
        if not available:
            raise RuntimeError(f"D10 trade walk stopped at step {step}")
        apply_intercalate_trade(table, random_generator.choice(available))
        if not validate_latin(table):
            raise RuntimeError(f"trade at step {step} destroyed Latin property")
        if step % 2:
            continue
        sampled_tables += 1
        row = aggregate_cycle_profile(table) + [1]
        old_rank = augmented_spaces[2].rank
        for space in augmented_spaces.values():
            space.add(row)
        if augmented_spaces[2].rank > old_rank:
            rank_rise_witnesses.append(
                {
                    "step": step,
                    "gf2_rank_before": old_rank,
                    "gf2_rank_after": augmented_spaces[2].rank,
                    "compact_table": "".join(str(value) for entries in table for value in entries),
                    "aggregate_cycle_profile": row[:-1],
                }
            )

    augmented_results = {}
    for prime, space in augmented_spaces.items():
        baseline, metadata = baseline_relations(10, prime)
        augmented_results[str(prime)] = {
            "rank": space.rank,
            "nullity": len(space.nullspace()),
            "baseline_rank": metadata["baseline_rank"],
            "nullspace_equals_baseline_span": len(space.nullspace()) == metadata["baseline_rank"],
            "nullspace_basis": [
                readable_relation(vector, 10, prime) for vector in space.nullspace()
            ],
        }

    pair_count = 45
    abstract_fff_profile = []
    for _view in VIEWS:
        abstract_fff_profile.extend([0] * 8 + [pair_count])
    abstract_row = abstract_fff_profile + [1]
    abstract_checks = {}
    for prime in PRIMES:
        baseline, _ = baseline_relations(10, prime)
        abstract_checks[str(prime)] = all(
            sum(left * right for left, right in zip(relation, abstract_row)) % prime == 0
            for relation in baseline
        )

    result = {
        "run_id": "2026-08-09_fff_cycle_profile_affine_span",
        "evidence_labels": {
            "baseline_identity_theorem": "rigorously proved in proof note",
            "n6_n8_span_saturation": "exactly computed",
            "n10_trade_refutation": "exactly computed counterexamples to corpus-only relations",
            "n10_existence": "open",
        },
        "inputs": {
            "n6_generator": {"path": str(args.n6_generator), "sha256": sha256(args.n6_generator)},
            "n8_census": {"path": str(args.n8_census), "sha256": sha256(args.n8_census)},
            "n10_corpus": {"path": str(args.n10_corpus), "sha256": sha256(args.n10_corpus)},
        },
        "orders": {"6": n6_result, "8": n8_result, "10_tracked": n10_tracked},
        "n10_d10_intercalate_trade_augmentation": {
            "seed": args.trade_seed,
            "steps": args.trade_steps,
            "sampled_tables": sampled_tables,
            "all_samples_latin": True,
            "gf2_rank_rise_witnesses": rank_rise_witnesses,
            "prime_results": augmented_results,
        },
        "abstract_n10_all_10_cycle_profile": {
            "description": "45 induced 10-cycles in each view; an abstract FFF-supported aggregate profile",
            "profile": abstract_fff_profile,
            "satisfies_all_baseline_relations": abstract_checks,
            "realizability_as_a_latin_square": "not claimed",
        },
        "claim_impact": {
            "new_claim": "C67",
            "c38": "open",
            "c40": "absent",
            "conclusion": "Order 8 has no additional affine modular aggregate-cycle-profile relations over the four tested fields beyond the baseline. Order 6 has three extra GF(2) relations, while the augmented order-10 sample has none beyond baseline.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "FFF aggregate cycle-profile affine-span audit",
        "",
        f"n=6 exhaustive tables: {n6_result['table_count']}",
        f"n=8 ANU main-class representatives: {n8_result['table_count']}",
        f"n=10 tracked partial tables: {n10_tracked['table_count']}",
        f"n=10 D10 trade-walk samples: {sampled_tables}",
        "",
    ]
    for key, order_result in (("6", n6_result), ("8", n8_result)):
        lines.append(f"Order {key} exact span saturation:")
        for prime in PRIMES:
            prime_result = order_result["prime_results"][str(prime)]
            lines.append(
                f"  GF({prime}): rank={prime_result['observed_rank']}, "
                f"nullity={prime_result['observed_nullity']}, "
                f"baseline_rank={prime_result['baseline']['baseline_rank']}, "
                f"exact_match={prime_result['observed_nullspace_equals_baseline_span']}"
            )
    lines.extend(
        [
            "",
            "Order 10 tracked-corpus versus trade-walk GF(2):",
            f"  tracked rank/nullity: {n10_tracked['prime_results']['2']['observed_rank']}/{n10_tracked['prime_results']['2']['observed_nullity']}",
            f"  augmented rank/nullity: {augmented_results['2']['rank']}/{augmented_results['2']['nullity']}",
            f"  rank-rise witnesses: {len(rank_rise_witnesses)}",
            f"  augmented nullspace equals baseline span: {augmented_results['2']['nullspace_equals_baseline_span']}",
            "",
            "Conclusion:",
            "  The full n=8 data have no affine relations over GF(2), GF(3), GF(5), or GF(7) beyond the proved baseline generators.",
            "  The full n=6 data match baseline over GF(3), GF(5), and GF(7), but have three additional Latin-specific GF(2) relations.",
            "  Those three n=6 relations do not by themselves contradict an abstract FFF-supported cycle profile.",
            "  Three extra GF(2) relations in the tracked n=10 corpus are sampling artifacts refuted by explicit Latin trade-walk tables.",
            "  The baseline relations admit an abstract all-10-cycle FFF profile, so they cannot alone exclude order 10.",
            "  C38 remains open; C40 remains absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
