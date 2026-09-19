#!/usr/bin/env python3
"""Audit C89 cellwise Walsh identities for exact holonomy masks."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOL = runpy.run_path(str(ROOT / "repro_runs/2026-08-11_fff_color_parity_holonomy/scripts/audit_color_parity_holonomy.py"))
SURFACE = HOL["SURFACE"]
SMALL = HOL["SMALL"]
PAIR = HOL["PAIR"]


def parity(value: int) -> int:
    return value.bit_count() & 1


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
    dimension_counts = Counter()
    component_cell_checks = 0
    transform_checks = 0
    inversion_checks = 0
    parseval_checks = 0
    compatible_potential_checks = 0

    for component_id, component in enumerate(components):
        exact_masks = [m for m in range(8) if HOL["exact_mask_on_component"](component, alphas, m)]
        basis = HOL["binary_basis"](exact_masks)
        d = len(basis)
        dimension_counts[d] += 1
        potentials = [HOL["mask_potential_on_component"](component, alphas, mask) for mask in basis]
        if any(potential is None for potential in potentials):
            errors.append(["basis_potential", component_id, basis])
            continue
        labels = {flag: sum(potentials[i][flag] << i for i in range(d)) for flag in component}
        cells = defaultdict(lambda: [0] * (1 << d))
        for flag in component:
            for cell in flags[flag]["cells"]:
                cells[cell][labels[flag]] += 1

        for coefficients in range(1 << d):
            mask = 0
            for i, basis_mask in enumerate(basis):
                if coefficients & (1 << i):
                    mask ^= basis_mask
            direct = HOL["mask_potential_on_component"](component, alphas, mask)
            if direct is None:
                errors.append(["combined_mask_not_exact", component_id, coefficients, mask])
                continue
            for flag in component:
                expected = parity(coefficients & labels[flag])
                if direct[flag] != expected:
                    errors.append(["compatible_potential", component_id, coefficients, flag, direct[flag], expected])
                    break
            compatible_potential_checks += 1

        for cell, counts in cells.items():
            component_cell_checks += 1
            transform = [
                sum((1 if parity(c & a) == 0 else -1) * count for a, count in enumerate(counts))
                for c in range(1 << d)
            ]
            for c, value in enumerate(transform):
                direct_value = sum((1 if parity(c & labels[flag]) == 0 else -1) for flag in component if cell in flags[flag]["cells"])
                if value != direct_value:
                    errors.append(["walsh_transform", component_id, cell, c, value, direct_value])
                transform_checks += 1
            for a, count in enumerate(counts):
                numerator = sum((1 if parity(c & a) == 0 else -1) * transform[c] for c in range(1 << d))
                if numerator != (1 << d) * count or numerator < 0:
                    errors.append(["fourier_inversion", component_id, cell, a, numerator, count, d])
                inversion_checks += 1
            if sum(value * value for value in transform) != (1 << d) * sum(count * count for count in counts):
                errors.append(["parseval", component_id, cell, transform, counts])
            parseval_checks += 1

    return {
        "source_index": source_index,
        "order": len(table),
        "component_count": len(components),
        "exact_space_dimension_counts": dict(sorted(dimension_counts.items())),
        "compatible_potential_checks": compatible_potential_checks,
        "component_cell_checks": component_cell_checks,
        "transform_checks": transform_checks,
        "inversion_checks": inversion_checks,
        "parseval_checks": parseval_checks,
        "errors": errors,
    }


def summarize(name: str, records: list[dict]) -> dict:
    dimensions = Counter()
    for record in records:
        dimensions.update({int(d): count for d, count in record["exact_space_dimension_counts"].items()})
    errors = [[record["source_index"], error] for record in records for error in record["errors"]]
    keys = ("component_count", "compatible_potential_checks", "component_cell_checks", "transform_checks", "inversion_checks", "parseval_checks")
    return {"name": name, "table_count": len(records), **{key: sum(r[key] for r in records) for key in keys}, "exact_space_dimension_counts": dict(sorted(dimensions.items())), "error_count": len(errors), "errors": errors[:100]}


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
    keys = ("table_count", "component_count", "compatible_potential_checks", "component_cell_checks", "transform_checks", "inversion_checks", "parseval_checks", "error_count")
    totals = {key: sum(dataset[key] for dataset in datasets.values()) for key in keys}
    dimensions = Counter()
    for dataset in datasets.values():
        dimensions.update({int(d): count for d, count in dataset["exact_space_dimension_counts"].items()})
    totals["exact_space_dimension_counts"] = dict(sorted(dimensions.items()))
    payload = {"audit_version": "cellwise_holonomy_fourier_v1", "datasets": datasets, "totals": totals, "claim_boundary": ["C89 couples exact masks cellwise within one component.", "It is not a cross-component or order-10 obstruction.", "C38 remains open and C40 absent."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Cellwise holonomy Fourier audit", ""] + [f"{key.replace('_', ' ')}: {totals[key]}" for key in keys] + [f"exact-space dimensions: {totals['exact_space_dimension_counts']}", ""]
    for name, data in datasets.items():
        lines.extend([name, f"- tables/components: {data['table_count']} / {data['component_count']}", f"- component-cell checks: {data['component_cell_checks']}", f"- transform/inversion/Parseval: {data['transform_checks']} / {data['inversion_checks']} / {data['parseval_checks']}", f"- errors: {data['error_count']}", ""])
    lines.extend(["Boundary:", "- C89 is rigorous and exactly audited.", "- It is componentwise and does not decide order 10.", "- C38 remains open and C40 absent."])
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
