#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import itertools
import json
import subprocess
from pathlib import Path


TYPES = ("10", "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(binary: Path, output_dir: Path, job: tuple[str, tuple[str, ...], str]) -> dict:
    case_id, palette, root = job
    stem = f"{case_id}_root_{root.replace('+', '_')}"
    output = output_dir / f"{stem}.json"
    summary = output_dir / f"{stem}_summary.txt"
    command = [str(binary), case_id, *palette, root, str(output), str(summary)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        raise RuntimeError(f"failed {' '.join(command)}: {completed.stderr}")
    record = json.loads(output.read_text())
    record["output_sha256"] = sha256(output)
    record["command"] = command
    representatives = record.pop("representative_task_ordinals")
    record["representative_count"] = len(representatives)
    record["representative_task_ordinals_sha256"] = hashlib.sha256(
        ("\n".join(map(str, representatives)) + "\n").encode()
    ).hexdigest()
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    args.result_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for index, palette in enumerate(itertools.combinations(TYPES, 5), start=1):
        case_id = f"f{index:02d}"
        jobs.extend((case_id, palette, root) for root in palette)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(lambda job: run_one(args.binary, args.result_dir, job), jobs))
    records.sort(key=lambda row: (row["case_id"], row["orbit_count"], row["root_type"]))
    best = {}
    for record in records:
        best.setdefault(record["case_id"], record)
    payload = {
        "schema_version": "five-type-root-orbit-inventory-v1",
        "type_order": list(TYPES),
        "palette_count": 21,
        "record_count": len(records),
        "workers": args.workers,
        "binary_path": str(args.binary.resolve()),
        "binary_sha256": sha256(args.binary),
        "all_records_valid": all(row["valid"] for row in records),
        "best_roots": {key: {name: row[name] for name in (
            "palette", "root_type", "unfiltered_candidates", "level1_candidates",
            "full_initial_tasks", "residual_group_size", "orbit_count",
        )} for key, row in sorted(best.items())},
        "records": records,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["Five-type root-orbit inventory", ""]
    for case_id, row in sorted(best.items(), key=lambda item: item[1]["orbit_count"]):
        lines.append(
            f"{case_id} {'/'.join(row['palette'])}: root={row['root_type']} "
            f"vertices={row['level1_candidates']} tasks={row['full_initial_tasks']} "
            f"group={row['residual_group_size']} orbits={row['orbit_count']}"
        )
    lines += ["", f"records valid: {sum(r['valid'] for r in records)}/{len(records)}"]
    args.summary.write_text("\n".join(lines) + "\n")
    if len(records) != 105 or not payload["all_records_valid"]:
        raise SystemExit("invalid five-type orbit inventory")


if __name__ == "__main__":
    main()
