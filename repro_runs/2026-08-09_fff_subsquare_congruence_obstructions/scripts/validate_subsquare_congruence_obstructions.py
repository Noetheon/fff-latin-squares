#!/usr/bin/env python3
"""Validate the subsquare and congruence obstruction theorems on frozen data."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
VIEWS = ("row", "col", "sym")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_compact(compact: str) -> list[list[int]]:
    n = int(len(compact) ** 0.5)
    if n * n != len(compact):
        raise ValueError(f"invalid compact table length {len(compact)}")
    return [[int(value) for value in compact[r * n : (r + 1) * n]] for r in range(n)]


def compact_table(table: list[list[int]]) -> str:
    return "".join(str(value) for row in table for value in row)


def validate_latin(table: list[list[int]]) -> bool:
    n = len(table)
    expected = list(range(n))
    return (
        all(len(row) == n and sorted(row) == expected for row in table)
        and all(sorted(table[row][col] for row in range(n)) == expected for col in range(n))
    )


def view_lines(table: list[list[int]], view: str) -> list[list[int]]:
    n = len(table)
    if view == "row":
        return table
    if view == "col":
        return [[table[row][col] for row in range(n)] for col in range(n)]
    if view == "sym":
        return [
            [next(row for row in range(n) if table[row][col] == symbol) for col in range(n)]
            for symbol in range(n)
        ]
    raise ValueError(view)


def cycle_lengths(permutation: list[int]) -> tuple[int, ...]:
    seen = [False] * len(permutation)
    lengths: list[int] = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        cursor = start
        length = 0
        while not seen[cursor]:
            seen[cursor] = True
            cursor = permutation[cursor]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def view_has_odd_cycle(lines: list[list[int]]) -> bool:
    inverses = []
    for line in lines:
        inverse = [0] * len(line)
        for index, value in enumerate(line):
            inverse[value] = index
        inverses.append(inverse)
    for first, second in itertools.combinations(range(len(lines)), 2):
        permutation = [inverses[second][value] for value in lines[first]]
        if any(length > 1 and length % 2 for length in cycle_lengths(permutation)):
            return True
    return False


def pattern(table: list[list[int]]) -> str:
    return "".join("T" if view_has_odd_cycle(view_lines(table, view)) else "F" for view in VIEWS)


def subsquares(table: list[list[int]], order: int) -> list[dict[str, Any]]:
    n = len(table)
    found = []
    for rows in itertools.combinations(range(n), order):
        for columns in itertools.combinations(range(n), order):
            symbols = sorted({table[row][column] for row in rows for column in columns})
            if len(symbols) != order:
                continue
            symbol_index = {symbol: index for index, symbol in enumerate(symbols)}
            reduced_labels = [
                [symbol_index[table[row][column]] for column in columns]
                for row in rows
            ]
            if not validate_latin(reduced_labels):
                raise AssertionError("detected block is not a Latin subsquare")
            found.append(
                {
                    "rows": list(rows),
                    "columns": list(columns),
                    "symbols": symbols,
                    "pattern": pattern(reduced_labels),
                }
            )
    return found


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("latin_trade_search_congruence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pair_partitions(elements: tuple[int, ...]) -> Iterable[list[tuple[int, ...]]]:
    if not elements:
        yield []
        return
    first = elements[0]
    for index in range(1, len(elements)):
        second = elements[index]
        rest = elements[1:index] + elements[index + 1 :]
        for partition in pair_partitions(rest):
            yield [(first, second), *partition]


def two_block_partitions(n: int) -> Iterable[list[tuple[int, ...]]]:
    block_size = n // 2
    for rest in itertools.combinations(range(1, n), block_size - 1):
        first = (0, *rest)
        first_set = set(first)
        second = tuple(value for value in range(n) if value not in first_set)
        yield [first, second]


def is_congruence(table: list[list[int]], partition: list[tuple[int, ...]]) -> bool:
    block_of = {value: block for block, values in enumerate(partition) for value in values}
    quotient_products: dict[tuple[int, int], int] = {}
    for left in range(len(table)):
        for right in range(len(table)):
            key = (block_of[left], block_of[right])
            value = block_of[table[left][right]]
            previous = quotient_products.setdefault(key, value)
            if previous != value:
                return False
    return True


def congruence_block_sizes(table: list[list[int]]) -> list[int]:
    n = len(table)
    candidates: list[tuple[int, Iterable[list[tuple[int, ...]]]]] = []
    if n % 2 == 0:
        candidates.append((2, pair_partitions(tuple(range(n)))))
        if n // 2 > 1:
            candidates.append((n // 2, two_block_partitions(n)))
    found = []
    for block_size, partitions in candidates:
        if any(is_congruence(table, partition) for partition in partitions):
            found.append(block_size)
    return found


def binary_extension(quotient_order: int, mask: int) -> list[list[int]]:
    n = 2 * quotient_order
    table = []
    for encoded_row in range(n):
        quotient_row, row_bit = divmod(encoded_row, 2)
        row = []
        for encoded_column in range(n):
            quotient_column, column_bit = divmod(encoded_column, 2)
            output_block = (quotient_row + quotient_column) % quotient_order
            twist = (mask >> (quotient_row * quotient_order + quotient_column)) & 1
            row.append(2 * output_block + (row_bit ^ column_bit ^ twist))
        table.append(row)
    return table


def explicit_nongroup_fff_loop() -> list[list[int]]:
    table = []
    for encoded_row in range(8):
        left, left_bit = divmod(encoded_row, 2)
        row = []
        for encoded_column in range(8):
            right, right_bit = divmod(encoded_column, 2)
            twist = int(left == 1 and right == 1)
            row.append(2 * ((left + right) % 4) + (left_bit ^ right_bit ^ twist))
        table.append(row)
    return table


def is_associative(table: list[list[int]]) -> bool:
    n = len(table)
    return all(
        table[table[x][y]][z] == table[x][table[y][z]]
        for x in range(n)
        for y in range(n)
        for z in range(n)
    )


def identity_basis_closed(table: list[list[int]]) -> bool:
    translations = {tuple(row) for row in table}
    for first in translations:
        for second in translations:
            composition = tuple(first[second[value]] for value in range(len(table)))
            if composition not in translations:
                return False
    return True


def extract_table(payload: Any) -> list[list[int]] | None:
    if isinstance(payload, dict):
        for key in ("table", "decoded_table", "latin_square"):
            value = payload.get(key)
            if isinstance(value, list) and value and isinstance(value[0], list):
                return [[int(cell) for cell in row] for row in value]
    return None


def collect_tracked_n10_tables(root: Path) -> tuple[dict[str, list[list[int]]], dict[str, list[str]]]:
    tables: dict[str, list[list[int]]] = {}
    sources: dict[str, list[str]] = {}
    for path in sorted((root / "repro_runs").glob("*/results/**/*table*.json")):
        try:
            table = extract_table(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if table is None or len(table) != 10 or not validate_latin(table):
            continue
        compact = compact_table(table)
        tables.setdefault(compact, table)
        sources.setdefault(compact, []).append(str(path.relative_to(root)))
    return tables, sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-json", type=Path, required=True)
    parser.add_argument("--small-order-generator", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    core = json.loads(args.core_json.read_text(encoding="utf-8"))
    fff_entries = core["counterexamples"]
    if len(fff_entries) != 230:
        raise AssertionError(f"expected 230 order-8 FFF entries, found {len(fff_entries)}")

    intercalate_counts: Counter[int] = Counter()
    order4_counts: Counter[int] = Counter()
    order3_total = 0
    monotonicity_failures = []
    extremal = []
    per_entry = []
    for entry in fff_entries:
        table = parse_compact(entry["square"])
        by_order = {order: subsquares(table, order) for order in (2, 3, 4)}
        for order, items in by_order.items():
            for item in items:
                if item["pattern"] != "FFF":
                    monotonicity_failures.append(
                        {"line_number": entry["line_number"], "order": order, "subsquare": item}
                    )
        counts = {str(order): len(items) for order, items in by_order.items()}
        intercalate_counts[counts["2"]] += 1
        order3_total += counts["3"]
        order4_counts[counts["4"]] += 1
        per_entry.append(
            {
                "line_number": entry["line_number"],
                "group_isotopic": entry["group_isotopic"],
                "subsquare_counts": counts,
            }
        )
    minimum_intercalates = min(intercalate_counts)
    maximum_intercalates = max(intercalate_counts)
    for item in per_entry:
        count = item["subsquare_counts"]["2"]
        if count in (minimum_intercalates, maximum_intercalates):
            extremal.append(item)

    generator = load_generator(args.small_order_generator)
    order6_congruence_counts: Counter[str] = Counter()
    order6_non_ttt_congruence_examples = []
    order6_total = 0
    for index, generated in enumerate(generator.reduced_latin_squares(6), start=1):
        table = [list(row) for row in generated]
        order6_total += 1
        block_sizes = congruence_block_sizes(table)
        if not block_sizes:
            continue
        table_pattern = pattern(table)
        key = f"blocks_{'_'.join(map(str, block_sizes))}:{table_pattern}"
        order6_congruence_counts[key] += 1
        if table_pattern != "TTT":
            order6_non_ttt_congruence_examples.append(
                {"index": index, "block_sizes": block_sizes, "pattern": table_pattern}
            )

    extension3_counts: Counter[str] = Counter()
    for mask in range(1 << 9):
        table = binary_extension(3, mask)
        if not validate_latin(table):
            raise AssertionError("binary extension is not Latin")
        extension3_counts[pattern(table)] += 1

    rng = random.Random(20260809)
    q5_masks = {0, (1 << 25) - 1}
    q5_masks.update(1 << bit for bit in range(25))
    while len(q5_masks) < 4096:
        q5_masks.add(rng.getrandbits(25))
    extension5_counts: Counter[str] = Counter()
    for mask in sorted(q5_masks):
        table = binary_extension(5, mask)
        if not validate_latin(table):
            raise AssertionError("binary extension is not Latin")
        extension5_counts[pattern(table)] += 1

    explicit_loop = explicit_nongroup_fff_loop()
    explicit_loop_checks = {
        "latin": validate_latin(explicit_loop),
        "identity_zero": all(explicit_loop[0][x] == x and explicit_loop[x][0] == x for x in range(8)),
        "pattern": pattern(explicit_loop),
        "associative": is_associative(explicit_loop),
        "identity_basis_closed": identity_basis_closed(explicit_loop),
        "left_associativity_value": explicit_loop[explicit_loop[2][2]][4],
        "right_associativity_value": explicit_loop[2][explicit_loop[2][4]],
        "compact_table": compact_table(explicit_loop),
    }

    tracked_n10, tracked_sources = collect_tracked_n10_tables(ROOT)
    tracked_congruence_counts: Counter[str] = Counter()
    tracked_imprimitive = []
    for compact, table in tracked_n10.items():
        block_sizes = congruence_block_sizes(table)
        tracked_congruence_counts["simple" if not block_sizes else "imprimitive"] += 1
        if block_sizes:
            tracked_imprimitive.append(
                {
                    "compact_table": compact,
                    "block_sizes": block_sizes,
                    "pattern": pattern(table),
                    "sources": tracked_sources[compact],
                }
            )

    result = {
        "evidence_labels": {
            "theorems": "rigorously proved in proof note",
            "computations": "exactly computed except explicitly labelled deterministic q5 sample",
        },
        "inputs": {
            "core_json": {
                "path": str(args.core_json.resolve()),
                "sha256": sha256_file(args.core_json),
            },
            "small_order_generator": {
                "path": str(args.small_order_generator.resolve()),
                "sha256": sha256_file(args.small_order_generator),
            },
        },
        "order8_fff_subsquare_census": {
            "fff_square_count": len(fff_entries),
            "pattern_monotonicity_failure_count": len(monotonicity_failures),
            "pattern_monotonicity_failures": monotonicity_failures,
            "order3_subsquare_total": order3_total,
            "intercalate_count_distribution": dict(sorted(intercalate_counts.items())),
            "order4_subsquare_count_distribution": dict(sorted(order4_counts.items())),
            "minimum_intercalates": minimum_intercalates,
            "maximum_intercalates": maximum_intercalates,
            "extremal_entries": extremal,
            "half_order_counts_are_multiples_of_four": all(count % 4 == 0 for count in order4_counts),
        },
        "order6_congruence_census": {
            "reduced_square_count": order6_total,
            "congruence_pattern_counts": dict(sorted(order6_congruence_counts.items())),
            "congruence_imprimitive_total": sum(order6_congruence_counts.values()),
            "non_ttt_congruence_example_count": len(order6_non_ttt_congruence_examples),
            "non_ttt_congruence_examples": order6_non_ttt_congruence_examples,
        },
        "binary_extensions": {
            "cyclic_quotient_order3": {
                "status": "exhaustive",
                "twist_function_count": 1 << 9,
                "pattern_counts": dict(sorted(extension3_counts.items())),
            },
            "cyclic_quotient_order5": {
                "status": "deterministic sample; theorem does not depend on sample",
                "seed": 20260809,
                "twist_function_sample_count": len(q5_masks),
                "full_twist_space_size": 1 << 25,
                "pattern_counts": dict(sorted(extension5_counts.items())),
            },
            "explicit_nongroup_fff_loop": explicit_loop_checks,
        },
        "tracked_order10_tables": {
            "distinct_valid_table_count": len(tracked_n10),
            "representative_operation_congruence_counts": dict(sorted(tracked_congruence_counts.items())),
            "imprimitive_examples": tracked_imprimitive,
            "scope_note": "This checks the stored operation only, not every isotope, and proves no existence result.",
        },
        "overall_ok": (
            not monotonicity_failures
            and order3_total == 0
            and not order6_non_ttt_congruence_examples
            and extension3_counts == Counter({"TTT": 512})
            and extension5_counts == Counter({"TTT": len(q5_masks)})
            and explicit_loop_checks["latin"]
            and explicit_loop_checks["identity_zero"]
            and explicit_loop_checks["pattern"] == "FFF"
            and not explicit_loop_checks["associative"]
            and not explicit_loop_checks["identity_basis_closed"]
            and explicit_loop_checks["left_associativity_value"] == 1
            and explicit_loop_checks["right_associativity_value"] == 0
        ),
    }
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    order6_counts = result["order6_congruence_census"]["congruence_pattern_counts"]
    summary = "\n".join(
        [
            "FFF subsquare and congruence obstruction validation",
            "",
            f"Overall OK: {result['overall_ok']}",
            "",
            "Order-8 FFF subsquare census (exact over 230 frozen representatives):",
            f"- pattern-monotonicity failures: {len(monotonicity_failures)}",
            f"- order-3 subsquares: {order3_total}",
            f"- intercalate range: {minimum_intercalates}..{maximum_intercalates}",
            f"- intercalate distribution: {dict(sorted(intercalate_counts.items()))}",
            f"- order-4 subsquare distribution: {dict(sorted(order4_counts.items()))}",
            f"- extremal entries: {extremal}",
            "",
            "Order-6 congruence census (exact over 9,408 reduced squares):",
            f"- congruence-imprimitive squares: {sum(order6_congruence_counts.values())}",
            f"- counts: {order6_counts}",
            f"- non-TTT congruence examples: {len(order6_non_ttt_congruence_examples)}",
            "",
            "Binary extensions of odd cyclic quotients:",
            f"- order-3 quotient: exhaustive 512/512 twists, {dict(extension3_counts)}",
            f"- order-5 quotient: deterministic {len(q5_masks)}-twist sample, {dict(extension5_counts)}",
            "",
            "Explicit theoretical order-8 loop:",
            f"- Latin/identity/pattern: {explicit_loop_checks['latin']}/{explicit_loop_checks['identity_zero']}/{explicit_loop_checks['pattern']}",
            f"- associative: {explicit_loop_checks['associative']}",
            f"- identity-basis closure: {explicit_loop_checks['identity_basis_closed']}",
            "",
            "Tracked order-10 tables:",
            f"- distinct valid tables: {len(tracked_n10)}",
            f"- stored-operation congruence counts: {dict(tracked_congruence_counts)}",
            "",
            "Claim boundary:",
            "- The proof excludes congruence-imprimitive FFF quasigroups of order 2p.",
            "- It does not decide simple quasigroups of order 10; C38 remains open.",
        ]
    ) + "\n"
    args.output_summary.write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
