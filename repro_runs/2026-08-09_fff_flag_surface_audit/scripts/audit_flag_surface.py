#!/usr/bin/env python3
"""Audit the three-coloured cycle-flag surface on frozen Latin-square data."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import multiprocessing as mp
import runpy
import time
from collections import Counter, defaultdict, deque
from itertools import combinations, permutations, product
from pathlib import Path
from typing import Iterable


VIEWS = ("row", "col", "sym")
COLORS = (0, 1, 2)  # alpha_R, alpha_C, alpha_S


def sha256_json(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def parse_compact(compact: str, n: int) -> list[list[int]]:
    compact = compact.strip()
    if len(compact) != n * n:
        raise ValueError(f"expected {n*n} symbols, found {len(compact)}")
    return [
        [int(value) for value in compact[n * row : n * (row + 1)]]
        for row in range(n)
    ]


def compact_table(table: list[list[int]]) -> str:
    return "".join(str(value) for row in table for value in row)


def inverse(permutation: list[int]) -> list[int]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return result


def cycles(permutation: list[int]) -> list[tuple[int, ...]]:
    seen = [False] * len(permutation)
    result = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        support = []
        point = start
        while not seen[point]:
            seen[point] = True
            support.append(point)
            point = permutation[point]
        result.append(tuple(support))
    return result


def view_lines(table: list[list[int]]) -> dict[str, list[list[int]]]:
    n = len(table)
    symbol_lines = [[0] * n for _ in range(n)]
    for row in range(n):
        for column, symbol in enumerate(table[row]):
            symbol_lines[symbol][column] = row
    return {
        "row": table,
        "col": [[table[row][column] for row in range(n)] for column in range(n)],
        "sym": symbol_lines,
    }


def atom_cell_mask(
    table: list[list[int]],
    lines: dict[str, list[list[int]]],
    view: str,
    first: int,
    second: int,
    support: tuple[int, ...],
) -> int:
    n = len(table)
    mask = 0
    if view == "row":
        for column in support:
            mask |= 1 << (first * n + column)
            mask |= 1 << (second * n + column)
    elif view == "col":
        for row in support:
            mask |= 1 << (row * n + first)
            mask |= 1 << (row * n + second)
    else:
        for column in support:
            mask |= 1 << (lines[view][first][column] * n + column)
            mask |= 1 << (lines[view][second][column] * n + column)
    return mask


def build_atoms(table: list[list[int]]) -> tuple[list[dict], dict, dict[str, list[int]]]:
    n = len(table)
    lines = view_lines(table)
    atoms: list[dict] = []
    point_to_atom = {}
    atoms_by_view = {view: [] for view in VIEWS}
    for view in VIEWS:
        inverses = [inverse(line) for line in lines[view]]
        for first in range(n):
            for second in range(first):
                permutation = [inverses[second][value] for value in lines[view][first]]
                low, high = second, first
                for support in cycles(permutation):
                    atom_id = len(atoms)
                    mask = atom_cell_mask(table, lines, view, first, second, support)
                    atom = {
                        "id": atom_id,
                        "view": view,
                        "lines": (low, high),
                        "length": len(support),
                        "support": tuple(sorted(support)),
                        "cell_mask": mask,
                    }
                    if mask.bit_count() != 2 * len(support):
                        raise AssertionError("atom support size mismatch")
                    atoms.append(atom)
                    atoms_by_view[view].append(atom_id)
                    for point in support:
                        point_to_atom[(view, low, high, point)] = atom_id
    return atoms, point_to_atom, atoms_by_view


def atom_for(point_to_atom: dict, view: str, first: int, second: int, point: int) -> int:
    low, high = sorted((first, second))
    return point_to_atom[(view, low, high, point)]


def build_flags(table: list[list[int]], point_to_atom: dict) -> list[dict]:
    n = len(table)
    row_inverses = [inverse(row) for row in table]
    flags = []
    for row in range(n):
        for other_row in range(n):
            if row == other_row:
                continue
            for column in range(n):
                symbol = table[row][column]
                other_column = row_inverses[other_row][symbol]
                other_symbol = table[row][other_column]
                if column == other_column or symbol == other_symbol:
                    raise AssertionError("degenerate flag")
                row_atom = atom_for(point_to_atom, "row", row, other_row, column)
                col_atom = atom_for(point_to_atom, "col", column, other_column, row)
                sym_atom = atom_for(point_to_atom, "sym", symbol, other_symbol, column)
                cells = (
                    row * n + column,
                    other_row * n + other_column,
                    row * n + other_column,
                )
                flags.append(
                    {
                        "atoms": (row_atom, col_atom, sym_atom),
                        "cells": cells,
                        "edge_keys": (
                            (col_atom, sym_atom, row),
                            (row_atom, sym_atom, other_column),
                            (row_atom, col_atom, symbol),
                        ),
                    }
                )
    return flags


def build_dual_involutions(flags: list[dict]) -> tuple[list[list[int]], list[list]]:
    alphas = [[-1] * len(flags) for _ in COLORS]
    bad_groups = []
    for color in COLORS:
        groups = defaultdict(list)
        for flag_id, flag in enumerate(flags):
            groups[flag["edge_keys"][color]].append(flag_id)
        for key, members in groups.items():
            if len(members) != 2:
                bad_groups.append([color, list(key), len(members)])
                continue
            first, second = members
            alphas[color][first] = second
            alphas[color][second] = first
    return alphas, bad_groups


def cell_coordinates(table: list[list[int]], cell: int) -> tuple[int, int, int]:
    n = len(table)
    row, column = divmod(cell, n)
    return row, column, table[row][column]


def share_coordinate(table: list[list[int]], first: int, second: int) -> bool:
    left = cell_coordinates(table, first)
    right = cell_coordinates(table, second)
    return sum(a == b for a, b in zip(left, right)) == 1


def connected_components(adjacency: list[set[int]]) -> list[list[int]]:
    unseen = set(range(len(adjacency)))
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        component = []
        while queue:
            node = queue.pop()
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(component))
    return result


def is_bipartite(nodes: list[int], adjacency: list[set[int]]) -> bool:
    colors = {}
    for start in nodes:
        if start in colors:
            continue
        colors[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in adjacency[node]:
                if neighbor not in colors:
                    colors[neighbor] = 1 - colors[node]
                    queue.append(neighbor)
                elif colors[neighbor] == colors[node]:
                    return False
    return True


def canonical_surface_signature(components: list[dict]) -> str:
    forms = []
    for axis_order in permutations(range(3)):
        transformed = []
        for component in components:
            transformed.append(
                [
                    component["faces"],
                    component["euler"],
                    component["orientable"],
                    [component["length_histograms"][axis] for axis in axis_order],
                ]
            )
        forms.append(sorted(transformed, key=lambda item: json.dumps(item, sort_keys=True)))
    return sha256_json(min(forms, key=lambda item: json.dumps(item, sort_keys=True)))


def canonical_word(word: tuple[int, ...]) -> tuple[int, ...]:
    candidates = []
    for color_permutation in permutations(COLORS):
        mapped = tuple(color_permutation[color] for color in word)
        for sequence in (mapped, tuple(reversed(mapped))):
            for offset in range(len(sequence)):
                candidates.append(sequence[offset:] + sequence[:offset])
    return min(candidates)


def mixed_word_representatives(max_length: int) -> list[tuple[int, ...]]:
    representatives = set()
    for length in range(3, max_length + 1):
        for word in product(COLORS, repeat=length):
            if len(set(word)) < 3:
                continue
            if any(word[index] == word[(index + 1) % length] for index in range(length)):
                continue
            representatives.add(canonical_word(word))
    return sorted(representatives, key=lambda word: (len(word), word))


def trace_word(alphas: list[list[int]], word: tuple[int, ...]) -> int:
    fixed = 0
    for start in range(len(alphas[0])):
        point = start
        for color in word:
            point = alphas[color][point]
        fixed += point == start
    return fixed


def mixed_trace_profile(alphas: list[list[int]], words: list[tuple[int, ...]]) -> list:
    result = []
    for word in words:
        color_profiles = []
        for color_permutation in permutations(COLORS):
            mapped = tuple(color_permutation[color] for color in word)
            color_profiles.append(trace_word(alphas, mapped))
        result.append(["".join(map(str, word)), sorted(color_profiles)])
    return result


def analyze_table(
    table: list[list[int]],
    mixed_words: list[tuple[int, ...]],
    compute_trace: bool,
) -> dict:
    n = len(table)
    atoms, point_to_atom, atoms_by_view = build_atoms(table)
    flags = build_flags(table, point_to_atom)
    alphas, bad_edge_groups = build_dual_involutions(flags)
    errors = []
    if len(flags) != n * n * (n - 1):
        errors.append(["flag_count", len(flags), n * n * (n - 1)])
    errors.extend(["edge_group", *entry] for entry in bad_edge_groups[:10])
    if any(target < 0 for alpha in alphas for target in alpha):
        errors.append(["incomplete_dual_involution"])

    atom_degrees = Counter()
    pair_codegrees = {"row_col": Counter(), "row_sym": Counter(), "col_sym": Counter()}
    triple_counts = Counter()
    cell_degrees = Counter()
    cell_pair_counts = Counter()
    cell_atom_counts = Counter()
    for flag in flags:
        row_atom, col_atom, sym_atom = flag["atoms"]
        for atom_id in flag["atoms"]:
            atom_degrees[atom_id] += 1
        pair_codegrees["row_col"][row_atom, col_atom] += 1
        pair_codegrees["row_sym"][row_atom, sym_atom] += 1
        pair_codegrees["col_sym"][col_atom, sym_atom] += 1
        triple_counts[flag["atoms"]] += 1
        for cell in flag["cells"]:
            cell_degrees[cell] += 1
            for atom_id in flag["atoms"]:
                cell_atom_counts[cell, atom_id] += 1
        for first, second in combinations(sorted(flag["cells"]), 2):
            cell_pair_counts[first, second] += 1

    for atom in atoms:
        expected = 2 * atom["length"]
        if atom_degrees[atom["id"]] != expected:
            errors.append(["atom_degree", atom["id"], atom_degrees[atom["id"]], expected])
    codegree_histogram = Counter()
    for pair_type, counts in pair_codegrees.items():
        for pair, count in counts.items():
            codegree_histogram[count] += 1
            lengths = [atoms[atom_id]["length"] for atom_id in pair]
            if count not in (2, 4):
                errors.append(["pair_codegree", pair_type, list(pair), count])
            if (count == 4) != (lengths == [2, 2]):
                errors.append(["pair_codegree_intercalate", pair_type, list(pair), count, lengths])

    triple_histogram = Counter(triple_counts.values())
    for atom_triple, count in triple_counts.items():
        lengths = [atoms[atom_id]["length"] for atom_id in atom_triple]
        if count not in (1, 4):
            errors.append(["triple_multiplicity", list(atom_triple), count])
        if (count == 4) != (lengths == [2, 2, 2]):
            errors.append(["triple_intercalate", list(atom_triple), count, lengths])

    for cell in range(n * n):
        if cell_degrees[cell] != 3 * (n - 1):
            errors.append(["cell_degree", cell, cell_degrees[cell], 3 * (n - 1)])
    expected_adjacent_pairs = n * n * 3 * (n - 1) // 2
    if len(cell_pair_counts) != expected_adjacent_pairs:
        errors.append(["latin_graph_edge_count", len(cell_pair_counts), expected_adjacent_pairs])
    for pair, count in cell_pair_counts.items():
        if count != 2 or not share_coordinate(table, *pair):
            errors.append(["cell_pair_gram", list(pair), count])
    for atom in atoms:
        for cell in range(n * n):
            expected = 3 if (atom["cell_mask"] >> cell) & 1 else 0
            observed = cell_atom_counts[cell, atom["id"]]
            if observed != expected:
                errors.append(["cell_atom_gram", cell, atom["id"], observed, expected])
                if len(errors) > 30:
                    break
        if len(errors) > 30:
            break

    dual_adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag_id, neighbor in enumerate(alpha):
            if neighbor >= 0:
                dual_adjacency[flag_id].add(neighbor)
    flag_components = connected_components(dual_adjacency)
    components = []
    atom_to_component = {}
    for component_id, flag_ids in enumerate(flag_components):
        atom_ids = sorted({atom_id for flag_id in flag_ids for atom_id in flags[flag_id]["atoms"]})
        for atom_id in atom_ids:
            if atom_id in atom_to_component and atom_to_component[atom_id] != component_id:
                errors.append(["atom_component_split", atom_id])
            atom_to_component[atom_id] = component_id
        faces = len(flag_ids)
        if 3 * faces % 2:
            errors.append(["nonintegral_edge_count", component_id, faces])
        edge_count = 3 * faces // 2
        euler = len(atom_ids) - edge_count + faces
        length_histograms = []
        for view in VIEWS:
            length_histograms.append(
                sorted(Counter(atoms[atom_id]["length"] for atom_id in atom_ids if atoms[atom_id]["view"] == view).items())
            )
        components.append(
            {
                "vertices": len(atom_ids),
                "edges": edge_count,
                "faces": faces,
                "euler": euler,
                "orientable": is_bipartite(flag_ids, dual_adjacency),
                "length_histograms": length_histograms,
                "has_length_two": any(atoms[atom_id]["length"] == 2 for atom_id in atom_ids),
            }
        )

    link_preserving = {"row": (1, 2), "col": (0, 2), "sym": (0, 1)}
    incident_flags = defaultdict(list)
    for flag_id, flag in enumerate(flags):
        for atom_id in flag["atoms"]:
            incident_flags[atom_id].append(flag_id)
    for atom in atoms:
        members = incident_flags[atom["id"]]
        allowed = link_preserving[atom["view"]]
        seen = {members[0]}
        queue = [members[0]]
        while queue:
            flag_id = queue.pop()
            for color in allowed:
                neighbor = alphas[color][flag_id]
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if len(seen) != 2 * atom["length"]:
            errors.append(["link_cycle", atom["id"], len(seen), 2 * atom["length"]])

    intercalates = sum(atoms[atom_id]["length"] == 2 for atom_id in atoms_by_view["row"])
    for component_id, component in enumerate(components):
        if component["has_length_two"]:
            expected = (component["vertices"], component["edges"], component["faces"], component["euler"], component["orientable"])
            if expected != (3, 6, 4, 1, False):
                errors.append(["intercalate_component", component_id, list(expected)])

    total_euler = sum(component["euler"] for component in components)
    expected_euler = len(atoms) - n * n * (n - 1) // 2
    if total_euler != expected_euler:
        errors.append(["euler", total_euler, expected_euler])

    pattern = "".join(
        "F" if all(atoms[atom_id]["length"] % 2 == 0 for atom_id in atoms_by_view[view]) else "T"
        for view in VIEWS
    )
    if pattern == "FFF":
        for component_id, component in enumerate(components):
            if not component["has_length_two"] and component["euler"] >= 0:
                errors.append(["fff_residual_euler", component_id, component["euler"]])

    pair_trace_errors = []
    pair_colors = {"row": (1, 2), "col": (0, 2), "sym": (0, 1)}
    for view in VIEWS:
        for power in range(1, n + 1):
            observed = trace_word(alphas, pair_colors[view] * power)
            expected = 2 * sum(
                atoms[atom_id]["length"]
                for atom_id in atoms_by_view[view]
                if power % atoms[atom_id]["length"] == 0
            )
            if observed != expected:
                pair_trace_errors.append([view, power, observed, expected])
    errors.extend(["pair_trace", *entry] for entry in pair_trace_errors)
    rainbow_trace = trace_word(alphas, (0, 1, 2))
    if rainbow_trace != 4 * intercalates:
        errors.append(["rainbow_trace", rainbow_trace, 4 * intercalates])

    trace_profile = mixed_trace_profile(alphas, mixed_words) if compute_trace else None
    return {
        "pattern": pattern,
        "atom_count": len(atoms),
        "flag_count": len(flags),
        "component_count": len(components),
        "intercalates": intercalates,
        "orientable_component_count": sum(component["orientable"] for component in components),
        "nonorientable_component_count": sum(not component["orientable"] for component in components),
        "surface_signature_sha256": canonical_surface_signature(components),
        "mixed_trace_signature_sha256": sha256_json(trace_profile) if trace_profile is not None else None,
        "mixed_trace_profile": trace_profile,
        "codegree_histogram": dict(sorted(codegree_histogram.items())),
        "triple_histogram": dict(sorted(triple_histogram.items())),
        "errors": errors[:50],
    }


def audit_dataset(
    name: str,
    tables: Iterable[tuple[int, list[list[int]], dict]],
    expected_count: int | None,
    mixed_words: list[tuple[int, ...]],
    trace_selector,
) -> tuple[dict, list[dict]]:
    started = time.perf_counter()
    count = 0
    patterns = Counter()
    error_count = 0
    first_errors = []
    surface_signatures = Counter()
    trace_records = []
    zero_intercalate_count = 0
    zero_intercalate_nonorientable_count = 0
    component_histogram = Counter()
    for source_index, table, metadata in tables:
        count += 1
        keep_trace = bool(trace_selector(source_index, metadata))
        result = analyze_table(table, mixed_words, keep_trace)
        patterns[result["pattern"]] += 1
        surface_signatures[result["surface_signature_sha256"]] += 1
        component_histogram[result["component_count"]] += 1
        if result["intercalates"] == 0:
            zero_intercalate_count += 1
            if result["nonorientable_component_count"]:
                zero_intercalate_nonorientable_count += 1
        if result["errors"]:
            error_count += len(result["errors"])
            if len(first_errors) < 20:
                first_errors.append([source_index, result["errors"][:5]])
        if keep_trace:
            trace_records.append(
                {
                    "source_index": source_index,
                    **metadata,
                    "compact_table": compact_table(table),
                    **{key: value for key, value in result.items() if key != "mixed_trace_profile"},
                    "mixed_trace_profile": result["mixed_trace_profile"],
                }
            )
    if expected_count is not None and count != expected_count:
        raise RuntimeError(f"{name}: expected {expected_count}, found {count}")
    return (
        {
            "name": name,
            "table_count": count,
            "pattern_counts": dict(sorted(patterns.items())),
            "error_count": error_count,
            "first_errors": first_errors,
            "distinct_surface_signature_count": len(surface_signatures),
            "component_count_histogram": dict(sorted(component_histogram.items())),
            "zero_intercalate_count": zero_intercalate_count,
            "zero_intercalate_with_nonorientable_component_count": zero_intercalate_nonorientable_count,
            "trace_record_count": len(trace_records),
            "elapsed_seconds": time.perf_counter() - started,
        },
        trace_records,
    )


def analyze_compact_task(task: tuple[int, str, int]) -> tuple[int, dict]:
    source_index, compact, n = task
    return source_index, analyze_table(parse_compact(compact, n), [], False)


def audit_n8_parallel(
    census_path: Path,
    expected_count: int,
    limit: int | None,
    workers: int,
) -> dict:
    started = time.perf_counter()
    with gzip.open(census_path, "rt", encoding="ascii") as handle:
        tasks = [
            (index, line.strip(), 8)
            for index, line in enumerate(handle, start=1)
            if limit is None or index <= limit
        ]
    if len(tasks) != expected_count:
        raise RuntimeError(f"order8_complete: expected {expected_count}, found {len(tasks)}")
    patterns = Counter()
    surface_signatures = Counter()
    component_histogram = Counter()
    error_count = 0
    first_errors = []
    zero_intercalate_count = 0
    zero_intercalate_nonorientable_count = 0
    context = mp.get_context("spawn")
    with context.Pool(processes=workers) as pool:
        for source_index, result in pool.imap_unordered(
            analyze_compact_task, tasks, chunksize=64
        ):
            patterns[result["pattern"]] += 1
            surface_signatures[result["surface_signature_sha256"]] += 1
            component_histogram[result["component_count"]] += 1
            if result["intercalates"] == 0:
                zero_intercalate_count += 1
                if result["nonorientable_component_count"]:
                    zero_intercalate_nonorientable_count += 1
            if result["errors"]:
                error_count += len(result["errors"])
                if len(first_errors) < 20:
                    first_errors.append([source_index, result["errors"][:5]])
    return {
        "name": "order8_complete",
        "table_count": len(tasks),
        "pattern_counts": dict(sorted(patterns.items())),
        "error_count": error_count,
        "first_errors": first_errors,
        "distinct_surface_signature_count": len(surface_signatures),
        "component_count_histogram": dict(sorted(component_histogram.items())),
        "zero_intercalate_count": zero_intercalate_count,
        "zero_intercalate_with_nonorientable_component_count": zero_intercalate_nonorientable_count,
        "trace_record_count": 0,
        "workers": workers,
        "elapsed_seconds": time.perf_counter() - started,
    }


def n6_tables(generator_path: Path, limit: int | None):
    module = runpy.run_path(str(generator_path))
    for index, square in enumerate(module["reduced_latin_squares"](6), start=1):
        if limit is not None and index > limit:
            break
        yield index, [list(row) for row in square], {}


def n8_tables(census_path: Path, limit: int | None):
    with gzip.open(census_path, "rt", encoding="ascii") as handle:
        for index, line in enumerate(handle, start=1):
            if limit is not None and index > limit:
                break
            yield index, parse_compact(line, 8), {}


def fff_tables(metadata_path: Path):
    with metadata_path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), parse_compact(row["square"], 8), {
                "fff_index": int(row["index"]),
                "group_isotopic": row["group_isotopic"].lower() == "true",
            }


def n10_tables(corpus_path: Path):
    corpus = json.loads(corpus_path.read_text())
    compacts = sorted(corpus["tracked_order10_source_paths"])
    for index, compact in enumerate(compacts, start=1):
        yield index, parse_compact(compact, 10), {
            "source_paths": corpus["tracked_order10_source_paths"][compact]
        }


def collision_groups(records: list[dict], key: str) -> list[list[int]]:
    groups = defaultdict(list)
    for record in records:
        groups[record[key]].append(record["source_index"])
    return sorted(sorted(values) for values in groups.values() if len(values) > 1)


def attach_prior_signatures(
    records: list[dict], c70_path: Path, c72_path: Path
) -> tuple[list[list[int]], list[dict]]:
    c70 = json.loads(c70_path.read_text())
    c70_records = c70["orders"]["8"]["kept_table_summaries"]
    c70_by_source = {
        record["source_index"]: record["incidence_signature_sha256"]
        for record in c70_records
    }
    c72 = json.loads(c72_path.read_text())
    c72_by_source = {
        record["source_index"]: record["structural_joint_signature_sha256"]
        for record in c72["records"]
    }
    for record in records:
        source = record["source_index"]
        record["c70_incidence_signature_sha256"] = c70_by_source[source]
        record["c72_structural_joint_signature_sha256"] = c72_by_source[source]
        record["c70_surface_joint_sha256"] = sha256_json(
            [c70_by_source[source], record["surface_signature_sha256"]]
        )
        record["c70_trace_joint_sha256"] = sha256_json(
            [c70_by_source[source], record["mixed_trace_signature_sha256"]]
        )
        record["c72_trace_joint_sha256"] = sha256_json(
            [c72_by_source[source], record["mixed_trace_signature_sha256"]]
        )
    c70_collisions = collision_groups(records, "c70_incidence_signature_sha256")
    distinguishing = []
    by_source = {record["source_index"]: record for record in records}
    for group in c70_collisions:
        if len(group) != 2:
            continue
        left, right = map(by_source.get, group)
        left_profile = {word: values for word, values in left["mixed_trace_profile"]}
        right_profile = {word: values for word, values in right["mixed_trace_profile"]}
        first_word = next(
            (
                word
                for word in sorted(left_profile, key=lambda value: (len(value), value))
                if left_profile[word] != right_profile[word]
            ),
            None,
        )
        distinguishing.append(
            {
                "source_indices": group,
                "first_distinguishing_word": first_word,
                "left_trace_orbit": left_profile.get(first_word) if first_word else None,
                "right_trace_orbit": right_profile.get(first_word) if first_word else None,
            }
        )
    return c70_collisions, distinguishing


def joint_trace_cutoff_counts(records: list[dict], max_length: int) -> dict[str, int]:
    result = {}
    for cutoff in range(3, max_length + 1):
        signatures = set()
        for record in records:
            prefix = [
                entry
                for entry in record["mixed_trace_profile"]
                if len(entry[0]) <= cutoff
            ]
            signatures.add(
                sha256_json([record["c70_incidence_signature_sha256"], prefix])
            )
        result[str(cutoff)] = len(signatures)
    return result


def write_summary(payload: dict, path: Path) -> None:
    lines = ["Three-coloured cycle-flag surface audit", ""]
    lines.append(f"mixed word orbits through length {payload['max_word_length']}: {payload['mixed_word_orbit_count']}")
    for key in ("order6_complete", "order8_complete", "order8_fff", "order10_tracked"):
        data = payload[key]
        lines.extend(
            [
                "",
                f"{key}:",
                f"- tables: {data['table_count']}",
                f"- patterns: {data['pattern_counts']}",
                f"- identity errors: {data['error_count']}",
                f"- distinct surface signatures: {data['distinct_surface_signature_count']}",
                f"- zero-intercalate tables: {data['zero_intercalate_count']}",
                f"- zero-intercalate with nonorientable component: {data['zero_intercalate_with_nonorientable_component_count']}",
                f"- elapsed seconds: {data['elapsed_seconds']:.6f}",
            ]
        )
    lines.extend(
        [
            "",
            "Order-8 FFF refinements:",
            f"- distinct mixed-trace signatures: {payload['order8_fff_trace_distinct_count']}",
            f"- surface collision groups: {payload['order8_fff_surface_collision_groups']}",
            f"- mixed-trace collision groups: {payload['order8_fff_trace_collision_groups']}",
            f"- sources 13/19 surface equal: {payload['source13_19_surface_equal']}",
            f"- sources 13/19 mixed traces equal: {payload['source13_19_trace_equal']}",
            f"- C70 + surface distinct: {payload['order8_fff_c70_surface_joint_distinct_count']}",
            f"- C70 + mixed traces distinct: {payload['order8_fff_c70_trace_joint_distinct_count']}",
            f"- C72 structural + mixed traces distinct: {payload['order8_fff_c72_trace_joint_distinct_count']}",
            f"- C70 + trace cutoff counts: {payload['order8_fff_c70_trace_cutoff_distinct_counts']}",
            f"- shortest words separating old C70 collisions: {payload['order8_fff_c70_collision_distinguishing_words']}",
            "",
            "Claim boundary:",
            "- C38 remains open and C40 remains absent.",
            "- Finite trace separation is an exact invariant, not an order-10 theorem.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n6-generator", type=Path, required=True)
    parser.add_argument("--n8-census", type=Path, required=True)
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--c70-census", type=Path, required=True)
    parser.add_argument("--c72-refinement", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--max-word-length", type=int, default=10)
    parser.add_argument("--n6-limit", type=int)
    parser.add_argument("--n8-limit", type=int)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    mixed_words = mixed_word_representatives(args.max_word_length)
    expected_n6 = args.n6_limit if args.n6_limit is not None else 9408
    expected_n8 = args.n8_limit if args.n8_limit is not None else 283657
    n6_summary, _ = audit_dataset(
        "order6_complete",
        n6_tables(args.n6_generator, args.n6_limit),
        expected_n6,
        mixed_words,
        lambda _index, _meta: False,
    )
    n8_summary = audit_n8_parallel(
        args.n8_census,
        expected_n8,
        args.n8_limit,
        args.workers,
    )
    fff_summary, fff_records = audit_dataset(
        "order8_fff",
        fff_tables(args.fff_metadata),
        230,
        mixed_words,
        lambda _index, _meta: True,
    )
    n10_summary, n10_records = audit_dataset(
        "order10_tracked",
        n10_tables(args.n10_corpus),
        135,
        mixed_words,
        lambda _index, _meta: True,
    )
    c70_collisions, c70_distinguishing = attach_prior_signatures(
        fff_records, args.c70_census, args.c72_refinement
    )
    fff_by_source = {record["source_index"]: record for record in fff_records}
    payload = {
        "audit_version": "fff_three_colored_flag_surface_v1",
        "max_word_length": args.max_word_length,
        "mixed_word_orbit_count": len(mixed_words),
        "mixed_word_representatives": ["".join(map(str, word)) for word in mixed_words],
        "order6_complete": n6_summary,
        "order8_complete": n8_summary,
        "order8_fff": fff_summary,
        "order10_tracked": n10_summary,
        "order8_fff_trace_distinct_count": len({record["mixed_trace_signature_sha256"] for record in fff_records}),
        "order8_fff_surface_collision_groups": collision_groups(fff_records, "surface_signature_sha256"),
        "order8_fff_trace_collision_groups": collision_groups(fff_records, "mixed_trace_signature_sha256"),
        "order8_fff_c70_collision_groups": c70_collisions,
        "order8_fff_c70_collision_distinguishing_words": c70_distinguishing,
        "order8_fff_c70_surface_joint_distinct_count": len({record["c70_surface_joint_sha256"] for record in fff_records}),
        "order8_fff_c70_trace_joint_distinct_count": len({record["c70_trace_joint_sha256"] for record in fff_records}),
        "order8_fff_c72_trace_joint_distinct_count": len({record["c72_trace_joint_sha256"] for record in fff_records}),
        "order8_fff_c70_trace_cutoff_distinct_counts": joint_trace_cutoff_counts(fff_records, args.max_word_length),
        "source13_19_surface_equal": fff_by_source[13]["surface_signature_sha256"] == fff_by_source[19]["surface_signature_sha256"],
        "source13_19_trace_equal": fff_by_source[13]["mixed_trace_signature_sha256"] == fff_by_source[19]["mixed_trace_signature_sha256"],
        "order8_fff_records": fff_records,
        "order10_tracked_records": n10_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(payload, args.summary)
    if any(payload[key]["error_count"] for key in ("order6_complete", "order8_complete", "order8_fff", "order10_tracked")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
