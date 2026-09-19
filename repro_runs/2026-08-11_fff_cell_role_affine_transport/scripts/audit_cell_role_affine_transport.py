#!/usr/bin/env python3
"""Audit C90 affine transport of role-resolved holonomy labels."""

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
    role_transport_checks = equal_role_checks = delta_invariance_checks = divisibility_checks = 0
    delta_nonzero_cells = orientable_cells = 0
    incidence_distribution = Counter()

    for component_id, component in enumerate(components):
        exact_masks = [m for m in range(8) if HOL["exact_mask_on_component"](component, alphas, m)]
        basis = HOL["binary_basis"](exact_masks)
        d = len(basis)
        potentials = [HOL["mask_potential_on_component"](component, alphas, mask) for mask in basis]
        labels = {flag: sum(potentials[i][flag] << i for i in range(d)) for flag in component}
        shifts = [sum(((mask >> view) & 1) << i for i, mask in enumerate(basis)) for view in range(3)]
        delta = shifts[0] ^ shifts[1] ^ shifts[2]
        orientable = 7 in exact_masks
        cells = defaultdict(lambda: [[0] * (1 << d) for _ in range(3)])
        for flag in component:
            for role, cell in enumerate(flags[flag]["cells"]):
                cells[cell][role][labels[flag]] += 1
        for cell, counts in cells.items():
            totals = [sum(role_counts) for role_counts in counts]
            equal_role_checks += 1
            if len(set(totals)) != 1:
                errors.append(["equal_role_totals", component_id, cell, totals])
            incidence_distribution[sum(totals)] += 1
            for a in range(1 << d):
                tests = (
                    (counts[2][a ^ shifts[0]], counts[0][a], 0),
                    (counts[2][a ^ shifts[1]], counts[1][a], 1),
                    (counts[1][a ^ shifts[2]], counts[0][a], 2),
                )
                for left, right, view in tests:
                    role_transport_checks += 1
                    if left != right:
                        errors.append(["role_transport", component_id, cell, a, view, left, right, shifts])
                delta_invariance_checks += 1
                if counts[0][a ^ delta] != counts[0][a]:
                    errors.append(["delta_invariance", component_id, cell, a, delta, counts[0]])
            divisibility_checks += 1
            if delta:
                delta_nonzero_cells += 1
                if totals[0] % 2 or sum(totals) % 6:
                    errors.append(["delta_divisibility", component_id, cell, delta, totals])
            if orientable:
                orientable_cells += 1
                if not delta or sum(totals) % 6:
                    errors.append(["orientable_divisibility", component_id, cell, delta, totals])
    return {"source_index": source_index, "order": len(table), "component_count": len(components), "role_transport_checks": role_transport_checks, "equal_role_checks": equal_role_checks, "delta_invariance_checks": delta_invariance_checks, "divisibility_checks": divisibility_checks, "delta_nonzero_cells": delta_nonzero_cells, "orientable_cells": orientable_cells, "incidence_distribution": dict(sorted(incidence_distribution.items())), "errors": errors}

def summarize(name: str, records: list[dict]) -> dict:
    dist = Counter()
    for record in records:
        dist.update({int(k): v for k, v in record["incidence_distribution"].items()})
    errors = [[record["source_index"], error] for record in records for error in record["errors"]]
    keys = ("component_count", "role_transport_checks", "equal_role_checks", "delta_invariance_checks", "divisibility_checks", "delta_nonzero_cells", "orientable_cells")
    return {"name": name, "table_count": len(records), **{key: sum(r[key] for r in records) for key in keys}, "incidence_distribution": dict(sorted(dist.items())), "error_count": len(errors), "errors": errors[:100]}

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
    keys = ("table_count", "component_count", "role_transport_checks", "equal_role_checks", "delta_invariance_checks", "divisibility_checks", "delta_nonzero_cells", "orientable_cells", "error_count")
    totals = {key: sum(data[key] for data in datasets.values()) for key in keys}
    dist = Counter()
    for data in datasets.values():
        dist.update({int(k): v for k, v in data["incidence_distribution"].items()})
    totals["incidence_distribution"] = dict(sorted(dist.items()))
    payload = {"audit_version": "cell_role_affine_transport_v1", "datasets": datasets, "totals": totals, "claim_boundary": ["C90 is rigorous and componentwise.", "It does not decide order 10.", "C38 remains open and C40 absent."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Cell-role affine transport audit", ""] + [f"{key.replace('_', ' ')}: {totals[key]}" for key in keys] + [f"incidence distribution: {totals['incidence_distribution']}", ""]
    for name, data in datasets.items():
        lines.extend([name, f"- tables/components: {data['table_count']} / {data['component_count']}", f"- role transports: {data['role_transport_checks']}", f"- delta-nonzero/orientable cells: {data['delta_nonzero_cells']} / {data['orientable_cells']}", f"- errors: {data['error_count']}", ""])
    lines.extend(["Boundary:", "- C90 is rigorous and exactly audited.", "- It remains componentwise and does not decide order 10.", "- C38 remains open and C40 absent."])
    args.summary.write_text("\n".join(lines) + "\n")
    return int(totals["error_count"] != 0)

if __name__ == "__main__":
    raise SystemExit(main())
