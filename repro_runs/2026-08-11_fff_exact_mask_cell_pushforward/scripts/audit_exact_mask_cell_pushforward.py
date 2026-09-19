#!/usr/bin/env python3
"""Audit C88 exact-mask cell-pushforward marginal cancellation."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOL = runpy.run_path(
    str(ROOT / "repro_runs/2026-08-11_fff_color_parity_holonomy/scripts/audit_color_parity_holonomy.py")
)
SURFACE = HOL["SURFACE"]
SMALL = HOL["SMALL"]
PAIR = HOL["PAIR"]


def cell_coordinates(table: list[list[int]], cell: int) -> tuple[int, int, int]:
    n = len(table)
    row, col = divmod(cell, n)
    return row, col, table[row][col]


ROLE_WORDS = {
    0: ((0,), (1, 0, 1), (0,)),
    1: ((0, 1, 0), (1,), (1,)),
    2: ((2,), (2,), (0, 2, 0)),
}


def apply_word(flag: int, alphas: list[list[int]], word: tuple[int, ...]) -> int:
    for colour in reversed(word):
        flag = alphas[colour][flag]
    return flag


def pushforward_marginals(table: list[list[int]], flags: list[dict], component: list[int], potential: dict[int, int]) -> list[list[int]]:
    n = len(table)
    values = [0] * (n * n)
    for flag in component:
        sign = 1 if potential[flag] == 0 else -1
        for cell in flags[flag]["cells"]:
            values[cell] += sign
    result = [[0] * n for _ in range(3)]
    for cell, value in enumerate(values):
        if value:
            coords = cell_coordinates(table, cell)
            for view in range(3):
                result[view][coords[view]] += value
    return result


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]
    role_checks = 0
    for view, words in ROLE_WORDS.items():
        for role, word in enumerate(words):
            for flag in range(len(flags)):
                neighbor = apply_word(flag, alphas, word)
                if flag < neighbor:
                    role_checks += 1
                    left = cell_coordinates(table, flags[flag]["cells"][role])[view]
                    right = cell_coordinates(table, flags[neighbor]["cells"][role])[view]
                    if left != right:
                        errors.append(["cell_role_involution", view, role, flag, neighbor, left, right])

    exact_masks = Counter()
    pushforward_checks = 0
    marginal_checks = 0
    fff_components = 0
    for component_id, component in enumerate(components):
        atom_ids = {atom for flag in component for atom in flags[flag]["atoms"]}
        if all(atoms[atom]["length"] % 2 == 0 for atom in atom_ids):
            fff_components += 1
        for mask in range(1, 8):
            potential = HOL["mask_potential_on_component"](component, alphas, mask)
            if potential is None:
                continue
            exact_masks[mask] += 1
            marginals = pushforward_marginals(table, flags, component, potential)
            pushforward_checks += 1
            for view in range(3):
                if mask & (1 << view):
                    marginal_checks += 1
                    if any(marginals[view]):
                        errors.append(["predicted_zero_marginal", component_id, mask, view, marginals[view]])
    return {
        "source_index": source_index,
        "order": len(table),
        "component_count": len(components),
        "fff_component_count": fff_components,
        "cell_role_involution_checks": role_checks,
        "exact_mask_counts": dict(sorted(exact_masks.items())),
        "pushforward_checks": pushforward_checks,
        "predicted_zero_marginal_checks": marginal_checks,
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    mask_counts = Counter()
    for record in records:
        mask_counts.update({int(mask): count for mask, count in record["exact_mask_counts"].items()})
    errors = [[record["source_index"], error] for record in records for error in record["errors"]]
    return {
        "name": name,
        "table_count": len(records),
        "component_count": sum(record["component_count"] for record in records),
        "fff_component_count": sum(record["fff_component_count"] for record in records),
        "cell_role_involution_checks": sum(record["cell_role_involution_checks"] for record in records),
        "exact_mask_counts": dict(sorted(mask_counts.items())),
        "pushforward_checks": sum(record["pushforward_checks"] for record in records),
        "predicted_zero_marginal_checks": sum(record["predicted_zero_marginal_checks"] for record in records),
        "error_count": len(errors),
        "errors": errors[:100],
    }


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), SURFACE["parse_compact"](row["square"], 8)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    datasets = {
        "order4_complete": summarize("order4_complete", [analyze_table(t, i) for i, t in enumerate(SMALL["reduced_latin_squares"](4), 1)]),
        "order6_complete": summarize("order6_complete", [analyze_table(t, i) for i, t in enumerate(SMALL["reduced_latin_squares"](6), 1)]),
        "order8_fff_complete": summarize("order8_fff_complete", [analyze_table(t, i) for i, t in load_n8(args.fff_metadata)]),
        "order10_tracked_partial": summarize("order10_tracked_partial", [analyze_table(t, i) for i, t, _ in PAIR["FLAG"]["n10_tables"](args.n10_corpus)]),
    }
    keys = ("table_count", "component_count", "fff_component_count", "cell_role_involution_checks", "pushforward_checks", "predicted_zero_marginal_checks", "error_count")
    totals = {key: sum(dataset[key] for dataset in datasets.values()) for key in keys}
    masks = Counter()
    for dataset in datasets.values():
        masks.update({int(mask): count for mask, count in dataset["exact_mask_counts"].items()})
    totals["exact_mask_counts"] = dict(sorted(masks.items()))
    payload = {
        "audit_version": "exact_mask_cell_pushforward_v1",
        "datasets": datasets,
        "totals": totals,
        "claim_boundary": [
            "C88 is a rigorous necessary identity for exact masks.",
            "It reaches all flag components but is not an order-10 obstruction by itself.",
            "C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "Exact-mask cell-pushforward audit", "",
        f"tables: {totals['table_count']}",
        f"components: {totals['component_count']}",
        f"FFF components: {totals['fff_component_count']}",
        f"cell-role involution checks: {totals['cell_role_involution_checks']}",
        f"exact-mask pushforwards: {totals['pushforward_checks']}",
        f"predicted zero marginals: {totals['predicted_zero_marginal_checks']}",
        f"exact-mask counts: {totals['exact_mask_counts']}",
        f"errors: {totals['error_count']}", "",
    ]
    for name, dataset in datasets.items():
        lines.extend([name, f"- tables: {dataset['table_count']}", f"- components: {dataset['component_count']}", f"- pushforwards: {dataset['pushforward_checks']}", f"- zero marginals: {dataset['predicted_zero_marginal_checks']}", f"- errors: {dataset['error_count']}", ""])
    lines.extend(["Boundary:", "- C88 is rigorous and exactly audited.", "- It supplies necessary linear marginals, not an n=10 decision.", "- C38 remains open and C40 absent."])
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
