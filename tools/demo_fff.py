#!/usr/bin/env python3
"""Small direct cycle checker, not a census or an order-10 proof checker."""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inverse(permutation):
    result = [0] * len(permutation)
    for i, value in enumerate(permutation):
        result[value] = i
    return result


def cycles(permutation):
    seen, result = set(), []
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycle, point = [], start
        while point not in seen:
            seen.add(point)
            cycle.append(point)
            point = permutation[point]
        result.append(cycle)
    return result


def validate(table):
    if not isinstance(table, list) or not table:
        raise ValueError("Expected a nonempty square table")
    n = len(table)
    symbols = set(range(n))
    if any(not isinstance(row, list) or len(row) != n
           or any(type(x) is not int for x in row) for row in table):
        raise ValueError("Expected an n x n table of integer labels 0..n-1")
    if any(set(row) != symbols for row in table):
        raise ValueError("Each row must contain every symbol once")
    if any({table[r][c] for r in range(n)} != symbols for c in range(n)):
        raise ValueError("Each column must contain every symbol once")

    columns = [[table[r][c] for r in range(n)] for c in range(n)]
    positions = [inverse(row) for row in table]
    # Symbol lines map row -> column; their matching acts on column labels.
    symbol_lines = [[positions[r][s] for r in range(n)] for s in range(n)]
    views = {}
    for view, lines in (("row", table), ("col", columns), ("sym", symbol_lines)):
        records = []
        for a, b in combinations(range(n), 2):
            if view == "sym":
                source_inverse = inverse(lines[a])
                permutation = [lines[b][source_inverse[j]] for j in range(n)]
            else:
                target_inverse = inverse(lines[b])
                permutation = [target_inverse[value] for value in lines[a]]
            decomposition = cycles(permutation)
            if any(len(cycle) == 1 for cycle in decomposition):
                raise AssertionError("Distinct Latin lines cannot have fixed points")
            odd = [cycle for cycle in decomposition if len(cycle) % 2]
            records.append({"lines": [a, b], "permutation": permutation,
                            "cycles": decomposition, "odd_cycles": odd})
        views[view] = {"pairs_checked": len(records),
                       "has_odd_cycle": any(item["odd_cycles"] for item in records),
                       "pairs": records}
    pattern = "".join("T" if views[v]["has_odd_cycle"] else "F"
                      for v in ("row", "col", "sym"))
    return {"order": n, "latin": True,
            "reduced": table[0] == list(range(n))
            and [row[0] for row in table] == list(range(n)),
            "pattern": pattern, "fff": pattern == "FFF", "views": views}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", nargs="?", type=Path,
                        default=ROOT / "examples/order8_fff.json")
    parser.add_argument("--output", type=Path, help="Optional complete JSON cycle report")
    args = parser.parse_args()
    payload = args.table.read_bytes()
    document = json.loads(payload)
    try:
        result = validate(document["table"] if isinstance(document, dict) else document)
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    result["input_sha256"] = hashlib.sha256(payload).hexdigest()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"order={result['order']} latin={result['latin']} reduced={result['reduced']} "
          f"pattern={result['pattern']} FFF={result['fff']}")
    print("line pairs: " + ", ".join(
        f"{view}={data['pairs_checked']}" for view, data in result["views"].items()))
    print("Scope: this table only; not a census, an order-10 rerun or expert review.")


if __name__ == "__main__":
    main()
