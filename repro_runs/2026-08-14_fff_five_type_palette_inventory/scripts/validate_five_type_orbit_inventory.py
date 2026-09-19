#!/usr/bin/env python3
import argparse
import hashlib
import itertools
import json
from pathlib import Path


TYPES = ("10", "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    records = inventory.get("records", [])
    expected = {f"f{i:02d}": tuple(p) for i, p in enumerate(itertools.combinations(TYPES, 5), 1)}
    record_checks = []
    for record in records:
        per_root = Path(record["command"][-2])
        raw = json.loads(per_root.read_text()) if per_root.is_file() else {}
        reps = raw.get("representative_task_ordinals", [])
        rep_hash = hashlib.sha256(("\n".join(map(str, reps)) + "\n").encode()).hexdigest()
        checks = {
            "schema": raw.get("schema_version") == "five-type-root-orbit-dimension-v1",
            "palette": tuple(record.get("palette", [])) == expected.get(record.get("case_id")),
            "root_in_palette": record.get("root_type") in record.get("palette", []),
            "record_valid": record.get("valid") is True,
            "complete_cover": record.get("covered_tasks") == record.get("full_initial_tasks") == record.get("orbit_union_total"),
            "bucket_sum": sum(record.get("bucket_sizes", [])) == record.get("level1_candidates"),
            "selected_bucket": (
                len(record.get("bucket_sizes", [])) == 8
                and record.get("bucket_sizes", [])[record.get("initial_bucket", -1)]
                == record.get("full_initial_tasks")
            ),
            "smallest_bucket": record.get("full_initial_tasks") == min(record.get("bucket_sizes", [0])),
            "orbit_sizes_sum": sum(int(size) * count for size, count in record.get("orbit_size_counts", {}).items()) == record.get("full_initial_tasks"),
            "orbit_sizes_divide_group": all(
                record.get("residual_group_size", 0) % int(size) == 0
                for size in record.get("orbit_size_counts", {})
            ),
            "no_escape": record.get("orbit_escape") is False,
            "representatives": len(reps) == record.get("representative_count") == record.get("orbit_count"),
            "representatives_sorted_unique_in_range": (
                reps == sorted(set(reps))
                and all(0 <= item < record.get("full_initial_tasks", 0) for item in reps)
            ),
            "representative_hash": rep_hash == record.get("representative_task_ordinals_sha256"),
            "per_root_hash": per_root.is_file() and sha256(per_root) == record.get("output_sha256"),
        }
        record_checks.append({"case_id": record.get("case_id"), "root_type": record.get("root_type"), "checks": checks, "valid": all(checks.values())})
    roots = {case: {r["root_type"] for r in records if r["case_id"] == case} for case in expected}
    best = inventory.get("best_roots", {})
    best_checks = {}
    for case, palette in expected.items():
        candidates = [r for r in records if r["case_id"] == case]
        minimum = min((r["orbit_count"], r["root_type"]) for r in candidates)
        actual = best.get(case, {})
        best_checks[case] = (actual.get("orbit_count"), actual.get("root_type")) == minimum
    checks = {
        "schema": inventory.get("schema_version") == "five-type-root-orbit-inventory-v1",
        "type_order": tuple(inventory.get("type_order", [])) == TYPES,
        "palette_count": inventory.get("palette_count") == 21 == len(expected),
        "record_count": inventory.get("record_count") == 105 == len(records),
        "all_records_valid": inventory.get("all_records_valid") is True,
        "five_roots_each": all(roots[c] == set(expected[c]) for c in expected),
        "all_record_checks": all(r["valid"] for r in record_checks),
        "all_best_checks": all(best_checks.values()),
        "binary_hash": Path(inventory["binary_path"]).is_file() and sha256(Path(inventory["binary_path"])) == inventory.get("binary_sha256"),
    }
    result = {"schema_version": "five-type-root-orbit-inventory-validation-v1", "inventory_sha256": sha256(args.inventory), "checks": checks, "best_root_checks": best_checks, "record_checks": record_checks, "all_checks_passed": all(checks.values())}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join(["Five-type orbit inventory validation", "", f"records checked: {len(records)}/105", f"record checks passed: {sum(r['valid'] for r in record_checks)}/{len(records)}", f"best roots passed: {sum(best_checks.values())}/21", f"all checks passed: {str(result['all_checks_passed']).lower()}"]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("five-type inventory validation failed")


if __name__ == "__main__":
    main()
