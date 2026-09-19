#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def elapsed(path: Path) -> float:
    match = re.search(r"^\s*([0-9.]+) real", path.read_text(), re.MULTILINE)
    if not match:
        raise SystemExit(f"missing time record: {path}")
    return float(match.group(1))


def swaps(path: Path) -> int:
    matches = re.findall(r"^\s*(\d+)\s+swaps\s*$", path.read_text(), re.MULTILINE)
    if len(matches) != 1:
        raise SystemExit(f"missing or ambiguous swap record: {path}")
    return int(matches[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    for workers in (1, 8, 10):
        parser.add_argument(f"--w{workers}-checkpoint", type=Path, required=True)
        parser.add_argument(f"--w{workers}-time", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    records = {}
    semantic = []
    for workers in (1, 8, 10):
        checkpoint = getattr(args, f"w{workers}_checkpoint")
        time_log = getattr(args, f"w{workers}_time")
        data = json.loads(checkpoint.read_text())
        raw = data["raw_result"]
        projection = {
            key: raw[key]
            for key in (
                "full_initial_tasks", "total_initial_tasks", "task_start",
                "task_end_exclusive", "completed_tasks", "search_nodes",
                "crossview_odd_cycle_prunes", "fff_found", "slice_complete",
            )
        }
        semantic.append(projection)
        records[str(workers)] = {
            "checkpoint_path": str(checkpoint.resolve()),
            "checkpoint_sha256": sha256(checkpoint),
            "time_log_path": str(time_log.resolve()),
            "time_log_sha256": sha256(time_log),
            "elapsed_seconds": elapsed(time_log),
            "swaps": swaps(time_log),
            "semantic_projection": projection,
            "status": data["status"],
            "workers": data["workers"],
        }

    same = semantic[0] == semantic[1] == semantic[2]
    result = {
        "schema_version": "f15-worker-benchmark-v1",
        "records": records,
        "semantic_counts_identical": same,
        "speedup_10_vs_1": records["1"]["elapsed_seconds"] / records["10"]["elapsed_seconds"],
        "speedup_10_vs_8": records["8"]["elapsed_seconds"] / records["10"]["elapsed_seconds"],
        "accepted_workers": 10,
        "valid": same
        and all(record["status"] == "complete_negative" for record in records.values())
        and all(record["swaps"] == 0 for record in records.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "f15 identical-slice worker benchmark", "",
        f"elapsed 1/8/10: {records['1']['elapsed_seconds']:.2f}/"
        f"{records['8']['elapsed_seconds']:.2f}/{records['10']['elapsed_seconds']:.2f} seconds",
        f"speedup 10 vs 1: {result['speedup_10_vs_1']:.3f}x",
        f"speedup 10 vs 8: {result['speedup_10_vs_8']:.3f}x",
        f"semantic counts identical: {str(same).lower()}",
        f"swaps 1/8/10: {records['1']['swaps']}/{records['8']['swaps']}/{records['10']['swaps']}",
        "accepted workers: 10",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")
    if not result["valid"]:
        raise SystemExit("invalid worker benchmark")


if __name__ == "__main__":
    main()
