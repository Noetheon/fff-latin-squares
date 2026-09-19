#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    left = json.loads(args.left.read_text())
    right = json.loads(args.right.read_text())
    keys = (
        "completed_tasks", "search_nodes", "crossview_odd_cycle_prunes",
        "fff_found", "negative_search_complete",
    )
    checks = {key: left.get(key) == right.get(key) for key in keys}
    result = {
        "schema_version": "five-type-search-merge-equivalence-v1",
        "label": args.label,
        "left_sha256": sha256(args.left),
        "right_sha256": sha256(args.right),
        "values": {key: left.get(key) for key in keys},
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(f"{key}: {str(value).lower()}" for key, value in checks.items())
        + f"\nall checks passed: {str(result['all_checks_passed']).lower()}\n"
    )
    if not result["all_checks_passed"]:
        raise SystemExit("merge comparison failed")


if __name__ == "__main__":
    main()
