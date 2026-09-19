#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp = Path(handle.name)
    os.replace(temp, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    expected_plan_hash = plan.pop("plan_payload_sha256", None)
    if expected_plan_hash != canonical_sha(plan):
        raise SystemExit("invalid plan payload hash")
    plan["plan_payload_sha256"] = expected_plan_hash

    rows = []
    errors = []
    seen_ids = set()
    seen_ordinals = set()
    for expected in plan["tasking"]["slices"]:
        path = args.checkpoint_dir / f"{expected['slice_id']}.json"
        if not path.exists():
            errors.append(f"missing {expected['slice_id']}")
            continue
        try:
            row = json.loads(path.read_text())
            raw_info = row["artifacts"]["raw_result"]
            raw_path = Path(raw_info["path"])
            if raw_path.parent.resolve() != args.checkpoint_dir.resolve():
                errors.append(f"raw path escapes checkpoint {expected['slice_id']}")
                continue
            if sha256(raw_path) != raw_info["sha256"]:
                errors.append(f"raw hash mismatch {expected['slice_id']}")
                continue
            raw = json.loads(raw_path.read_text())
            if raw != row.get("raw_result"):
                errors.append(f"embedded/raw mismatch {expected['slice_id']}")
            row["raw_result"] = raw
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"malformed {expected['slice_id']}: {error}")
            continue
        if row.get("slice_id") in seen_ids:
            errors.append(f"duplicate slice id {row.get('slice_id')}")
        if row.get("ordinal") in seen_ordinals:
            errors.append(f"duplicate ordinal {row.get('ordinal')}")
        seen_ids.add(row.get("slice_id"))
        seen_ordinals.add(row.get("ordinal"))
        bindings = {
            "plan_payload_sha256": plan["plan_payload_sha256"],
            "graph_sha256": plan["graph"]["sha256"],
            "task_list_sha256": plan["tasking"]["task_list_sha256"],
            "source_bundle_sha256": plan["search"]["source_bundle_sha256"],
            "search_binary_sha256": plan["search"]["binary_sha256"],
            "task_file_sha256": (
                plan["tasking"].get("task_reduction") or {}
            ).get("task_file_sha256"),
        }
        for key, value in bindings.items():
            if row.get(key) != value:
                errors.append(f"{key} mismatch {expected['slice_id']}")
        if row.get("slice_id") != expected["slice_id"] or row.get("ordinal") != expected["ordinal"]:
            errors.append(f"slice identity mismatch {expected['slice_id']}")
        if (row.get("task_start"), row.get("task_end_exclusive")) != (
            expected["start"], expected["end_exclusive"]
        ):
            errors.append(f"interval mismatch {expected['slice_id']}")
        if row.get("task_vertices_sha256") != expected["task_vertices_sha256"]:
            errors.append(f"task vertex hash mismatch {expected['slice_id']}")
        if row.get("status") != "complete_negative" or row.get("checks", {}).get(
            "valid_complete_negative"
        ) is not True:
            errors.append(f"nonnegative or invalid slice {expected['slice_id']}")
        rows.append(row)

    rows.sort(key=lambda row: row["task_start"])
    cursor = 0
    for row in rows:
        if not isinstance(row["task_start"], int) or not isinstance(row["task_end_exclusive"], int):
            errors.append("noninteger interval")
            continue
        if row["task_start"] != cursor or row["task_end_exclusive"] <= row["task_start"]:
            errors.append(f"cover gap/overlap/reversal at {cursor}")
        cursor = row["task_end_exclusive"]
    total = plan["tasking"]["total_initial_tasks"]
    if cursor != total:
        errors.append("cover does not end at total_initial_tasks")

    result = {
        "schema_version": "four-type-slice-merge-v2",
        "status": "complete_negative" if not errors and len(rows) == len(plan["tasking"]["slices"]) else "invalid",
        "case_id": plan["case"]["case_id"],
        "plan_payload_sha256": plan["plan_payload_sha256"],
        "graph_sha256": plan["graph"]["sha256"],
        "task_list_sha256": plan["tasking"]["task_list_sha256"],
        "task_file_sha256": (
            plan["tasking"].get("task_reduction") or {}
        ).get("task_file_sha256"),
        "source_bundle_sha256": plan["search"]["source_bundle_sha256"],
        "search_binary_sha256": plan["search"]["binary_sha256"],
        "total_initial_tasks": total,
        "slice_count_expected": len(plan["tasking"]["slices"]),
        "slice_count_present": len(rows),
        "completed_tasks": sum(row["raw_result"]["completed_tasks"] for row in rows),
        "search_nodes": sum(row["raw_result"]["search_nodes"] for row in rows),
        "crossview_odd_cycle_prunes": sum(
            row["raw_result"]["crossview_odd_cycle_prunes"] for row in rows
        ),
        "fff_found": any(row["raw_result"]["fff_found"] for row in rows),
        "errors": errors,
        "complete_disjoint_cover": not errors and len(rows) == len(plan["tasking"]["slices"]) and cursor == total,
        "slice_wrapper_sha256": {
            row["slice_id"]: sha256(args.checkpoint_dir / f"{row['slice_id']}.json")
            for row in rows
        },
    }
    result["negative_search_complete"] = (
        result["status"] == "complete_negative"
        and result["completed_tasks"] == total
        and not result["fff_found"]
    )
    atomic_write(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
    atomic_write(args.summary, "\n".join([
        f"case: {result['case_id']}",
        f"status: {result['status']}",
        f"slices: {result['slice_count_present']}/{result['slice_count_expected']}",
        f"tasks: {result['completed_tasks']}/{result['total_initial_tasks']}",
        f"nodes/prunes: {result['search_nodes']}/{result['crossview_odd_cycle_prunes']}",
        f"FFF found: {str(result['fff_found']).lower()}",
        f"complete disjoint cover: {str(result['complete_disjoint_cover']).lower()}",
        f"negative search complete: {str(result['negative_search_complete']).lower()}",
    ]) + "\n")
    if not result["negative_search_complete"]:
        raise SystemExit("merge is not a complete negative search")


if __name__ == "__main__":
    main()
