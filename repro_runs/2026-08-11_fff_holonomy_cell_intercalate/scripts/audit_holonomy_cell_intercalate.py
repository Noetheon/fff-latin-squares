#!/usr/bin/env python3
"""Audit C87 oriented cell pushforwards on every intercalate component."""

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


def direct_intercalate_degrees(table: list[list[int]]) -> tuple[int, list[int]]:
    n = len(table)
    degrees = [0] * (n * n)
    count = 0
    for r in range(n):
        for rr in range(r + 1, n):
            for c in range(n):
                for cc in range(c + 1, n):
                    if table[r][c] == table[rr][cc] and table[r][cc] == table[rr][c]:
                        count += 1
                        for x in (r * n + c, r * n + cc, rr * n + c, rr * n + cc):
                            degrees[x] += 1
    return count, degrees


def marginals(table: list[list[int]], values: list[int]) -> dict[str, list[int]]:
    n = len(table)
    return {
        "row": [sum(values[r * n + c] for c in range(n)) for r in range(n)],
        "col": [sum(values[r * n + c] for r in range(n)) for c in range(n)],
        "sym": [
            sum(values[r * n + c] for r in range(n) for c in range(n) if table[r][c] == s)
            for s in range(n)
        ],
    }


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            adjacency[flag].add(neighbor)
    components = SURFACE["connected_components"](adjacency)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]
    component_degrees = [0] * (n * n)
    intercalate_components = 0
    vector_checks = 0
    product_checks = 0

    for component_id, component in enumerate(components):
        atom_ids = {atom for flag in component for atom in flags[flag]["atoms"]}
        if not (
            len(component) == 4
            and len(atom_ids) == 3
            and all(atoms[atom]["length"] == 2 for atom in atom_ids)
        ):
            continue
        intercalate_components += 1
        support = sorted({cell for flag in component for cell in flags[flag]["cells"]})
        if len(support) != 4:
            errors.append(["support_size", component_id, support])
            continue
        for cell in support:
            component_degrees[cell] += 1

        vectors = {}
        for mask in (3, 5, 6):
            potential = HOL["mask_potential_on_component"](component, alphas, mask)
            if potential is None:
                errors.append(["mask_not_exact", component_id, mask])
                continue
            values = [0] * (n * n)
            for flag in component:
                sign = 1 if potential[flag] == 0 else -1
                for cell in flags[flag]["cells"]:
                    values[cell] += sign
            vectors[mask] = values
            actual_support = [cell for cell, value in enumerate(values) if value]
            if actual_support != support or any(abs(values[cell]) != 1 for cell in support):
                errors.append(["oriented_support", component_id, mask, actual_support])
            sums = marginals(table, values)
            zero_views = {3: ("row", "col"), 5: ("row", "sym"), 6: ("col", "sym")}[mask]
            remaining = ({"row", "col", "sym"} - set(zero_views)).pop()
            if any(sums[view] != [0] * n for view in zero_views):
                errors.append(["zero_marginal", component_id, mask, sums])
            nonzero = sorted(value for value in sums[remaining] if value)
            if nonzero != [-2, 2]:
                errors.append(["endpoint_marginal", component_id, mask, remaining, sums[remaining]])
            vector_checks += 1

        if len(vectors) == 3:
            products = [vectors[3][cell] * vectors[5][cell] * vectors[6][cell] for cell in support]
            if len(set(products)) != 1 or abs(products[0]) != 1:
                errors.append(["triple_product", component_id, products])
            product_checks += len(support)

    direct_count, direct_degrees = direct_intercalate_degrees(table)
    if direct_count != intercalate_components:
        errors.append(["intercalate_count", direct_count, intercalate_components])
    if direct_degrees != component_degrees:
        errors.append(["cell_degrees", direct_degrees, component_degrees])
    return {
        "source_index": source_index,
        "order": n,
        "intercalates": direct_count,
        "component_checks": intercalate_components,
        "oriented_vector_checks": vector_checks,
        "triple_product_cell_checks": product_checks,
        "cell_degree_checks": n * n,
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    errors = [[record["source_index"], error] for record in records for error in record["errors"]]
    return {
        "name": name,
        "table_count": len(records),
        "intercalate_count": sum(record["intercalates"] for record in records),
        "component_checks": sum(record["component_checks"] for record in records),
        "oriented_vector_checks": sum(record["oriented_vector_checks"] for record in records),
        "triple_product_cell_checks": sum(record["triple_product_cell_checks"] for record in records),
        "cell_degree_checks": sum(record["cell_degree_checks"] for record in records),
        "intercalate_count_distribution": dict(sorted(Counter(record["intercalates"] for record in records).items())),
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
    totals = {
        key: sum(dataset[key] for dataset in datasets.values())
        for key in ("table_count", "intercalate_count", "component_checks", "oriented_vector_checks", "triple_product_cell_checks", "cell_degree_checks", "error_count")
    }
    payload = {"audit_version": "holonomy_cell_intercalate_v1", "datasets": datasets, "totals": totals, "claim_boundary": ["C87 couples C85 to the C84 Y layer only.", "The X layer and order 10 remain open.", "C38 remains open and C40 absent."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Holonomy-to-cell intercalate audit", "", f"tables: {totals['table_count']}", f"intercalates/components: {totals['intercalate_count']}", f"oriented vectors: {totals['oriented_vector_checks']}", f"triple-product cell checks: {totals['triple_product_cell_checks']}", f"cell-degree checks: {totals['cell_degree_checks']}", f"errors: {totals['error_count']}", ""]
    for name, dataset in datasets.items():
        lines.extend([name, f"- tables: {dataset['table_count']}", f"- intercalates: {dataset['intercalate_count']}", f"- oriented vectors: {dataset['oriented_vector_checks']}", f"- errors: {dataset['error_count']}", ""])
    lines.extend(["Boundary:", "- C87 is rigorous and exactly audited.", "- Only the C84 multiplicity-four Y layer is coupled.", "- C38 remains open and C40 absent."])
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
