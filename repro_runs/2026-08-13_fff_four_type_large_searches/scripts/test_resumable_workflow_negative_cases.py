#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


def make_graph(path: Path) -> None:
    root = bytes((1, 0, 3, 2, 5, 4, 7, 6, 9, 8))
    vertices = [
        bytes((2, 0, 1, 3, 4, 5, 6, 7, 8, 9)),
        bytes((3, 0, 1, 2, 4, 5, 6, 7, 8, 9)),
    ]
    with path.open("wb") as handle:
        handle.write(b"O8HTv1\0\0")
        handle.write(struct.pack("<II", 2, 1))
        handle.write(root)
        for vertex in vertices:
            handle.write(vertex)
        handle.write(struct.pack("<QQ", 2, 1))


def rejected(auditor: Path, graph: Path, directory: Path, name: str) -> bool:
    completed = subprocess.run([
        "python3", str(auditor), "--graph", str(graph),
        "--output", str(directory / f"{name}.json"),
        "--summary", str(directory / f"{name}.txt"),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return completed.returncode != 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_runner(path: Path):
    spec = importlib.util.spec_from_file_location("four_type_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural-auditor", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--merger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        valid = temp / "valid.bin"
        make_graph(valid)
        checks = {}

        valid_run = subprocess.run([
            "python3", str(args.structural_auditor), "--graph", str(valid),
            "--output", str(temp / "valid.json"),
            "--summary", str(temp / "valid.txt"),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        checks["valid_control_accepted"] = valid_run.returncode == 0

        mutations = {}
        data = bytearray(valid.read_bytes())
        changed = bytearray(data); changed[6] = 1; mutations["magic_byte_6"] = changed
        changed = bytearray(data); changed[7] = 1; mutations["magic_byte_7"] = changed
        mutations["truncated_header"] = data[:12]
        mutations["truncated_vertices"] = data[:35]
        mutations["truncated_adjacency"] = data[:-1]
        mutations["appended_byte"] = data + b"x"
        changed = bytearray(data); struct.pack_into("<I", changed, 12, 2); mutations["wrong_words"] = changed
        changed = bytearray(data); changed[26:36] = bytes((2, 0, 1, 3, 4, 5, 6, 7, 8, 8)); mutations["invalid_permutation"] = changed
        changed = bytearray(data); changed[36:46] = changed[26:36]; mutations["duplicate_vertex"] = changed
        changed = bytearray(data); changed[26:36], changed[36:46] = changed[36:46], changed[26:36]; mutations["unsorted_vertices"] = changed
        changed = bytearray(data); struct.pack_into("<Q", changed, 46, 3); mutations["nonzero_diagonal"] = changed
        changed = bytearray(data); struct.pack_into("<Q", changed, 46, (1 << 63) | 2); mutations["nonzero_padding"] = changed

        for name, payload in mutations.items():
            path = temp / f"{name}.bin"
            path.write_bytes(payload)
            checks[f"reject_{name}"] = rejected(
                args.structural_auditor, path, temp, name
            )

        runner = load_runner(args.runner)
        checkpoint = temp / "checkpoint"
        checkpoint.mkdir()
        raw_path = checkpoint / "s0000.raw.json"
        raw = {
            "total_initial_tasks": 1,
            "task_start": 0,
            "task_end_exclusive": 1,
            "completed_tasks": 1,
            "search_nodes": 7,
            "crossview_odd_cycle_prunes": 3,
            "fff_found": False,
            "slice_complete": True,
        }
        raw_path.write_text(json.dumps(raw) + "\n")
        wrapper_path = checkpoint / "s0000.json"
        wrapper = {
            "status": "complete_negative",
            "plan_payload_sha256": "stale-plan",
            "slice_id": "s0000",
            "task_start": 0,
            "task_end_exclusive": 1,
            "task_file_sha256": None,
            "artifacts": {"raw_result": {"path": str(raw_path), "sha256": sha256(raw_path)}},
            "raw_result": raw,
            "checks": {"valid_complete_negative": True},
        }
        wrapper_path.write_text(json.dumps(wrapper) + "\n")
        resume_plan = {"plan_payload_sha256": "current-plan", "tasking": {"task_reduction": None}}
        expected = {"slice_id": "s0000", "start": 0, "end_exclusive": 1}
        checks["reject_stale_resume_checkpoint"] = not runner.validate_existing(
            wrapper_path, resume_plan, expected, checkpoint
        )
        wrapper["plan_payload_sha256"] = "current-plan"
        wrapper["raw_result"] = {**raw, "search_nodes": 8}
        wrapper_path.write_text(json.dumps(wrapper) + "\n")
        checks["reject_embedded_raw_mismatch_on_resume"] = not runner.validate_existing(
            wrapper_path, resume_plan, expected, checkpoint
        )

        merge_plan = {
            "schema_version": "four-type-task-plan-v2",
            "case": {"case_id": "test"},
            "graph": {"sha256": "graph"},
            "search": {"source_bundle_sha256": "source", "binary_sha256": "binary"},
            "tasking": {
                "task_list_sha256": "tasks",
                "task_reduction": None,
                "total_initial_tasks": 1,
                "slices": [{
                    "slice_id": "s0000", "ordinal": 0, "start": 0,
                    "end_exclusive": 1, "task_vertices_sha256": "slice",
                }],
            },
        }
        merge_plan["plan_payload_sha256"] = canonical_sha(merge_plan)
        plan_path = temp / "plan.json"
        plan_path.write_text(json.dumps(merge_plan) + "\n")
        wrapper.update({
            "schema_version": "four-type-task-slice-v2",
            "status": "complete_negative",
            "case_id": "test",
            "plan_payload_sha256": merge_plan["plan_payload_sha256"],
            "graph_sha256": "graph",
            "task_list_sha256": "tasks",
            "source_bundle_sha256": "source",
            "search_binary_sha256": "binary",
            "task_file_sha256": None,
            "task_vertices_sha256": "slice",
            "ordinal": 0,
            "raw_result": {**raw, "search_nodes": 8},
        })
        wrapper_path.write_text(json.dumps(wrapper) + "\n")
        merge_run = subprocess.run([
            "python3", str(args.merger), "--plan", str(plan_path),
            "--checkpoint-dir", str(checkpoint), "--output", str(temp / "merge.json"),
            "--summary", str(temp / "merge.txt"),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        checks["reject_embedded_raw_mismatch_on_merge"] = merge_run.returncode != 0

    result = {
        "schema_version": "four-type-workflow-negative-tests-v1",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        f"negative workflow tests: {result['passed']}/{result['total']} passed\n"
        f"all checks passed: {str(result['all_checks_passed']).lower()}\n"
    )
    if not result["all_checks_passed"]:
        raise SystemExit("negative workflow tests failed")


if __name__ == "__main__":
    main()
