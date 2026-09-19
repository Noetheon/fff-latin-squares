#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


GRAPH_SHA256 = "8fe34d2fdd3bc8e9eec6fb8cab01ba316ef54c4750413c74d4bf7ce35fb342bb"


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

    structural = load(results / "f06_structural_graph_audit.json")
    semantic = load(results / "f06_complete_graph_audit.json")
    binding = load(results / "f06_graph_audit_binding.json")
    source_audit = load(results / "f06_source_generalization_audit.json")
    orbit = load(results / "f06_graph_root_orbit_audit.json")
    sliced_plan = load(results / "f06_task_plan_sliced.json")
    monolithic_plan = load(results / "f06_task_plan_monolithic.json")
    full_plan = load(results / "f06_task_plan_full_root_bucket.json")
    sliced = load(results / "f06_final_sliced_merge.json")
    monolithic = load(results / "f06_final_monolithic_merge.json")
    full = load(results / "f06_full_root_bucket_merge.json")
    equivalence = load(results / "f06_sliced_monolithic_equivalence.json")
    independent = load(results / "f06_independent_binary_clique_binding.json")
    graph = Path(binding["graph_path"])
    task_file = args.run / "data" / "f06_task_ordinals.txt"

    expected_orbit_sizes = {"12": 3, "24": 1, "48": 272}
    graph_hash_current = sha256(graph) if graph.is_file() else None
    checks = {
        "source_generalization_audit": source_audit.get("all_checks_passed") is True
        and sum(source_audit.get("checks", {}).values()) == 10,
        "structural_graph_audit": structural.get("valid") is True
        and structural.get("vertices") == 122496
        and structural.get("words") == 1914
        and structural.get("actual_size_bytes") == 1876883738,
        "external_graph_hash_frozen": graph_hash_current == GRAPH_SHA256
        and structural.get("graph_sha256") == GRAPH_SHA256
        and binding.get("graph_sha256") == GRAPH_SHA256,
        "semantic_graph_audit": semantic.get("valid") is True
        and semantic.get("stored_vertices") == 122496
        and semantic.get("independently_enumerated_vertices") == 122496
        and semantic.get("pairs_checked") == 7502573760
        and semantic.get("edges") == 682657152,
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
        == sha256(results / "f06_structural_graph_audit.json")
        and binding.get("semantic_audit_sha256")
        == sha256(results / "f06_complete_graph_audit.json"),
        "orbit_dimension_binding": orbit.get("valid") is True
        and all(orbit.get("dimension_checks", {}).values())
        and orbit.get("graph_sha256") == GRAPH_SHA256,
        "orbit_cover_exact": orbit.get("full_initial_task_count") == 13116
        and orbit.get("orbit_count") == 276
        and orbit.get("orbit_size_counts") == expected_orbit_sizes
        and orbit.get("covered_task_count") == 13116
        and all(orbit.get("checks", {}).values()),
        "task_file_bound": task_file.is_file()
        and sha256(task_file) == orbit.get("task_ordinals_sha256")
        == sliced_plan["tasking"]["task_reduction"]["task_file_sha256"]
        == monolithic_plan["tasking"]["task_reduction"]["task_file_sha256"]
        and len(task_file.read_text().splitlines()) == 276,
        "reduced_plans_bound": sliced.get("plan_payload_sha256")
        == sliced_plan.get("plan_payload_sha256")
        and monolithic.get("plan_payload_sha256")
        == monolithic_plan.get("plan_payload_sha256")
        and sliced_plan["graph"]["sha256"] == monolithic_plan["graph"]["sha256"]
        == GRAPH_SHA256,
        "reduced_sliced_complete_negative": complete_negative(
            sliced, 276, 191468291, 124696625
        ),
        "reduced_monolithic_complete_negative": complete_negative(
            monolithic, 276, 191468291, 124696625
        ),
        "reduced_decompositions_equivalent": equivalence.get("all_checks_passed") is True
        and sliced.get("task_list_sha256") == monolithic.get("task_list_sha256")
        and sliced.get("search_binary_sha256") == monolithic.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256") == monolithic.get("source_bundle_sha256"),
        "full_root_plan_bound": full.get("plan_payload_sha256")
        == full_plan.get("plan_payload_sha256")
        and full_plan["graph"]["sha256"] == GRAPH_SHA256
        and full_plan["tasking"]["task_reduction"] is None
        and full_plan["tasking"]["total_initial_tasks"] == 13116,
        "full_root_bucket_complete_negative": complete_negative(
            full, 13116, 8923849056, 5801498838
        ),
        "search_implementations_bound": sliced.get("search_binary_sha256")
        == monolithic.get("search_binary_sha256")
        == full.get("search_binary_sha256")
        and sliced.get("source_bundle_sha256")
        == monolithic.get("source_bundle_sha256")
        == full.get("source_bundle_sha256"),
        "independent_binary_clique_audit": independent.get("all_checks_passed") is True
        and all(independent.get("checks", {}).values())
        and independent["files"]["f06_graph"]["sha256"] == GRAPH_SHA256
        and independent["files"]["f06_result"]["sha256"]
        == sha256(results / "f06_binary_clique_table_audit.json")
        and independent["files"]["source"]["sha256"]
        == sha256(args.run / "scripts" / "enumerate_binary_graph_clique_tables.cpp"),
    }
    result = {
        "schema_version": "five-type-f06-run-validation-v1",
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "result": {
            "case_id": "f06",
            "palette": ["10", "2+2+2+2+2", "4+2+2+2", "6+4", "8+2"],
            "graph_sha256": GRAPH_SHA256,
            "vertices": 122496,
            "edges": 682657152,
            "orbits": 276,
            "full_tasks": 13116,
            "reduced_nodes": 191468291,
            "full_root_nodes": 8923849056,
            "fff_found": False,
            "transversal_clique_count": 2880,
            "exact_palette_clique_count": 0,
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f06 run validation", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "graph vertices/edges: 122496/682657152",
        "full tasks/orbits: 13116/276",
        "reduced/full-root nodes: 191468291/8923849056",
        "independent transversal 8-cliques: 2880",
        "independent exact-palette cliques: 0",
        "FFF found: false",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"f06 validation failed: {failed}")


if __name__ == "__main__":
    main()
