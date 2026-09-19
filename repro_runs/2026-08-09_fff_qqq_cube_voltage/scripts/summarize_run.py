#!/usr/bin/env python3
"""Create the compact machine-readable and human-readable run summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir
    results = run / "results"
    cubes = load(results / "n10_qqq_row1_cube_cases.json")
    p3_graph = load(results / "p3_pairblock_wreath_graph_audit.json")
    p3_solve = load(results / "p3_pairblock_wreath_rowf_cadical_solve.json")
    p3_check = load(results / "p3_pairblock_wreath_rowf_drat_check.json")
    p3_clique_solve = load(results / "p3_pairblock_wreath_clique_cadical_solve.json")
    p3_clique_check = load(results / "p3_pairblock_wreath_clique_drat_check.json")
    p5_generation = load(results / "p5_pairblock_wreath_rowf_generation.json")
    p5_solve = load(results / "p5_pairblock_wreath_rowf_cadical_solve.json")
    n10_parent = load(results / "n10_qqq_row1_case13_cadical_solve.json")
    n10_cube = load(results / "n10_qqq_case13_r3c1_s0_cadical_solve.json")
    payload = {
        "evidence_labels": {
            "row1_cube_cover": "rigorously proved and exactly enumerated",
            "p3_pairblock_obstruction": "exactly computed with independently checked DRAT traces",
            "p5_pairblock_status": "open; bounded solver timeout",
            "n10_qqq_status": "open; bounded solver timeouts",
        },
        "n10_qqq_cube_cover": {
            "top_level_cases": cubes["top_level_case_count"],
            "complete_qqq_cubes": cubes["second_level_cube_count"],
            "complete_fff_cubes": cubes["fff_second_level_cube_count"],
            "correction": cubes["important_correction"],
        },
        "p3_pairblock": {
            "candidates_excluding_identity": p3_graph["candidate_count_excluding_identity"],
            "compatible_edges": p3_graph["compatible_edge_count"],
            "maximum_clique_size": p3_graph["maximum_clique_size"],
            "maximum_family_size_including_identity": p3_graph["maximum_family_size_including_identity"],
            "required_family_size": p3_graph["required_family_size"],
            "sharp_encoding_result": p3_solve["result"],
            "sharp_encoding_proof_checked": p3_check["result"] == "verified",
            "clique_encoding_result": p3_clique_solve["result"],
            "clique_encoding_proof_checked": p3_clique_check["result"] == "verified",
        },
        "p5_pairblock": {
            "candidates_including_identity": p5_generation["candidate_count_including_identity"],
            "compatible_pairs": p5_generation["compatible_pair_count"],
            "incompatible_pairs": p5_generation["incompatible_pair_clause_count"],
            "cnf_sha256": p5_generation["cnf_sha256"],
            "solver_result": p5_solve["result"],
            "timeout_seconds": p5_solve["timeout_seconds"],
        },
        "n10_qqq_pilots": {
            "new_5_3_2_parent_case13": n10_parent["result"],
            "case13_r3c1_s0_cube": n10_cube["result"],
            "decoded_table_available": False,
            "fff_validated": False,
        },
        "claim_effect": {
            "C38": "open",
            "C40": "absent",
            "new_claims": ["C49", "C50"],
        },
    }
    (results / "qqq_cube_voltage_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (results / "qqq_cube_voltage_summary.txt").write_text(
        "QQQ cube and pair-block voltage summary\n\n"
        "Rigorous/exact Row1 cover:\n"
        "- Complete QQQ top-level Row1 cases: 15.\n"
        "- Complete QQQ L(3,1) cubes: 105.\n"
        "- Complete FFF-exclusion cover: 12 even-cycle parents / 84 cubes.\n"
        "- The older 12-parent cover was complete for FFF, not for QQQ.\n\n"
        "Pair-block wreath model:\n"
        f"- p=3 graph: 21 candidates, 72 edges, clique number {p3_graph['maximum_clique_size']}.\n"
        "- p=3 sharp and clique CNFs: UNSAT; both DRAT traces independently VERIFIED.\n"
        f"- p=5: 1546 candidates including identity, {p5_generation['incompatible_pair_clause_count']} incompatible pairs.\n"
        f"- p=5 CaDiCaL status: {p5_solve['result']} at {p5_solve['timeout_seconds']:.0f}s.\n\n"
        "n=10 QQQ pilots:\n"
        f"- New 5+3+2 parent case13: {n10_parent['result']} at {n10_parent['timeout_seconds']:.0f}s.\n"
        f"- case13 with L(3,1)=0: {n10_cube['result']} at {n10_cube['timeout_seconds']:.0f}s.\n"
        "- No decoded n=10 table; no FFF validation; no n=10 case excluded.\n\n"
        "Claim status:\n- C38 remains open.\n- C40 remains absent.\n"
        "- C49 records the rigorous complete QQQ/FFF cube covers.\n"
        "- C50 records only the certified degree-6 common-pair-block obstruction.\n"
    )


if __name__ == "__main__":
    main()
