#!/usr/bin/env python3
"""Refine C70 signatures by cross-view cycle-component support overlaps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import runpy
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path


VIEWS = ("row", "col", "sym")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cycle_atoms(table: list[list[int]], base: dict) -> dict[str, list[tuple[int, int]]]:
    n = len(table)
    lines = base["view_lines"](table)
    atoms = {view: [] for view in VIEWS}
    for view in VIEWS:
        inverses = [base["inverse"](line) for line in lines[view]]
        for first in range(n):
            for second in range(first):
                permutation = [
                    inverses[second][value] for value in lines[view][first]
                ]
                for length, support in base["cycles_with_support"](permutation):
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
                    if mask.bit_count() != 2 * length:
                        raise RuntimeError("cycle atom has incorrect support size")
                    atoms[view].append((length, mask))
    return atoms


def overlap_signature(
    atoms: dict[str, list[tuple[int, int]]], n: int
) -> tuple[str, str, dict[str, dict[str, int]], list]:
    ordered = {}
    structural = {}
    marginal_errors = []
    for left in VIEWS:
        for right in VIEWS:
            if left == right:
                continue
            counter: Counter[str] = Counter()
            matrix = []
            for left_index, (left_length, left_mask) in enumerate(atoms[left]):
                row_sum = 0
                matrix_row = []
                for right_length, right_mask in atoms[right]:
                    overlap = (left_mask & right_mask).bit_count()
                    row_sum += overlap
                    matrix_row.append(overlap)
                    counter[f"{left_length},{right_length},{overlap}"] += 1
                expected = 2 * left_length * (n - 1)
                if row_sum != expected:
                    marginal_errors.append(
                        [left, right, left_index, row_sum, expected]
                    )
                matrix.append(matrix_row)
            ordered[left, right] = counter
            left_colors = [f"L{length}" for length, _ in atoms[left]]
            right_colors = [f"L{length}" for length, _ in atoms[right]]
            for _ in range(4):
                next_left = []
                for row_index, color in enumerate(left_colors):
                    neighbors = sorted(
                        (matrix[row_index][column_index], right_colors[column_index])
                        for column_index in range(len(right_colors))
                    )
                    encoded = json.dumps([color, neighbors], separators=(",", ":"))
                    next_left.append(hashlib.sha256(encoded.encode("ascii")).hexdigest())
                next_right = []
                for column_index, color in enumerate(right_colors):
                    neighbors = sorted(
                        (matrix[row_index][column_index], left_colors[row_index])
                        for row_index in range(len(left_colors))
                    )
                    encoded = json.dumps([color, neighbors], separators=(",", ":"))
                    next_right.append(hashlib.sha256(encoded.encode("ascii")).hexdigest())
                left_colors, right_colors = next_left, next_right
            edge_colors = Counter(
                (
                    left_colors[row_index],
                    matrix[row_index][column_index],
                    right_colors[column_index],
                )
                for row_index in range(len(left_colors))
                for column_index in range(len(right_colors))
            )
            structural[left, right] = {
                "left_colors": sorted(Counter(left_colors).items()),
                "right_colors": sorted(Counter(right_colors).items()),
                "edge_colors": sorted((list(key), value) for key, value in edge_colors.items()),
            }

    canonical_forms = []
    for axis_order in permutations(VIEWS):
        payload = []
        for first, second in ((0, 1), (0, 2), (1, 2)):
            counter = ordered[axis_order[first], axis_order[second]]
            payload.append(sorted(counter.items()))
        canonical_forms.append(payload)
    canonical = min(canonical_forms)
    encoded = json.dumps(canonical, separators=(",", ":")).encode("ascii")
    structural_forms = []
    for axis_order in permutations(VIEWS):
        payload = []
        for first, second in ((0, 1), (0, 2), (1, 2)):
            payload.append(structural[axis_order[first], axis_order[second]])
        structural_forms.append(payload)
    structural_encoded = min(
        json.dumps(form, sort_keys=True, separators=(",", ":"))
        for form in structural_forms
    ).encode("ascii")
    readable = {
        f"{left}_{right}": dict(sorted(counter.items()))
        for (left, right), counter in ordered.items()
        if VIEWS.index(left) < VIEWS.index(right)
    }
    return (
        sha256_bytes(encoded),
        sha256_bytes(structural_encoded),
        readable,
        marginal_errors,
    )


def collision_groups(records: list[dict], key: str) -> list[dict]:
    groups = defaultdict(list)
    for record in records:
        groups[record[key]].append(record["source_index"])
    return [
        {"signature": signature, "source_indices": sorted(indices)}
        for signature, indices in sorted(groups.items())
        if len(indices) > 1
    ]


def triple_overlap_signature(atoms: dict[str, list[tuple[int, int]]]) -> str:
    counter: Counter[tuple[int, int, int, int]] = Counter()
    for row_length, row_mask in atoms["row"]:
        for col_length, col_mask in atoms["col"]:
            pair_mask = row_mask & col_mask
            for sym_length, sym_mask in atoms["sym"]:
                counter[
                    (row_length, col_length, sym_length, (pair_mask & sym_mask).bit_count())
                ] += 1
    forms = []
    for axis_order in permutations(range(3)):
        transformed = sorted(
            (
                (key[axis_order[0]], key[axis_order[1]], key[axis_order[2]], key[3]),
                value,
            )
            for key, value in counter.items()
        )
        forms.append(json.dumps(transformed, separators=(",", ":")))
    return sha256_bytes(min(forms).encode("ascii"))


def incidence_wl_signature(
    atoms: dict[str, list[tuple[int, int]]], n: int
) -> str:
    forms = []
    for axis_order in permutations(VIEWS):
        colors = ["cell"] * (n * n)
        adjacency = [[] for _ in range(n * n)]
        for axis, view in enumerate(axis_order):
            for length, mask in atoms[view]:
                node = len(colors)
                colors.append(f"axis{axis}_length{length}")
                adjacency.append([])
                for cell in range(n * n):
                    if (mask >> cell) & 1:
                        adjacency[node].append(cell)
                        adjacency[cell].append(node)
        for _ in range(12):
            descriptions = [
                json.dumps(
                    [colors[node], sorted(colors[neighbor] for neighbor in adjacency[node])],
                    separators=(",", ":"),
                )
                for node in range(len(colors))
            ]
            palette = {
                description: str(index)
                for index, description in enumerate(sorted(set(descriptions)))
            }
            next_colors = [palette[description] for description in descriptions]
            if next_colors == colors:
                break
            colors = next_colors
        forms.append(
            json.dumps(sorted(Counter(colors).items()), separators=(",", ":"))
        )
    return sha256_bytes(min(forms).encode("ascii"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-script", type=Path, required=True)
    parser.add_argument("--census-json", type=Path, required=True)
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    base = runpy.run_path(str(args.base_script))
    census = json.loads(args.census_json.read_text())
    source = census["orders"]["8"]["kept_table_summaries"]
    metadata = {}
    with args.fff_metadata.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            metadata[int(row["line_number"])] = {
                "group_isotopic": row["group_isotopic"].lower() == "true",
                "fff_index": int(row["index"]),
            }
    records = []
    all_errors = []
    overlap_counts: Counter[str] = Counter()
    joint_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    structural_joint_counts: Counter[str] = Counter()
    for entry in source:
        table = base["parse_compact"](entry["compact_table"], 8)
        atoms = cycle_atoms(table, base)
        overlap_sha, structural_sha, overlap_histograms, errors = overlap_signature(
            atoms, 8
        )
        all_errors.extend([[entry["source_index"], *error] for error in errors])
        joint_sha = sha256_bytes(
            (entry["incidence_signature_sha256"] + overlap_sha).encode("ascii")
        )
        structural_joint_sha = sha256_bytes(
            (entry["incidence_signature_sha256"] + structural_sha).encode("ascii")
        )
        overlap_counts[overlap_sha] += 1
        joint_counts[joint_sha] += 1
        structural_counts[structural_sha] += 1
        structural_joint_counts[structural_joint_sha] += 1
        records.append(
            {
                "source_index": entry["source_index"],
                **metadata[entry["source_index"]],
                "incidence_signature_sha256": entry[
                    "incidence_signature_sha256"
                ],
                "component_overlap_signature_sha256": overlap_sha,
                "joint_signature_sha256": joint_sha,
                "component_overlap_structural_signature_sha256": structural_sha,
                "structural_joint_signature_sha256": structural_joint_sha,
                "overlap_histograms": overlap_histograms,
            }
        )

    before = collision_groups(records, "incidence_signature_sha256")
    after = collision_groups(records, "joint_signature_sha256")
    structural_after = collision_groups(records, "structural_joint_signature_sha256")
    source_by_index = {entry["source_index"]: entry for entry in source}
    remaining_diagnostics = []
    for group in structural_after:
        for source_index in group["source_indices"]:
            entry = source_by_index[source_index]
            table = base["parse_compact"](entry["compact_table"], 8)
            atoms = cycle_atoms(table, base)
            remaining_diagnostics.append(
                {
                    "source_index": source_index,
                    **metadata[source_index],
                    "triple_overlap_signature_sha256": triple_overlap_signature(atoms),
                    "cell_atom_incidence_1wl_signature_sha256": incidence_wl_signature(
                        atoms, 8
                    ),
                }
            )
    payload = {
        "audit_version": "fff_component_overlap_refinement_v1",
        "table_count": len(records),
        "c70_distinct_signature_count": len(
            {record["incidence_signature_sha256"] for record in records}
        ),
        "component_overlap_distinct_signature_count": len(overlap_counts),
        "joint_distinct_signature_count": len(joint_counts),
        "component_overlap_structural_distinct_signature_count": len(
            structural_counts
        ),
        "structural_joint_distinct_signature_count": len(structural_joint_counts),
        "c70_collision_groups": before,
        "joint_collision_groups": after,
        "structural_joint_collision_groups": structural_after,
        "remaining_collision_diagnostics": remaining_diagnostics,
        "marginal_error_count": len(all_errors),
        "marginal_errors": all_errors,
        "records": records,
        "claim_effect": {"C38": "open", "C40": "absent"},
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "FFF cycle-component overlap refinement",
        "",
        f"tables: {len(records)}",
        f"C70 distinct signatures: {payload['c70_distinct_signature_count']}",
        f"C70 collision groups: {len(before)}",
        f"component-overlap distinct signatures: {payload['component_overlap_distinct_signature_count']}",
        f"joint distinct signatures: {payload['joint_distinct_signature_count']}",
        f"joint collision groups: {len(after)}",
        f"structural-overlap distinct signatures: {payload['component_overlap_structural_distinct_signature_count']}",
        f"structural joint distinct signatures: {payload['structural_joint_distinct_signature_count']}",
        f"structural joint collision groups: {len(structural_after)}",
        f"overlap marginal errors: {len(all_errors)}",
        "",
        "C70 collisions before refinement:",
    ]
    lines.extend(
        f"- {group['source_indices']}" for group in before
    )
    lines.extend(["", "Collisions after joint refinement:"])
    lines.extend(
        [f"- {group['source_indices']}" for group in after] or ["- none"]
    )
    lines.extend(["", "Collisions after structural overlap refinement:"])
    lines.extend(
        [f"- {group['source_indices']}" for group in structural_after]
        or ["- none"]
    )
    if remaining_diagnostics:
        lines.extend(["", "Remaining collision diagnostics:"])
        for entry in remaining_diagnostics:
            lines.append(
                "- source {source_index}: group_isotopic={group_isotopic}, triple_overlap={triple_overlap_signature_sha256}, cell_atom_1WL={cell_atom_incidence_1wl_signature_sha256}".format(
                    **entry
                )
            )
    lines.extend(
        [
            "",
            "Conservative conclusion:",
            "- This is an exact order-8 classification invariant, not an order-10 theorem.",
            "- C38 remains open and C40 remains absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    if all_errors:
        raise SystemExit("component-overlap marginal audit failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
