#!/usr/bin/env python3
"""Independent stdlib FFF18 palette audit using physical bipartite matchings."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
from hashlib import sha256
from itertools import combinations, permutations
import json
from math import isfinite
from pathlib import Path
import sys


N = 18
IDENTITY = tuple(range(N))
ROOT = (1, 2, 3, 0, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17, 16)
SEEDS = (
    (2, 0, 4, 5, 1, 3, 8, 9, 6, 7, 12, 13, 10, 11, 16, 17, 14, 15),
    (2, 4, 1, 5, 0, 3, 8, 9, 6, 7, 12, 13, 10, 11, 16, 17, 14, 15),
)
TARGET_TYPE = (2,) * 7 + (4,)
EXPECTED_DOMAIN_SHA256 = "34abf2b0a33c5e45825a867438ec6ba811da50c0e1c29321137ae8a05cd681bb"
SHARP_SIX = (
    (0, 1, 2, 3, 4, 5), (1, 2, 3, 0, 5, 4), (2, 0, 4, 5, 1, 3),
    (3, 4, 5, 1, 0, 2), (4, 5, 0, 2, 3, 1), (5, 3, 1, 4, 2, 0),
)
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / ".audit/local/fff18_near_palette_four_line/independent_core_check.json"


class VerificationError(ValueError):
    """A mathematical or input-validation gate failed."""


class CertificateError(VerificationError):
    """A certificate is malformed or disagrees with fresh checks."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def permutation(values, n, label="permutation"):
    if not isinstance(values, (list, tuple)):
        raise VerificationError(f"{label}: expected a permutation array")
    if len(values) != n or any(type(x) is not int for x in values):
        raise VerificationError(f"{label}: expected {n} integer images")
    if set(values) != set(range(n)):
        raise VerificationError(f"{label}: images are not exactly 0..{n - 1}")
    return tuple(values)


def inverse(p):
    result = [0] * len(p)
    for x, y in enumerate(p):
        result[y] = x
    return tuple(result)


def matching_cycles(first, second):
    """Alternate physical matching colors; do not form a relative permutation.

    A coincident edge retains both colors as parallel edges. Its component
    has two physical vertices and contributes relative length one.
    """
    n = len(first)
    a = permutation(first, n, "first matching")
    b = permutation(second, n, "second matching")
    adjacency = [[n + a[x], n + b[x]] for x in range(n)]
    adjacency.extend([[0, 0] for _ in range(n)])
    for color, p in enumerate((a, b)):
        for x, y in enumerate(p):
            adjacency[n + y][color] = x
    visited, cycles = set(), []
    for start in range(2 * n):
        if start in visited:
            continue
        current, color, vertices = start, 0, []
        while current not in visited:
            visited.add(current)
            vertices.append(current)
            current = adjacency[current][color]
            color ^= 1
        require(current == start and color == 0, "alternating walk failed to close")
        require(len(vertices) % 2 == 0, "physical matching cycle has odd length")
        require(sum(v < n for v in vertices) == len(vertices) // 2,
                "physical cycle is not bipartite-balanced")
        cycles.append(tuple(sorted(vertices)))
    return tuple(sorted(cycles, key=lambda c: (len(c), c)))


def physical_pair_type(first, second):
    return tuple(len(cycle) // 2 for cycle in matching_cycles(first, second))


def physical_components(*lines):
    """Connected components of a three-colored physical matching graph."""
    require(len(lines) == 3, "exceptional-core check requires three lines")
    n = len(lines[0])
    checked = [permutation(line, n, "triangle line") for line in lines]
    adjacency = [[] for _ in range(2 * n)]
    for line in checked:
        for x, y in enumerate(line):
            adjacency[x].append(n + y)
            adjacency[n + y].append(x)
    remaining, components = set(range(2 * n)), []
    while remaining:
        start = min(remaining)
        component, pending = {start}, [start]
        remaining.remove(start)
        while pending:
            for vertex in adjacency[pending.pop()]:
                if vertex in remaining:
                    remaining.remove(vertex)
                    component.add(vertex)
                    pending.append(vertex)
        require(sum(v < n for v in component) * 2 == len(component),
                "triangle component is not bipartite-balanced")
        components.append(tuple(sorted(component)))
    return tuple(sorted(components, key=lambda c: (len(c), c)))


def exceptional_core(*lines):
    n = len(lines[0])
    components = physical_components(*lines)
    require(tuple(len(c) // 2 for c in components) == (4, 4, 4, 6),
            "triangle domain component sizes are not 4+4+4+6")
    core_vertices = set(components[-1])
    for a, b in combinations(lines, 2):
        cycles = matching_cycles(a, b)
        require(tuple(len(c) // 2 for c in cycles) == TARGET_TYPE,
                "triangle has a pair outside 4+2^7")
        exceptional = [c for c in cycles if len(c) == 8]
        require(len(exceptional) == 1 and set(exceptional[0]) <= core_vertices,
                "exceptional physical 8-cycle is outside the six-point core")
    return tuple(v for v in components[-1] if v < n)


def build_generators():
    generators = []
    rotation = list(IDENTITY)
    rotation[:4] = [1, 2, 3, 0]
    generators.append(tuple(rotation))
    for pair in range(7):
        p = list(IDENTITY)
        x = 4 + 2 * pair
        p[x], p[x + 1] = p[x + 1], p[x]
        generators.append(tuple(p))
    for pair in range(6):
        p = list(IDENTITY)
        x = 4 + 2 * pair
        p[x:x + 4] = [x + 2, x + 3, x, x + 1]
        generators.append(tuple(p))
    for i, g in enumerate(generators):
        permutation(g, N, f"generator {i}")
        require(all(g[ROOT[x]] == ROOT[g[x]] for x in range(N)),
                f"generator {i} does not commute with A")
    return generators


def orbit_closure(seed, generators):
    permutation(seed, N, "orbit seed")
    operations = [(g, inverse(g)) for g in generators]
    seen, queue = {seed}, deque([seed])
    while queue:
        p = queue.popleft()
        for g, gi in operations:
            q = tuple(g[p[gi[x]]] for x in range(N))
            if q not in seen:
                seen.add(q)
                queue.append(q)
                require(len(seen) <= 6720, "seed orbit exceeds expected size 6720")
    require(len(seen) == 6720, f"seed orbit size is {len(seen)}, expected 6720")
    return seen


def permutation_stream_sha256(points):
    stream = "".join(",".join(map(str, p)) + "\n" for p in sorted(points)).encode("ascii")
    return sha256(stream).hexdigest()


def json_sha256(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("ascii")).hexdigest()


def type_key(typ):
    return "+".join(map(str, reversed(typ)))


def scan_sharp_controls():
    for row in SHARP_SIX:
        permutation(row, 6, "FTF6 row")
    require(all(len({row[c] for row in SHARP_SIX}) == 6 for c in range(6)),
            "six-line control is not Latin")
    column_lines = tuple(zip(*SHARP_SIX))
    row_inverses = [inverse(row) for row in SHARP_SIX]
    symbol_lines = tuple(tuple(row[s] for row in row_inverses) for s in range(6))
    scans, pattern = {}, ""
    for name, lines in (("row", SHARP_SIX), ("column", column_lines),
                        ("symbol", symbol_lines)):
        types = Counter(physical_pair_type(a, b) for a, b in combinations(lines, 2))
        bad = sum(count for typ, count in types.items() if any(k % 2 for k in typ))
        scans[name] = {"pairs_checked": sum(types.values()), "odd_pairs": bad,
                       "pair_type_histogram": {type_key(t): c for t, c in sorted(types.items())}}
        pattern += "T" if bad else "F"
    require(pattern == "FTF", f"six-line control pattern is {pattern}, not FTF")
    require(scans["row"]["pair_type_histogram"] == {"4+2": 15},
            "six-line row control is not homogeneous 4+2")
    rectangle = tuple(row + tuple(base + (x ^ r)
                                 for base in (6, 10, 14) for x in range(4))
                      for r, row in enumerate(SHARP_SIX[:4]))
    for row in rectangle:
        permutation(row, N, "rectangle row")
    require(all(len({row[c] for row in rectangle}) == 4 for c in range(N)),
            "four-line order-18 control has a column collision")
    pairs = []
    for i, j in combinations(range(4), 2):
        typ = physical_pair_type(rectangle[i], rectangle[j])
        require(typ == TARGET_TYPE, f"rectangle pair {i},{j} has type {typ}")
        pairs.append({"rows": [i, j], "pair_type": list(typ)})
    require(rectangle[0] == IDENTITY and rectangle[1] == ROOT and rectangle[2] == SEEDS[0],
            "sharp control does not match prescribed roots")
    return {
        "sharp_degree6_table": [list(row) for row in SHARP_SIX],
        "sharp_degree6_pattern": pattern, "sharp_degree6_views": scans,
        "sharp_four_line_control": {"rows": [list(row) for row in rectangle], "size": 4,
                                   "latin_rectangle": True, "all_six_relative_types": "4+2^7",
                                   "full_latin_square": False},
        "rectangle_sha256": permutation_stream_sha256(rectangle),
        "rectangle_row_pairs": pairs, "rectangle_row_pairs_checked": len(pairs),
    }


def partial_odd_matching_cycles(first, second, right_size):
    """Find closed odd cycles in two injective, possibly partial matchings.

    Endpoints of open paths have degree one. They are rejected regardless of
    the number of left vertices; both colors must be present at every vertex.
    """
    require(len(first) == len(second), "partial matching lengths differ")
    left_size = len(first)
    for line in (first, second):
        require(all(type(x) is int and 0 <= x < right_size for x in line),
                "partial matching image out of range")
        require(len(set(line)) == left_size, "partial matching is not injective")
    adjacency = [[] for _ in range(left_size + right_size)]
    for color, line in enumerate((first, second)):
        for row, value in enumerate(line):
            right = left_size + value
            adjacency[row].append((color, right))
            adjacency[right].append((color, row))
    remaining = {v for v, edges in enumerate(adjacency) if edges}
    cycles = []
    while remaining:
        start = min(remaining)
        pending, component = [start], {start}
        remaining.remove(start)
        while pending:
            for _, v in adjacency[pending.pop()]:
                if v in remaining:
                    remaining.remove(v)
                    component.add(v)
                    pending.append(v)
        if any(len(adjacency[v]) != 2 or {c for c, _ in adjacency[v]} != {0, 1}
               for v in component):
            continue
        row_labels = sorted(v for v in component if v < left_size)
        right_labels = sorted(v - left_size for v in component if v >= left_size)
        require(len(row_labels) == len(right_labels), "closed partial cycle is unbalanced")
        if len(row_labels) < 3 or len(row_labels) % 2 == 0:
            continue
        current, color, walked = start, 0, set()
        while current not in walked:
            walked.add(current)
            edges = [v for c, v in adjacency[current] if c == color]
            require(len(edges) == 1, "partial alternating walk has ambiguous color")
            current, color = edges[0], color ^ 1
        require(current == start and color == 0 and walked == component,
                "partial matching component is not a closed alternating cycle")
        cycles.append({"domain_rows": row_labels, "range_labels": right_labels,
                       "relative_cycle_length": len(row_labels),
                       "physical_vertex_count": len(component)})
    return cycles


def partial_crossview_witnesses(rows):
    """Use physical row/symbol and row/column matching graphs, not relative arcs."""
    n = len(rows[0])
    require(all(len(row) == n for row in rows), "partial rectangle row lengths differ")
    checked = [permutation(row, n, "partial rectangle row") for row in rows]
    require(all(len({row[c] for row in checked}) == len(rows) for c in range(n)),
            "partial rectangle has a column collision")
    witnesses = []
    for c, d in combinations(range(n), 2):
        first = tuple(row[c] for row in checked)
        second = tuple(row[d] for row in checked)
        for cycle in partial_odd_matching_cycles(first, second, n):
            support = sorted((r, col) for r in cycle["domain_rows"] for col in (c, d))
            witnesses.append({"view": "column", "line_pair": [c, d], **cycle,
                              "support_cells": [list(cell) for cell in support]})
    row_inverses = [inverse(row) for row in checked]
    for s, t in combinations(range(n), 2):
        first = tuple(row[s] for row in row_inverses)
        second = tuple(row[t] for row in row_inverses)
        for cycle in partial_odd_matching_cycles(first, second, n):
            support = sorted((r, col) for r in cycle["domain_rows"]
                             for col in (first[r], second[r]))
            witnesses.append({"view": "symbol", "line_pair": [s, t], **cycle,
                              "support_cells": [list(cell) for cell in support]})
    return witnesses


def complete_local_rectangle(rows, candidates):
    """Find one explicit six-row Latin completion by finite row backtracking."""
    n = len(rows[0])
    if len(rows) == n:
        return rows
    for row in candidates:
        if all(all(row[c] != old[c] for old in rows) for c in range(n)):
            result = complete_local_rectangle(rows + (row,), candidates)
            if result is not None:
                return result
    return None


def local_triangle_witness_audit():
    local_id, local_root = tuple(range(6)), ROOT[:6]
    candidates = tuple(permutations(range(6)))
    palette = [b for b in candidates if physical_pair_type(local_id, b) == (2, 4)]
    retained = [b for b in palette if physical_pair_type(local_root, b) == (2, 4)]
    require(len(candidates) == 720 and len(palette) == 90 and len(retained) == 16,
            "complete local-six palette enumeration counts differ")
    local_generators = ((1, 2, 3, 0, 4, 5), (0, 1, 2, 3, 5, 4))
    operations = [(g, inverse(g)) for g in local_generators]
    seed_orbits = []
    for seed in (s[:6] for s in SEEDS):
        reached, queue = {seed}, deque([seed])
        while queue:
            b = queue.popleft()
            for g, gi in operations:
                q = tuple(g[b[gi[x]]] for x in range(6))
                if q not in reached:
                    reached.add(q)
                    queue.append(q)
        seed_orbits.append(reached)
    require(seed_orbits[0].isdisjoint(seed_orbits[1])
            and seed_orbits[0] | seed_orbits[1] == set(retained),
            "local seed closure does not agree with complete S6 enumeration")
    records, histogram = [], Counter()
    for b in retained:
        partial = (local_id, local_root, b)
        require(tuple(len(c) // 2 for c in physical_components(*partial)) == (6,),
                "local triangle is not one connected six-point core")
        witnesses = partial_crossview_witnesses(partial)
        counts = tuple(sum(w["view"] == view for w in witnesses) for view in ("column", "symbol"))
        histogram[counts] += 1
        require(len(witnesses) == 1 and witnesses[0]["relative_cycle_length"] == 3,
                "local triangle does not have exactly one closed odd three-cycle")
        completion = complete_local_rectangle(partial, candidates)
        require(completion is not None, "local Latin rectangle has no explicit completion")
        completed_witnesses = partial_crossview_witnesses(completion)
        require(all(w in completed_witnesses for w in witnesses),
                "closed partial witness did not persist in explicit Latin completion")
        embedded = tuple(row + tuple(base + (x ^ r)
                                     for base in (6, 10, 14) for x in range(4))
                         for r, row in enumerate(partial))
        embedded_witnesses = partial_crossview_witnesses(embedded)
        require(all(w in embedded_witnesses for w in witnesses),
                "local witness did not persist in an order-18 triangle embedding")
        records.append({
            "third_line": list(b), "rows": [list(row) for row in partial],
            "column_odd_three_cycles": counts[0], "symbol_odd_three_cycles": counts[1],
            "witnesses": witnesses, "explicit_latin_completion": [list(row) for row in completion],
            "completion_preserves_witness": True, "degree18_embedding_preserves_witness": True,
        })
    # A true alternating 6-cycle and two broken versions distinguish cycles from paths.
    closed = partial_odd_matching_cycles((0, 1, 2), (1, 2, 0), 4)
    require(len(closed) == 1 and closed[0]["relative_cycle_length"] == 3,
            "positive closed-three-cycle detector control failed")
    require(not partial_odd_matching_cycles((0, 1), (1, 2), 4),
            "truncated two-row path was incorrectly reported as an odd witness")
    require(not partial_odd_matching_cycles((0, 1, 2), (1, 2, 3), 4),
            "open three-row path was incorrectly reported as an odd witness")
    return {
        "permutations_examined": len(candidates), "type_4_plus_2_count": len(palette),
        "retained_triangle_count": len(retained),
        "local_seed_orbit_sizes": sorted(map(len, seed_orbits)),
        "templates_sha256": permutation_stream_sha256(retained),
        "column_symbol_witness_count_histogram": {
            f"{col},{sym}": count for (col, sym), count in sorted(histogram.items())},
        "records": records, "explicit_latin_completions_checked": len(records),
        "degree18_triangle_embeddings_checked": len(records),
        "detector_controls": {"closed_three_cycle": "pass", "truncated_path": "rejected",
                              "open_three_row_path": "rejected"},
        "scope": "all local six-point templates; extension persistence follows from closed matching components",
        "unrestricted_fff18_decided": False,
    }


def compute_audit():
    generators = build_generators()
    orbits = [orbit_closure(seed, generators) for seed in SEEDS]
    require(orbits[0].isdisjoint(orbits[1]), "the two seed orbits overlap")
    domain = sorted(orbits[0] | orbits[1])
    require(len(domain) == 13440, "domain is not exactly 13440 distinct points")
    domain_hash = permutation_stream_sha256(domain)
    require(domain_hash == EXPECTED_DOMAIN_SHA256, "fresh domain SHA-256 mismatch")
    cores, core_histogram = {}, Counter()
    for b in domain:
        core = exceptional_core(IDENTITY, ROOT, b)
        require(set(range(4)) <= set(core), "root four-cycle is not in the core")
        require(sum(b[x] >= 4 for x in range(4)) == 2,
                "domain point does not have exactly two outside root incidences")
        cores[b] = core
        core_histogram[core] += 1
    index = {p: i for i, p in enumerate(domain)}
    records = []
    for seed, orbit in sorted(zip(SEEDS, orbits), key=lambda item: min(item[1])):
        representative = min(orbit)
        common_core = cores[representative]
        neighbors, type_counts = [], Counter()
        diamonds = {"same_core": Counter(), "different_core": Counter()}
        for c in domain:
            typ = physical_pair_type(representative, c)
            type_counts[typ] += 1
            if all(length % 2 == 0 for length in typ):
                category = "same_core" if cores[c] == common_core else "different_core"
                diamonds[category][type_key(typ)] += 1
            if typ == TARGET_TYPE:
                neighbors.append(c)
        require(len(neighbors) == 39,
                f"representative {representative} has {len(neighbors)} neighbors, not 39")
        for c in neighbors:
            require(cores[c] == common_core, "root-A exceptional cores differ on an edge")
            require(exceptional_core(IDENTITY, representative, c) == common_core,
                    "id,B,C exceptional core differs from root-A core")
            require(exceptional_core(ROOT, representative, c) == common_core,
                    "A,B,C exceptional core differs from root-A core")
        induced_edges = [[index[c], index[d]] for c, d in combinations(neighbors, 2)
                         if physical_pair_type(c, d) == TARGET_TYPE]
        require(not induced_edges, "a representative neighborhood contains an edge")
        spectra = {category: dict(sorted(counts.items())) for category, counts in diamonds.items()}
        records.append({
            "seed": list(seed), "representative": list(representative),
            "orbit_size": len(orbit), "orbit_sha256": permutation_stream_sha256(orbit),
            "domain_points_checked": len(domain), "compatible_fourth_lines_count": len(neighbors),
            "compatible_fourth_lines": [list(c) for c in neighbors],
            "compatible_fourth_lines_sha256": permutation_stream_sha256(neighbors),
            "neighbor_indices": [index[c] for c in neighbors],
            "exceptional_core": list(common_core), "all_four_triangle_cores_equal": True,
            "cross_core_fourth_lines": sum(cores[c] != common_core for c in neighbors),
            "five_near_edges_sixth_even_spectra": spectra,
            "five_near_edges_sixth_even_count": sum(sum(counts.values()) for counts in diamonds.values()),
            "pair_type_histogram": {type_key(t): count for t, count in sorted(type_counts.items())},
            "neighbor_pairs_checked": len(neighbors) * (len(neighbors) - 1) // 2,
            "neighbor_induced_edges": induced_edges, "neighbor_induced_edge_count": len(induced_edges),
        })
    report = {
        "schema": "fff18-near-palette-independent-v1", "status": "pass", "order": N,
        "root": list(ROOT), "target_cycle_type": list(TARGET_TYPE),
        "centralizing_generators": [list(g) for g in generators],
        "generators_sha256": json_sha256([list(g) for g in generators]),
        "generator_commutation_checked": len(generators),
        "orbit_count": len(orbits), "orbit_sizes": sorted(map(len, orbits)),
        "triangle_domain_count": len(domain), "triangle_domain_sha256": domain_hash,
        "domain_hash_encoding": "lexicographically sorted comma-separated decimal images; LF after every permutation",
        "all_domain_triangles_physically_checked": len(domain),
        "exceptional_core_histogram": {",".join(map(str, core)): count
                                     for core, count in sorted(core_histogram.items())},
        "orbits": records, "common_core_four_line_property": True,
        "normalized_generated_family_maximum": 4, "unrestricted_fff18_decided": False,
        "scope": "generated homogeneous 4+2^7 domain; no mixed-palette FFF18 exclusion",
        "independence": "conjugation closure; alternating physical bipartite matchings; no parent code imports",
    }
    report.update(scan_sharp_controls())
    report["local_triangle_witnesses"] = local_triangle_witness_audit()
    return report


def compare_certificate(certificate, fresh):
    """Compare supported semantic fields; proof prose is explicitly unchecked."""
    if not isinstance(certificate, dict):
        raise CertificateError("certificate must be a JSON object")
    compared, unsupported = [], []

    def equal(value, expected, label):
        if json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) != (
                json.dumps(expected, sort_keys=True, separators=(",", ":"), allow_nan=False)):
            raise CertificateError(f"certificate mismatch: {label}")
        compared.append(label)

    global_fields = (
        "order", "root", "target_cycle_type", "orbit_count", "orbit_sizes",
        "triangle_domain_count", "triangle_domain_sha256", "generators_sha256",
        "generator_commutation_checked", "all_domain_triangles_physically_checked",
        "exceptional_core_histogram", "common_core_four_line_property",
        "unrestricted_fff18_decided", "sharp_four_line_control",
    )
    for field in global_fields:
        if field in certificate:
            equal(certificate[field], fresh[field], field)
    if "centralizing_generators" in certificate:
        supplied = certificate["centralizing_generators"]
        if not isinstance(supplied, list) or len(supplied) != len(fresh["centralizing_generators"]):
            raise CertificateError("certificate must contain all 14 generators")
        try:
            actual = [permutation(p, N, "certificate generator") for p in supplied]
        except VerificationError as error:
            raise CertificateError(str(error)) from error
        equal(sorted(actual), sorted(tuple(g) for g in fresh["centralizing_generators"]),
              "centralizing_generators")
    if "orbits" in certificate:
        supplied = certificate["orbits"]
        if not isinstance(supplied, list) or len(supplied) != fresh["orbit_count"]:
            raise CertificateError("certificate must contain both orbit records")
        expected = {tuple(r["representative"]): r for r in fresh["orbits"]}
        seen = set()
        for entry in supplied:
            if not isinstance(entry, dict):
                raise CertificateError("certificate orbit record must be an object")
            try:
                rep = permutation(entry.get("representative"), N, "certificate representative")
            except VerificationError as error:
                raise CertificateError(str(error)) from error
            if rep not in expected or rep in seen:
                raise CertificateError("certificate representative is unknown or duplicated")
            seen.add(rep)
            record, label = expected[rep], f"orbits[{len(seen) - 1}]"
            compared.append(label + ".representative")
            for key, value in entry.items():
                if key == "representative":
                    continue
                if key not in record:
                    unsupported.append(label + "." + key)
                    continue
                if key == "compatible_fourth_lines":
                    if not isinstance(value, list):
                        raise CertificateError("certificate neighbors must be an array")
                    try:
                        points = [permutation(p, N, "certificate neighbor") for p in value]
                    except VerificationError as error:
                        raise CertificateError(str(error)) from error
                    if len(set(points)) != len(points):
                        raise CertificateError("certificate neighbor list has duplicates")
                    equal(sorted(points), sorted(tuple(p) for p in record[key]), label + "." + key)
                else:
                    equal(value, record[key], label + "." + key)
    supported = set(global_fields) | {"centralizing_generators", "orbits"}
    unsupported.extend(key for key in certificate if key not in supported)
    substantive = {"triangle_domain_count", "triangle_domain_sha256", "orbit_sizes",
                   "centralizing_generators", "generators_sha256", "orbits"}
    if not substantive.intersection(certificate):
        raise CertificateError("certificate contains no supported domain/orbit/generator evidence")
    return {"status": "pass", "fields_compared": compared,
            "unsupported_fields_not_validated": sorted(unsupported),
            "diamond_spectra_compared": any(".five_near_edges_sixth_even_spectra" in f for f in compared)}


def compare_triangle_certificate(certificate, fresh):
    """Compare the parent's local-six witness data, not its general proof."""
    if not isinstance(certificate, dict):
        raise CertificateError("triangle certificate must be a JSON object")
    local = fresh["local_triangle_witnesses"]
    expected_histogram = {
        f"col={col},sym={sym}": count
        for key, count in local["column_symbol_witness_count_histogram"].items()
        for col, sym in [key.split(",")]
    }
    for field, expected in (
        ("local_triangle_count", local["retained_triangle_count"]),
        ("local_witness_histogram", expected_histogram),
    ):
        if field not in certificate or json.dumps(certificate[field], sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise CertificateError(f"triangle certificate mismatch: {field}")
    supplied = certificate.get("local_triangle_witnesses")
    if not isinstance(supplied, list) or len(supplied) != len(local["records"]):
        raise CertificateError("triangle certificate must contain all 16 local witness records")

    def signature(witness):
        if not isinstance(witness, dict) or witness.get("view") not in ("col", "sym"):
            raise CertificateError("triangle witness has an unknown view")
        view = witness["view"]
        coordinate = "symbols" if view == "col" else "columns"
        if witness.get("cycle_coordinate") != coordinate:
            raise CertificateError("triangle witness cycle coordinate disagrees with its view")
        pair, labels, cells = (witness.get(key) for key in ("line_pair", "cycle_labels", "support_cells"))
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(x) is not int or not 0 <= x < 6 for x in pair)
                or len(set(pair)) != 2):
            raise CertificateError("triangle witness line pair is invalid")
        if (not isinstance(labels, list) or len(labels) != 3
                or any(type(x) is not int or not 0 <= x < 6 for x in labels)
                or len(set(labels)) != 3):
            raise CertificateError("triangle witness labels are not three distinct core labels")
        if (not isinstance(cells, list) or len(cells) != 6
                or any(not isinstance(cell, list) or len(cell) != 2
                       or any(type(x) is not int for x in cell)
                       or not 0 <= cell[0] < 3 or not 0 <= cell[1] < 6 for cell in cells)):
            raise CertificateError("triangle witness support cells are invalid")
        if len({tuple(cell) for cell in cells}) != 6:
            raise CertificateError("triangle witness support repeats a cell")
        return view, tuple(sorted(pair)), tuple(sorted(labels)), tuple(sorted(tuple(c) for c in cells))

    expected = {tuple(r["third_line"]): r for r in local["records"]}
    seen = set()
    for entry in supplied:
        if not isinstance(entry, dict):
            raise CertificateError("triangle witness record is not an object")
        try:
            third = permutation(entry.get("third_line"), 6, "triangle certificate third line")
        except VerificationError as error:
            raise CertificateError(str(error)) from error
        if third in seen or third not in expected:
            raise CertificateError("triangle certificate has a duplicate or unknown template")
        seen.add(third)
        record = expected[third]
        if json.dumps(entry.get("rows"), separators=(",", ":")) != json.dumps(record["rows"], separators=(",", ":")):
            raise CertificateError("triangle certificate partial rows mismatch")
        witnesses = entry.get("persistent_witnesses")
        if not isinstance(witnesses, list):
            raise CertificateError("triangle certificate has no witness array")
        actual = [signature(w) for w in witnesses]
        wanted = [
            ("col" if w["view"] == "column" else "sym", tuple(w["line_pair"]),
             tuple(w["range_labels"]), tuple(tuple(c) for c in w["support_cells"]))
            for w in record["witnesses"]
        ]
        if sorted(actual) != sorted(wanted):
            raise CertificateError("triangle certificate physical witness support mismatch")
    supported = {"local_triangle_count", "local_witness_histogram", "local_triangle_witnesses"}
    return {
        "status": "pass", "local_records_compared": len(seen),
        "fields_compared": sorted(supported),
        "unsupported_fields_not_validated": sorted(set(certificate) - supported),
        "scope": "local-six counts, rows and exact physical witness supports only; not the parent's global proof or census",
    }


def triangle_comparison_controls(fresh):
    local = fresh["local_triangle_witnesses"]
    positive = {
        "local_triangle_count": local["retained_triangle_count"],
        "local_witness_histogram": {
            f"col={col},sym={sym}": count
            for key, count in local["column_symbol_witness_count_histogram"].items()
            for col, sym in [key.split(",")]
        },
        "local_triangle_witnesses": [
            {"third_line": r["third_line"], "rows": r["rows"], "persistent_witnesses": [
                {"view": "col" if w["view"] == "column" else "sym",
                 "cycle_coordinate": "symbols" if w["view"] == "column" else "columns",
                 "line_pair": w["line_pair"], "cycle_labels": w["range_labels"],
                 "support_cells": w["support_cells"]}
                for w in r["witnesses"]]} for r in local["records"]
        ],
    }
    compare_triangle_certificate(positive, fresh)
    reordered = deepcopy(positive)
    reordered["local_triangle_witnesses"].reverse()
    for record in reordered["local_triangle_witnesses"]:
        for witness in record["persistent_witnesses"]:
            witness["support_cells"].reverse()
            witness["cycle_labels"].reverse()
    compare_triangle_certificate(reordered, fresh)
    rejected = []
    for name in ("wrong_histogram", "missing_record", "duplicate_record", "broken_support",
                 "wrong_view", "nonclosed_labels", "duplicate_support", "boolean_label"):
        bad = deepcopy(positive)
        record = bad["local_triangle_witnesses"][0]
        witness = record["persistent_witnesses"][0]
        if name == "wrong_histogram":
            key = next(iter(bad["local_witness_histogram"]))
            bad["local_witness_histogram"][key] += 1
        elif name == "missing_record":
            bad["local_triangle_witnesses"].pop()
        elif name == "duplicate_record":
            bad["local_triangle_witnesses"][1] = deepcopy(record)
        elif name == "broken_support":
            witness["support_cells"].pop()
        elif name == "wrong_view":
            witness["view"] = "sym" if witness["view"] == "col" else "col"
        elif name == "nonclosed_labels":
            witness["cycle_labels"][-1] = 5
        elif name == "duplicate_support":
            witness["support_cells"][1] = witness["support_cells"][0]
        else:
            witness["cycle_labels"][0] = True
        try:
            compare_triangle_certificate(bad, fresh)
        except CertificateError:
            rejected.append(name)
        else:
            raise VerificationError(f"malformed triangle witness certificate accepted: {name}")
    return {"positive_controls": 2, "rejected_controls": rejected,
            "rejected_control_count": len(rejected)}


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_json_constant(value):
    raise CertificateError(f"nonfinite JSON constant: {value}")


def finite_json_float(value):
    parsed = float(value)
    if not isfinite(parsed):
        raise CertificateError(f"nonfinite JSON number: {value}")
    return parsed


def load_certificate(raw):
    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys,
                          parse_constant=reject_json_constant, parse_float=finite_json_float)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CertificateError(f"invalid JSON certificate: {error}") from error


def run_malformed_controls(fresh):
    positive = {key: deepcopy(fresh[key]) for key in (
        "order", "root", "orbit_sizes", "triangle_domain_count",
        "triangle_domain_sha256", "centralizing_generators", "orbits")}
    compare_certificate(positive, fresh)
    hash_only = {"triangle_domain_sha256": fresh["triangle_domain_sha256"], "orbits": [
        {key: r[key] for key in ("representative", "orbit_size", "compatible_fourth_lines_count",
                                "compatible_fourth_lines_sha256", "exceptional_core",
                                "five_near_edges_sixth_even_spectra")} for r in fresh["orbits"]]}
    compare_certificate(hash_only, fresh)
    cases = [("non_object", []), ("vacuous", {}),
             ("wrong_domain_count", {"triangle_domain_count": 13439}),
             ("wrong_domain_hash", {"triangle_domain_sha256": "0" * 64}),
             ("boolean_count", {"triangle_domain_count": True})]
    for name in (
        "wrong_generator", "missing_orbit", "duplicate_representative",
        "wrong_neighbor_count", "wrong_neighbor_hash", "missing_neighbor",
        "duplicate_neighbor", "nonpermutation_neighbor", "boolean_image", "wrong_core",
        "wrong_diamond_count", "missing_diamond_type", "wrong_diamond_core_category",
    ):
        changed = deepcopy(positive)
        first = changed["orbits"][0]
        if name == "wrong_generator":
            changed["centralizing_generators"][0] = list(IDENTITY)
        elif name == "missing_orbit":
            changed["orbits"].pop()
        elif name == "duplicate_representative":
            changed["orbits"][1] = deepcopy(first)
        elif name == "wrong_neighbor_count":
            first["compatible_fourth_lines_count"] -= 1
        elif name == "wrong_neighbor_hash":
            first["compatible_fourth_lines_sha256"] = "0" * 64
        elif name == "missing_neighbor":
            first["compatible_fourth_lines"].pop()
        elif name == "duplicate_neighbor":
            first["compatible_fourth_lines"].append(first["compatible_fourth_lines"][0])
        elif name == "nonpermutation_neighbor":
            first["compatible_fourth_lines"][0][0] = first["compatible_fourth_lines"][0][1]
        elif name == "boolean_image":
            first["compatible_fourth_lines"][0][0] = True
        elif name == "wrong_core":
            first["exceptional_core"] = [0, 1, 2, 3, 6, 7]
        else:
            spectra = first["five_near_edges_sixth_even_spectra"]
            key = next(iter(spectra["same_core"]))
            if name == "wrong_diamond_count":
                spectra["same_core"][key] += 1
            elif name == "missing_diamond_type":
                del spectra["same_core"][key]
            else:
                spectra["different_core"][key] = spectra["same_core"].pop(key)
        cases.append((name, changed))
    rejected = []
    for name, changed in cases:
        try:
            compare_certificate(changed, fresh)
        except CertificateError:
            rejected.append(name)
        else:
            raise VerificationError(f"malformed certificate control accepted: {name}")
    for name, raw in (
        ("duplicate_json_key", b'{"triangle_domain_count":13439,"triangle_domain_count":13440}'),
        ("nonfinite_json", b'{"triangle_domain_count":NaN}'),
        ("overflowing_json_number", b'{"triangle_domain_count":1e999}'),
        ("broken_json", b'{"triangle_domain_count":'),
    ):
        try:
            load_certificate(raw)
        except CertificateError:
            rejected.append(name)
        else:
            raise VerificationError(f"malformed JSON control accepted: {name}")
    require(physical_pair_type(IDENTITY, IDENTITY) == (1,) * N,
            "coincident matching control lost fixed points")
    require(physical_pair_type(tuple(range(6)), (1, 2, 0, 4, 5, 3)) == (3, 3),
            "odd physical matching control did not detect 3+3")
    try:
        physical_pair_type(IDENTITY, (0,) * N)
    except VerificationError:
        rejected.append("invalid_matching")
    else:
        raise VerificationError("invalid physical matching control was accepted")
    return {"positive_certificate_controls": 2, "rejected_controls": rejected,
            "rejected_control_count": len(rejected), "physical_fixed_and_odd_controls": "pass"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="fresh JSON report inside repository .audit/local")
    parser.add_argument("--certificate", type=Path, help="optional parent JSON for semantic comparison")
    parser.add_argument("--triangle-certificate", type=Path,
                        help="optional parent local-six cross-view witness certificate")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    audit_root = (REPO_ROOT / ".audit/local").resolve()
    if not output.is_relative_to(audit_root):
        parser.error("--output must be inside .audit/local; frozen or parent files are never overwritten")
    if output.exists():
        parser.error("--output already exists; choose a fresh audit path")
    for input_path in (args.certificate, args.triangle_certificate):
        if input_path is not None and input_path.resolve() == output:
            parser.error("output and input certificate must be different paths")
    try:
        report = compute_audit()
        report["malformed_controls"] = run_malformed_controls(report)
        report["triangle_certificate_controls"] = triangle_comparison_controls(report)
        report["script_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
        report["python_version"] = sys.version.split()[0]
        report["certificate_comparison"] = {"status": "not_requested"}
        report["triangle_certificate_comparison"] = {"status": "not_requested"}
        if args.certificate is not None:
            raw = args.certificate.read_bytes()
            comparison = compare_certificate(load_certificate(raw), report)
            comparison["input_sha256"] = sha256(raw).hexdigest()
            report["certificate_comparison"] = comparison
        if args.triangle_certificate is not None:
            raw = args.triangle_certificate.read_bytes()
            comparison = compare_triangle_certificate(load_certificate(raw), report)
            comparison["input_sha256"] = sha256(raw).hexdigest()
            report["triangle_certificate_comparison"] = comparison
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="ascii") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    except (OSError, VerificationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: 2 disjoint 6720-point orbits; 13440 physical triangles; 39 neighbors per representative")
    print("PASS: common cores; edge-free neighborhoods; sharp Latin 4x18 control; computed diamond spectra")
    print("PASS: all 16 local triangles have one persistent cross-view 3-cycle; broken-path controls")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
