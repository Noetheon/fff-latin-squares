#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def validate_plan(plan: dict) -> None:
    expected = plan.pop("plan_payload_sha256", None)
    actual = canonical_sha(plan)
    plan["plan_payload_sha256"] = expected
    if expected != actual or plan.get("schema_version") != "master-task-plan-v1":
        raise SystemExit("invalid task-plan payload hash or schema")


def validate_existing(path: Path, plan: dict, expected: dict, checkpoint: Path) -> bool:
    try:
        row = json.loads(path.read_text())
        if row.get("status") != "complete_negative":
            return False
        if row.get("plan_payload_sha256") != plan["plan_payload_sha256"]:
            return False
        if row.get("task_file_sha256") != (
            plan["tasking"].get("task_reduction") or {}
        ).get("task_file_sha256"):
            return False
        if row.get("slice_id") != expected["slice_id"]:
            return False
        if (row.get("task_start"), row.get("task_end_exclusive")) != (
            expected["start"], expected["end_exclusive"]
        ):
            return False
        raw_path = Path(row["artifacts"]["raw_result"]["path"])
        if raw_path.parent.resolve() != checkpoint.resolve():
            return False
        if sha256(raw_path) != row["artifacts"]["raw_result"]["sha256"]:
            return False
        raw = json.loads(raw_path.read_text())
        return raw == row["raw_result"] and row.get("checks", {}).get(
            "valid_complete_negative"
        ) is True
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def artifact(path: Path) -> dict | None:
    if not path.exists():
        return None
    return {"path": str(path.resolve()), "sha256": sha256(path), "size_bytes": path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--only-slice")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.workers <= 0:
        raise SystemExit("workers must be positive")
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    graph = Path(plan["graph"]["path_hint"])
    binary = Path(plan["search"]["binary_path_hint"])
    if sha256(graph) != plan["graph"]["sha256"]:
        raise SystemExit("graph hash mismatch")
    if sha256(binary) != plan["search"]["binary_sha256"]:
        raise SystemExit("search binary hash mismatch")
    if canonical_sha(plan["search"]["sources"]) != plan["search"]["source_bundle_sha256"]:
        raise SystemExit("source bundle metadata mismatch")
    for source in plan["search"]["sources"]:
        if sha256(Path(source["path"])) != source["sha256"]:
            raise SystemExit(f"source hash mismatch: {source['path']}")
    reduction = plan["tasking"].get("task_reduction")
    task_file = None
    if reduction:
        task_file = Path(reduction["task_file_path"])
        if sha256(task_file) != reduction["task_file_sha256"]:
            raise SystemExit("task ordinal file hash mismatch")
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    selected = plan["tasking"]["slices"]
    if args.only_slice:
        selected = [item for item in selected if item["slice_id"] == args.only_slice]
        if len(selected) != 1:
            raise SystemExit("unknown slice id")
    for item in selected:
        sid = item["slice_id"]
        wrapper_path = args.checkpoint_dir / f"{sid}.json"
        if args.resume and wrapper_path.exists() and validate_existing(
            wrapper_path, plan, item, args.checkpoint_dir
        ):
            continue
        raw_path = args.checkpoint_dir / f"{sid}.raw.json"
        summary_path = args.checkpoint_dir / f"{sid}.summary.txt"
        table_path = args.checkpoint_dir / f"{sid}.table.json"
        stdout_path = args.checkpoint_dir / f"{sid}.stdout"
        stderr_path = args.checkpoint_dir / f"{sid}.stderr"
        for stale in (raw_path, summary_path, table_path, stdout_path, stderr_path):
            stale.unlink(missing_ok=True)
        count = item["count"]
        command = [
            str(binary), str(graph), str(args.workers), str(item["start"]),
            str(count), str(raw_path), str(summary_path), str(table_path),
            f"{plan['case']['case_id']}_{sid}", "slice",
        ]
        if task_file:
            command.append(str(task_file))
        started_at = datetime.now(timezone.utc).isoformat()
        started = time.monotonic()
        with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
            completed = subprocess.run(command, stdout=stdout, stderr=stderr)
        elapsed = time.monotonic() - started
        finished_at = datetime.now(timezone.utc).isoformat()
        raw = json.loads(raw_path.read_text()) if raw_path.exists() else {}
        found = raw.get("fff_found") is True
        checks = {
            "exit_zero": completed.returncode == 0,
            "total_tasks_match_plan": raw.get("total_initial_tasks")
            == plan["tasking"]["total_initial_tasks"],
            "full_tasks_match_plan": raw.get("full_initial_tasks")
            == plan["tasking"]["full_initial_tasks"],
            "interval_matches_plan": raw.get("task_start") == item["start"]
            and raw.get("task_end_exclusive") == item["end_exclusive"],
            "task_vertex_slice_hash_matches": item["task_vertices_sha256"]
            == canonical_sha(plan["tasking"]["task_vertices"][item["start"]:item["end_exclusive"]]),
            "completed_tasks_match_interval": raw.get("completed_tasks") == count,
            "negative_slice_complete": raw.get("slice_complete") is True
            and raw.get("fff_found") is False,
            "positive_candidate_preserved": found and table_path.exists(),
        }
        binding_ok = all(checks[key] for key in (
            "exit_zero", "total_tasks_match_plan", "interval_matches_plan",
            "task_vertex_slice_hash_matches", "full_tasks_match_plan",
        ))
        checks["valid_complete_negative"] = binding_ok and checks[
            "completed_tasks_match_interval"
        ] and checks["negative_slice_complete"]
        checks["valid_unconfirmed_witness"] = binding_ok and checks[
            "positive_candidate_preserved"
        ]
        status = "complete_negative" if checks["valid_complete_negative"] else (
            "witness_found_unconfirmed" if checks["valid_unconfirmed_witness"] else "error"
        )
        artifacts = {
            "raw_result": artifact(raw_path),
            "summary": artifact(summary_path),
            "table": artifact(table_path),
            "stdout": artifact(stdout_path),
            "stderr": artifact(stderr_path),
        }
        wrapper = {
            "schema_version": "master-task-slice-v1",
            "status": status,
            "case_id": plan["case"]["case_id"],
            "slice_id": sid,
            "ordinal": item["ordinal"],
            "task_start": item["start"],
            "task_end_exclusive": item["end_exclusive"],
            "task_vertices_sha256": item["task_vertices_sha256"],
            "plan_payload_sha256": plan["plan_payload_sha256"],
            "graph_sha256": plan["graph"]["sha256"],
            "task_list_sha256": plan["tasking"]["task_list_sha256"],
            "task_file_sha256": reduction.get("task_file_sha256") if reduction else None,
            "source_bundle_sha256": plan["search"]["source_bundle_sha256"],
            "search_binary_sha256": plan["search"]["binary_sha256"],
            "workers": args.workers,
            "started_at": started_at,
            "finished_at": finished_at,
            "elapsed_seconds": elapsed,
            "command": command,
            "exit_code": completed.returncode,
            "termination_reason": "process_exit",
            "artifacts": artifacts,
            "raw_result": raw,
            "checks": checks,
        }
        atomic_json(wrapper_path, wrapper)
        if status == "witness_found_unconfirmed":
            raise SystemExit(
                f"candidate preserved in {table_path}; confirm with independent validator and one-worker rerun"
            )
        if status != "complete_negative":
            raise SystemExit(f"slice validation failed: {sid}")


if __name__ == "__main__":
    main()
