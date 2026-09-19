#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--expected-graph-sha256", required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    graph_sha = sha256(args.graph)
    audit_sha = sha256(args.audit)
    search_sha = sha256(args.search)
    audit = json.loads(args.audit.read_text())
    search = json.loads(args.search.read_text())
    checks = {
        "graph_sha256_matches_expected": graph_sha
        == args.expected_graph_sha256,
        "audit_valid": audit.get("valid") is True,
        "candidate_list_errors_zero": audit.get("candidate_list_errors") == 0,
        "edge_errors_zero": audit.get("edge_errors") == 0,
        "reverse_edge_errors_zero": audit.get("reverse_edge_errors") == 0,
        "search_complete": search.get("slice_complete") is True
        and search.get("completed_tasks") == search.get("total_initial_tasks"),
        "search_found_no_fff": search.get("fff_found") is False,
    }
    result = {
        "result_version": "graph-search-binding-v1",
        "case_id": args.case_id,
        "graph_path_during_run": str(args.graph),
        "graph_sha256": graph_sha,
        "expected_graph_sha256": args.expected_graph_sha256,
        "expected_graph_sha256_source": args.expected_source,
        "audit_path": str(args.audit),
        "audit_sha256": audit_sha,
        "search_path": str(args.search),
        "search_sha256": search_sha,
        "audit_summary": {
            "stored_vertices": audit.get("stored_vertices"),
            "pairs_checked": audit.get("pairs_checked"),
            "edges": audit.get("edges"),
        },
        "search_summary": {
            "total_initial_tasks": search.get("total_initial_tasks"),
            "completed_tasks": search.get("completed_tasks"),
            "search_nodes": search.get("search_nodes"),
            "crossview_odd_cycle_prunes": search.get(
                "crossview_odd_cycle_prunes"
            ),
            "fff_found": search.get("fff_found"),
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    if not result["all_checks_passed"]:
        raise SystemExit(json.dumps(result, indent=2, sort_keys=True))

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(
            [
                f"case: {args.case_id}",
                f"graph_sha256: {graph_sha}",
                f"expected_source: {args.expected_source}",
                f"audit_sha256: {audit_sha}",
                f"search_sha256: {search_sha}",
                "audit_valid: true",
                "reverse_edge_errors: 0",
                "search_complete: true",
                "fff_found: false",
                "all_checks_passed: true",
            ]
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
