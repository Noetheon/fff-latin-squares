#!/usr/bin/env python3
"""Summarize the certified p=3/p=5 projection-voltage computation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    r = args.results
    p3_gen = load(r / "p3_projection_generation.json")
    p3_solve = load(r / "p3_projection_solve.json")
    p3_check = load(r / "p3_projection_drat_check.json")
    p5_gen = load(r / "p5_projection_generation.json")
    p5_solve = load(r / "p5_projection_solve.json")
    p5_check = load(r / "p5_projection_drat_check.json")
    p5_kissat = load(r / "p5_projection_kissat_solve.json")
    p5_cp1 = load(r / "p5_projection_cpsat_crosscheck.json")
    p5_cp8 = load(r / "p5_projection_cpsat8_crosscheck.json")
    triangle_gen = load(r / "p5_projection_triangle_generation.json")
    triangle_solve = load(r / "p5_projection_triangle_solve.json")
    triangle_check = load(r / "p5_projection_triangle_drat_check.json")
    three_gen = load(r / "p5_projection_three_class_generation.json")
    three_solve = load(r / "p5_projection_three_class_solve.json")
    three_check = load(r / "p5_projection_three_class_drat_check.json")
    payload = {
        "theorem_boundary": {
            "projection_injectivity": "rigorously proved",
            "p3_pairblock_row_f": "unsat with independently checked DRAT",
            "p5_pairblock_row_f": "unsat with independently checked DRAT",
            "degree10_one_view_primitivity": "proof-checked computational consequence plus rigorous block-size-5 lemma",
            "full_n10_fff": "open",
        },
        "p3": {
            "variables": p3_gen["variables"],
            "clauses": p3_gen["clauses"],
            "cadical_result": p3_solve["result"],
            "proof_checked": p3_check["result"],
        },
        "p5": {
            "variables": p5_gen["variables"],
            "clauses": p5_gen["clauses"],
            "cnf_sha256": p5_gen["cnf_sha256"],
            "cadical_result": p5_solve["result"],
            "cadical_seconds": p5_solve["elapsed_seconds"],
            "kissat_result": p5_kissat["result"],
            "kissat_seconds": p5_kissat["elapsed_seconds"],
            "proof_checked": p5_check["result"],
            "proof_sha256": p5_check["proof"]["sha256"],
            "cpsat_one_worker": p5_cp1["result"],
            "cpsat_eight_workers": p5_cp8["result"],
            "compact_triangle_classification": {
                "variables": triangle_gen["variables"],
                "clauses": triangle_gen["clauses"],
                "global_odd_cycle_forbidden_triangles": triangle_gen[
                    "global_odd_cycle_forbidden_triangles"
                ],
                "common_three_cycle_forbidden_triangles_total": triangle_gen[
                    "common_three_cycle_forbidden_triangles_total"
                ],
                "forbidden_triangle_overlap": triangle_gen["forbidden_triangle_overlap"],
                "all_forbidden_triangle_union": triangle_gen["all_forbidden_triangle_union"],
                "selected_forbidden_triangle_union": triangle_gen[
                    "selected_forbidden_triangle_union"
                ],
                "cnf_sha256": triangle_gen["cnf_sha256"],
                "cadical_result": triangle_solve["result"],
                "cadical_seconds": triangle_solve["elapsed_seconds"],
                "proof_checked": triangle_check["result"],
                "proof_sha256": triangle_check["proof"]["sha256"],
            },
            "three_class_triangle_classification": {
                "variables": three_gen["variables"],
                "clauses": three_gen["clauses"],
                "selected_three_class_counts": three_gen["selected_three_class_counts"],
                "selected_forbidden_triangle_union": three_gen[
                    "selected_forbidden_triangle_union"
                ],
                "cnf_sha256": three_gen["cnf_sha256"],
                "cadical_result": three_solve["result"],
                "cadical_seconds": three_solve["elapsed_seconds"],
                "proof_checked": three_check["result"],
                "proof_sha256": three_check["proof"]["sha256"],
            },
        },
        "claim_effect": {
            "C58": "rigorous",
            "C59": "A+B checked",
            "C61": "A+B checked finite classification",
            "C62": "A+B checked three-class strengthening",
            "C38": "open",
            "C40": "absent",
        },
        "scope_warning": "One-view normalized primitivity is not a full n=10 FFF existence or nonexistence result.",
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Pair-block projection-voltage result\n\n"
        "Projection injectivity: rigorously proved\n"
        f"p=3: {p3_solve['result'].upper()}, DRAT {p3_check['result'].upper()}\n"
        f"p=5 formula: {p5_gen['variables']} variables, {p5_gen['clauses']} clauses\n"
        f"p=5 CaDiCaL: {p5_solve['result'].upper()} in {p5_solve['elapsed_seconds']:.6f}s\n"
        f"p=5 Kissat: {p5_kissat['result'].upper()} in {p5_kissat['elapsed_seconds']:.6f}s\n"
        f"p=5 DRAT: {p5_check['result'].upper()}\n"
        "Compact p=5 projection classification: "
        f"{triangle_gen['variables']} variables, {triangle_gen['clauses']} clauses; "
        f"CaDiCaL {triangle_solve['result'].upper()} in {triangle_solve['elapsed_seconds']:.6f}s; "
        f"DRAT {triangle_check['result'].upper()}\n"
        "Three-class strengthening: "
        f"{three_gen['variables']} variables, {three_gen['clauses']} clauses; "
        f"{three_gen['selected_forbidden_triangle_union']} selected triples; "
        f"CaDiCaL {three_solve['result'].upper()} in {three_solve['elapsed_seconds']:.6f}s; "
        f"DRAT {three_check['result'].upper()}\n"
        "Consequence: every normalized row-F, col-F, or sym-F family of degree 10 preserves no nontrivial block system\n"
        "Scope: one-view primitivity only; n=10 FFF remains open\n"
        "C38: open\nC40: absent\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
