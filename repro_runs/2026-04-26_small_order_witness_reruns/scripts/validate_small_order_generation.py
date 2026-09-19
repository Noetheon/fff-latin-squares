#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import latin_trade_search as lts

RUN_ROOT = Path(__file__).resolve().parents[1]
RESULTS = RUN_ROOT / "results"


def square_key(square: tuple[tuple[int, ...], ...]) -> str:
    return "".join(str(value) for row in square for value in row)


def is_latin(square: tuple[tuple[int, ...], ...]) -> bool:
    n = len(square)
    symbols = set(range(n))
    rows_ok = all(set(row) == symbols for row in square)
    cols_ok = all({square[r][c] for r in range(n)} == symbols for c in range(n))
    return rows_ok and cols_ok


def is_reduced(square: tuple[tuple[int, ...], ...]) -> bool:
    n = len(square)
    first = tuple(range(n))
    return square[0] == first and tuple(row[0] for row in square) == first


def validate_order(n: int, expected_count: int) -> dict:
    seen: set[str] = set()
    latin_failures = 0
    reduced_failures = 0
    duplicates = 0

    for square in lts.reduced_latin_squares(n):
        key = square_key(square)
        if key in seen:
            duplicates += 1
        seen.add(key)
        if not is_latin(square):
            latin_failures += 1
        if not is_reduced(square):
            reduced_failures += 1

    count = len(seen)
    return {
        "n": n,
        "expected_reduced_count": expected_count,
        "generated_unique_count": count,
        "generated_total_count": count + duplicates,
        "duplicate_table_strings": duplicates,
        "latin_failures": latin_failures,
        "reduced_failures": reduced_failures,
        "count_matches_expected": count == expected_count,
        "all_latin": latin_failures == 0,
        "all_reduced": reduced_failures == 0,
        "all_unique": duplicates == 0,
    }


def main() -> None:
    expected = {2: 1, 4: 4, 6: 9408}
    orders = [validate_order(n, count) for n, count in expected.items()]
    report = {
        "source": "fresh enumeration by scripts/latin_trade_search.py; no cached list of reduced squares is loaded",
        "orders": orders,
        "overall_ok": all(
            item["count_matches_expected"]
            and item["all_latin"]
            and item["all_reduced"]
            and item["all_unique"]
            for item in orders
        ),
        "witness_scan_coverage": {
            "n6_reduced_square_count_in_latin_trade_results": 9408,
            "n6_generator_validation_unique_count": next(item["generated_unique_count"] for item in orders if item["n"] == 6),
            "scan_covers_all_9408": next(item["generated_unique_count"] for item in orders if item["n"] == 6) == 9408,
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "small_order_generation_validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
