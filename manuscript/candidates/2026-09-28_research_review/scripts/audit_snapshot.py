#!/usr/bin/env python3
"""Read-only manuscript/evidence audit with independent, bounded finite controls."""

import argparse
from collections import Counter, deque
import csv
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from math import comb, factorial, isqrt, prod
from pathlib import Path
import re
import time
import verify_review_certificates as review

HERE = Path(__file__).resolve().parents[1]
EVIDENCE = HERE / "evidence"
VIEWS = ("row", "col", "sym")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_table(path):
    if path.suffix == ".csv":
        rows = list(csv.reader(path.read_text(encoding="utf-8-sig").splitlines()))
        if rows and all(len(row) == len(rows) for row in rows) and all(
                value.isdecimal() for row in rows for value in row):
            return [[int(value) for value in row] for row in rows]
        labels = rows[0][1:]
        mapping = {label: i for i, label in enumerate(labels)}
        require(len(mapping) == len(labels) and [row[0] for row in rows[1:]] == labels,
                "CSV axis labels are inconsistent")
        return [[mapping[x] for x in row[1:]] for row in rows[1:]]
    data = read_json(path)
    return data if isinstance(data, list) else data.get("table", data.get("square"))


def lines(table):
    n = len(table)
    expected = set(range(n))
    require(n > 0 and all(len(row) == n and set(row) == expected for row in table),
            "non-Latin row")
    columns = [list(col) for col in zip(*table)]
    require(all(set(col) == expected for col in columns), "non-Latin column")
    symbols = [[-1] * n for _ in range(n)]
    for r, row in enumerate(table):
        for c, s in enumerate(row):
            symbols[s][c] = r
    return table, columns, symbols


def partition(first, second):
    inverse = [0] * len(second)
    for i, value in enumerate(second):
        inverse[value] = i
    permutation = [inverse[x] for x in first]
    remaining = set(range(len(first)))
    lengths = []
    while remaining:
        start = min(remaining)
        node, length = start, 0
        while node in remaining:
            remaining.remove(node)
            length += 1
            node = permutation[node]
        require(node == start, "invalid permutation")
        lengths.append(length)
    return tuple(sorted(lengths))


def matching_partition(first, second):
    """Independent alternating components on positions and values, not composition."""
    n = len(first)
    adjacency = [[] for _ in range(2 * n)]
    for i in range(n):
        for value in (first[i], second[i]):
            adjacency[i].append(n + value)
            adjacency[n + value].append(i)
    visited = set()
    lengths = []
    for start in range(n):
        if start in visited:
            continue
        pending = [start]
        component = set()
        while pending:
            vertex = pending.pop()
            if vertex in component:
                continue
            component.add(vertex)
            pending.extend(x for x in adjacency[vertex] if x not in component)
        visited.update(component)
        require(len(component) % 2 == 0, "unbalanced matching component")
        lengths.append(len(component) // 2)
    return tuple(sorted(lengths))


def scan(table, independent=True):
    spectrum = Counter()
    odd_counts = {}
    for view, family in zip(VIEWS, lines(table)):
        failures = 0
        for a, b in combinations(range(len(table)), 2):
            shape = partition(family[a], family[b])
            require(1 not in shape, "distinct Latin lines have a fixed point")
            if independent:
                require(shape == matching_partition(family[a], family[b]),
                        "cycle and matching-component scanners disagree")
            spectrum[shape] += 1
            failures += any(x % 2 for x in shape)
        odd_counts[view] = failures
    signature = tuple(sorted(spectrum.items()))
    payload = [[list(shape), count] for shape, count in signature]
    pattern = "".join("T" if odd_counts[v] else "F" for v in VIEWS)
    return {
        "latin": True, "order": len(table), "pattern": pattern, "fff": pattern == "FFF",
        "line_pairs_checked": 3 * comb(len(table), 2), "odd_pair_counts": odd_counts,
        "spectrum_sha256": hashlib.sha256(
            json.dumps(payload, separators=(",", ":")).encode("ascii")).hexdigest(),
    }, signature


def color_channel(first, second):
    n = len(first)
    adjacency = [[] for _ in range(2 * n)]
    for i in range(n):
        for value, parity in ((first[i], 0), (second[i], 1)):
            adjacency[i].append((n + value, parity))
            adjacency[n + value].append((i, parity))
    colors = [None] * (2 * n)
    for root in range(2 * n):
        if colors[root] is not None:
            continue
        colors[root] = 0
        queue = deque([root])
        while queue:
            vertex = queue.popleft()
            for other, parity in adjacency[vertex]:
                value = colors[vertex] ^ parity
                if colors[other] is None:
                    colors[other] = value
                    queue.append(other)
                elif colors[other] != value:
                    return False
    require(sum(colors[:n]) * 2 == n and sum(colors[n:]) * 2 == n,
            "color channel violates automatic balance")
    require(colors[0] == 0, "single gauge was not satisfied")
    for i in range(n):
        for v in range(n):
            a, b, e, h = first[i] == v, second[i] == v, colors[i], colors[n + v]
            clauses = ((not a or not e or h), (not a or e or not h),
                       (not b or e or h), (not b or not e or not h))
            require(all(clauses), "channel assignment violates a printed clause")
    return True


def fibred(fibres, quotient=None):
    n, m = len(fibres[0]), len(fibres)
    quotient = quotient or [[y ^ z for z in range(m)] for y in range(m)]
    return [[m * fibres[y][r][c] + quotient[y][z]
             for c in range(n) for z in range(m)] for r in range(n) for y in range(m)]


def pattern_or(*patterns):
    return "".join("T" if any(p[i] == "T" for p in patterns) else "F" for i in range(3))


def affine_table(p, a):
    b = (1 - a) % p
    return [[(c if r == p else r if c == p else p if r == c else (a*r + b*c) % p)
             for c in range(p + 1)] for r in range(p + 1)]


def multiplicative_order(p, a):
    value = a % p
    for k in range(1, p):
        if value == 1:
            return k
        value = value * a % p
    raise ValueError("invalid multiplicative order")


def affine_pattern(p, a):
    b = (1 - a) % p
    parameters = (a, b, pow(a, -1, p))
    return "".join("F" if pow(t, -1, p) % 2 == 0
                   and multiplicative_order(p, (1-t) % p) % 2 == 0 else "T"
                   for t in parameters)


def affine_histogram(d):
    """Enumerate independent image bases using a span, then every translation."""
    n = 1 << d
    histogram = Counter()
    groups = []
    for basis in product(range(1, n), repeat=d):
        span = {0}
        for image in basis:
            if image in span:
                break
            span |= {x ^ image for x in span}
        else:
            linear = []
            for x in range(n):
                y = 0
                for i, image in enumerate(basis):
                    if x & (1 << i):
                        y ^= image
                linear.append(y)
            for shift in range(n):
                permutation = tuple(x ^ shift for x in linear)
                count = len(partition(list(permutation), list(range(n))))
                histogram[count] += 1
                if d <= 3:
                    groups.append(permutation)
    require(sum(histogram.values()) == n * prod(n-(1 << i) for i in range(d)),
            "affine group has wrong size")
    return histogram, groups


def source_graph(entry):
    visited = set()
    def visit(path):
        require(path.is_relative_to(HERE) and path.is_file(), "missing or external TeX source")
        if path in visited:
            return
        visited.add(path)
        text = path.read_text()
        for name in re.findall(r"\\input\{([^}]+)\}", text):
            visit((HERE / (name if name.endswith(".tex") else name + ".tex")).resolve())
    visit(HERE / entry)
    return visited


def audit_sources():
    retained = []
    for name in ("capture.json", "additional_capture.json", "dependency_capture.json",
                 "review_additions_capture.json", "palette_capture.json"):
        for item in read_json(EVIDENCE / name)["files"]:
            if item["snapshot"].startswith("evidence/"):
                path = HERE / item["snapshot"]
                require(path.is_file() and path.stat().st_size == item["bytes"]
                        and digest(path) == item["sha256"], f"captured evidence changed: {path}")
                retained.append(item)
    entries = {}
    for entry in ("main.tex", "main_core.tex"):
        paths = source_graph(entry)
        content = "\n".join(path.read_text() for path in sorted(paths))
        labels = re.findall(r"\\label\{([^}]+)\}", content)
        refs = set(re.findall(r"\\(?:eqref|ref)\{([^}]+)\}", content))
        require(len(labels) == len(set(labels)), f"duplicate labels in {entry}")
        require(refs <= set(labels), f"undefined references in {entry}: {refs-set(labels)}")
        require(not re.search(r"\\author\{[^}]+\}|pdfauthor=\{[^}]+\}|/Users/", content),
                f"unapproved identity or local path in {entry}")
        for label in ("thm:row-fibred-pattern", "thm:affine-fibre-orbits",
                      "cthm:dyadic-fff20-bound", "thm:affine-criterion",
                      "thm:affine-large-prime", "cthm:fff98", "thm:value-color-channel"):
            require(label in labels, f"missing updated theorem {label}")
        entries[entry] = {"source_files": len(paths), "labels": len(labels),
                          "references_resolve": True, "author_metadata_empty": True}
    return {"immutable_files_checked": len(retained), "entries": entries}


def run_finite_checks():
    data = EVIDENCE / "data"
    populations = {}
    palette_text = (HERE / "sections/07_order10_exclusion.tex").read_text()
    for case in ("f12", "f08", "f13", "f14", "f09", "f10", "f15"):
        record = read_json(data / f"{case}_candidate_population.json")
        require(record["valid"] and record["fff_count"] == 0 and
                sum(record["pattern_counts"].values()) == record["clique_count"] and
                record["exact_palette_count"] <= record["clique_count"], "candidate population mismatch")
        require(re.search(r"all\s+\$" + str(record["clique_count"]) + r"\$ candidates", palette_text),
                "candidate population not explicit in revised paper")
        populations[case] = {key: record[key] for key in
                             ("clique_count", "exact_palette_count", "pattern_counts")}
    witness_text = (HERE / "sections/08_nonpower_fff.tex").read_text()
    printed_rows = re.findall(r"^\s*(\d+)\s*&\s*([0-9& ]+)\\\\", witness_text, re.MULTILINE)
    printed = [[int(value.strip()) for value in cells.split("&")] for _, cells in printed_rows]
    require([int(index) for index, _ in printed_rows] == list(range(12))
            and printed == load_table(data / "order12_first.json"),
            "printed order12 table differs from frozen witness")
    controls = {}
    for name in ("order12_first.json", "order12_preferred.json", "order14.csv",
                 "order36_seed60322.csv", "order36_seed60324.csv", "order98.json"):
        checked, _ = scan(load_table(data / name))
        require(checked["fff"], f"positive control failed: {name}")
        controls[name] = checked
    pattern_records = read_json(data / "order8_pattern_controls.json")["selected_pattern_examples"]
    examples = {}
    channel_pairs = 0
    for record in pattern_records:
        flat = [int(x) for x in record["compact_square"]]
        table = [flat[i:i+8] for i in range(0, 64, 8)]
        checked, _ = scan(table)
        require(checked["pattern"] == record["summary"]["pattern_name"], "order8 pattern drift")
        examples[checked["pattern"]] = table
        for family in lines(table):
            for a, b in combinations(range(8), 2):
                expected = all(x % 2 == 0 for x in partition(family[a], family[b]))
                require(color_channel(family[a], family[b]) == expected, "channel equivalence failed")
                channel_pairs += 1
    require(set(examples) == {"".join(bits) for bits in product("FT", repeat=3)},
            "not all eight patterns tested")
    c4 = [[(r+c) % 4 for c in range(4)] for r in range(4)]
    v4 = [[r ^ c for c in range(4)] for r in range(4)]
    extension_checks = 0
    for pattern, table in examples.items():
        for fibres, quotient, expected in (
            ([table, examples["FFF"]], None, pattern),
            ([c4 if y % 2 else v4 for y in range(8)], table, pattern)):
            checked, _ = scan(fibred(fibres, quotient))
            require(checked["pattern"] == expected, "fibre/quotient pattern equality failed")
            extension_checks += 1
    affine_count = 0
    for p in range(3, 44, 2):
        if any(p % q == 0 for q in range(2, isqrt(p)+1)):
            continue
        for a in range(2, p):
            checked, _ = scan(affine_table(p, a))
            require(checked["pattern"] == affine_pattern(p, a), "affine three-view criterion failed")
            affine_count += 1
    require(affine_count == 253, "affine control coverage drift")
    require(sum(Fraction(2303, 1000)**k / factorial(k) for k in range(10)) > 10,
            "logarithm cutoff inequality failed")
    require(260 * Fraction(15318, 1000)**3 < 935000, "rational cutoff failed")
    source = load_table(data / "steiner20.json")
    frozen = read_json(EVIDENCE / "runs/2026-09-26_fff20_steiner_trade_mainclasses/results/trade_mainclass_audit.json")
    require(digest(data / "steiner20.json") == frozen["source_sha256"], "source hash mismatch")
    components = frozen["source_row_pair_components"]
    require(len(components) == 10 and sorted(x for pair in components for x in pair) == list(range(20)),
            "trade mask does not cover columns")
    spectra = {}
    tables = {}
    for mask in range(1024):
        table = [row[:] for row in source]
        for bit, pair in enumerate(components):
            if mask & (1 << bit):
                for c in pair:
                    table[0][c], table[1][c] = table[1][c], table[0][c]
        checked, signature = scan(table)
        require(checked["fff"], f"trade mask {mask} not FFF")
        spectra.setdefault(signature, []).append(mask)
        tables[mask] = table
    require(len(spectra) == 512 and all(len(masks) == 2 and masks[0] ^ masks[1] == 1023
                                      for masks in spectra.values()), "trade classes changed")
    for mask in range(512):
        opposite = tables[1023 ^ mask]
        require([tables[mask][1], tables[mask][0], *tables[mask][2:]] == opposite,
                "complementary mask is not a global row swap")
    for item in frozen["representatives"]:
        checked, _ = scan(tables[item["mask"]], independent=False)
        require(checked["spectrum_sha256"] == item["spectrum_sha256"], "frozen source spectrum drift")
    quadratic = read_json(data / "quadratic_sources.json")["quadratic_f19"]["fff_candidates"]
    for coefficients in ((2, 2), (8, 8)):
        table = next(item["table"] for item in quadratic if tuple(item["coefficients"]) == coefficients)
        checked, signature = scan(table)
        require(checked["fff"] and signature not in spectra, "quadratic class not distinct")
        spectra[signature] = [coefficients]
    require(len(spectra) == 514, "incorrect base class bound")
    affine_frozen = read_json(EVIDENCE / "runs/2026-09-26_fff_affine_orbit_fibres/results/affine_orbit_fibres_audit.json")
    burnside = []
    group3 = None
    for record in affine_frozen["burnside_counts"]:
        d = record["dimension"]
        histogram, group = affine_histogram(d)
        numerator = sum(514**cycles * count for cycles, count in histogram.items())
        order = sum(histogram.values())
        require(numerator % order == 0, "nonintegral Burnside count")
        count = numerator // order
        require(count == record["affine_coloring_orbits"], "Burnside bound mismatch")
        count_text = (HERE / "sections/10_fibred_class_growth.tex").read_text()
        expected_cell = "$" + str(20*(1 << d)) + "$ & $" + str(count) + "$"
        require(expected_cell in count_text, "displayed bound differs from exact count")
        require({str(k): v for k, v in histogram.items()} == record["cycle_count_histogram"],
                "affine cycle histogram mismatch")
        burnside.append({"order": 20*(1 << d), "bound": count, "group_order": order})
        if d == 3:
            group3 = group
    plane, tetra = {0, 1, 2, 3}, {0, 1, 2, 4}
    orbit0 = {tuple(sorted(p[x] for x in plane)) for p in group3}
    orbit1 = {tuple(sorted(p[x] for x in tetra)) for p in group3}
    require(len(orbit0) == 14 and len(orbit1) == 56 and not orbit0 & orbit1,
            "plane and tetrahedron are not separated")
    reps = frozen["representatives"]
    first, second = tables[reps[0]["mask"]], tables[reps[1]["mask"]]
    physical160 = []
    full_spectra = []
    for positions in (plane, tetra):
        checked, spectrum = scan(fibred([first if y in positions else second for y in range(8)]))
        require(checked["fff"], "order160 physical control failed")
        physical160.append(checked)
        full_spectra.append(spectrum)
    require(full_spectra[0] == full_spectra[1], "exact order160 spectra differ")
    return {
        "direct_binary_rank_certificates": review.verify_bundle(),
        "review_scope_controls": review.scope_control(scan),
        "frozen_palette_populations_reconciled": populations,
        "positive_controls": controls, "all_eight_patterns_tested": sorted(examples),
        "printed_order12_table_exact_match": True,
        "color_channel_pair_truth_tables": channel_pairs,
        "row_fibred_pattern_controls": extension_checks, "affine_parameter_tables": affine_count,
        "rational_cutoff_inequalities": True, "trade_masks_freshly_scanned": 1024,
        "trade_family_main_classes": 512, "fff20_base_class_lower_bound": 514,
        "burnside_counts": burnside, "order160_physical_controls": physical160,
        "order160_spectra_compared_as_exact_tuples": True,
        "full_output_census": False, "order18_decided": False,
        "heavy_solvers_run": False, "historical_unsat_proofs_rerun": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    result = {"sources": audit_sources(), "finite_checks": run_finite_checks(),
              "overall_pass": True, "elapsed_seconds": round(time.monotonic()-start, 3)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"overall_pass": True, "elapsed_seconds": result["elapsed_seconds"],
                      "report": str(args.output)}))


if __name__ == "__main__":
    main()
