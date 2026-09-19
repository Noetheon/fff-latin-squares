#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "3e023c53194d6a60b24ad2f37e746b05b9d7e55c53dec8fcfe3cd8fb6cd09376"
REDUCED_NODES = 2514104197
REDUCED_PRUNES = 1769153203
CONTROL_NODES = 2514104197
CONTROL_PRUNES = 1769153203


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


def merge_comparison_valid(result: dict, tasks: int, nodes: int, prunes: int) -> bool:
    required = {
        "completed_tasks": tasks,
        "total_initial_tasks": tasks,
        "search_nodes": nodes,
        "crossview_odd_cycle_prunes": prunes,
        "fff_found": False,
        "negative_search_complete": True,
        "complete_disjoint_cover": True,
        "status": "complete_negative",
    }
    checks = result.get("checks", {})
    return (
        result.get("all_checks_passed") is True
        and all(checks.values())
        and all(result.get("values", {}).get(key) == value for key, value in required.items())
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    frozen = (REDUCED_NODES, REDUCED_PRUNES, CONTROL_NODES, CONTROL_PRUNES)
    if any(value is None for value in frozen):
        raise SystemExit("noninvolution master completion counts are not frozen yet")

    results = args.run / "results"
    inventory_results = args.run.parent / "2026-08-26_fff_six_type_master_inventory" / "results"
    structural = load(results / "noninvolution_graph_structural_audit.json")
    semantic = load(results / "noninvolution_graph_complete_audit.json")
    binding = load(results / "noninvolution_graph_audit_binding.json")
    orbit = load(results / "noninvolution_graph_root_orbit_audit.json")
    reduced_plan = load(results / "noninvolution_task_plan_reduced.json")
    control_plan = load(results / "noninvolution_task_plan_control.json")
    reduced = load(results / "noninvolution_reduced_merge.json")
    control = load(results / "noninvolution_control_merge.json")
    comparison = load(results / "noninvolution_reduced_control_comparison.json")
    validator_audit = load(results / "noninvolution_validator_fail_closed_audit.json")
    inventory = load(inventory_results / "master_inventory_binding.json")
    scratch_control = load(inventory_results / "incremental_scratch_search_control.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "noninvolution_task_ordinals.txt"

    checks = {
        "master_inventory_bound": inventory.get("all_checks_passed") is True
        and inventory["cases"]["noninvolution_master_6_types"]["triple_filtered_candidates"] == 172368
        and inventory["cases"]["noninvolution_master_6_types"]["root_task_count"] == 18300
        and inventory["cases"]["noninvolution_master_6_types"]["orbit_count"] == 386,
        "external_graph_hash_frozen": graph.is_file()
        and sha256(graph) == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 172368
        and structural.get("words") == 2694
        and structural.get("actual_size_bytes") == 3716598842,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 172368
        and semantic.get("independently_enumerated_vertices") == 172368
        and semantic.get("pairs_checked") == 14855277528
        and semantic.get("edges") == 1650487056,
        "semantic_errors_zero": all(
            semantic.get(key) == 0
            for key in (
                "candidate_list_errors", "edge_errors", "reverse_edge_errors",
                "format_errors", "diagonal_errors", "padding_errors",
                "canonical_root_errors",
            )
        ),
        "graph_audit_binding": binding.get("all_checks_passed") is True
        and binding.get("structural_audit_sha256") == sha256(results / "noninvolution_graph_structural_audit.json")
        and binding.get("semantic_audit_sha256") == sha256(results / "noninvolution_graph_complete_audit.json"),
        "orbit_cover_exact": orbit.get("valid") is True
        and all(orbit.get("checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256
        and orbit.get("full_initial_tasks") == 18300
        and orbit.get("orbit_count") == 386
        and orbit.get("orbit_size_counts") == {"12": 5, "24": 2, "48": 379}
        and orbit.get("covered_task_count") == 18300,
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == reduced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 386,
        "plans_bound": reduced_plan["graph"]["sha256"] == control_plan["graph"]["sha256"] == GRAPH_SHA256
        and reduced_plan["tasking"]["total_initial_tasks"] == 386
        and control_plan["tasking"]["total_initial_tasks"] == 386
        and reduced.get("plan_payload_sha256") == reduced_plan.get("plan_payload_sha256")
        and control.get("plan_payload_sha256") == control_plan.get("plan_payload_sha256"),
        "reduced_complete_negative": complete_negative(reduced, 386, REDUCED_NODES, REDUCED_PRUNES),
        "control_complete_negative": complete_negative(
            control, 386, CONTROL_NODES, CONTROL_PRUNES
        ),
        "reduced_control_exact_match": merge_comparison_valid(
            comparison, 386, REDUCED_NODES, REDUCED_PRUNES
        ),
        "search_implementation_bound": reduced.get("search_binary_sha256")
        == control.get("search_binary_sha256")
        == reduced_plan["search"]["binary_sha256"]
        == control_plan["search"]["binary_sha256"]
        and reduced.get("source_bundle_sha256")
        == control.get("source_bundle_sha256")
        == reduced_plan["search"]["source_bundle_sha256"]
        == control_plan["search"]["source_bundle_sha256"]
        and reduced_plan["search"]["sources"][0]["sha256"]
        == sha256(args.run / "scripts" / "search_partite_fff_incremental_scratch.cpp"),
        "incremental_scratch_positive_controls": scratch_control.get("all_checks_passed") is True
        and all(scratch_control.get("checks", {}).values()),
        "validator_fail_closed": validator_audit.get("all_checks_passed") is True
        and all(validator_audit.get("checks", {}).values()),
    }
    result = {
        "schema_version": "noninvolution-six-type-master-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "noninvolution_master_6_types",
            "palette": ["10", "4+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 172368,
            "edges": 1650487056,
            "orbits": 386,
            "full_tasks": 18300,
            "reduced_nodes": REDUCED_NODES,
            "control_nodes": CONTROL_NODES,
            "fff_found": False,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Noninvolution six-type master run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 172368/1650487056",
        "full tasks/orbits: 18300/386",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"noninvolution master validation failed: {failed}")


if __name__ == "__main__":
    main()
