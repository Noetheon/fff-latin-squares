#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "7ac03b6431e39070b334c3d8cfd4a12b58180226f5e0319c175547ebca1ac5c4"


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

    structural = load(results / "f05_structural_graph_audit.json")
    semantic = load(results / "f05_complete_graph_audit.json")
    binding = load(results / "f05_graph_audit_binding.json")
    source_audit = load(results / "f05_source_generalization_audit.json")
    orbit = load(results / "f05_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f05_task_plan_sliced.json")
    monolithic_plan = load(results / "f05_task_plan_monolithic.json")
    full_plan = load(results / "f05_task_plan_full_root_bucket.json")
    sliced = load(results / "f05_final_sliced_merge.json")
    monolithic = load(results / "f05_final_monolithic_merge.json")
    full = load(results / "f05_full_root_bucket_merge.json")
    equivalence = load(results / "f05_sliced_monolithic_equivalence.json")
    independent = load(results / "f05_independent_binary_clique_binding.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f05_task_ordinals.txt"

    expected_orbit_sizes = {"12": 3, "48": 247}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 111504
        and structural.get("words") == 1743
        and structural.get("actual_size_bytes") == 1555926842,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 111504
        and semantic.get("independently_enumerated_vertices") == 111504
        and semantic.get("pairs_checked") == 6216515256
        and semantic.get("edges") == 519519120,
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
        == sha256(results / "f05_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f05_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 11892
        and orbit.get("orbit_count") == 250
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 11892
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 250,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(
            sliced, 250, 77581245, 43919752
        ),
        "reduced_monolithic_complete_negative": complete_negative(
            monolithic, 250, 77581245, 43919752
        ),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 11892,
        "full_root_bucket_complete_negative": complete_negative(
            full, 11892, 3648558242, 2064511150
        ),
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == full.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == full.get("source_bundle_sha256"),
        "independent_binary_clique_audit": independent.get("all_checks_passed") is True
        and all(independent.get("checks", {}).values())
        and independent["files"]["f05_graph"]["sha256"] == GRAPH_SHA256
        and independent["files"]["f05_result"]["sha256"]
        == sha256(results / "f05_binary_clique_table_audit.json")
        and independent["files"]["source"]["sha256"]
        == sha256(args.run / "scripts" / "enumerate_binary_graph_clique_tables.cpp"),
    }
    result = {
        "schema_version": "five-type-f05-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f05",
            "palette": ["10", "2+2+2+2+2", "4+2+2+2", "6+2+2", "8+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 111504,
            "edges": 519519120,
            "orbits": 250,
            "full_tasks": 11892,
            "reduced_nodes": 77581245,
            "full_root_nodes": 3648558242,
            "fff_found": False,
            "transversal_clique_count": 8832,
            "exact_palette_clique_count": 8832,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f05 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 111504/519519120",
        "full tasks/orbits: 11892/250",
        "reduced/full-root nodes: 77581245/3648558242",
        "independent transversal 8-cliques: 8832",
        "independent exact-palette cliques: 8832",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f05 validation failed: {failed}")


if __name__ == "__main__":
    main()
