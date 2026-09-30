#!/usr/bin/env python3
"""Literal small-order controls; no producer or algebra-module imports."""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import sys
from time import monotonic


Q4_MASKS = {0, 1, 65535, 0x1234, 0xA55A, 0x8421}
TABLES = {
    "C2": [[(r + c) % 2 for c in range(2)] for r in range(2)],
    "C4": [[(r + c) % 4 for c in range(4)] for r in range(4)],
    "V4": [[r ^ c for c in range(4)] for r in range(4)],
}
SOURCE21 = "0123456710325476231076543201674545761032546701236754321076452301"
SOURCE21_TABLE = [[int(c) for c in SOURCE21[r * 8:(r + 1) * 8]] for r in range(8)]
SOURCE21_MASK = 18374403900871474688
SOURCE21_BASE_SHA256 = "116bad5e6f74807dfa64e21b4f2267a14e7288b54aab8a963e3dbd5001538a0a"
SOURCE_HASHES = {
    "repro_runs/2026-09-23_fff18_central_extension_mask_search/results/central_extension_screen_225x2x32.json":
        "bdc2e07a2e4e05777f85fc672c7a6c0cdfd22a0083245658970e9129c6389b9c",
    "repro_runs/2026-09-25_fff18_nongroup16_c190_targeted_pilot/results/selected_fff16_base.json":
        "a002d1e82b936e332c710c0b85cf709010ef88572992ffb1dd723ce6de42e1e6",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, label)
    return value


def latin(table):
    require(type(table) is list and len(table) >= 2, "invalid table")
    n = len(table)
    for row in table:
        require(type(row) is list and len(row) == n, "invalid table row")
        for value in row:
            integer(value, 0, n - 1, "nonliteral/out-of-range table value")
        require(set(row) == set(range(n)), "non-Latin row")
    require(all({table[r][c] for r in range(n)} == set(range(n))
                for c in range(n)), "non-Latin column")
    return n


def plex_cells(table, cells):
    q = len(table)
    require(type(cells) is list and len(cells) == 2 * q,
            "a simple two-plex needs exactly 2q cells")
    result = []
    for cell in cells:
        require(type(cell) is list and len(cell) == 2, "malformed plex cell")
        r = integer(cell[0], 0, q - 1, "invalid plex row")
        c = integer(cell[1], 0, q - 1, "invalid plex column")
        result.append((r, c))
    require(len(set(result)) == len(result), "repeated quotient cell")
    for values in ([r for r, c in result], [c for r, c in result],
                   [table[r][c] for r, c in result]):
        require(Counter(values) == Counter({i: 2 for i in range(q)}),
                "not a two-plex in all three coordinates")
    return tuple(sorted(result))


def all_plexes(table):
    q = len(table)
    answer = []
    for cells in combinations([(r, c) for r in range(q) for c in range(q)], 2 * q):
        if all(Counter(values) == Counter({i: 2 for i in range(q)})
               for values in ([r for r, c in cells], [c for r, c in cells],
                              [table[r][c] for r, c in cells])):
            answer.append(cells)
    return answer


def physical_table(table, mask):
    q = len(table)
    integer(mask, 0, (1 << (q * q)) - 1, "invalid twist mask")
    return [[2 * table[r // 2][c // 2]
             + ((r & 1) ^ (c & 1) ^ ((mask >> (q * (r // 2) + c // 2)) & 1))
             for c in range(2 * q)] for r in range(2 * q)]


def physical_transversals(table):
    n = latin(table)
    require(n <= 8, "literal enumeration is restricted to n <= 8")
    return [p for p in permutations(range(n))
            if len({table[r][p[r]] for r in range(n)}) == n]


def projection(quotient, transversal):
    return plex_cells(quotient, [[r // 2, c // 2]
                                for r, c in enumerate(transversal)])


def restricted_transversals(quotient, table, cells, node_cap=2000000):
    """Literal DFS restricted to one supplied projection; never enumerate 16!."""
    n = latin(table)
    cells = tuple(cells)
    number = {cell: i for i, cell in enumerate(cells)}
    options = [[2 * c + bit for a, c in cells if a == r // 2 for bit in range(2)]
               for r in range(n)]
    chosen = []
    answer = []
    nodes = 0

    def visit(r, used_columns, used_symbols, used_cells):
        nonlocal nodes
        nodes += 1
        require(nodes <= node_cap, "restricted literal DFS node cap exceeded")
        if r == n:
            answer.append(tuple(chosen))
            return
        for c in options[r]:
            s = table[r][c]
            bit = 1 << number[(r // 2, c // 2)]
            if not ((used_columns >> c) & 1 or (used_symbols >> s) & 1 or used_cells & bit):
                chosen.append(c)
                visit(r + 1, used_columns | (1 << c), used_symbols | (1 << s), used_cells | bit)
                chosen.pop()

    visit(0, 0, 0, 0)
    for transversal in answer:
        validate_transversal(table, transversal)
        require(projection(quotient, transversal) == cells, "restricted DFS projection mismatch")
    return answer, nodes


def component_prediction(table, cells, mask):
    q = len(table)
    adjacency = [set() for _ in range(q)]
    for coordinate in (0, 1):
        for line in range(q):
            symbols = [table[r][c] for r, c in cells if (r, c)[coordinate] == line]
            require(len(symbols) == 2 and symbols[0] != symbols[1], "invalid matching")
            a, b = symbols
            adjacency[a].add(b)
            adjacency[b].add(a)
    unseen = set(range(q))
    components = []
    while unseen:
        reached = set()
        todo = [min(unseen)]
        while todo:
            v = todo.pop()
            if v not in reached:
                reached.add(v)
                todo.extend(adjacency[v] - reached)
        unseen -= reached
        parity = sum((mask >> (q * r + c)) & 1
                     for r, c in cells if table[r][c] in reached) % 2
        components.append({"symbols": sorted(reached), "twist_parity": parity,
                           "required_parity": len(reached) % 2})
    compatible = all(c["twist_parity"] == c["required_parity"] for c in components)
    return (1 << (q + len(components))) if compatible else 0, components


def literal_twist_census(quotient, deadline=None):
    """Count from physical column permutations, not from the component formula."""
    q = len(quotient)
    n = 2 * q
    counts = [0] * (1 << (q * q))
    free_count = q * q - q
    gray_flips = [(k & -k).bit_length() - 1 for k in range(1, 1 << free_count)]
    eligible = 0
    for columns in permutations(range(n)):
        if deadline is not None and monotonic() > deadline:
            raise ValueError("literal full-census time budget exceeded")
        indices = [q * (r // 2) + columns[r] // 2 for r in range(n)]
        if len(set(indices)) != n:
            continue
        by_symbol = [[] for _ in range(q)]
        for r, c in enumerate(columns):
            by_symbol[quotient[r // 2][c // 2]].append(r)
        if any(len(rows) != 2 for rows in by_symbol):
            continue
        eligible += 1
        base = 0
        toggles = [1 << i for i in range(q * q) if i not in indices]
        for r, t in by_symbol:
            i, j = indices[r], indices[t]
            rhs = 1 ^ (r & 1) ^ (t & 1) ^ (columns[r] & 1) ^ (columns[t] & 1)
            base |= rhs << j
            toggles.append((1 << i) | (1 << j))
        require(len(toggles) == free_count, "literal census free-coordinate mismatch")
        value = base
        counts[value] += 1
        for flip in gray_flips:
            value ^= toggles[flip]
            counts[value] += 1
    return counts, eligible


def views(table):
    n = len(table)
    # Symbol lines use row positions; the column-position convention has
    # inverse/conjugate relative permutations and hence the same cycle types.
    symbol = [[None] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            symbol[table[r][c]][r] = c
    return {"row": table,
            "col": [[table[r][c] for r in range(n)] for c in range(n)],
            "sym": symbol}


def cycle_lengths(first, second):
    inverse = {value: i for i, value in enumerate(second)}
    p = [inverse[value] for value in first]
    unseen = set(range(len(p)))
    result = []
    while unseen:
        start = min(unseen)
        v = start
        length = 0
        while v in unseen:
            unseen.remove(v)
            length += 1
            v = p[v]
        require(v == start, "not a permutation cycle")
        result.append(length)
    return sorted(result)


def profile(table):
    n = latin(table)
    bad = {}
    for name, lines in views(table).items():
        bad[name] = sum(any(length % 2 for length in cycle_lengths(lines[a], lines[b]))
                        for a, b in combinations(range(n), 2))
    return {"n": n, "latin": True, "bad_pairs": bad,
            "pattern": "".join("T" if bad[v] else "F" for v in ("row", "col", "sym"))}


def validate_transversal(table, transversal):
    n = len(table)
    require(type(transversal) in (list, tuple) and len(transversal) == n, "invalid transversal container")
    for column in transversal:
        integer(column, 0, n - 1, "nonliteral/out-of-range transversal column")
    require(set(transversal) == set(range(n)), "not a column permutation")
    require(len({table[r][transversal[r]] for r in range(n)}) == n, "not a transversal")


def prolong(table, first, second):
    n = len(table)
    validate_transversal(table, first)
    validate_transversal(table, second)
    require(all(first[r] != second[r] for r in range(n)), "transversals intersect")
    result = [row[:] + [None, None] for row in table] + [[None] * (n + 2) for _ in range(2)]
    for t, transversal in enumerate((first, second)):
        for r, c in enumerate(transversal):
            s = table[r][c]
            result[r][c] = n + t
            result[r][n + t] = s
            result[n + t][c] = s
    for t in range(2):
        for u in range(2):
            result[n + t][n + u] = n + (t ^ u)
    latin(result)
    return result


def paired_line_check(quotient, table, first, second):
    validate_transversal(table, first)
    validate_transversal(table, second)
    require(all(a != b for a, b in zip(first, second)), "pair is not disjoint")
    if projection(quotient, first) != projection(quotient, second):
        return {"covered": False}
    q = len(quotient)
    choices = [{(r // 2, c // 2): (r & 1, c & 1, table[r][c] & 1)
                for r, c in enumerate(t)} for t in (first, second)]
    differences = {cell: tuple(a ^ b for a, b in zip(choices[0][cell], choices[1][cell]))
                   for cell in choices[0]}
    require(all((dx ^ dy ^ dz) == 0 and (dx or dy)
                for dx, dy, dz in differences.values()), "invalid fibre difference relation")
    extended = views(prolong(table, first, second))
    checked = Counter()
    failures = []
    expected = [2] * (q - 2) + [3, 3]
    for position, view in enumerate(("row", "col", "sym")):
        for line in range(q):
            bits = {d[position] for (r, c), d in differences.items()
                    if (r, c, quotient[r][c])[position] == line}
            require(len(bits) == 1, "difference is not constant on a quotient matching")
            if bits == {0}:
                lengths = cycle_lengths(extended[view][2 * line], extended[view][2 * line + 1])
                checked[view] += 1
                if lengths != expected:
                    failures.append({"view": view, "line": line, "cycle_lengths": lengths})
    require(sum(checked.values()) > 0, "same-projection pair has no zero difference")
    return {"covered": True, "paired_lines_checked": dict(checked), "failures": failures}


def different_projection_guard(quotient, table, groups):
    for first_group, second_group in combinations(groups.values(), 2):
        for first in first_group:
            for second in second_group:
                if all(a != b for a, b in zip(first, second)):
                    require(paired_line_check(quotient, table, first, second) == {"covered": False},
                            "different projection incorrectly covered")
                    return {"first": list(first), "second": list(second), "covered": False}
    return None


def check_control(quotient, mask, entries=None, total=None):
    table = physical_table(quotient, mask)
    physical = physical_transversals(table)
    groups = {}
    for transversal in physical:
        cells = projection(quotient, transversal)
        groups.setdefault(cells, []).append(transversal)
    plexes = all_plexes(quotient)
    predictions = {}
    component_counts = Counter()
    for cells in plexes:
        expected, components = component_prediction(quotient, cells, mask)
        actual = len(groups.get(cells, []))
        require(actual == expected, "component prediction disagrees with literal enumeration")
        predictions[cells] = expected
        component_counts[len(components)] += 1
    if entries is not None:
        require(type(entries) is list, "projected_transversal_counts must be a list")
        seen = set()
        supplied_total = 0
        for entry in entries:
            require(type(entry) is dict and "cells" in entry and "count" in entry,
                    "malformed projected count")
            cells = plex_cells(quotient, entry["cells"])
            require(cells not in seen, "duplicate projected count")
            seen.add(cells)
            count = integer(entry["count"], 0, 40320, "invalid projected count")
            require(count == predictions[cells], "producer projected count mismatch")
            supplied_total += count
        require(seen == set(plexes), "projected counts must cover every plex, including zero counts")
        integer(total, 0, 40320, "invalid total_transversals")
        require(total == supplied_total == len(physical), "producer total mismatch")
    ordered_pairs = 0
    paired_lines = Counter()
    counterexamples = []
    for transversals in groups.values():
        for first in transversals:
            for second in transversals:
                if all(a != b for a, b in zip(first, second)):
                    ordered_pairs += 1
                    result = paired_line_check(quotient, table, first, second)
                    require(result["covered"], "same-projection pair escaped scope")
                    paired_lines.update(result["paired_lines_checked"])
                    if result["failures"]:
                        counterexamples.append({"first": list(first), "second": list(second),
                                                "failures": result["failures"]})
    different_guard = different_projection_guard(quotient, table, groups)
    return {"twist_mask": mask, "total_transversals": len(physical),
            "simple_two_plexes": len(plexes), "liftable_plexes": len(groups),
            "component_count_distribution": dict(sorted(component_counts.items())),
            "physical_profile": profile(table), "ordered_same_projection_disjoint_pairs": ordered_pairs,
            "paired_lines_checked": dict(paired_lines), "counterexamples": counterexamples,
            "different_projection_guard": different_guard}


def check_source21(quotient, record):
    require(record.get("all_base_transversals_enumerated") is False,
            "source21 control must explicitly retain restricted scope")
    mask = record["twist_mask"]
    require(mask == SOURCE21_MASK, "source21 twist differs from the frozen control")
    table = physical_table(quotient, mask)
    compact = json.dumps(table, separators=(",", ":")).encode("ascii")
    require(hashlib.sha256(compact).hexdigest() == SOURCE21_BASE_SHA256,
            "source21 physical base differs from the frozen compact-table hash")
    entries = record["projected_transversal_counts"]
    require(type(entries) is list and len(entries) == 2, "source21 needs exactly two selected projections")
    groups = {}
    nodes = 0
    paired_lines = Counter()
    ordered_pairs = 0
    counterexamples = []
    for entry in entries:
        require(type(entry) is dict and "cells" in entry and "count" in entry, "invalid source21 projection")
        cells = plex_cells(quotient, entry["cells"])
        require(cells not in groups, "duplicate source21 projection")
        physical, visited = restricted_transversals(quotient, table, cells)
        nodes += visited
        integer(entry["count"], 0, 2000000, "invalid restricted count")
        expected, components = component_prediction(quotient, cells, mask)
        require(len(physical) == entry["count"] == expected, "restricted source21 lift count mismatch")
        if "one_constructed_transversal" in entry:
            witness = entry["one_constructed_transversal"]
            require(type(witness) is list and len(witness) == 16, "invalid producer transversal witness")
            for value in witness:
                integer(value, 0, 15, "nonliteral witness column")
            require(tuple(witness) in physical, "producer witness is not in the literal restricted enumeration")
        groups[cells] = physical
        for first in physical:
            for dx, dy in ((0, 1), (1, 0), (1, 1)):
                second = [None] * len(first)
                for r, c in enumerate(first):
                    second[r ^ dx] = c ^ dy
                result = paired_line_check(quotient, table, first, second)
                require(result["covered"], "global fibre flip changed projection")
                ordered_pairs += 1
                paired_lines.update(result["paired_lines_checked"])
                if result["failures"]:
                    counterexamples.append({"first": list(first), "second": second, "failures": result["failures"]})
    total = sum(len(group) for group in groups.values())
    integer(record["total_transversals"], 0, 4000000, "invalid selected source21 total")
    require(record["total_transversals"] == total, "source21 selected total mismatch")
    return {"quotient_name": "source21_comm", "twist_mask": mask, "total_transversals": total,
            "all_base_transversals_enumerated": False, "projection_count": 2,
            "count_scope": "only the two supplied projections", "literal_dfs_nodes": nodes,
            "physical_profile": profile(table), "producer_projected_counts_checked": True,
            "ordered_same_projection_disjoint_pairs": ordered_pairs, "pairs_exhaustive": False,
            "pair_method": "three global fibre flips per literal transversal",
            "paired_lines_checked": dict(paired_lines), "counterexamples": counterexamples,
            "different_projection_guard": different_projection_guard(quotient, table, groups)}


def check_document(document, census_seconds=60):
    require(type(document) is dict, "input must be an object")
    integer(census_seconds, 1, 120, "census-seconds must be in 1..120")
    require(type(document.get("quotients")) is list, "missing quotient list")
    quotients = {}
    for record in document["quotients"]:
        require(type(record) is dict and type(record.get("name")) is str, "invalid quotient record")
        name = record["name"]
        require(name not in quotients, "duplicate quotient name")
        require(name in TABLES or name == "source21_comm", "unsupported quotient name")
        latin(record.get("table"))
        expected_table = SOURCE21_TABLE if name == "source21_comm" else TABLES[name]
        require(record["table"] == expected_table, "quotient differs from the labelled control")
        quotients[name] = record["table"]
    require(set(TABLES) <= set(quotients), "controls require C2, C4 and V4")
    require(type(document.get("controls")) is list, "missing controls")
    controls = {}
    for record in document["controls"]:
        require(type(record) is dict and type(record.get("quotient_name")) is str, "invalid control")
        name = record["quotient_name"]
        require(name in quotients, "unknown control quotient")
        q = len(quotients[name])
        mask = integer(record.get("twist_mask"), 0, (1 << (q * q)) - 1, "invalid control mask")
        key = (name, mask)
        require(key not in controls, "duplicate quotient/mask control")
        require("projected_transversal_counts" in record and "total_transversals" in record,
                "missing count fields")
        controls[key] = record
    for name in TABLES:
        masks = set(range(16)) if name == "C2" else Q4_MASKS
        require({mask for n, mask in controls if n == name} == masks,
                "controls must use exactly all 16 C2 masks or the six agreed order-four masks")
    if "source21_comm" in quotients:
        require({mask for n, mask in controls if n == "source21_comm"} == {SOURCE21_MASK},
                "source21 requires exactly its one frozen twist control")
    census = {}
    require(type(document.get("full_twist_census")) is list, "missing full_twist_census")
    for record in document["full_twist_census"]:
        require(type(record) is dict and type(record.get("quotient_name")) is str, "invalid census")
        name = record["quotient_name"]
        require(name in TABLES and name not in census, "unknown/duplicate census quotient")
        counts = record.get("counts")
        q = len(quotients[name])
        require(type(counts) is list and len(counts) == (1 << (q * q)),
                "full census must have one count per twist mask")
        for value in counts:
            integer(value, 0, 24 if q == 2 else 40320, "invalid census count")
        census[name] = counts
    require(set(census) == set(TABLES), "complete twist censuses are required for C2, C4 and V4")
    results = []
    for name in TABLES:
        masks = range(16) if name == "C2" else sorted(Q4_MASKS)
        for mask in masks:
            record = controls.get((name, mask))
            result = check_control(quotients[name], mask,
                                   None if record is None else record["projected_transversal_counts"],
                                   None if record is None else record["total_transversals"])
            if name in census:
                require(result["total_transversals"] == census[name][mask], "selected census count mismatch")
            result["quotient_name"] = name
            result["producer_projected_counts_checked"] = record is not None
            result["pairs_exhaustive"] = True
            results.append(result)
    if "source21_comm" in quotients:
        results.append(check_source21(quotients["source21_comm"], controls[("source21_comm", SOURCE21_MASK)]))
    deadline = monotonic() + census_seconds
    full_results = []
    for name in TABLES:
        if name not in census:
            continue
        started = monotonic()
        counts, eligible = literal_twist_census(quotients[name], deadline)
        require(counts == census[name], "literal complete twist census disagrees with producer: " + name)
        digest = hashlib.sha256(json.dumps(counts, separators=(",", ":")).encode("ascii")).hexdigest()
        full_results.append({"quotient_name": name, "masks_checked": len(counts),
                             "eligible_physical_column_permutations": eligible,
                             "total_transversals_across_twists": sum(counts),
                             "counts_sha256": digest, "seconds": monotonic() - started,
                             "method": "literal physical permutations and disjoint symbol-pair equations"})
    counterexamples = sum(len(r["counterexamples"]) for r in results)
    return {"verified": counterexamples == 0, "all_producer_counts_match": True,
            "scope": "C2 all 16 twists; C4/V4 six twists each; optional source21 two projections and global flips only",
            "not_claimed": "different-projection exclusion, general FFF16/FFF18 decision, or a new theorem proof",
            "controls_checked": len(results), "producer_controls_checked": len(controls),
            "ordered_pairs_checked": sum(r["ordered_same_projection_disjoint_pairs"] for r in results),
            "counterexample_count": counterexamples, "full_twist_census_checked": full_results,
            "results": results}


def bind_sources(document):
    require(type(document) is dict, "input must be an object")
    root = Path(__file__).resolve().parents[3]
    claimed = document.get("input_sha256")
    require(type(claimed) is dict and claimed == SOURCE_HASHES, "source input-hash declarations differ")
    for path, digest in SOURCE_HASHES.items():
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest,
                "source input hash mismatch: " + path)
    producer = Path(__file__).with_name("voltage_lifts.py")
    digest = hashlib.sha256(producer.read_bytes()).hexdigest()
    require(document.get("producer_sha256") == digest, "producer source hash mismatch")
    return {"producer_sha256": digest, "source_input_sha256": dict(SOURCE_HASHES)}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("nonfinite JSON number: " + value)


def self_test():
    checked = 0
    for mask in range(16):
        result = check_control(TABLES["C2"], mask)
        require(result["total_transversals"] == (8 if mask.bit_count() % 2 == 0 else 0),
                "C2 literal parity control failed")
        require(not result["counterexamples"], "C2 same-projection counterexample")
        checked += 1
    cells = [[r, c] for r in range(2) for c in range(2)]
    malformed = [cells[:-1], cells[:-1] + [cells[0]], [[False, 0]] + cells[1:],
                 [[0, 2]] + cells[1:], [[0, 0, 0]] + cells[1:]]
    for candidate in malformed:
        try:
            plex_cells(TABLES["C2"], candidate)
        except ValueError:
            checked += 1
        else:
            raise ValueError("malformed-cell negative guard failed")
    for name in ("C4", "V4"):
        result = check_control(TABLES[name], 0)
        require(not result["counterexamples"] and result["different_projection_guard"] is not None,
                "order-four pair/scope control failed")
        checked += 1
    counts, eligible = literal_twist_census(TABLES["C2"])
    require(counts == [8 if mask.bit_count() % 2 == 0 else 0 for mask in range(16)]
            and eligible == 16, "literal complete C2 census failed")
    checked += 1
    try:
        json.loads('{"x":1,"x":2}', object_pairs_hook=unique_object)
    except ValueError:
        checked += 1
    else:
        raise ValueError("duplicate JSON guard failed")
    try:
        validate_transversal([[0, 1], [1, 0]], [False, 1])
    except ValueError:
        checked += 1
    else:
        raise ValueError("nonliteral transversal guard failed")
    try:
        check_control(TABLES["C2"], 1, [], 0)
    except ValueError:
        checked += 1
    else:
        raise ValueError("missing zero-count plex guard failed")
    result = check_control(TABLES["C2"], 1, [{"cells": cells, "count": 0}], 0)
    require(result["total_transversals"] == 0, "complete zero-count plex control failed")
    checked += 1
    return {"self_test": True, "controls": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--census-seconds", type=int, default=60,
                        help="shared literal full-census time cap (default 60, at most 120 seconds)")
    args = parser.parse_args()
    try:
        if args.self_test:
            require(args.input is None and args.output is None, "self-test does not use files")
            print(json.dumps(self_test(), sort_keys=True, separators=(",", ":")))
            return 0
        require(args.input is not None and args.output is not None, "--input and --output are required")
        integer(args.census_seconds, 1, 120, "census-seconds must be in 1..120")
        output = args.output.resolve()
        audit = (Path(__file__).resolve().parents[3] / ".audit").resolve()
        require(output.is_relative_to(audit) and not output.exists(), "output must be fresh under workspace .audit")
        require(output.parent.is_dir(), "output parent directory must already exist")
        raw = args.input.read_bytes()
        document = json.loads(raw, object_pairs_hook=unique_object,
                              parse_constant=reject_constant)
        bindings = bind_sources(document)
        result = check_document(document, args.census_seconds)
        result.update(bindings)
        result["input_sha256"] = hashlib.sha256(raw).hexdigest()
        result["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        with output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps({key: result[key] for key in ("verified", "controls_checked", "producer_controls_checked",
                                                       "ordered_pairs_checked", "counterexample_count")},
                         sort_keys=True, separators=(",", ":")))
        return 0 if result["verified"] else 1
    except (ValueError, OSError, TypeError, KeyError) as error:
        print("independent checker: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
