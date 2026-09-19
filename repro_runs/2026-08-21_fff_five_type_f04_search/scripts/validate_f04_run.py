#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "e3c41c65e3a3dcb7a14d2870ede2173b2ab39cfa57924f727a867287b70ed953"


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

    structural = load(results / "f04_structural_graph_audit.json")
    semantic = load(results / "f04_complete_graph_audit.json")
    binding = load(results / "f04_graph_audit_binding.json")
    source_audit = load(results / "f04_source_generalization_audit.json")
    orbit = load(results / "f04_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f04_task_plan_sliced.json")
    monolithic_plan = load(results / "f04_task_plan_monolithic.json")
    full_plan = load(results / "f04_task_plan_full_root_bucket.json")
    sliced = load(results / "f04_final_sliced_merge.json")
    monolithic = load(results / "f04_final_monolithic_merge.json")
    full = load(results / "f04_full_root_bucket_merge.json")
    equivalence = load(results / "f04_sliced_monolithic_equivalence.json")
    independent = load(results / "f04_independent_binary_clique_binding.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f04_task_ordinals.txt"

    expected_orbit_sizes = {"12": 6, "24": 2, "48": 180}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 70080
        and structural.get("words") == 1095
        and structural.get("actual_size_bytes") == 614601626,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 70080
        and semantic.get("independently_enumerated_vertices") == 70080
        and semantic.get("pairs_checked") == 2455568160
        and semantic.get("edges") == 171224640,
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
        == sha256(results / "f04_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f04_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 8760
        and orbit.get("orbit_count") == 188
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 8760
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 188,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(
            sliced, 188, 4150300, 1734075
        ),
        "reduced_monolithic_complete_negative": complete_negative(
            monolithic, 188, 4150300, 1734075
        ),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 8760,
        "full_root_bucket_complete_negative": complete_negative(
            full, 8760, 189231296, 78788328
        ),
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == full.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == full.get("source_bundle_sha256"),
        "independent_binary_clique_audit": independent.get("all_checks_passed") is True
        and all(independent.get("checks", {}).values())
        and independent["files"]["f04_graph"]["sha256"] == GRAPH_SHA256
        and independent["files"]["f04_result"]["sha256"]
        == sha256(results / "f04_binary_clique_table_audit.json")
        and independent["files"]["source"]["sha256"]
        == sha256(args.run / "scripts" / "enumerate_binary_graph_clique_tables.cpp"),
    }
    result = {
        "schema_version": "five-type-f04-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f04",
            "palette": ["10", "2+2+2+2+2", "4+2+2+2", "6+2+2", "6+4"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 70080,
            "edges": 171224640,
            "orbits": 188,
            "full_tasks": 8760,
            "reduced_nodes": 4150300,
            "full_root_nodes": 189231296,
            "fff_found": False,
            "transversal_clique_count": 0,
            "exact_palette_clique_count": 0,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f04 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 70080/171224640",
        "full tasks/orbits: 8760/188",
        "reduced/full-root nodes: 4150300/189231296",
        "independent transversal 8-cliques: 0",
        "independent exact-palette cliques: 0",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f04 validation failed: {failed}")


if __name__ == "__main__":
    main()
