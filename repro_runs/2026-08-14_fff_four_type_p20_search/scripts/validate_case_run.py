#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


COMMON_SCRIPTS = (
    "audit_complete_four_type_candidate_graph.cpp",
    "audit_graph_structure.py",
    "bind_graph_audits.py",
    "build_filtered_four_type_candidate_graph.cpp",
    "compare_search_merges.py",
    "create_task_plan.py",
    "merge_task_slices.py",
    "partial_cycle.hpp",
    "run_task_plan.py",
    "search_partite_fff.cpp",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--graph-sha256", required=True)
    parser.add_argument("--vertices", type=int, required=True)
    parser.add_argument("--pairs", type=int, required=True)
    parser.add_argument("--edges", type=int, required=True)
    parser.add_argument("--full-tasks", type=int, required=True)
    parser.add_argument("--orbits", type=int, required=True)
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--prunes", type=int, required=True)
    parser.add_argument("--reference-scripts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    r = args.run / "results"
    prefix = args.case
    structural = load(r / f"{prefix}_structural_graph_audit.json")
    semantic = load(r / f"{prefix}_complete_graph_audit.json")
    binding = load(r / f"{prefix}_graph_audit_binding.json")
    orbits = load(r / f"{prefix}_graph_root_orbit_audit.json")
    sliced_plan_path = r / f"{prefix}_task_plan_sliced.json"
    monolithic_plan_path = r / f"{prefix}_task_plan_monolithic.json"
    sliced_plan = load(sliced_plan_path)
    monolithic_plan = load(monolithic_plan_path)
    sliced = load(r / f"{prefix}_final_sliced_merge.json")
    monolithic = load(r / f"{prefix}_final_monolithic_merge.json")
    equivalence = load(r / f"{prefix}_sliced_monolithic_equivalence.json")
    graph_path = Path(binding["graph_path"])
    task_file = args.run / "data" / f"{prefix}_task_ordinals.txt"
    source_matches = {
        name: sha256(args.run / "scripts" / name)
        == sha256(args.reference_scripts / name)
        for name in COMMON_SCRIPTS
    }
    checks = {
        "common_sources_match_hardened_c125": all(source_matches.values()),
        "structural_valid": structural.get("valid") is True,
        "graph_hash_frozen": graph_path.is_file()
        and sha256(graph_path) == args.graph_sha256
        and structural.get("graph_sha256") == args.graph_sha256
        and binding.get("graph_sha256") == args.graph_sha256,
        "semantic_valid": semantic.get("valid") is True,
        "graph_counts_exact": semantic.get("stored_vertices") == args.vertices
        and semantic.get("pairs_checked") == args.pairs
        and semantic.get("edges") == args.edges,
        "all_graph_error_counts_zero": all(semantic.get(key) == 0 for key in (
            "candidate_list_errors", "edge_errors", "reverse_edge_errors",
            "format_errors", "diagonal_errors", "padding_errors",
        )),
        "graph_audit_binding_valid": binding.get("all_checks_passed") is True,
        "audit_hash_bindings_exact":
        binding.get("structural_audit_sha256")
        == sha256(r / f"{prefix}_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(r / f"{prefix}_complete_graph_audit.json"),
        "orbit_cover_valid": orbits.get("valid") is True
        and orbits.get("full_initial_task_count") == args.full_tasks
        and orbits.get("orbit_count") == args.orbits
        and orbits.get("covered_task_count") == args.full_tasks
        and sum(int(size) * count for size, count in orbits.get("orbit_size_counts", {}).items())
        == args.full_tasks,
        "task_file_bound": task_file.is_file()
        and sha256(task_file)
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == args.orbits,
        "plan_bindings_exact":
        sliced.get("plan_payload_sha256") == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256") == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == args.graph_sha256
        and sliced_plan["search"]["source_bundle_sha256"]
        == monolithic_plan["search"]["source_bundle_sha256"]
        == sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256"),
        "sliced_complete_negative": sliced.get("negative_search_complete") is True
        and sliced.get("complete_disjoint_cover") is True
        and sliced.get("errors") == [],
        "monolithic_complete_negative": monolithic.get("negative_search_complete") is True
        and monolithic.get("complete_disjoint_cover") is True
        and monolithic.get("errors") == [],
        "search_counts_exact": sliced.get("completed_tasks") == args.orbits
        and sliced.get("search_nodes") == args.nodes
        and sliced.get("crossview_odd_cycle_prunes") == args.prunes
        and sliced.get("fff_found") is False
        and monolithic.get("completed_tasks") == args.orbits
        and monolithic.get("search_nodes") == args.nodes
        and monolithic.get("crossview_odd_cycle_prunes") == args.prunes
        and monolithic.get("fff_found") is False,
        "search_decompositions_equal": equivalence.get("all_checks_passed") is True
        and sliced.get("graph_sha256") == monolithic.get("graph_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256")
        and sliced.get("task_file_sha256") == monolithic.get("task_file_sha256")
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256"),
    }
    result = {
        "schema_version": "four-type-case-run-validation-v1",
        "case_id": args.case,
        "checks": checks,
        "source_matches": source_matches,
        "reference_scripts": str(args.reference_scripts.resolve()),
        "graph_path": str(graph_path),
        "sliced_plan_sha256": sha256(sliced_plan_path),
        "monolithic_plan_sha256": sha256(monolithic_plan_path),
        "task_file_sha256": sha256(task_file),
        "all_checks_passed": all(checks.values()),
        "result": {
            "graph_sha256": args.graph_sha256,
            "vertices": args.vertices,
            "pairs": args.pairs,
            "edges": args.edges,
            "full_tasks": args.full_tasks,
            "orbits": args.orbits,
            "nodes": args.nodes,
            "prunes": args.prunes,
            "fff_found": False,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        f"Four-type {args.case} run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"graph pairs/edges: {args.pairs}/{args.edges}",
        f"full tasks/orbits: {args.full_tasks}/{args.orbits}",
        f"nodes/prunes: {args.nodes}/{args.prunes}",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("case validation failed")


if __name__ == "__main__":
    main()
