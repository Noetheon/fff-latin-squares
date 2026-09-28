#!/usr/bin/env python3
"""Portable fresh controls for the C271 paper update; no solver or census run."""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import audit_snapshot as base
import verify_review_certificates as rank

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "evidence/data"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def captured_sources():
    record = base.read_json(HERE / "evidence/update_capture.json")
    for item in record["files"]:
        path = (HERE / item["snapshot"]).resolve()
        require(path.is_relative_to(HERE) and path.is_file(), "missing update capture")
        require(path.stat().st_size == item["bytes"] and base.digest(path) == item["sha256"],
                "update capture hash mismatch: " + item["snapshot"])
    return len(record["files"])


def corner_table(p, a, trade=True):
    require(0 < a < p-1, "invalid affine coefficient")
    b = (a+1)*pow(a, -1, p) % p
    table = [[p if r == p and c == p else
              b*c % p if r == p else
              (a+1)*r % p if c == p else
              p if c == a*r % p else (r+c) % p
              for c in range(p+1)] for r in range(p+1)]
    if trade:
        for row in (0, p):
            table[row][0], table[row][p] = table[row][p], table[row][0]
    return table


def intercalates(table):
    count = 0
    for r, s in combinations(range(len(table)), 2):
        for c, d in combinations(range(len(table)), 2):
            count += table[r][c] == table[s][d] and table[r][d] == table[s][c]
    return count


def table_from_descriptor(item):
    if "quadratic_coefficients" in item:
        candidates = base.read_json(DATA / "quadratic_sources.json")["quadratic_f19"]["fff_candidates"]
        tables = [row["table"] for row in candidates
                  if row["coefficients"] == item["quadratic_coefficients"]]
        require(len(tables) == 1, "ambiguous quadratic representative")
        return tables[0]
    table = base.load_table(DATA / "steiner20.json")
    a, b = item["row_pair"]
    inverse = {value: c for c, value in enumerate(table[b])}
    components = rank.cycles([inverse[x] for x in table[a]])
    require(len(components) == 10 and all(len(c) == 2 for c in components),
            "representative does not belong to an eligible two-cycle family")
    for bit, component in enumerate(components):
        if item["mask"] & (1 << bit):
            for c in component:
                table[a][c], table[b][c] = table[b][c], table[a][c]
    return table


def minor_certificate(table):
    n = len(table)
    kept = rank.minor_rows(n)
    row_index = {line: i for i, line in enumerate(kept)}
    pivots, cells = {}, []
    for r in range(n):
        for c in range(n):
            vector = sum(1 << row_index[line] for line in (r, n+c, 2*n+table[r][c])
                         if line in row_index)
            while vector:
                pivot = vector.bit_length()-1
                if pivot not in pivots:
                    pivots[pivot] = vector
                    cells.append(n*r+c)
                    break
                vector ^= pivots[pivot]
    require(len(cells) == 3*n-2, "input admits an additional binary dependence")
    rank.verify_minor(table, cells)
    return {"table_sha256_raw_bytes": rank.table_hash(table), "rank": len(cells),
            "cell_columns": cells}


def expanded_family():
    record = base.read_json(DATA / "expanded_order20_representatives.json")
    require(len(record["representatives"]) == 1702, "wrong expanded input count")
    exact_spectra, certificates, intercalate_counts = set(), [], []
    for index, descriptor in enumerate(record["representatives"]):
        table = table_from_descriptor(descriptor)
        checked, spectrum = base.scan(table)
        require(checked["fff"], "expanded representative is not FFF")
        require(spectrum not in exact_spectra, "expanded spectra collide")
        twice_cycles = sum(shape.count(2)*count for shape, count in spectrum)
        require(twice_cycles % 3 == 0, "inconsistent three-view intercalate count")
        intercalate_counts.append(twice_cycles//3)
        exact_spectra.add(spectrum)
        certificates.append({"id": index, **minor_certificate(table)})
    extra = corner_table(19, 7)
    checked, spectrum = base.scan(extra)
    require(checked["fff"] and intercalates(extra) == 1, "new corner positive failed")
    require(spectrum not in exact_spectra, "corner table does not add a spectrum")
    exact_spectra.add(spectrum)
    certificates.append({"id": "corner19_7", **minor_certificate(extra)})
    require(len(exact_spectra) == 1703, "wrong class lower bound")
    require(min(intercalate_counts) >= 19, "expanded input intercalate bound failed")
    return {"freshly_reconstructed_tables": 1703, "exact_distinct_spectra": 1703,
            "all_latin_fff": True, "binary_rank": 58,
            "independently_checked_minors": certificates,
            "original_1702_min_intercalates": min(intercalate_counts),
            "corner_intercalates": 1,
            "C157_dependency": False,
            "order40_lower_bound": 1703*1704//2,
            "historical_22528_mask_search_rerun": False,
            "complete_order20_census": False}


def block_returns():
    records = []
    for filename in ("order12_first.json", "order12_preferred.json"):
        table = base.load_table(DATA / filename)
        quotient = [[table[4*a][4*b]//4 for b in range(3)] for a in range(3)]
        require(base.scan(quotient)[0]["pattern"] == "TTT", "quotient control drift")
        for a in range(3):
            for b in range(3):
                block = [[table[4*a+x][4*b+y] % 4 for y in range(4)] for x in range(4)]
                require(all(table[4*a+x][4*b+y]//4 == quotient[a][b]
                            for x in range(4) for y in range(4)), "not a block substitution")
                require(base.scan(block)[0]["fff"], "inner block is not FFF")
        pairs = 0
        for family in base.lines(table):
            for u, v in combinations(range(12), 2):
                inv = {value: i for i, value in enumerate(family[v])}
                perm = [inv[value] for value in family[u]]
                projected = [perm[4*b]//4 for b in range(3)]
                require(all(perm[4*b+y]//4 == projected[b] for b in range(3) for y in range(4)),
                        "relative map does not project")
                predicted = []
                for cycle in rank.cycles(projected):
                    start, d = cycle[0], len(cycle)
                    ret = []
                    for y in range(4):
                        point = 4*start+y
                        for _ in range(d):
                            point = perm[point]
                        require(point//4 == start, "return leaves fibre")
                        ret.append(point % 4)
                    predicted.extend(d*len(inner) for inner in rank.cycles(ret))
                require(sorted(predicted) == sorted(len(c) for c in rank.cycles(perm)),
                        "block-return cycle formula mismatch")
                pairs += 1
        records.append({"source": filename, "line_pairs": pairs,
                        "quotient_pattern": "TTT", "block_patterns": ["FFF"]*9,
                        "whole_pattern": base.scan(table)[0]["pattern"]})
    return records


def corner_controls():
    examples, tested, generic_count, p17 = {}, 0, 0, []
    for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43):
        for a in range(1, p-1):
            old, new = corner_table(p, a, False), corner_table(p, a)
            before, _ = base.scan(old, independent=False)
            after, _ = base.scan(new, independent=False)
            require(before["pattern"] == after["pattern"], "corner pattern changed")
            tested += 1
            if p == 17:
                p17.append(after["pattern"])
            if p >= 5 and a not in {1, p-2, -pow(2, -1, p) % p}:
                require(intercalates(old) == p and intercalates(new) == 1,
                        "generic intercalate formula failed")
                for r in range(1, p):
                    c = -r % p
                    require(new[r][c] == 0, "contraction hole changed")
                    row_domain = {new[r][0], new[r][p]}
                    col_domain = {new[0][c], new[p][c]}
                    require(not row_domain & col_domain, "claimed empty domain is nonempty")
                generic_count += 1
            if (p, a) in {(13, 3), (19, 7)}:
                result, _ = base.scan(new, independent=True)
                require(result["fff"], "corner positive control failed")
                examples[f"p{p}_a{a}"] = {**result, "intercalates": intercalates(new),
                                           "table": new, "empty_hole_domains": p-1}
    require(tested == 253 and generic_count == 216 and "FFF" not in p17,
            "corner coverage counts disagree")
    return {"parameters_tested": tested, "generic_parameters": generic_count,
            "three_view_pattern_preserved": True, "positives": examples,
            "p17_patterns": p17, "unrestricted_order18_decided": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Choose a fresh output; retained reports are immutable.")
    start = time.monotonic()
    result = {"captured_update_files_verified": captured_sources(),
              "expanded_class_family": expanded_family(), "block_returns": block_returns(),
              "corner_trade": corner_controls(), "overall_pass": True,
              "order18_decided": False, "heavy_solver_runs": False,
              "historical_DRAT_rechecked": False,
              "elapsed_seconds": round(time.monotonic()-start, 3)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "order20_lower_bound": 1703,
                      "order40_lower_bound": result["expanded_class_family"]["order40_lower_bound"],
                      "elapsed_seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
