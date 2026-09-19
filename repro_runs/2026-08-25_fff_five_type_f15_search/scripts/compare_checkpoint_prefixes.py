#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


SEMANTIC_FIELDS = (
    "completed_tasks",
    "crossview_odd_cycle_prunes",
    "fff_found",
    "full_initial_tasks",
    "search_nodes",
    "slice_complete",
    "task_end_exclusive",
    "task_start",
    "total_initial_tasks",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wrappers(path: Path) -> dict[str, Path]:
    return {
        file.stem: file
        for file in sorted(path.glob("s*.json"))
        if ".raw." not in file.name
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-checkpoint", type=Path, required=True)
    parser.add_argument("--new-checkpoint", type=Path, required=True)
    parser.add_argument("--expected-overlap", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    old_files = wrappers(args.old_checkpoint)
    new_files = wrappers(args.new_checkpoint)
    overlap = sorted(set(old_files) & set(new_files))
    if len(overlap) < args.expected_overlap:
        raise SystemExit(
            f"only {len(overlap)} overlapping slices; expected {args.expected_overlap}"
        )
    selected = overlap[:args.expected_overlap]
    rows = []
    errors = []
    for slice_id in selected:
        old = json.loads(old_files[slice_id].read_text())
        new = json.loads(new_files[slice_id].read_text())
        semantic_match = all(
            old.get("raw_result", {}).get(field)
            == new.get("raw_result", {}).get(field)
            for field in SEMANTIC_FIELDS
        )
        binding_match = (
            old.get("graph_sha256") == new.get("graph_sha256")
            and old.get("task_list_sha256") == new.get("task_list_sha256")
            and old.get("task_start") == new.get("task_start")
            and old.get("task_end_exclusive") == new.get("task_end_exclusive")
            and old.get("task_vertices_sha256") == new.get("task_vertices_sha256")
        )
        both_complete_negative = (
            old.get("status") == new.get("status") == "complete_negative"
            and old.get("checks", {}).get("valid_complete_negative") is True
            and new.get("checks", {}).get("valid_complete_negative") is True
        )
        if not semantic_match:
            errors.append(f"semantic mismatch {slice_id}")
        if not binding_match:
            errors.append(f"task/graph binding mismatch {slice_id}")
        if not both_complete_negative:
            errors.append(f"invalid status {slice_id}")
        old_elapsed = old.get("elapsed_seconds")
        new_elapsed = new.get("elapsed_seconds")
        rows.append({
            "slice_id": slice_id,
            "task_start": old.get("task_start"),
            "task_end_exclusive": old.get("task_end_exclusive"),
            "semantic_match": semantic_match,
            "binding_match": binding_match,
            "both_complete_negative": both_complete_negative,
            "search_nodes": old.get("raw_result", {}).get("search_nodes"),
            "crossview_odd_cycle_prunes": old.get("raw_result", {}).get(
                "crossview_odd_cycle_prunes"
            ),
            "old_elapsed_seconds": old_elapsed,
            "new_elapsed_seconds": new_elapsed,
            "old_over_new_speedup": (
                old_elapsed / new_elapsed
                if isinstance(old_elapsed, (int, float))
                and isinstance(new_elapsed, (int, float))
                and new_elapsed > 0
                else None
            ),
            "old_wrapper_sha256": sha256(old_files[slice_id]),
            "new_wrapper_sha256": sha256(new_files[slice_id]),
        })

    result = {
        "schema_version": "f15-original-vs-incremental-scratch-prefix-v1",
        "old_checkpoint": str(args.old_checkpoint.resolve()),
        "new_checkpoint": str(args.new_checkpoint.resolve()),
        "expected_overlap": args.expected_overlap,
        "compared_slices": len(rows),
        "compared_tasks": sum(row["task_end_exclusive"] - row["task_start"] for row in rows),
        "all_semantic_fields_match": all(row["semantic_match"] for row in rows),
        "all_task_graph_bindings_match": all(row["binding_match"] for row in rows),
        "all_complete_negative": all(row["both_complete_negative"] for row in rows),
        "errors": errors,
        "rows": rows,
        "valid": not errors and len(rows) == args.expected_overlap,
        "evidence_boundary": (
            "Implementation-equivalence control over the overlapping prefix only; "
            "the accepted exclusion still requires the complete new full-root cover."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "f15 original versus incremental-scratch prefix",
        "",
        f"slices/tasks compared: {result['compared_slices']}/{result['compared_tasks']}",
        f"semantic fields match: {str(result['all_semantic_fields_match']).lower()}",
        f"task/graph bindings match: {str(result['all_task_graph_bindings_match']).lower()}",
        f"all complete negative: {str(result['all_complete_negative']).lower()}",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")
    if not result["valid"]:
        raise SystemExit(f"prefix comparison failed: {errors}")


if __name__ == "__main__":
    main()
