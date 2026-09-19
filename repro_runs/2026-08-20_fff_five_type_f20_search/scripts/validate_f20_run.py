#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "a6a744038dd1cde7372214f9bc0f373aba32af8fdd37b8ba3b70bd1beca31282"


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
    results = args.run / "results"

    structural = load(results / "f20_structural_graph_audit.json")
    semantic = load(results / "f20_complete_graph_audit.json")
    binding = load(results / "f20_graph_audit_binding.json")
    source_audit = load(results / "f20_source_generalization_audit.json")
    orbit = load(results / "f20_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f20_task_plan_sliced.json")
    monolithic_plan = load(results / "f20_task_plan_monolithic.json")
    full_plan = load(results / "f20_task_plan_full_root_bucket.json")
    sliced = load(results / "f20_final_sliced_merge.json")
    monolithic = load(results / "f20_final_monolithic_merge.json")
    full = load(results / "f20_full_root_bucket_merge.json")
    equivalence = load(results / "f20_sliced_monolithic_equivalence.json")
    independent = load(results / "f20_independent_binary_clique_binding.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f20_task_ordinals.txt"

    expected_orbit_sizes = {"12": 6, "24": 2, "48": 130}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 50880
        and structural.get("words") == 795
        and structural.get("actual_size_bytes") == 324105626,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 50880
        and semantic.get("independently_enumerated_vertices") == 50880
        and semantic.get("pairs_checked") == 1294361760
        and semantic.get("edges") == 95413440,
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
        == sha256(results / "f20_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f20_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 6360
        and orbit.get("orbit_count") == 138
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 6360
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 138,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(sliced, 138, 2084371, 880583),
        "reduced_monolithic_complete_negative": complete_negative(monolithic, 138, 2084371, 880583),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 6360,
        "full_root_bucket_complete_negative": complete_negative(full, 6360, 94079536, 39479984),
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == full.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == full.get("source_bundle_sha256"),
        "independent_binary_clique_audit": independent.get("all_checks_passed") is True
        and all(independent.get("checks", {}).values())
        and independent["files"]["f20_graph"]["sha256"] == GRAPH_SHA256
        and independent["files"]["f20_result"]["sha256"]
        == sha256(results / "f20_binary_clique_table_audit.json")
        and independent["files"]["source"]["sha256"]
        == sha256(args.run / "scripts" / "enumerate_binary_graph_clique_tables.cpp"),
    }
    result = {
        "schema_version": "five-type-f20-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f20",
            "palette": ["2+2+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 50880,
            "edges": 95413440,
            "orbits": 138,
            "full_tasks": 6360,
            "reduced_nodes": 2084371,
            "full_root_nodes": 94079536,
            "fff_found": False,
            "transversal_clique_count": 23040,
            "exact_palette_clique_count": 19200,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f20 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 50880/95413440",
        "full tasks/orbits: 6360/138",
        "reduced/full-root nodes: 2084371/94079536",
        "independent transversal 8-cliques: 23040",
        "independent exact-palette cliques: 19200",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f20 validation failed: {failed}")


if __name__ == "__main__":
    main()
