#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path

RUN = Path("repro_runs/2026-08-13_fff_four_type_palette_inventory")
RESULTS = RUN / "results"
INVENTORY = json.loads((RESULTS / "four_type_palette_inventory.json").read_text())
HASH_TABLE = RESULTS / "four_type_graph_hashes.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_equal(left: dict, right: dict, keys: tuple[str, ...]) -> bool:
    return all(left.get(key) == right.get(key) for key in keys)


graph_hashes = {}
if HASH_TABLE.exists():
    for line in HASH_TABLE.read_text().splitlines()[1:]:
        case_id, digest = line.split("\t")
        graph_hashes[case_id] = digest

rows = []
for case in INVENTORY["cases"]:
    case_id = case["case_id"]
    audit_path = RESULTS / f"{case_id}_hashbound_complete_graph_audit.json"
    search_path = RESULTS / f"{case_id}_hashbound_full_fff_search.json"
    binding_path = RESULTS / f"{case_id}_graph_search_binding.json"
    if not audit_path.exists() or not search_path.exists() or not binding_path.exists():
        continue
    audit = json.loads(audit_path.read_text())
    search = json.loads(search_path.read_text())
    binding = json.loads(binding_path.read_text())
    original_audit = json.loads(
        (RESULTS / f"{case_id}_complete_graph_audit.json").read_text()
    )
    original_search = json.loads(
        (RESULTS / f"{case_id}_full_fff_search.json").read_text()
    )
    rows.append(
        {
            "case_id": case_id,
            "palette": case["palette"],
            "root_type": case["recommended_root"],
            "stored_vertices": audit["stored_vertices"],
            "independently_enumerated_vertices": audit["independently_enumerated_vertices"],
            "pairs_checked": audit["pairs_checked"],
            "edges": audit["edges"],
            "candidate_list_errors": audit["candidate_list_errors"],
            "edge_errors": audit["edge_errors"],
            "reverse_edge_errors": audit["reverse_edge_errors"],
            "graph_valid": audit["valid"],
            "tasks": search["total_initial_tasks"],
            "completed_tasks": search["completed_tasks"],
            "search_nodes": search["search_nodes"],
            "crossview_prunes": search["crossview_odd_cycle_prunes"],
            "fff_found": search["fff_found"],
            "slice_complete": search["slice_complete"],
            "graph_sha256": binding["graph_sha256"],
            "binding_checks_passed": binding["all_checks_passed"],
            "audit_sha256_matches_binding": sha256(audit_path)
            == binding["audit_sha256"],
            "search_sha256_matches_binding": sha256(search_path)
            == binding["search_sha256"],
            "graph_sha256_matches_frozen_table": graph_hashes.get(case_id)
            == binding["graph_sha256"],
            "audit_semantic_match_original": selected_equal(
                audit,
                original_audit,
                (
                    "stored_vertices",
                    "independently_enumerated_vertices",
                    "candidate_list_errors",
                    "pairs_checked",
                    "edges",
                    "edge_errors",
                    "reverse_edge_errors",
                    "crossview_filter_level",
                    "valid",
                ),
            ),
            "search_semantic_match_original": selected_equal(
                search,
                original_search,
                (
                    "total_initial_tasks",
                    "completed_tasks",
                    "task_start",
                    "task_end_exclusive",
                    "search_nodes",
                    "crossview_odd_cycle_prunes",
                    "fff_found",
                    "slice_complete",
                ),
            ),
        }
    )

rigorous = [
    case for case in INVENTORY["cases"] if case["rigorous_exclusion"] is not None
]
rigorous_ids = {case["case_id"] for case in rigorous}
searched_ids = {row["case_id"] for row in rows}
inventory_ids = {case["case_id"] for case in INVENTORY["cases"]}
checks = {
    "exact_rigorous_case_count_2": len(rigorous) == 2,
    "exact_searched_case_count_25": len(rows) == 25,
    "exact_frozen_graph_hash_count_25": len(graph_hashes) == 25,
    "excluded_cases_disjoint": rigorous_ids.isdisjoint(searched_ids),
    "excluded_and_remaining_partition_inventory": (
        len(inventory_ids - rigorous_ids - searched_ids) == 8
        and rigorous_ids | searched_ids <= inventory_ids
    ),
    "all_graphs_valid": all(row["graph_valid"] for row in rows),
    "all_candidate_lists_exact": all(
        row["candidate_list_errors"] == 0
        and row["stored_vertices"] == row["independently_enumerated_vertices"]
        for row in rows
    ),
    "all_edges_exact_and_symmetric": all(
        row["edge_errors"] == 0 and row["reverse_edge_errors"] == 0 for row in rows
    ),
    "all_graph_search_bindings_passed": all(
        row["binding_checks_passed"]
        and row["audit_sha256_matches_binding"]
        and row["search_sha256_matches_binding"]
        and row["graph_sha256_matches_frozen_table"]
        for row in rows
    ),
    "all_hashbound_reruns_semantically_match_original": all(
        row["audit_semantic_match_original"]
        and row["search_semantic_match_original"]
        for row in rows
    ),
    "all_searches_complete": all(
        row["slice_complete"] and row["tasks"] == row["completed_tasks"] for row in rows
    ),
    "no_fff_found": all(not row["fff_found"] for row in rows),
}
excluded = len(rigorous) + len(rows)
output = {
    "result_version": "degree10-four-type-complete-searches-v2-hashbound",
    "rigorous_exclusions": [
        {"case_id": case["case_id"], "palette": case["palette"],
         "reason": case["rigorous_exclusion"]}
        for case in rigorous
    ],
    "computational_exclusions": rows,
    "totals": {
        "rigorous_cases": len(rigorous),
        "searched_cases": len(rows),
        "excluded_four_type_palettes": excluded,
        "remaining_four_type_palettes": 35 - excluded,
        "pairs_checked": sum(row["pairs_checked"] for row in rows),
        "search_nodes": sum(row["search_nodes"] for row in rows),
        "crossview_prunes": sum(row["crossview_prunes"] for row in rows),
    },
    "checks": checks,
    "all_checks_passed": all(checks.values()),
    "claim_boundary": "exact listed four-type palette exclusions only; order 10 open",
}
(RESULTS / "four_type_search_results.json").write_text(
    json.dumps(output, indent=2, sort_keys=True) + "\n"
)
lines = [
    "Degree-10 four-type exact exclusions",
    "",
    f"rigorous/searched exclusions: {len(rigorous)}/{len(rows)}",
    f"palettes excluded/remaining: {excluded}/{35-excluded}",
    f"pairs audited: {output['totals']['pairs_checked']}",
    f"search nodes/prunes: {output['totals']['search_nodes']}/{output['totals']['crossview_prunes']}",
    f"all checks passed: {output['all_checks_passed']}",
    "",
]
lines += [f"{case['case_id']} rigorous {case['rigorous_exclusion']}" for case in rigorous]
lines += [
    f"{row['case_id']} vertices={row['stored_vertices']} tasks={row['tasks']} "
    f"nodes={row['search_nodes']} FFF={row['fff_found']}"
    for row in rows
]
lines += ["", "C38 open; C40 absent"]
(RESULTS / "four_type_search_results_summary.txt").write_text(
    "\n".join(lines) + "\n"
)
