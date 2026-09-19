#!/usr/bin/env python3
"""Bounded fresh finite reruns using the shipped generators, never frozen writes."""
from __future__ import annotations

import argparse
import json
import runpy
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMALL = ROOT / "repro_runs/2026-04-26_small_order_witness_reruns"
CORE = ROOT / "repro_runs/2026-04-26_order8_core"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use a fresh output below the package .audit directory")
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    small = runpy.run_path(str(SMALL / "scripts/latin_trade_search.py"))
    frozen = json.loads((SMALL / "results/latin_trade_results.json").read_text())
    expected = {r["n"]: r for r in frozen["orders"]}
    records = []
    for n in (2, 4, 6):
        seen, patterns, count, failures = set(), Counter(), 0, 0
        for table in small["reduced_latin_squares"](n):
            count += 1
            key = tuple(tuple(row) for row in table)
            valid = (len(table) == n and all(len(row) == n and set(row) == set(range(n)) for row in table)
                     and all({table[r][c] for r in range(n)} == set(range(n)) for c in range(n)))
            reduced = tuple(table[0]) == tuple(range(n)) and tuple(row[0] for row in table) == tuple(range(n))
            failures += int(not valid or not reduced or key in seen)
            seen.add(key)
            pattern = tuple(small["has_odd_cycle_view"](table, view) for view in ("row", "col", "sym"))
            patterns[str(pattern)] += 1
        records.append(dict(n=n, generated=count, unique=len(seen), tables_scanned=count,
                            latin_reduced_uniqueness_failures=failures,
                            patterns=dict(sorted(patterns.items())),
                            passed=failures == 0 and count == expected[n]["reduced_count"]
                            and dict(patterns) == expected[n]["patterns_any_pairs"]))
    scanner = runpy.run_path(str(CORE / "scripts/order8_recheck_scanner.py"))
    fresh = scanner["scan_main_classes"](CORE / "data/latin_mc8.txt.gz", log_every=0)
    old = json.loads((CORE / "results/order8_recheck_fullscan_results.json").read_text())
    fresh_scan, old_scan = dict(fresh["scan"]), dict(old["scan"])
    fresh_scan.pop("elapsed_seconds")
    old_scan.pop("elapsed_seconds")
    comparison = dict(
        input_sha256_matches=fresh["input"]["sha256"] == old["input"]["sha256"],
        input_size_matches=fresh["input"]["size_bytes"] == old["input"]["size_bytes"],
        all_scan_fields_except_runtime_match=fresh_scan == old_scan,
        complete_counterexample_list_matches=fresh["counterexamples"] == old["counterexamples"])
    (out / "order8_fresh.json").write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
    report = dict(passed=all(r["passed"] for r in records) and all(comparison.values()),
                  small_orders=records, order8_comparison=comparison,
                  order8_total=fresh_scan["total_main_classes"],
                  order8_patterns=fresh_scan["pattern_counts"],
                  ignored_order8_fields=["input.path", "scan.elapsed_seconds"],
                  small_order_comparison_fields=["reduced_count", "patterns_any_pairs"],
                  scope="Fresh supplied-generator/scanner reruns, not independent implementations or census completeness certification.",
                  order10_exhaustive_search_rerun=False,
                  elapsed_seconds=round(time.monotonic() - start, 3))
    (out / "finite_reruns.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
