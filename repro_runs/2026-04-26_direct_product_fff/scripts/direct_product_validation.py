#!/usr/bin/env python3
"""Validate small direct-product FFF examples from frozen order-8 inputs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
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
PATTERN_FROM_NAME = {value: key for key, value in PATTERN_NAMES.items()}
ALL_PATTERN_NAMES = list(PATTERN_FROM_NAME)
VIEWS = ("row", "col", "sym")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_text_input(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="ascii", newline="")
    return path.open("rt", encoding="ascii", newline="")


def iter_compact_squares(path: Path):
    with open_text_input(path) as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            compact = raw_line.strip()
            if compact:
                yield line_number, compact


def parse_compact_square(compact: str) -> tuple[tuple[int, ...], ...]:
    order = int(math.isqrt(len(compact)))
    if order * order != len(compact):
        raise ValueError(f"compact square length is not a square: {len(compact)}")
    return tuple(
        tuple(int(ch) for ch in compact[row * order : (row + 1) * order])
        for row in range(order)
    )


def validate_latin_square(table: tuple[tuple[int, ...], ...]) -> bool:
    order = len(table)
    expected = list(range(order))
    if any(len(row) != order for row in table):
        return False
    if any(sorted(row) != expected for row in table):
        return False
    for col in range(order):
        if sorted(table[row][col] for row in range(order)) != expected:
            return False
    return True


def positions_for_lines(lines: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(lines[0])
    position_maps = []
    for line in lines:
        if len(line) != order:
            raise ValueError(f"inconsistent line length: {line!r}")
        positions = [None] * order
        for index, value in enumerate(line):
            if positions[value] is not None:
                raise ValueError(f"line is not a permutation: {line!r}")
            positions[value] = index
        if any(position is None for position in positions):
            raise ValueError(f"line is not a permutation: {line!r}")
        position_maps.append(tuple(int(position) for position in positions))
    return tuple(position_maps)


def induced_permutation(lines: tuple[tuple[int, ...], ...], first: int, second: int) -> tuple[int, ...]:
    position_maps = positions_for_lines(lines)
    return tuple(position_maps[second][value] for value in lines[first])


def cycle_lengths_by_point(perm: tuple[int, ...]) -> tuple[int, ...]:
    lengths = [0] * len(perm)
    seen = [False] * len(perm)
    for start in range(len(perm)):
        if seen[start]:
            continue
        orbit = []
        cursor = start
        while not seen[cursor]:
            seen[cursor] = True
            orbit.append(cursor)
            cursor = perm[cursor]
        for point in orbit:
            lengths[point] = len(orbit)
    return tuple(lengths)


def cycle_lengths(perm: tuple[int, ...]) -> list[int]:
    lengths = []
    seen = [False] * len(perm)
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


def has_nontrivial_odd_cycle(perm: tuple[int, ...]) -> bool:
    return any(length > 1 and length % 2 == 1 for length in cycle_lengths(perm))


def column_lines(table: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(table)
    return tuple(tuple(table[row][col] for row in range(order)) for col in range(order))


def symbol_lines(table: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    order = len(table)
    lines = [[None] * order for _ in range(order)]
    for row_index, row in enumerate(table):
        for col_index, symbol in enumerate(row):
            if lines[symbol][col_index] is not None:
                raise ValueError("symbol view contains a duplicate occurrence in a column")
            lines[symbol][col_index] = row_index
    return tuple(tuple(int(value) for value in line) for line in lines)


def view_lines(table: tuple[tuple[int, ...], ...], view: str) -> tuple[tuple[int, ...], ...]:
    if view == "row":
        return table
    if view == "col":
        return column_lines(table)
    if view == "sym":
        return symbol_lines(table)
    raise ValueError(f"unknown view: {view}")


def view_has_odd_cycle(table: tuple[tuple[int, ...], ...], view: str) -> bool:
    lines = view_lines(table, view)
    for first, second in combinations(range(len(lines)), 2):
        if has_nontrivial_odd_cycle(induced_permutation(lines, first, second)):
            return True
    return False


def fff_pattern(table: tuple[tuple[int, ...], ...]) -> dict[str, bool]:
    return {view: view_has_odd_cycle(table, view) for view in VIEWS}


def pattern_tuple(pattern: dict[str, bool]) -> tuple[bool, bool, bool]:
    return tuple(pattern[view] for view in VIEWS)


def pattern_name(pattern: dict[str, bool]) -> str:
    return PATTERN_NAMES[pattern_tuple(pattern)]


def pattern_or_name(left_name: str, right_name: str) -> str:
    left = PATTERN_FROM_NAME[left_name]
    right = PATTERN_FROM_NAME[right_name]
    return PATTERN_NAMES[tuple(a or b for a, b in zip(left, right))]


def order8_pattern_count_check(fullscan: dict[str, Any]) -> dict[str, Any]:
    counts = fullscan["scan"]["pattern_counts"]
    missing = [name for name in ALL_PATTERN_NAMES if int(counts.get(name, 0)) <= 0]
    return {
        "source": "order8 fullscan JSON scan.pattern_counts",
        "counts": {name: int(counts.get(name, 0)) for name in ALL_PATTERN_NAMES},
        "all_eight_patterns_nonempty": not missing,
        "missing_or_empty_patterns": missing,
    }


def closure_profile(table: tuple[tuple[int, ...], ...], view: str) -> dict[str, Any]:
    lines = view_lines(table, view)
    base_positions = positions_for_lines((lines[0],))[0]
    basis = tuple(tuple(base_positions[value] for value in line) for line in lines)
    basis_set = set(basis)
    first_failure = None
    for i, left in enumerate(basis):
        for j, right in enumerate(basis):
            composed = tuple(left[right[point]] for point in range(len(left)))
            if composed not in basis_set:
                first_failure = {
                    "left_basis_index": i,
                    "right_basis_index": j,
                    "composition_prefix": list(composed[: min(12, len(composed))]),
                }
                return {
                    "closed": False,
                    "basis_size": len(basis),
                    "distinct_basis_size": len(basis_set),
                    "first_failure": first_failure,
                }
    return {
        "closed": True,
        "basis_size": len(basis),
        "distinct_basis_size": len(basis_set),
        "first_failure": None,
    }


def group_table_cyclic(order: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((i + j) % order for j in range(order)) for i in range(order))


def group_table_c2_squared() -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(i ^ j for j in range(4)) for i in range(4))


def direct_product(
    left: tuple[tuple[int, ...], ...],
    right: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, ...], ...]:
    n = len(left)
    m = len(right)
    rows = []
    for a in range(n):
        for alpha in range(m):
            row = []
            for b in range(n):
                for beta in range(m):
                    row.append(left[a][b] * m + right[alpha][beta])
            rows.append(tuple(row))
    return tuple(rows)


def verify_product_permutation_formula(
    left: tuple[tuple[int, ...], ...],
    right: tuple[tuple[int, ...], ...],
    product: tuple[tuple[int, ...], ...],
) -> dict[str, Any]:
    n = len(left)
    m = len(right)
    checked_pairs = 0
    checked_points = 0
    for view in ("row", "col", "sym"):
        left_lines = view_lines(left, view)
        right_lines = view_lines(right, view)
        product_lines = view_lines(product, view)
        for first in range(n * m):
            a, alpha = divmod(first, m)
            for second in range(first + 1, n * m):
                b, beta = divmod(second, m)
                product_perm = induced_permutation(product_lines, first, second)
                left_perm = induced_permutation(left_lines, a, b)
                right_perm = induced_permutation(right_lines, alpha, beta)
                left_lengths = cycle_lengths_by_point(left_perm)
                right_lengths = cycle_lengths_by_point(right_perm)
                product_lengths = cycle_lengths_by_point(product_perm)
                checked_pairs += 1
                for x in range(n):
                    for y in range(m):
                        expected = left_perm[x] * m + right_perm[y]
                        actual = product_perm[x * m + y]
                        if actual != expected:
                            return {
                                "ok": False,
                                "failed_check": "permutation_formula",
                                "view": view,
                                "first": first,
                                "second": second,
                                "point": x * m + y,
                                "actual": actual,
                                "expected": expected,
                            }
                        expected_length = math.lcm(left_lengths[x], right_lengths[y])
                        actual_length = product_lengths[x * m + y]
                        if actual_length != expected_length:
                            return {
                                "ok": False,
                                "failed_check": "cycle_lcm",
                                "view": view,
                                "first": first,
                                "second": second,
                                "point": x * m + y,
                                "actual_length": actual_length,
                                "expected_length": expected_length,
                            }
                        checked_points += 1
    return {
        "ok": True,
        "views_checked": ["row", "col", "sym"],
        "line_pairs_checked": checked_pairs,
        "point_lcm_checks": checked_points,
    }


def summarize_square(table: tuple[tuple[int, ...], ...], include_closure: bool = True) -> dict[str, Any]:
    pattern = fff_pattern(table)
    summary = {
        "order": len(table),
        "latin": validate_latin_square(table),
        "pattern_has_odd_cycle": pattern,
        "pattern_name": pattern_name(pattern),
        "fff": not any(pattern.values()),
    }
    if include_closure:
        closures = {view: closure_profile(table, view) for view in VIEWS}
        summary.update(
            {
                "closure_by_view": closures,
                "group_isotopic_by_row_closure": closures["row"]["closed"],
                "closure_views_agree": len({closures[view]["closed"] for view in closures}) == 1,
            }
        )
    return summary


def select_order8_examples(fullscan: dict[str, Any]) -> list[dict[str, Any]]:
    examples = []
    for wanted, label in ((True, "order8_group_isotopic_fff"), (False, "order8_nongroup_fff")):
        for entry in fullscan["counterexamples"]:
            if bool(entry["group_isotopic"]) == wanted:
                table = parse_compact_square(entry["square"])
                examples.append(
                    {
                        "label": label,
                        "source_index": entry["index"],
                        "source_line_number": entry["line_number"],
                        "source_group_isotopic": entry["group_isotopic"],
                        "compact_square": entry["square"],
                        "table": table,
                        "summary": summarize_square(table),
                    }
                )
                break
        else:
            raise ValueError(f"no example found for group_isotopic={wanted}")
    return examples


def find_first_pattern_examples(main_classes: Path, names: list[str]) -> dict[str, dict[str, Any]]:
    wanted = set(names)
    found: dict[str, dict[str, Any]] = {}
    for index, (line_number, compact) in enumerate(iter_compact_squares(main_classes), start=1):
        table = parse_compact_square(compact)
        summary = summarize_square(table, include_closure=False)
        name = summary["pattern_name"]
        if name in wanted and name not in found:
            found[name] = {
                "label": f"order8_pattern_{name}",
                "source_index": index,
                "source_line_number": line_number,
                "compact_square": compact,
                "table": table,
                "summary": summary,
            }
            if set(found) == wanted:
                return found
    missing = sorted(wanted - set(found))
    raise ValueError(f"missing requested pattern examples in {main_classes}: {missing}")


def make_pattern_or_cases(pattern_examples: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    requested_pairs = [("FFF", "TFF"), ("TFF", "FTF"), ("FTF", "FFT")]
    cases = []
    for left_name, right_name in requested_pairs:
        left = pattern_examples[left_name]
        right = pattern_examples[right_name]
        product = direct_product(left["table"], right["table"])
        product_summary = summarize_square(product, include_closure=False)
        expected = pattern_or_name(left_name, right_name)
        cases.append(
            {
                "left_pattern": left_name,
                "left_source_index": left["source_index"],
                "right_pattern": right_name,
                "right_source_index": right["source_index"],
                "expected_or_pattern": expected,
                "product_summary": product_summary,
                "or_formula_holds": product_summary["pattern_name"] == expected,
                "product_formula_and_lcm_check": verify_product_permutation_formula(
                    left["table"], right["table"], product
                ),
            }
        )
    return cases


def make_c2_pattern_inflation_cases(
    pattern_examples: dict[str, dict[str, Any]],
    c2_table: tuple[tuple[int, ...], ...],
) -> list[dict[str, Any]]:
    cases = []
    for name in ALL_PATTERN_NAMES:
        example = pattern_examples[name]
        product = direct_product(example["table"], c2_table)
        product_summary = summarize_square(product, include_closure=False)
        cases.append(
            {
                "left_pattern": name,
                "left_source_index": example["source_index"],
                "left_source_line_number": example["source_line_number"],
                "right_factor": "C2",
                "expected_pattern": name,
                "product_summary": product_summary,
                "pattern_preserved": product_summary["pattern_name"] == name,
                "product_formula_and_lcm_check": verify_product_permutation_formula(
                    example["table"], c2_table, product
                ),
            }
        )
    return cases


def make_group_isotopy_equivalence_cases(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_label = {entry["label"]: entry for entry in examples}
    requested_pairs = [
        ("order8_group_isotopic_fff", "order8_group_isotopic_fff"),
        ("order8_group_isotopic_fff", "order8_nongroup_fff"),
        ("order8_nongroup_fff", "order8_nongroup_fff"),
    ]
    cases = []
    for left_label, right_label in requested_pairs:
        left = by_label[left_label]
        right = by_label[right_label]
        product = direct_product(left["table"], right["table"])
        product_summary = summarize_square(product, include_closure=True)
        expected = bool(left["source_group_isotopic"] and right["source_group_isotopic"])
        cases.append(
            {
                "left_example_label": left_label,
                "left_source_index": left["source_index"],
                "left_group_isotopic": left["source_group_isotopic"],
                "right_example_label": right_label,
                "right_source_index": right["source_index"],
                "right_group_isotopic": right["source_group_isotopic"],
                "expected_group_isotopic": expected,
                "product_summary": product_summary,
                "closure_equivalence_holds": product_summary["group_isotopic_by_row_closure"] == expected,
            }
        )
    return cases


def make_nongroup_fff_power2_family_cases(product_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for case in product_cases:
        if case["left_example_label"] != "order8_nongroup_fff":
            continue
        if case["right_group_label"] not in {"C2", "C2xC2"}:
            continue
        row_closed = case["product_summary"]["closure_by_view"]["row"]["closed"]
        cases.append(
            {
                "left_example_label": case["left_example_label"],
                "left_source_index": case["left_source_index"],
                "right_group_label": case["right_group_label"],
                "product_order": case["product_summary"]["order"],
                "product_fff": case["product_summary"]["fff"],
                "row_closure_closed": row_closed,
                "closure_views_agree": case["product_summary"]["closure_views_agree"],
                "passed": case["product_summary"]["fff"] and not row_closed,
            }
        )
    return cases


def make_summary_text(result: dict[str, Any]) -> str:
    lines = [
        "Direct-product FFF validation summary",
        "",
        f"Input fullscan: {result['inputs']['order8_fullscan']['path']}",
        f"Fullscan SHA-256: {result['inputs']['order8_fullscan']['sha256']}",
        f"Input main classes: {result['inputs']['order8_main_classes']['path']}",
        f"Main-class SHA-256: {result['inputs']['order8_main_classes']['sha256']}",
        f"Order-8 all eight patterns nonempty: {result['aggregate']['all_eight_order8_patterns_nonempty']}",
        f"Selected examples: {len(result['selected_order8_examples'])}",
        f"Selected pattern examples: {result['aggregate']['selected_pattern_names']}",
        f"Product cases: {len(result['product_cases'])}",
        f"All product cases Latin: {result['aggregate']['all_products_latin']}",
        f"All product cases FFF: {result['aggregate']['all_products_fff']}",
        f"All product permutation formulas checked: {result['aggregate']['all_product_formulas_ok']}",
        f"All product lcm checks passed: {result['aggregate']['all_lcm_checks_ok']}",
        f"Non-group products row-closure false: {result['aggregate']['nongroup_products_remain_nongroup_by_row_closure']}",
        f"All pattern OR cases passed: {result['aggregate']['all_pattern_or_cases_passed']}",
        f"All C2 pattern-inflation cases passed: {result['aggregate']['all_c2_pattern_inflation_cases_passed']}",
        f"All group-isotopy equivalence cases passed: {result['aggregate']['all_group_isotopy_equivalence_cases_passed']}",
        f"Non-group FFF C2/C2xC2 family checks passed: {result['aggregate']['nongroup_fff_c2_family_cases_passed']}",
        "",
        "Order-8 pattern counts:",
    ]
    for name, count in result["order8_pattern_count_check"]["counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend([
        "",
        "First example per pattern:",
    ])
    for example in result["selected_pattern_examples"]:
        lines.append(
            "- {pattern}: source_index={source_index}, line_number={line_number}".format(
                pattern=example["summary"]["pattern_name"],
                source_index=example["source_index"],
                line_number=example["source_line_number"],
            )
        )
    lines.extend([
        "",
        "FFF x 2-group cases:",
    ])
    for case in result["product_cases"]:
        lines.append(
            "- {example} x {group}: order {order}, FFF={fff}, "
            "row_closure={row_closed}, expected_group_isotopic={expected}".format(
                example=case["left_example_label"],
                group=case["right_group_label"],
                order=case["product_summary"]["order"],
                fff=case["product_summary"]["fff"],
                row_closed=case["product_summary"]["closure_by_view"]["row"]["closed"],
                expected=case["expected_group_isotopic"],
            )
        )
    lines.extend(["", "Pattern OR cases:"])
    for case in result["pattern_or_cases"]:
        lines.append(
            "- {left} x {right}: expected {expected}, actual {actual}, ok={ok}".format(
                left=case["left_pattern"],
                right=case["right_pattern"],
                expected=case["expected_or_pattern"],
                actual=case["product_summary"]["pattern_name"],
                ok=case["or_formula_holds"],
            )
        )
    lines.extend(["", "C2 pattern-inflation cases:"])
    for case in result["c2_pattern_inflation_cases"]:
        lines.append(
            "- {pattern} x C2: expected {expected}, actual {actual}, ok={ok}".format(
                pattern=case["left_pattern"],
                expected=case["expected_pattern"],
                actual=case["product_summary"]["pattern_name"],
                ok=case["pattern_preserved"],
            )
        )
    lines.extend(["", "Group-isotopy equivalence cases:"])
    for case in result["group_isotopy_equivalence_cases"]:
        lines.append(
            "- {left} x {right}: expected {expected}, row_closure={actual}, ok={ok}".format(
                left=case["left_example_label"],
                right=case["right_example_label"],
                expected=case["expected_group_isotopic"],
                actual=case["product_summary"]["group_isotopic_by_row_closure"],
                ok=case["closure_equivalence_holds"],
            )
        )
    lines.extend(["", "Non-group FFF C2-family checks:"])
    for case in result["nongroup_fff_power2_family_cases"]:
        lines.append(
            "- {left} x {right}: order {order}, FFF={fff}, row_closure_closed={row_closed}, ok={ok}".format(
                left=case["left_example_label"],
                right=case["right_group_label"],
                order=case["product_order"],
                fff=case["product_fff"],
                row_closed=case["row_closure_closed"],
                ok=case["passed"],
            )
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order8-fullscan", type=Path, required=True)
    parser.add_argument("--order8-main-classes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fullscan = json.loads(args.order8_fullscan.read_text())
    examples = select_order8_examples(fullscan)
    pattern_count_check = order8_pattern_count_check(fullscan)
    pattern_examples = find_first_pattern_examples(args.order8_main_classes, ALL_PATTERN_NAMES)
    groups = [
        {"label": "C2", "table": group_table_cyclic(2), "description": "cyclic group of order 2"},
        {"label": "C2xC2", "table": group_table_c2_squared(), "description": "elementary abelian group of order 4"},
        {"label": "C4", "table": group_table_cyclic(4), "description": "cyclic group of order 4"},
    ]

    group_summaries = []
    for group in groups:
        group_summaries.append(
            {
                "label": group["label"],
                "description": group["description"],
                "summary": summarize_square(group["table"]),
            }
        )

    selected = []
    product_cases = []
    for example in examples:
        selected.append({k: v for k, v in example.items() if k != "table"})
        for group in groups:
            product = direct_product(example["table"], group["table"])
            product_summary = summarize_square(product)
            formula_check = verify_product_permutation_formula(example["table"], group["table"], product)
            product_cases.append(
                {
                    "left_example_label": example["label"],
                    "left_source_index": example["source_index"],
                    "left_source_group_isotopic": example["source_group_isotopic"],
                    "right_group_label": group["label"],
                    "right_group_order": len(group["table"]),
                    "expected_group_isotopic": bool(example["source_group_isotopic"]),
                    "product_summary": product_summary,
                    "product_formula_and_lcm_check": formula_check,
                }
            )

    pattern_or_cases = make_pattern_or_cases(pattern_examples)
    c2_pattern_inflation_cases = make_c2_pattern_inflation_cases(pattern_examples, groups[0]["table"])
    group_isotopy_equivalence_cases = make_group_isotopy_equivalence_cases(examples)
    nongroup_fff_power2_family_cases = make_nongroup_fff_power2_family_cases(product_cases)

    result = {
        "run_id": "2026-04-26_direct_product_fff",
        "inputs": {
            "order8_fullscan": {
                "path": str(args.order8_fullscan),
                "size_bytes": args.order8_fullscan.stat().st_size,
                "sha256": sha256_file(args.order8_fullscan),
            },
            "order8_main_classes": {
                "path": str(args.order8_main_classes),
                "size_bytes": args.order8_main_classes.stat().st_size,
                "sha256": sha256_file(args.order8_main_classes),
            },
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "selected_order8_examples": selected,
        "selected_pattern_examples": [
            {key: value for key, value in pattern_examples[name].items() if key != "table"}
            for name in ALL_PATTERN_NAMES
        ],
        "order8_pattern_count_check": pattern_count_check,
        "groups": group_summaries,
        "product_cases": product_cases,
        "pattern_or_cases": pattern_or_cases,
        "c2_pattern_inflation_cases": c2_pattern_inflation_cases,
        "group_isotopy_equivalence_cases": group_isotopy_equivalence_cases,
        "nongroup_fff_power2_family_cases": nongroup_fff_power2_family_cases,
    }
    result["aggregate"] = {
        "all_eight_order8_patterns_nonempty": pattern_count_check["all_eight_patterns_nonempty"],
        "all_selected_examples_latin": all(entry["summary"]["latin"] for entry in selected),
        "all_selected_examples_fff": all(entry["summary"]["fff"] for entry in selected),
        "all_groups_latin": all(entry["summary"]["latin"] for entry in group_summaries),
        "all_groups_fff": all(entry["summary"]["fff"] for entry in group_summaries),
        "all_products_latin": all(case["product_summary"]["latin"] for case in product_cases),
        "all_products_fff": all(case["product_summary"]["fff"] for case in product_cases),
        "all_product_formulas_ok": all(case["product_formula_and_lcm_check"]["ok"] for case in product_cases),
        "all_lcm_checks_ok": all(case["product_formula_and_lcm_check"]["ok"] for case in product_cases),
        "all_pattern_or_cases_passed": all(
            case["or_formula_holds"] and case["product_formula_and_lcm_check"]["ok"]
            for case in pattern_or_cases
        ),
        "all_c2_pattern_inflation_cases_passed": all(
            case["pattern_preserved"] and case["product_formula_and_lcm_check"]["ok"]
            for case in c2_pattern_inflation_cases
        ),
        "all_group_isotopy_equivalence_cases_passed": all(
            case["closure_equivalence_holds"] and case["product_summary"]["closure_views_agree"]
            for case in group_isotopy_equivalence_cases
        ),
        "nongroup_fff_c2_family_cases_passed": all(
            case["passed"] and case["closure_views_agree"] for case in nongroup_fff_power2_family_cases
        ),
        "all_pattern_examples_latin": all(entry["summary"]["latin"] for entry in pattern_examples.values()),
        "selected_pattern_names": sorted(pattern_examples),
        "nongroup_products_remain_nongroup_by_row_closure": all(
            not case["product_summary"]["closure_by_view"]["row"]["closed"]
            for case in product_cases
            if not case["left_source_group_isotopic"]
        ),
        "group_products_group_isotopic_by_row_closure": all(
            case["product_summary"]["closure_by_view"]["row"]["closed"]
            for case in product_cases
            if case["left_source_group_isotopic"]
        ),
        "closure_views_agree_for_all_2group_products": all(
            case["product_summary"]["closure_views_agree"] for case in product_cases
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
