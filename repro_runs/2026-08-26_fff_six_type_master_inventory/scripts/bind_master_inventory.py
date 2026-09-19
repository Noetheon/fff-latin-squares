#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "involution_master_all_7_types": {
        "class_allowed_candidates": 190080,
        "triple_filtered_candidates": 190080,
        "bucket_counts": [0, 0, 23760, 23760, 23760, 23760, 23760, 23760, 23760, 23760],
        "residual_group_size": 48,
        "root_task_count": 23760,
        "orbit_size_counts": {"12": 12, "24": 4, "48": 490},
        "orbit_count": 506,
        "dense_graph_size_bytes": 4518201626,
    },
    "noninvolution_master_6_types": {
        "class_allowed_candidates": 196560,
        "triple_filtered_candidates": 172368,
        "bucket_counts": [0, 0, 18300, 18300, 22628, 22628, 22628, 22628, 22628, 22628],
        "residual_group_size": 48,
        "root_task_count": 18300,
        "orbit_size_counts": {"12": 5, "24": 2, "48": 379},
        "orbit_count": 386,
        "dense_graph_size_bytes": 3716598842,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_cpp(path: Path) -> dict:
    key_map = {
        "class_allowed": "class_allowed_candidates",
        "triple_allowed": "triple_filtered_candidates",
        "dense_graph_bytes": "dense_graph_size_bytes",
    }
    records = {}
    current = None
    for raw in path.read_text().splitlines():
        if not raw:
            continue
        if "=" not in raw:
            current = raw
            records[current] = {}
            continue
        if current is None:
            raise ValueError("C++ output starts without a case label")
        key, value = raw.split("=", 1)
        key = key_map.get(key, key)
        if key == "bucket_counts":
            parsed = [int(item) for item in value.split(",")]
        elif key == "orbit_size_counts":
            parsed = {
                size: int(count)
                for size, count in (item.split(":", 1) for item in value.split(","))
            }
        else:
            parsed = int(value)
        records[current][key] = parsed
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpp-output", type=Path, required=True)
    parser.add_argument("--python-output", type=Path, required=True)
    parser.add_argument("--cpp-source", type=Path, required=True)
    parser.add_argument("--python-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    cpp = parse_cpp(args.cpp_output)
    python_payload = json.loads(args.python_output.read_text())
    python_records = {
        record["case_id"]: {
            key: record[key]
            for key in EXPECTED[record["case_id"]]
        }
        for record in python_payload["cases"]
    }
    checks = {
        "case_ids_exact": set(cpp) == set(python_records) == set(EXPECTED),
        "cpp_matches_frozen_counts": cpp == EXPECTED,
        "python_matches_frozen_counts": python_records == EXPECTED,
        "implementations_match_exactly": cpp == python_records,
        "orbit_cover_involution": 12 * 12 + 4 * 24 + 490 * 48 == 23760,
        "orbit_cover_noninvolution": 5 * 12 + 2 * 24 + 379 * 48 == 18300,
        "involution_bucket_sum": sum(EXPECTED["involution_master_all_7_types"]["bucket_counts"]) == 190080,
        "noninvolution_bucket_sum": sum(EXPECTED["noninvolution_master_6_types"]["bucket_counts"]) == 172368,
    }
    result = {
        "schema_version": "six-type-master-inventory-binding-v1",
        "files": {
            "cpp_output": {"path": str(args.cpp_output.resolve()), "sha256": sha256(args.cpp_output)},
            "python_output": {"path": str(args.python_output.resolve()), "sha256": sha256(args.python_output)},
            "cpp_source": {"path": str(args.cpp_source.resolve()), "sha256": sha256(args.cpp_source)},
            "python_source": {"path": str(args.python_source.resolve()), "sha256": sha256(args.python_source)},
        },
        "cases": EXPECTED,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "evidence_boundary": (
            "Exact candidate, bucket, residual-group, orbit, and dense-size inventory only; "
            "no compatibility graph or FFF exclusion is claimed."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Six-type master inventory binding",
        "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "involution master: 190080 candidates, 23760 tasks, 506 orbits",
        "noninvolution master: 172368 candidates, 18300 tasks, 386 orbits",
        "dense graph sizes: 4518201626 / 3716598842 bytes",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
        "boundary: inventory only; no palette exclusion",
    ]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("master inventory binding failed")


if __name__ == "__main__":
    main()
