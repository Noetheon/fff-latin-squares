#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


EXPECTED_GRAPH_SHA256 = (
    "5198afaece05822dd7812e6a0408acf79648d5de7ff714c81e916544dd2d6828"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time_log(path: Path) -> dict:
    text = path.read_text()
    real = re.search(r"^\s*([0-9.]+) real", text, re.MULTILINE)
    rss = re.search(r"^\s*(\d+)\s+maximum resident set size", text, re.MULTILINE)
    swaps = re.search(r"^\s*(\d+)\s+swaps", text, re.MULTILINE)
    if not real or not rss or not swaps:
        raise SystemExit("cannot parse benchmark time log")
    return {
        "elapsed_seconds": float(real.group(1)),
        "maximum_resident_set_size": int(rss.group(1)),
        "swaps": int(swaps.group(1)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-result", type=Path, required=True)
    parser.add_argument("--time-log", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--task-ordinals", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.raw_result.read_text())
    reference = json.loads(args.reference.read_text())
    old = reference["records"]["10"]
    expected = old["semantic_projection"]
    timing = parse_time_log(args.time_log)
    fields = (
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
    graph_hash = sha256(args.graph)
    speedup = old["elapsed_seconds"] / timing["elapsed_seconds"]
    checks = {
        "reference_valid": reference.get("valid") is True
        and reference.get("semantic_counts_identical") is True,
        "graph_hash_frozen": graph_hash == EXPECTED_GRAPH_SHA256,
        "semantic_projection_exact": all(raw.get(field) == expected.get(field) for field in fields),
        "complete_negative": raw.get("completed_tasks") == 25
        and raw.get("slice_complete") is True
        and raw.get("fff_found") is False,
        "task_file_has_expected_size": len(args.task_ordinals.read_text().splitlines()) == 1872,
        "ten_workers_recorded": raw.get("workers") == 10,
        "time_log_zero_swaps": timing["swaps"] == 0,
        "incremental_not_slower_on_control": speedup > 1.0,
    }
    result = {
        "schema_version": "incremental-f15-search-benchmark-binding-v1",
        "files": {
            "raw_result": {"path": str(args.raw_result.resolve()), "sha256": sha256(args.raw_result)},
            "time_log": {"path": str(args.time_log.resolve()), "sha256": sha256(args.time_log)},
            "reference": {"path": str(args.reference.resolve()), "sha256": sha256(args.reference)},
            "graph": {"path": str(args.graph.resolve()), "sha256": graph_hash},
            "task_ordinals": {"path": str(args.task_ordinals.resolve()), "sha256": sha256(args.task_ordinals)},
            "source": {"path": str(args.source.resolve()), "sha256": sha256(args.source)},
            "binary": {"path": str(args.binary.resolve()), "sha256": sha256(args.binary)},
        },
        "old_search": {
            "elapsed_seconds": old["elapsed_seconds"],
            "workers": old["workers"],
            "semantic_projection": expected,
        },
        "incremental_search": {
            **timing,
            "workers": raw["workers"],
            "semantic_projection": {field: raw[field] for field in fields},
        },
        "speedup_old_over_incremental": speedup,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "evidence_boundary": (
            "Implementation-equivalence and hardware-specific performance control only; "
            "no new FFF exclusion."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Incremental f15 search benchmark binding",
        "",
        f"tasks/nodes/prunes: {raw['completed_tasks']}/{raw['search_nodes']}/{raw['crossview_odd_cycle_prunes']}",
        f"old/incremental seconds: {old['elapsed_seconds']:.2f}/{timing['elapsed_seconds']:.2f}",
        f"speedup: {speedup:.3f}x",
        f"swaps: {timing['swaps']}",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"incremental f15 benchmark binding failed: {failed}")


if __name__ == "__main__":
    main()
