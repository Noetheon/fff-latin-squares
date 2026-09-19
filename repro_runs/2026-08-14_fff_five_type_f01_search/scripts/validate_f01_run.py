#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "6360189d6f4dc2e5730884b51e1662715cb48be0321593a0f86ed0eb60ed98af"
DIMACS_SHA256 = "be4fb91894d0eef43d7832e69a3454c0eecf3669720b8e7ccf9f0592831f455a"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def complete_negative(result: dict, tasks: int, nodes: int) -> bool:
    return (
        result.get("status") == "complete_negative"
        and result.get("negative_search_complete") is True
        and result.get("complete_disjoint_cover") is True
        and result.get("completed_tasks") == tasks
        and result.get("total_initial_tasks") == tasks
        and result.get("search_nodes") == nodes
        and result.get("crossview_odd_cycle_prunes") == 0
        and result.get("fff_found") is False
        and result.get("errors") == []
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    results = args.run / "results"

    structural = load(results / "f01_structural_graph_audit.json")
    semantic = load(results / "f01_complete_graph_audit.json")
    binding = load(results / "f01_graph_audit_binding.json")
    source_audit = load(results / "f01_source_generalization_audit.json")
    orbit = load(results / "f01_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f01_task_plan_sliced.json")
    monolithic_plan = load(results / "f01_task_plan_monolithic.json")
    full_plan = load(results / "f01_task_plan_full_root_bucket.json")
    sliced = load(results / "f01_final_sliced_merge.json")
    monolithic = load(results / "f01_final_monolithic_merge.json")
    full = load(results / "f01_full_root_bucket_merge.json")
    equivalence = load(results / "f01_sliced_monolithic_equivalence.json")
    cliquer = load(results / "f01_cliquer_check.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f01_task_ordinals.txt"

    expected_orbit_sizes = {"12": 6, "24": 2, "48": 20}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 8640
        and structural.get("words") == 135
        and structural.get("actual_size_bytes") == 9417626,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 8640
        and semantic.get("independently_enumerated_vertices") == 8640
        and semantic.get("pairs_checked") == 37320480
        and semantic.get("edges") == 3163200,
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
        == sha256(results / "f01_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f01_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 1080
        and orbit.get("orbit_count") == 28
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 1080
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 28,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(sliced, 28, 1408),
        "reduced_monolithic_complete_negative": complete_negative(monolithic, 28, 1408),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 1080,
        "full_root_bucket_complete_negative": complete_negative(full, 1080, 53928),
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == full.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == full.get("source_bundle_sha256"),
        "independent_cliquer_negative": cliquer.get("valid") is True
        and cliquer.get("result") == "no_clique_of_size_8"
        and cliquer.get("requested_clique_size") == 8
        and cliquer["files"]["graph"]["sha256"] == GRAPH_SHA256
        and cliquer["files"]["dimacs"]["sha256"] == DIMACS_SHA256
        and cliquer["files"]["stdout"]["sha256"]
        == sha256(results / "f01_cliquer.stdout")
        and cliquer["files"]["stderr"]["sha256"]
        == sha256(results / "f01_cliquer.stderr"),
    }
    result = {
        "schema_version": "five-type-f01-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f01",
            "palette": ["10", "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 8640,
            "edges": 3163200,
            "orbits": 28,
            "full_tasks": 1080,
            "reduced_nodes": 1408,
            "full_root_nodes": 53928,
            "fff_found": False,
            "clique_size_8_found": False,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f01 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 8640/3163200",
        "full tasks/orbits: 1080/28",
        "reduced/full-root nodes: 1408/53928",
        "independent 8-clique found: false",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f01 validation failed: {failed}")


if __name__ == "__main__":
    main()
