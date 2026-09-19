#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "5198afaece05822dd7812e6a0408acf79648d5de7ff714c81e916544dd2d6828"
REDUCED_NODES = 5433616575
REDUCED_PRUNES = 3743909857
FULL_ROOT_NODES = 43244798259
FULL_ROOT_PRUNES = 29792601757
TRANSVERSAL_CLIQUE_COUNT = 32896
EXACT_PALETTE_CLIQUE_COUNT = 13504


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def complete_negative(result: dict, tasks: int, nodes: int, prunes: int) -> bool:
    return (
        result.get("status") == "complete_negative"
        and result.get("negative_search_complete") is True
        and result.get("complete_disjoint_cover") is True
        and result.get("completed_tasks") == tasks
        and result.get("total_initial_tasks") == tasks
        and result.get("search_nodes") == nodes
        and result.get("crossview_odd_cycle_prunes") == prunes
        and result.get("fff_found") is False
        and result.get("errors") == []
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    frozen_completion_counts = (
        REDUCED_NODES,
        REDUCED_PRUNES,
        FULL_ROOT_NODES,
        FULL_ROOT_PRUNES,
        TRANSVERSAL_CLIQUE_COUNT,
        EXACT_PALETTE_CLIQUE_COUNT,
    )
    if any(value is None for value in frozen_completion_counts):
        raise SystemExit("f15 completion counts are not frozen yet")
    results = args.run / "results"

    structural = load(results / "f15_structural_graph_audit.json")
    semantic = load(results / "f15_complete_graph_audit.json")
    binding = load(results / "f15_graph_audit_binding.json")
    source_audit = load(results / "f15_source_generalization_audit.json")
    orbit = load(results / "f15_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f15_task_plan_sliced.json")
    monolithic_plan = load(results / "f15_task_plan_monolithic.json")
    full_plan = load(results / "f15_task_plan_full_root_bucket_scratch.json")
    sliced = load(results / "f15_final_sliced_merge.json")
    monolithic = load(results / "f15_final_monolithic_merge.json")
    full = load(results / "f15_full_root_bucket_merge.json")
    prefix_equivalence = load(
        results / "f15_original_scratch_prefix_equivalence.json"
    )
    equivalence = load(results / "f15_sliced_monolithic_equivalence.json")
    independent = load(results / "f15_independent_binary_clique_binding.json")
    pattern_control = load(results / "f15_pattern_truth_table_audit.json")
    validator_audit = load(results / "f15_validator_fail_closed_audit.json")
    control_results = args.run.parent / "2026-08-26_fff_six_type_master_inventory" / "results"
    scratch_control = load(control_results / "incremental_scratch_search_control.json")
    scratch_benchmark = load(
        control_results / "incremental_scratch_f15_benchmark_binding.json"
    )
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f15_task_ordinals.txt"

    expected_orbit_sizes = {"2": 4, "8": 1868}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 145152
        and structural.get("words") == 2268
        and structural.get("actual_size_bytes") == 2635089434,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 145152
        and semantic.get("independently_enumerated_vertices") == 145152
        and semantic.get("pairs_checked") == 10534478976
        and semantic.get("edges") == 1129931264,
        "semantic_error_counts_zero": all(
            semantic.get(key) == 0
            for key in (
                "candidate_list_errors", "edge_errors", "reverse_edge_errors",
                "format_errors", "diagonal_errors", "padding_errors",
                "canonical_root_errors",
            )
        ),
        "graph_audit_binding": binding.get("all_checks_passed") is True
        and binding.get("structural_audit_sha256")
        == sha256(results / "f15_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f15_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 14952
        and orbit.get("orbit_count") == 1872
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 14952
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 1872,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(
            sliced, 1872, REDUCED_NODES, REDUCED_PRUNES
        ),
        "reduced_monolithic_complete_negative": complete_negative(
            monolithic, 1872, REDUCED_NODES, REDUCED_PRUNES
        ),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 14952,
        "full_root_bucket_complete_negative": complete_negative(
            full, 14952, FULL_ROOT_NODES, FULL_ROOT_PRUNES
        ),
        "original_scratch_prefix_equivalence": prefix_equivalence.get("valid") is True
        and prefix_equivalence.get("compared_slices") == 30
        and prefix_equivalence.get("compared_tasks") == 7500
        and prefix_equivalence.get("all_semantic_fields_match") is True
        and prefix_equivalence.get("all_task_graph_bindings_match") is True
        and prefix_equivalence.get("all_complete_negative") is True
        and prefix_equivalence.get("errors") == [],
        "incremental_scratch_controls": scratch_control.get("all_checks_passed") is True
        and all(scratch_control.get("checks", {}).values())
        and scratch_benchmark.get("all_checks_passed") is True
        and all(scratch_benchmark.get("checks", {}).values())
        and scratch_benchmark.get("speedup_old_over_incremental", 0) > 1,
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == sliced_plan["search"]["binary_sha256"]
        == monolithic_plan["search"]["binary_sha256"]
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == sliced_plan["search"]["source_bundle_sha256"]
        == monolithic_plan["search"]["source_bundle_sha256"]
        and full.get("search_binary_sha256") == full_plan["search"]["binary_sha256"]
        and full.get("source_bundle_sha256")
        == full_plan["search"]["source_bundle_sha256"]
        and full_plan["search"]["sources"][0]["sha256"]
        == sha256(args.run / "scripts" / "search_partite_fff_incremental_scratch.cpp"),
        "independent_binary_clique_audit": independent.get("all_checks_passed") is True
        and all(independent.get("checks", {}).values())
        and independent["files"]["f15_graph"]["sha256"] == GRAPH_SHA256
        and independent["files"]["f15_result"]["sha256"]
        == sha256(results / "f15_binary_clique_table_audit.json")
        and independent["files"]["source"]["sha256"]
        == sha256(args.run / "scripts" / "enumerate_binary_graph_clique_tables.cpp"),
        "all_pattern_truth_table_control": pattern_control.get("all_checks_passed") is True
        and set(pattern_control.get("expected_patterns", []))
        == {"FFF", "FFT", "FTF", "FTT", "TFF", "TFT", "TTF", "TTT"}
        and all(pattern_control.get("checks", {}).values()),
        "validator_fail_closed_audit": validator_audit.get("all_checks_passed") is True
        and sum(validator_audit.get("checks", {}).values()) == 10,
    }
    result = {
        "schema_version": "five-type-f15-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f15",
            "palette": ["10", "4+4+2", "6+2+2", "6+4", "8+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 145152,
            "edges": 1129931264,
            "orbits": 1872,
            "full_tasks": 14952,
            "reduced_nodes": REDUCED_NODES,
            "full_root_nodes": FULL_ROOT_NODES,
            "full_root_search": "incremental scratch bitset DFS",
            "fff_found": False,
            "transversal_clique_count": TRANSVERSAL_CLIQUE_COUNT,
            "exact_palette_clique_count": EXACT_PALETTE_CLIQUE_COUNT,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f15 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 145152/1129931264",
        "full tasks/orbits: 14952/1872",
        f"independent transversal 8-cliques: {TRANSVERSAL_CLIQUE_COUNT}",
        f"independent exact-palette cliques: {EXACT_PALETTE_CLIQUE_COUNT}",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f15 validation failed: {failed}")


if __name__ == "__main__":
    main()
