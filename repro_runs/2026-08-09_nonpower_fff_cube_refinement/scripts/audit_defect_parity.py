#!/usr/bin/env python3
"""Audit failed line-pair counts and proposed parity constraints."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
VIEWS = ("row", "col", "sym")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_table(table: list[list[int]] | tuple[tuple[int, ...], ...]) -> str:
    return "".join(str(value) for row in table for value in row)


def parse_compact(compact: str) -> list[list[int]]:
    n = int(len(compact) ** 0.5)
    if n * n != len(compact):
        raise ValueError(f"non-square compact table length: {len(compact)}")
    return [[int(value) for value in compact[r * n : (r + 1) * n]] for r in range(n)]


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


def induced_permutation(lines: list[list[int]], first: int, second: int) -> list[int]:
    inverse = [0] * len(lines)
    for index, value in enumerate(lines[second]):
        inverse[value] = index
    return [inverse[value] for value in lines[first]]


def table_profile(table: list[list[int]]) -> dict[str, Any]:
    if not validate_latin(table):
        raise ValueError("table is not Latin")
    by_view: dict[str, Any] = {}
    for view in VIEWS:
        lines = view_lines(table, view)
        failures = []
        for first, second in combinations(range(len(table)), 2):
            cycle_type = cycle_lengths(induced_permutation(lines, first, second))
            odd_lengths = [length for length in cycle_type if length % 2 == 1]
            if odd_lengths:
                failures.append(
                    {
                        "pair": [first, second],
                        "cycle_type": list(cycle_type),
                        "odd_cycle_count": len(odd_lengths),
                    }
                )
        by_view[view] = {
            "failed_pair_count": len(failures),
            "failed_pair_count_parity": len(failures) % 2,
            "failures": failures,
        }
    vector = [by_view[view]["failed_pair_count"] for view in VIEWS]
    return {
        "order": len(table),
        "defect_vector": vector,
        "total_failed_pair_count": sum(vector),
        "pattern": "".join("T" if value else "F" for value in vector),
        "by_view": by_view,
    }


def load_small_order_generator(path: Path):
    spec = importlib.util.spec_from_file_location("latin_trade_search_defect_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def aggregate_tables(tables: Iterable[list[list[int]]], keep_first_odd: bool = True) -> dict[str, Any]:
    vector_counts: Counter[tuple[int, int, int]] = Counter()
    pattern_counts: Counter[str] = Counter()
    view_parities = {view: Counter() for view in VIEWS}
    minimum: dict[str, Any] | None = None
    first_odd_view: dict[str, Any] | None = None
    all_failed_pairs_have_even_odd_cycle_count = True
    count = 0
    for table in tables:
        count += 1
        profile = table_profile(table)
        vector = tuple(profile["defect_vector"])
        vector_counts[vector] += 1
        pattern_counts[profile["pattern"]] += 1
        for index, view in enumerate(VIEWS):
            view_parities[view][vector[index] % 2] += 1
            for failure in profile["by_view"][view]["failures"]:
                if failure["odd_cycle_count"] % 2 != 0:
                    all_failed_pairs_have_even_odd_cycle_count = False
        if minimum is None or profile["total_failed_pair_count"] < minimum["total_failed_pair_count"]:
            minimum = {
                "index": count,
                "compact_table": compact_table(table),
                "defect_vector": list(vector),
                "total_failed_pair_count": profile["total_failed_pair_count"],
                "pattern": profile["pattern"],
            }
        if keep_first_odd and first_odd_view is None and any(value % 2 for value in vector):
            first_odd_view = {
                "index": count,
                "compact_table": compact_table(table),
                "profile": profile,
            }
    return {
        "table_count": count,
        "vector_counts": {",".join(map(str, key)): value for key, value in sorted(vector_counts.items())},
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "view_defect_count_parities": {
            view: {str(parity): count for parity, count in sorted(counter.items())}
            for view, counter in view_parities.items()
        },
        "minimum_total_defect": minimum,
        "first_odd_view_defect_count": first_odd_view,
        "all_failed_pairs_have_even_odd_cycle_count": all_failed_pairs_have_even_odd_cycle_count,
    }


def iter_order8_census(path: Path) -> Iterable[list[list[int]]]:
    with gzip.open(path, "rt", encoding="ascii") as handle:
        for line in handle:
            compact = line.strip()
            if compact:
                yield parse_compact(compact)


def extract_table(payload: Any) -> list[list[int]] | None:
    if isinstance(payload, dict):
        for key in ("table", "decoded_table", "latin_square"):
            value = payload.get(key)
            if isinstance(value, list) and value and isinstance(value[0], list):
                return [[int(cell) for cell in row] for row in value]
    return None


def collect_tracked_n10_tables(root: Path) -> tuple[list[list[list[int]]], dict[str, list[str]]]:
    unique: dict[str, list[list[int]]] = {}
    sources: dict[str, list[str]] = {}
    for path in sorted((root / "repro_runs").glob("*/results/**/*table*.json")):
        try:
            table = extract_table(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError, ValueError):
            continue
        if table is None or len(table) != 10 or not validate_latin(table):
            continue
        compact = compact_table(table)
        unique.setdefault(compact, table)
        sources.setdefault(compact, []).append(str(path.relative_to(root)))
    return list(unique.values()), sources


def make_summary(payload: dict[str, Any]) -> str:
    n6 = payload["order6_exhaustive"]
    n8 = payload["order8_mainclass_census"]
    n10 = payload["tracked_order10_tables"]
    lines = [
        "FFF defect-count and parity audit",
        "",
        "Exact datasets:",
        f"- n=6 reduced exhaustive: {n6['table_count']} tables",
        f"- n=8 main-class census: {n8['table_count']} tables",
        f"- n=10 distinct tracked valid tables: {n10['table_count']} tables",
        "",
        "Decisive counterexample to the proposed global parity rule:",
    ]
    counterexample = n8["first_odd_view_defect_count"]
    if counterexample:
        profile = counterexample["profile"]
        lines.extend(
            [
                f"- n=8 census line: {counterexample['index']}",
                f"- defect vector (row,col,sym): {profile['defect_vector']}",
                f"- total failed pairs: {profile['total_failed_pair_count']}",
                f"- compact table: {counterexample['compact_table']}",
                "- Therefore neither per-view nor total failed-pair parity is a general even-order invariant.",
            ]
        )
    lines.extend(
        [
            "",
            "Exact minima in the audited datasets:",
            f"- n=6 minimum total defects: {n6['minimum_total_defect']['total_failed_pair_count']} "
            f"with vector {n6['minimum_total_defect']['defect_vector']}",
            f"- n=8 minimum total defects: {n8['minimum_total_defect']['total_failed_pair_count']} "
            f"with vector {n8['minimum_total_defect']['defect_vector']}",
            f"- tracked n=10 minimum total defects: {n10['minimum_total_defect']['total_failed_pair_count']} "
            f"with vector {n10['minimum_total_defect']['defect_vector']}",
            "",
            "Rigorous/check boundary:",
            "- The even number of odd cycles inside each failed pair is rigorous (existing proof note).",
            "- The number of failed line pairs in a view need not be even; this audit gives an explicit counterexample.",
            "- The tracked n=10 minimum is only a finite search observation, not a lower-bound theorem.",
            "- C38 remains open and C40 is not created.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=RUN_DIR / "results" / "defect_parity_audit.json")
    parser.add_argument("--summary", type=Path, default=RUN_DIR / "results" / "defect_parity_audit_summary.txt")
    args = parser.parse_args()

    n6_generator_path = ROOT / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py"
    n8_census_path = ROOT / "repro_runs/2026-04-26_order8_core/data/latin_mc8.txt.gz"
    generator = load_small_order_generator(n6_generator_path)
    n10_tables, n10_sources = collect_tracked_n10_tables(ROOT)

    payload = {
        "run_id": "2026-08-09_nonpower_fff_cube_refinement",
        "inputs": {
            "n6_generator": {
                "path": str(n6_generator_path.relative_to(ROOT)),
                "sha256": sha256_file(n6_generator_path),
            },
            "n8_census": {
                "path": str(n8_census_path.relative_to(ROOT)),
                "sha256": sha256_file(n8_census_path),
            },
        },
        "order6_exhaustive": aggregate_tables(
            [[list(row) for row in table] for table in generator.reduced_latin_squares(6)]
        ),
        "order8_mainclass_census": aggregate_tables(iter_order8_census(n8_census_path)),
        "tracked_order10_tables": aggregate_tables(n10_tables),
        "tracked_order10_source_paths": n10_sources,
        "candidate_invariant_status": {
            "even_number_of_odd_cycles_within_each_failed_pair": "rigorously_proved_elsewhere_and_exactly_confirmed",
            "even_failed_pair_count_in_each_view_for_even_order": "disproved_by_explicit_n8_census_table",
            "even_total_failed_pair_count_for_even_order": "disproved_by_explicit_n8_census_table",
            "at_least_four_failed_pairs_for_non_fff_even_order": "disproved_by_n8_tables_with_two_total_failures",
            "at_least_four_failed_pairs_for_order10": "open_search_observation_only",
        },
        "claim_impact": {"C38": "open", "C40": "not_created"},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(make_summary(payload), encoding="utf-8")
    print(json.dumps({"n6": payload["order6_exhaustive"]["table_count"], "n8": payload["order8_mainclass_census"]["table_count"], "n10": payload["tracked_order10_tables"]["table_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
