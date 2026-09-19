#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
from pathlib import Path


MAGIC = b"O8HTv1\0\0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def checked_audit(path: Path, graph_hash: str, kind: str) -> dict:
    payload = json.loads(path.read_text())
    if payload.get("valid") is not True:
        raise SystemExit(f"{kind} audit is not valid")
    if kind == "structural" and payload.get("graph_sha256") != graph_hash:
        raise SystemExit("structural audit graph hash mismatch")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--palette", nargs="+", required=True)
    parser.add_argument("--root-type", required=True)
    parser.add_argument("--filter-level", type=int, default=2)
    parser.add_argument("--slice-width", type=int, default=64)
    parser.add_argument("--structural-audit", type=Path, required=True)
    parser.add_argument("--semantic-audit", type=Path, required=True)
    parser.add_argument("--audit-binding", type=Path, required=True)
    parser.add_argument("--search-source", type=Path, required=True)
    parser.add_argument("--source-dependency", type=Path, action="append", default=[])
    parser.add_argument("--search-binary", type=Path, required=True)
    parser.add_argument("--task-reduction-audit", type=Path)
    parser.add_argument("--search-task-file", type=Path)
    parser.add_argument("--compiler", required=True)
    parser.add_argument("--compiler-version", required=True)
    parser.add_argument("--compiler-flag", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.slice_width <= 0:
        raise SystemExit("slice width must be positive")

    graph_hash = sha256(args.graph)
    structural = checked_audit(args.structural_audit, graph_hash, "structural")
    semantic = checked_audit(args.semantic_audit, graph_hash, "semantic")
    binding = json.loads(args.audit_binding.read_text())
    if binding.get("all_checks_passed") is not True:
        raise SystemExit("graph/audit binding is not valid")
    if binding.get("graph_sha256") != graph_hash:
        raise SystemExit("graph/audit binding graph hash mismatch")
    if binding.get("structural_audit_sha256") != sha256(args.structural_audit):
        raise SystemExit("bound structural audit hash mismatch")
    if binding.get("semantic_audit_sha256") != sha256(args.semantic_audit):
        raise SystemExit("bound semantic audit hash mismatch")
    with args.graph.open("rb") as handle:
        magic = handle.read(8)
        n, words = struct.unpack("<II", handle.read(8))
        q1 = list(handle.read(10))
        vertices = [list(handle.read(10)) for _ in range(n)]
    expected_size = 26 + n * 10 + n * words * 8
    if magic != MAGIC or words != (n + 63) // 64:
        raise SystemExit("invalid graph header")
    if args.graph.stat().st_size != expected_size:
        raise SystemExit("graph size mismatch")

    buckets = [[] for _ in range(8)]
    for index, vertex in enumerate(vertices):
        bucket = vertex[0] - 2
        if not 0 <= bucket < 8:
            raise SystemExit(f"invalid first-image bucket at vertex {index}")
        buckets[bucket].append(index)
    initial_bucket = min(range(8), key=lambda bucket: (len(buckets[bucket]), bucket))
    full_task_vertices = buckets[initial_bucket]
    task_vertices = full_task_vertices
    task_reduction = None
    if bool(args.task_reduction_audit) != bool(args.search_task_file):
        raise SystemExit("task reduction audit and task file must be supplied together")
    if args.task_reduction_audit:
        reduction = json.loads(args.task_reduction_audit.read_text())
        if reduction.get("valid") is not True or reduction.get("graph_sha256") != graph_hash:
            raise SystemExit("invalid task reduction audit")
        if reduction.get("full_task_vertices_sha256") != canonical_sha(full_task_vertices):
            raise SystemExit("task reduction full-task hash mismatch")
        ordinals = [int(line) for line in args.search_task_file.read_text().splitlines()]
        if ordinals != reduction.get("selected_task_ordinals"):
            raise SystemExit("task ordinal file/audit mismatch")
        if sha256(args.search_task_file) != reduction.get("task_ordinals_sha256"):
            raise SystemExit("task ordinal file hash mismatch")
        task_vertices = [full_task_vertices[ordinal] for ordinal in ordinals]
        if sorted(task_vertices) != reduction.get("selected_task_vertices"):
            raise SystemExit("selected task vertices mismatch")
        task_reduction = {
            "audit_path": str(args.task_reduction_audit.resolve()),
            "audit_sha256": sha256(args.task_reduction_audit),
            "task_file_path": str(args.search_task_file.resolve()),
            "task_file_sha256": sha256(args.search_task_file),
            "full_initial_tasks": len(full_task_vertices),
            "selected_initial_tasks": len(task_vertices),
        }
    slices = []
    for ordinal, start in enumerate(range(0, len(task_vertices), args.slice_width)):
        end = min(start + args.slice_width, len(task_vertices))
        slices.append({
            "slice_id": f"s{ordinal:04d}",
            "ordinal": ordinal,
            "start": start,
            "end_exclusive": end,
            "count": end - start,
            "task_vertices_sha256": canonical_sha(task_vertices[start:end]),
        })
    task_payload = {"initial_bucket": initial_bucket, "task_vertices": task_vertices}
    sources = [args.search_source, *args.source_dependency]
    source_rows = [{"path": str(path.resolve()), "sha256": sha256(path)} for path in sources]
    source_bundle_hash = canonical_sha(source_rows)
    plan = {
        "schema_version": "master-task-plan-v1",
        "case": {
            "case_id": args.case_id,
            "palette_canonical": args.palette,
            "root_type": args.root_type,
            "filter_level": args.filter_level,
        },
        "graph": {
            "path_hint": str(args.graph.resolve()),
            "sha256": graph_hash,
            "size_bytes": args.graph.stat().st_size,
            "format": "O8HTv1-le",
            "vertices": n,
            "words": words,
            "canonical_root": q1,
            "bucket_sizes": [len(bucket) for bucket in buckets],
            "structural_audit_path": str(args.structural_audit.resolve()),
            "structural_audit_sha256": sha256(args.structural_audit),
            "semantic_audit_path": str(args.semantic_audit.resolve()),
            "semantic_audit_sha256": sha256(args.semantic_audit),
            "semantic_audit_valid": semantic["valid"],
            "audit_binding_path": str(args.audit_binding.resolve()),
            "audit_binding_sha256": sha256(args.audit_binding),
        },
        "search": {
            "binary_path_hint": str(args.search_binary.resolve()),
            "binary_sha256": sha256(args.search_binary),
            "source_bundle_sha256": source_bundle_hash,
            "sources": source_rows,
            "compiler": args.compiler,
            "compiler_version": args.compiler_version,
            "flags": args.compiler_flag,
        },
        "tasking": {
            "policy": "minimum_bucket_then_smallest_bucket_id",
            "initial_bucket": initial_bucket,
            "initial_bucket_value": initial_bucket + 2,
            "task_vertices": task_vertices,
            "task_list_sha256": canonical_sha(task_payload),
            "full_task_vertices_sha256": canonical_sha(full_task_vertices),
            "full_initial_tasks": len(full_task_vertices),
            "total_initial_tasks": len(task_vertices),
            "task_reduction": task_reduction,
            "slice_width": args.slice_width,
            "slices": slices,
        },
    }
    plan["plan_payload_sha256"] = canonical_sha(plan)
    args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
