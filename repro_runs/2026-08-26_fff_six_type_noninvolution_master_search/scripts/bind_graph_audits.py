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
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--structural-audit", type=Path, required=True)
    parser.add_argument("--semantic-audit", type=Path, required=True)
    parser.add_argument("--builder-source", type=Path, required=True)
    parser.add_argument("--auditor-source", type=Path, required=True)
    parser.add_argument("--partial-cycle-source", type=Path, required=True)
    parser.add_argument("--builder-binary", type=Path, required=True)
    parser.add_argument("--auditor-binary", type=Path, required=True)
    parser.add_argument("--build-command", nargs="+", required=True)
    parser.add_argument("--audit-command", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    graph_hash = sha256(args.graph)
    structural = json.loads(args.structural_audit.read_text())
    semantic = json.loads(args.semantic_audit.read_text())
    checks = {
        "structural_valid": structural.get("valid") is True,
        "semantic_valid": semantic.get("valid") is True,
        "structural_graph_hash_matches": structural.get("graph_sha256") == graph_hash,
        "vertex_counts_match": structural.get("vertices") == semantic.get("stored_vertices"),
        "pair_count_complete": semantic.get("pairs_checked")
        == structural.get("vertices") * (structural.get("vertices") - 1) // 2,
        "candidate_list_errors_zero": semantic.get("candidate_list_errors") == 0,
        "edge_errors_zero": semantic.get("edge_errors") == 0,
        "reverse_edge_errors_zero": semantic.get("reverse_edge_errors") == 0,
        "format_errors_zero": semantic.get("format_errors") == 0,
        "diagonal_errors_zero": semantic.get("diagonal_errors") == 0,
        "padding_errors_zero": semantic.get("padding_errors") == 0,
    }
    result = {
        "schema_version": "master-graph-audit-binding-v1",
        "graph_path": str(args.graph.resolve()),
        "graph_sha256": graph_hash,
        "graph_size_bytes": args.graph.stat().st_size,
        "structural_audit_path": str(args.structural_audit.resolve()),
        "structural_audit_sha256": sha256(args.structural_audit),
        "semantic_audit_path": str(args.semantic_audit.resolve()),
        "semantic_audit_sha256": sha256(args.semantic_audit),
        "builder_source_sha256": sha256(args.builder_source),
        "auditor_source_sha256": sha256(args.auditor_source),
        "partial_cycle_source_sha256": sha256(args.partial_cycle_source),
        "builder_binary_sha256": sha256(args.builder_binary),
        "auditor_binary_sha256": sha256(args.auditor_binary),
        "build_command": args.build_command,
        "audit_command": args.audit_command,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("graph/audit binding failed")


if __name__ == "__main__":
    main()
