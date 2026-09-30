#!/usr/bin/env python3
"""Small, direct checks of the compact selection; not a census rerun."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
DATA = PACKAGE.parent / "2026-09-28_research_review/evidence/data"
BASE = PACKAGE.parent / "2026-09-30_research_review"


def inverse(p):
    q = [0] * len(p)
    for i, j in enumerate(p):
        q[j] = i
    return q


def cycle_lengths(p):
    if sorted(p) != list(range(len(p))):
        raise ValueError("Not a permutation")
    seen, lengths = set(), []
    for point in range(len(p)):
        if point in seen:
            continue
        length, current = 0, point
        while current not in seen:
            seen.add(current)
            length += 1
            current = p[current]
        lengths.append(length)
    return sorted(lengths)


def scan(table):
    n = len(table)
    target = list(range(n))
    latin = n > 0 and all(len(row) == n and sorted(row) == target for row in table)
    latin = latin and all(sorted(row[c] for row in table) == target for c in target)
    if not latin:
        raise ValueError("Not a Latin square")
    rows = [list(row) for row in table]
    columns = [[row[c] for row in table] for c in target]
    symbols = [[columns[c].index(s) for c in target] for s in target]
    views = {}
    for name, lines in zip(("row", "col", "sym"), (rows, columns, symbols)):
        histogram, checked, odd = Counter(), 0, 0
        for a, b in combinations(lines, 2):
            inv = inverse(b)
            lengths = cycle_lengths([inv[x] for x in a])
            if 1 in lengths:
                raise AssertionError("A distinct-line permutation has a fixed point")
            histogram["+".join(map(str, lengths))] += 1
            checked += 1
            odd += any(length % 2 for length in lengths)
        views[name] = {"pairs_checked": checked, "odd_witness_pairs": odd,
                       "cycle_types": dict(sorted(histogram.items()))}
    pattern = "".join("T" if view["odd_witness_pairs"] else "F" for view in views.values())
    return {"order": n, "latin": True,
            "reduced": rows[0] == target and [row[0] for row in rows] == target,
            "pattern": pattern, "fff": pattern == "FFF", "views": views}


def closure(table):
    inv = inverse(table[0])
    family = {tuple(inv[x] for x in row) for row in table}
    for first in sorted(family):
        for second in sorted(family):
            composition = tuple(first[x] for x in second)
            if composition not in family:
                return {"closed": False, "failure": [first, second, composition]}
    return {"closed": True, "failure": None}


def product(left, right):
    n, m = len(left), len(right)
    return [[left[i][j] * m + right[a][b] for j in range(n) for b in range(m)]
            for i in range(n) for a in range(m)]


def twisted_loop():
    return [[2 * ((i + j) % 4) + (a ^ b ^ int(i == j == 1))
             for j in range(4) for b in range(2)]
            for i in range(4) for a in range(2)]


def displayed_order12(path=None):
    text = (path or BASE / "sections/08_nonpower_fff.tex").read_text()
    block = text.split(r"\begin{table}[ht]", 1)[1].split(r"\end{table}", 1)[0]
    table = []
    for line in block.splitlines():
        if re.match(r"^\d+\s+&", line):
            entries = [int(s.strip()) for s in line.split(r"\\", 1)[0].split("&")]
            if entries[0] != len(table):
                raise ValueError("Mislabelled table row")
            table.append(entries[1:])
    return table


def check(assembled_source=None):
    order12_input = DATA / "order12_first.json"
    controls_input = DATA / "order8_pattern_controls.json"
    order12 = json.loads(order12_input.read_text())["table"]
    displayed_source = ((assembled_source / "sections/07_short_order12.tex") if assembled_source
                        else BASE / "sections/08_nonpower_fff.tex")
    if displayed_order12(displayed_source) != order12:
        raise AssertionError("Displayed order-12 table differs from frozen input")
    records = {"order12": scan(order12)}
    assert records["order12"]["fff"] and records["order12"]["reduced"]
    assert sum(v["pairs_checked"] for v in records["order12"]["views"].values()) == 198
    loop = twisted_loop()
    records["explicit_order8_loop"] = {"table": loop, "validation": scan(loop),
                                       "closure": closure(loop)}
    assert records["explicit_order8_loop"]["validation"]["fff"]
    assert not records["explicit_order8_loop"]["closure"]["closed"]
    # Labels encode (i,a) as 2*i+a; the printed nonassociativity calculation.
    assert (loop[loop[2][2]][4], loop[2][loop[2][4]]) == (1, 0)
    records["loop_products"] = []
    for m in (2, 4):
        group = [[a ^ b for b in range(m)] for a in range(m)]
        p = product(loop, group)
        record = {"right_group_order": m, "validation": scan(p), "closure": closure(p)}
        assert record["validation"]["fff"] and not record["closure"]["closed"]
        records["loop_products"].append(record)
    group = [[a ^ b for b in range(8)] for a in range(8)]
    records["group_control"] = {"validation": scan(group), "closure": closure(group)}
    assert records["group_control"]["validation"]["fff"] and closure(group)["closed"]
    records["odd_negative_control"] = scan([[(a + b) % 3 for b in range(3)] for a in range(3)])
    assert records["odd_negative_control"]["pattern"] == "TTT"
    controls = json.loads(controls_input.read_text())
    records["pattern_controls"] = []
    expected_counts = {"FFF": 230, "FFT": 81, "FTF": 40, "FTT": 315,
                       "TFF": 133, "TFT": 209, "TTF": 232, "TTT": 282417}
    assert controls["order8_pattern_count_check"]["counts"] == expected_counts
    assert sum(expected_counts.values()) == 283657
    for example in controls["selected_pattern_examples"]:
        flat = list(map(int, example["compact_square"]))
        table = [flat[i:i + 8] for i in range(0, 64, 8)]
        expected = example["summary"]["pattern_name"]
        base = scan(table)
        inflated = scan(product(table, [[0, 1], [1, 0]]))
        assert base["pattern"] == inflated["pattern"] == expected
        records["pattern_controls"].append({"pattern": expected, "validation": base,
                                             "product_c2": inflated})
    assert {r["pattern"] for r in records["pattern_controls"]} == set(expected_counts)
    return {"passed": True, "new_mathematical_claims": False,
            "order8_census_rerun": False, "order10_rerun": False,
            "inputs_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (order12_input, controls_input,
                                        displayed_source)},
            "checks": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="Assembled Compact source directory")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / ".audit"):
        parser.error("Use .audit output")
    result = check(args.source.resolve() if args.source else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: order12/198 pairs; explicit nongroup8; products16/32; eight pattern controls and C2 products.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
