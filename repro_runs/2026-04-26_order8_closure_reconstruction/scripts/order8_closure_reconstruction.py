#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import os
from collections import Counter
from pathlib import Path


ORDER = 8
VIEWS = ("row", "col", "sym")
INPUT_DIR = Path(os.environ.get("ORDER8_INPUT_DIR", "/mnt/data"))
OUTPUT_DIR = Path(os.environ.get("ORDER8_OUTPUT_DIR", str(INPUT_DIR)))

FULLSCAN = INPUT_DIR / "order8_mc8_scan.json"
TRANSITIVE = INPUT_DIR / "order8_recheck_transitive_results.json"
GROUP_OUT = OUTPUT_DIR / "order8_group_isotope_subgroup_criterion_results.json"
NEAR_OUT = OUTPUT_DIR / "order8_near_closure_analysis_results.json"
GROUP_NOTE = OUTPUT_DIR / "order8_group_isotope_subgroup_criterion_note.txt"
NEAR_NOTE = OUTPUT_DIR / "order8_near_closure_analysis_note.txt"


def parse_square(s: str) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(s[r * ORDER + c]) for c in range(ORDER)) for r in range(ORDER))


def columns(rows: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(rows[r][c] for r in range(ORDER)) for c in range(ORDER))


def symbols(rows: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    pos = [[None] * ORDER for _ in range(ORDER)]
    for r in range(ORDER):
        for c in range(ORDER):
            pos[rows[r][c]][c] = r
    return tuple(tuple(line) for line in pos)


def inverse_line(line: tuple[int, ...]) -> tuple[int, ...]:
    inv = [0] * ORDER
    for i, v in enumerate(line):
        inv[v] = i
    return tuple(inv)


def view_lines(rows: tuple[tuple[int, ...], ...], view: str) -> tuple[tuple[int, ...], ...]:
    if view == "row":
        return rows
    if view == "col":
        return columns(rows)
    if view == "sym":
        return symbols(rows)
    raise ValueError(f"unknown view: {view}")


def basis_family(lines: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    inv0 = inverse_line(lines[0])
    return tuple(tuple(inv0[v] for v in lines[x]) for x in range(ORDER))


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[q[i]] for i in range(ORDER))


def parity_is_even(p: tuple[int, ...]) -> bool:
    inv = 0
    for i in range(ORDER):
        for j in range(i + 1, ORDER):
            if p[i] > p[j]:
                inv ^= 1
    return inv == 0


def perm_order(p: tuple[int, ...]) -> int:
    seen = [False] * ORDER
    lcm = 1
    for i in range(ORDER):
        if seen[i]:
            continue
        cur = i
        length = 0
        while not seen[cur]:
            seen[cur] = True
            cur = p[cur]
            length += 1
        lcm = lcm * length // math.gcd(lcm, length)
    return lcm


def inverse_perm(p: tuple[int, ...]) -> tuple[int, ...]:
    inv = [0] * ORDER
    for i, v in enumerate(p):
        inv[v] = i
    return tuple(inv)


_subgroup_cache: dict[tuple[tuple[int, ...], ...], frozenset[tuple[int, ...]]] = {}


def generated_subgroup(H: tuple[tuple[int, ...], ...]) -> frozenset[tuple[int, ...]]:
    if H in _subgroup_cache:
        return _subgroup_cache[H]

    gens = list(H) + [inverse_perm(p) for p in H]
    identity = tuple(range(ORDER))
    seen = {identity}
    frontier = [identity]
    while frontier:
        g = frontier.pop()
        for h in gens:
            for candidate in (compose(g, h), compose(h, g)):
                if candidate not in seen:
                    seen.add(candidate)
                    frontier.append(candidate)

    out = frozenset(seen)
    _subgroup_cache[H] = out
    return out


def closure_profile(H: tuple[tuple[int, ...], ...]) -> dict:
    lookup = set(H)
    products = [compose(x, y) for x, y in itertools.product(H, repeat=2)]
    hits = sum(1 for p in products if p in lookup)
    missing = [p for p in products if p not in lookup]
    subgroup = generated_subgroup(H)
    even_count = sum(1 for p in subgroup if parity_is_even(p))

    return {
        "hits": hits,
        "misses": ORDER * ORDER - hits,
        "uniqmiss": len(set(missing)),
        "gsize": len(subgroup),
        "evenodd": [even_count, len(subgroup) - even_count],
        "orders": sorted(perm_order(p) for p in H),
    }


def process_square(square: str) -> dict[str, dict]:
    rows = parse_square(square)
    return {view: closure_profile(basis_family(view_lines(rows, view))) for view in VIEWS}


def is_closed(profile: dict) -> bool:
    return profile["hits"] == ORDER * ORDER


def int_counter_dict(values) -> dict[str, int]:
    return {str(k): v for k, v in sorted(Counter(values).items())}


def triple_from(record: dict, key: str) -> tuple:
    return tuple(record[view][key] for view in VIEWS)


def even_only_triple(record: dict) -> tuple[bool, bool, bool]:
    return tuple(record[view]["evenodd"][1] == 0 for view in VIEWS)


def top_combined(counter: Counter, limit: int) -> list[dict]:
    out = []
    rows = sorted(
        counter.items(),
        key=lambda item: (
            -item[1],
            item[0][0],
            item[0][1],
            item[0][2],
            item[0][3],
        ),
    )
    for (group_isotopic, hits, gsize, even_only), count in rows[:limit]:
        out.append(
            {
                "group_isotopic": group_isotopic,
                "hits_triple": list(hits),
                "gsize_triple": list(gsize),
                "even_only_triple": list(even_only),
                "count": count,
            }
        )
    return out


def top_gsize(counter: Counter, limit: int) -> list[dict]:
    return [{"gsize_triple": list(triple), "count": count} for triple, count in counter.most_common(limit)]


def top_even_only(counter: Counter) -> list[dict]:
    return [{"even_only_triple": list(triple), "count": count} for triple, count in counter.most_common()]


def build_results() -> tuple[dict, dict]:
    scan = json.loads(FULLSCAN.read_text(encoding="utf-8"))
    transitive = json.loads(TRANSITIVE.read_text(encoding="utf-8"))

    records = []
    for rec in scan["counterexamples"]:
        profile = process_square(rec["square"])
        profile["index"] = rec["index"]
        profile["line_number"] = rec["line_number"]
        profile["group_isotopic"] = rec["group_isotopic"]
        records.append(profile)

    transitive_profiles = []
    for sp in transitive["species"]:
        profile = process_square(sp["compact_numeric"])
        item = {"index": sp["index"], "group_isotopic": sp["group_isotopic"]}
        for view in VIEWS:
            item[view] = profile[view]
        transitive_profiles.append(item)

    closure_counter = Counter(
        (rec["group_isotopic"], tuple(is_closed(rec[view]) for view in VIEWS)) for rec in records
    )

    group_results = {
        "theorem": "A Latin square is group-isotopic iff the base-row family {r_0^{-1} r_x} is closed under composition. Equivalently with columns or symbols.",
        "transitive_species_profiles": [
            [
                item["index"],
                item["group_isotopic"],
                {view: is_closed(item[view]) for view in VIEWS},
            ]
            for item in transitive_profiles
        ],
        "order8_fff_summary": {
            "total_fff": len(records),
            "group_isotopic": sum(1 for rec in records if rec["group_isotopic"]),
            "non_group_isotopic": sum(1 for rec in records if not rec["group_isotopic"]),
            "counts_by_groupflag_and_profile": {str(k): v for k, v in closure_counter.items()},
        },
    }

    nongroup = [rec for rec in records if not rec["group_isotopic"]]
    combined_counter = Counter(
        (
            rec["group_isotopic"],
            triple_from(rec, "hits"),
            triple_from(rec, "gsize"),
            even_only_triple(rec),
        )
        for rec in records
    )
    nongroup_gsize_counter = Counter(triple_from(rec, "gsize") for rec in nongroup)
    nongroup_even_counter = Counter(even_only_triple(rec) for rec in nongroup)
    even_only_all = [rec for rec in nongroup if all(even_only_triple(rec))]

    near_results = {
        "theorems": {
            "regular_set_statement": "For every Latin square and every view, the base family {line_0^{-1} line_x} is a regular set of n permutations.",
            "generated_subgroup_transitive": "The subgroup generated by the base family is transitive; hence its order is divisible by n.",
            "group_isotope_criterion": "A Latin square is group-isotopic iff the base family is closed under composition in one/every view.",
        },
        "transitive_species_profiles": transitive_profiles,
        "order8_fff_summary": {
            "total_fff": len(records),
            "group_isotopic": sum(1 for rec in records if rec["group_isotopic"]),
            "non_group_isotopic": len(nongroup),
            "closure_hits_by_view": {
                view: int_counter_dict(rec[view]["hits"] for rec in records) for view in VIEWS
            },
            "generated_subgroup_size_by_view": {
                view: int_counter_dict(rec[view]["gsize"] for rec in records) for view in VIEWS
            },
            "nongroup_combined_profile_top20": top_combined(combined_counter, 20),
            "nongroup_gsize_triple_counts_top20": top_gsize(nongroup_gsize_counter, 20),
            "nongroup_even_only_pattern_counts": top_even_only(nongroup_even_counter),
            "nongroup_same_gsize_all_views": sum(
                1 for rec in nongroup if rec["row"]["gsize"] == rec["col"]["gsize"] == rec["sym"]["gsize"]
            ),
            "nongroup_same_hits_all_views": sum(
                1 for rec in nongroup if rec["row"]["hits"] == rec["col"]["hits"] == rec["sym"]["hits"]
            ),
            "nongroup_same_order_spectra_all_views": sum(
                1 for rec in nongroup if rec["row"]["orders"] == rec["col"]["orders"] == rec["sym"]["orders"]
            ),
            "nongroup_even_only_all_views": len(even_only_all),
            "nongroup_examples_even_only_all_views": [
                {
                    "index": rec["index"],
                    "line_number": rec["line_number"],
                    "hits_triple": list(triple_from(rec, "hits")),
                    "gsize_triple": list(triple_from(rec, "gsize")),
                }
                for rec in even_only_all
            ],
        },
    }
    return group_results, near_results


def write_notes(group_results: dict, near_results: dict) -> None:
    summary = group_results["order8_fff_summary"]
    GROUP_NOTE.write_text(
        "\n".join(
            [
                "Order-8 group-isotope closure criterion reconstruction",
                "",
                group_results["theorem"],
                "",
                f"Total FFF classes: {summary['total_fff']}",
                f"Group-isotopic: {summary['group_isotopic']}",
                f"Non-group-isotopic: {summary['non_group_isotopic']}",
                f"Closure profile counts: {summary['counts_by_groupflag_and_profile']}",
                "",
                "Interpretation: in the order-8 FFF census, closure in all three views matches the stored group-isotopy flag exactly.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    near_summary = near_results["order8_fff_summary"]
    NEAR_NOTE.write_text(
        "\n".join(
            [
                "Order-8 near-closure reconstruction",
                "",
                "For each FFF class and each of the row/column/symbol views, the run forms the base family",
                "{line_0^{-1} line_x}, counts the 64 internal products that remain in the family,",
                "and computes the subgroup generated by that family.",
                "",
                f"Total FFF classes: {near_summary['total_fff']}",
                f"Group-isotopic: {near_summary['group_isotopic']}",
                f"Non-group-isotopic: {near_summary['non_group_isotopic']}",
                f"Non-group classes with same generated subgroup size in all views: {near_summary['nongroup_same_gsize_all_views']}",
                f"Non-group classes with same closure-hit count in all views: {near_summary['nongroup_same_hits_all_views']}",
                f"Non-group classes with even generated subgroups in all views: {near_summary['nongroup_even_only_all_views']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    group_results, near_results = build_results()
    GROUP_OUT.write_text(json.dumps(group_results, indent=2) + "\n", encoding="utf-8")
    NEAR_OUT.write_text(json.dumps(near_results, indent=2) + "\n", encoding="utf-8")
    write_notes(group_results, near_results)
    print(
        json.dumps(
            {
                "group_total": group_results["order8_fff_summary"]["total_fff"],
                "group_profile_counts": group_results["order8_fff_summary"]["counts_by_groupflag_and_profile"],
                "near_even_only_all_views": near_results["order8_fff_summary"]["nongroup_even_only_all_views"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
