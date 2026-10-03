#!/usr/bin/env python3
"""Independent matching-graph controls; no census or external scanner import."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import re

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def union_type(left, right):
    """A component of two perfect matchings encodes one permutation cycle."""
    n = len(left)
    require(sorted(left) == sorted(right) == list(range(n)), "Invalid matching")
    edges = {i: set() for i in range(2 * n)}
    for mapping in (left, right):
        for i, j in enumerate(mapping):
            edges[i].add(n + j)
            edges[n + j].add(i)
    unused, lengths = set(edges), []
    while unused:
        stack, size = [unused.pop()], 0
        while stack:
            i = stack.pop()
            size += 1
            for j in edges[i] & unused:
                unused.remove(j)
                stack.append(j)
        require(size % 2 == 0, "Unbalanced component")
        lengths.append(size // 2)
    return tuple(sorted(lengths))


def views(table):
    n = len(table)
    require(n > 0 and all(len(row) == n for row in table), "Not square")
    require(all(type(x) is int for row in table for x in row), "Noninteger entry")
    require(all(sorted(row) == list(range(n)) for row in table), "Not Latin rows")
    require(all(sorted(col) == list(range(n)) for col in zip(*table)), "Not Latin columns")
    triples = [(r, c, table[r][c]) for r in range(n) for c in range(n)]
    result = []
    for fixed, left, right in ((0, 1, 2), (1, 0, 2), (2, 0, 1)):
        maps = [[-1] * n for _ in range(n)]
        for t in triples:
            maps[t[fixed]][t[left]] = t[right]
        result.append(maps)
    return result


def scan(table):
    histograms = [Counter(union_type(a, b) for a, b in combinations(view, 2))
                  for view in views(table)]
    require(all(1 not in cycle for hist in histograms for cycle in hist), "Latin fixed point")
    pattern = "".join("T" if any(k % 2 for cycle in hist for k in cycle) else "F"
                      for hist in histograms)
    return {"pattern": pattern, "pairs": sum(sum(hist.values()) for hist in histograms),
            "histograms": [{"+".join(map(str, key)): hist[key] for key in sorted(hist)}
                           for hist in histograms]}


def sign(mapping):
    parity = sum(mapping[i] > mapping[j] for i in range(len(mapping))
                 for j in range(i + 1, len(mapping))) % 2
    return -1 if parity else 1


def signs(table):
    result = []
    for maps in views(table):
        value = 1
        for mapping in maps:
            value *= sign(mapping)
        result.append(value)
    return result


def check():
    source = PACKAGE / "evidence/pattern_witnesses.json"
    witnesses = json.loads(source.read_text())
    require(set(witnesses) == {"".join(p) for p in product("FT", repeat=3)}, "Missing pattern")
    printed = re.findall(r"\\mathsf\{([FT]{3})\}.*?\\texttt\{([0-7]{64})\}",
                         (PACKAGE / "sections/pattern_witnesses.tex").read_text())
    require(len(printed) == 8 and dict(printed) == witnesses, "Printed witness mismatch")
    previous_path = PACKAGE.parent / "2026-09-28_research_review/evidence/data/order8_pattern_controls.json"
    previous = json.loads(previous_path.read_text())["selected_pattern_examples"]
    require({r["summary"]["pattern_name"]: r["compact_square"] for r in previous}
            == witnesses, "Witness provenance changed")
    results, rejected = {}, 0
    for expected, encoded in sorted(witnesses.items()):
        require(len(encoded) == 64 and set(encoded) <= set("01234567"), "Invalid encoding")
        table = [list(map(int, encoded[start:start + 8])) for start in range(0, 64, 8)]
        result = scan(table)
        require(result["pattern"] == expected and result["pairs"] == 84, "Wrong base pattern")
        inflated = [[2 * table[r][c] + (a ^ b) for c in range(8) for b in range(2)]
                    for r in range(8) for a in range(2)]
        enlarged = scan(inflated)
        require(enlarged["pattern"] == expected, "Wrong product pattern")
        bad = [row[:] for row in table]
        bad[0][0] = bad[0][1]
        try:
            scan(bad)
        except ValueError:
            rejected += 1
        results[expected] = {"base": result, "product_with_C2": enlarged}
    require(rejected == 8, "Malformed controls accepted")

    sign_controls = []
    for n in (3, 4):
        table = [[(r + c) % n for c in range(n)] for r in range(n)]
        for axis in range(3):
            altered = [[0] * n for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    triple = [r, c, table[r][c]]
                    x = triple[axis]
                    triple[axis] = 1 - x if x < 2 else x
                    altered[triple[0]][triple[1]] = triple[2]
            ratios = [a * b for a, b in zip(signs(table), signs(altered))]
            expected = [(-1) ** n] * 3
            expected[axis] = 1
            changed = sum(a != b for ra, rb in zip(table, altered) for a, b in zip(ra, rb))
            require(ratios == expected and changed == 2 * n, "Wrong support/sign identity")
            sign_controls.append({"order": n, "view": ("row", "column", "symbol")[axis],
                                  "positions": n, "changed_cells": changed, "R_C_S_ratios": ratios})

    identity = tuple(range(6))
    factors = [p for p in permutations(range(6)) if union_type(identity, p) == (3, 3)]
    mixed = [p for p in permutations(range(6)) if union_type(identity, p) == (1, 1, 1, 3)]
    histogram = Counter(union_type(a, b) for a in factors for b in factors)
    require(histogram == {(1, 1, 1, 1, 1, 1): 40, (1, 1, 1, 3): 80,
                          (1, 1, 2, 2): 360, (1, 5): 720, (3, 3): 400}, "S6 mismatch")
    mixed_even = sum(union_type(a, b) == (2, 4) for a in mixed for b in factors)
    require(mixed_even == 720, "Mixed control mismatch")
    ordinary = {}
    for group in ("C9", "E9"):
        def plus(a, b):
            return ((a + b) % 9 if group == "C9"
                    else 3 * ((a // 3 + b // 3) % 3) + (a % 3 + b % 3) % 3)
        table = [[2 * plus(r // 2, c // 2) + ((r % 2) ^ (c % 2))
                  for c in range(18)] for r in range(18)]
        count = 0
        for g, r, c in product(range(9), range(18), range(18)):
            gc = 2 * plus(g, c // 2) + c % 2
            v = table[r][c]
            require(table[r][gc] == 2 * plus(g, v // 2) + v % 2, "Autotopy fails")
            count += 1
        require(scan(table)["pattern"] == "TTT", "Ordinary Latin negative fails")
        ordinary[group] = {"fixed_rows": 18, "free_columns_and_symbols": True,
                           "pattern": "TTT", "autotopy_equations": count}
    return {"passed": True, "scope": "Explicit witnesses and bounded countercontrols",
            "witness_input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "prior_witness_input_sha256": hashlib.sha256(previous_path.read_bytes()).hexdigest(),
            "eight_patterns": results, "malformed_controls_rejected": rejected,
            "support_sign_controls": sign_controls,
            "S6_histogram": {"+".join(map(str, k)): v for k, v in sorted(histogram.items())},
            "mixed_S6_even_products": mixed_even, "row_F_required_controls": ordinary,
            "full_order8_census": False, "unrestricted_order18": "open"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".audit") or output.exists():
        parser.error("Use a new file under .audit")
    result = check()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("PASS: eight witnesses/products; six sign controls; S6 and ordinary-Latin countercontrols")


if __name__ == "__main__":
    main()
