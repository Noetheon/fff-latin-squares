#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--historical-p35", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    results = args.run / "results"
    historical = load(args.historical_p35)
    p35_structural = load(results / "p35_structural_graph_audit.json")
    p35_semantic = load(results / "p35_complete_graph_audit.json")
    p35_binding = load(results / "p35_graph_audit_binding.json")
    p35_merge = load(results / "p35_final_slice_merge_w8.json")
    p35_worker_equivalence = load(results / "p35_final_worker_equivalence.json")
    p09_structural = load(results / "p09_involution_root_structural_graph_audit.json")
    p09_semantic = load(results / "p09_involution_root_complete_graph_audit.json")
    p09_binding = load(results / "p09_involution_root_graph_audit_binding.json")
    p09_orbits = load(results / "p09_involution_root_orbit_audit.json")
    p09_sliced = load(results / "p09_final_bound_sliced_merge.json")
    p09_monolithic = load(results / "p09_final_bound_monolithic_merge.json")
    p09_equivalence = load(results / "p09_sliced_monolithic_equivalence.json")
    negative_tests = load(results / "workflow_negative_tests.json")

    p35_expected = {
        "completed_tasks": 3656,
        "search_nodes": 22449129,
        "crossview_odd_cycle_prunes": 8399725,
        "fff_found": False,
    }
    p09_expected = {
        "completed_tasks": 260,
        "search_nodes": 57708321,
        "crossview_odd_cycle_prunes": 32587444,
        "fff_found": False,
    }
    checks = {
        "p35_graph_hash_historical": p35_structural.get("graph_sha256")
        == "e1d9db20dd6fd9e8468d9069c32357d80dd49c3721ea3fa19611d97e716751ef",
        "p35_structural_valid": p35_structural.get("valid") is True,
        "p35_semantic_valid": p35_semantic.get("valid") is True,
        "p35_binding_valid": p35_binding.get("all_checks_passed") is True,
        "p35_merge_complete": p35_merge.get("negative_search_complete") is True,
        "p35_worker_equivalence": p35_worker_equivalence.get("all_checks_passed") is True,
        "p35_exact_counts": all(p35_merge.get(key) == value for key, value in p35_expected.items()),
        "p35_historical_counts": all(historical.get(key) == value for key, value in p35_expected.items()),
        "p09_graph_hash_frozen": p09_structural.get("graph_sha256")
        == "5277ec91414b304bcb2078dc4d1566029f6aba7674c44458cf6a706a764a5873",
        "p09_structural_valid": p09_structural.get("valid") is True,
        "p09_semantic_valid": p09_semantic.get("valid") is True,
        "p09_binding_valid": p09_binding.get("all_checks_passed") is True,
        "p09_orbit_cover_valid": p09_orbits.get("valid") is True
        and p09_orbits.get("full_initial_task_count") == 12480
        and p09_orbits.get("orbit_count") == 260
        and p09_orbits.get("covered_task_count") == 12480,
        "p09_sliced_complete": p09_sliced.get("negative_search_complete") is True,
        "p09_monolithic_complete": p09_monolithic.get("negative_search_complete") is True,
        "p09_exact_counts": all(p09_sliced.get(key) == value for key, value in p09_expected.items()),
        "p09_sliced_monolithic_equal": p09_equivalence.get("all_checks_passed") is True,
        "negative_tests_pass": negative_tests.get("all_checks_passed") is True,
    }
    result = {
        "schema_version": "four-type-large-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "p35": p35_expected,
        "p09": {
            **p09_expected,
            "graph_vertices": p09_semantic["stored_vertices"],
            "graph_edges": p09_semantic["edges"],
            "graph_pairs_audited": p09_semantic["pairs_checked"],
            "full_initial_tasks": p09_orbits["full_initial_task_count"],
            "orbit_representatives": p09_orbits["orbit_count"],
        },
        "evidence_sha256": {
            name: sha256(results / name) for name in (
                "p09_involution_root_graph_audit_binding.json",
                "p09_involution_root_orbit_audit.json",
                "p09_final_bound_sliced_merge.json",
                "p09_final_bound_monolithic_merge.json",
            )
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Four-type large-search validation",
        "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"p35 exact historical control: {str(checks['p35_exact_counts'] and checks['p35_historical_counts']).lower()}",
        f"p09 graph pairs/edges: {p09_semantic['pairs_checked']}/{p09_semantic['edges']}",
        f"p09 full tasks/orbits: {p09_orbits['full_initial_task_count']}/{p09_orbits['orbit_count']}",
        f"p09 nodes/prunes: {p09_sliced['search_nodes']}/{p09_sliced['crossview_odd_cycle_prunes']}",
        f"p09 FFF found: {str(p09_sliced['fff_found']).lower()}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("run validation failed")


if __name__ == "__main__":
    main()
