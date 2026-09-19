#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("validate_f15_run", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    validator = load_validator(args.validator)
    tasks = 14952
    nodes = 123456789
    prunes = 98765432
    baseline = {
        "status": "complete_negative",
        "negative_search_complete": True,
        "complete_disjoint_cover": True,
        "completed_tasks": tasks,
        "total_initial_tasks": tasks,
        "search_nodes": nodes,
        "crossview_odd_cycle_prunes": prunes,
        "fff_found": False,
        "errors": [],
    }

    cases = {
        "baseline_accepts": (None, None, True),
        "wrong_status_rejects": ("status", "invalid", False),
        "incomplete_search_rejects": ("negative_search_complete", False, False),
        "incomplete_cover_rejects": ("complete_disjoint_cover", False, False),
        "missing_tasks_rejects": ("completed_tasks", tasks - 1, False),
        "wrong_total_rejects": ("total_initial_tasks", tasks + 1, False),
        "wrong_nodes_rejects": ("search_nodes", nodes + 1, False),
        "wrong_prunes_rejects": ("crossview_odd_cycle_prunes", prunes + 1, False),
        "positive_candidate_rejects": ("fff_found", True, False),
        "recorded_error_rejects": ("errors", ["synthetic mutation"], False),
    }
    checks = {}
    observations = {}
    for name, (field, value, expected) in cases.items():
        candidate = dict(baseline)
        if field is not None:
            candidate[field] = value
        actual = validator.complete_negative(candidate, tasks, nodes, prunes)
        checks[name] = actual is expected
        observations[name] = {
            "mutated_field": field,
            "mutated_value": value,
            "expected_acceptance": expected,
            "actual_acceptance": actual,
        }

    result = {
        "schema_version": "five-type-f15-validator-fail-closed-audit-v1",
        "validator": str(args.validator.resolve()),
        "checks": checks,
        "observations": observations,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f15 validator fail-closed audit",
        "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        "baseline complete-negative record accepted: true",
        "all single-field invalidating mutations rejected: "
        + str(all(checks[name] for name in checks if name != "baseline_accepts")).lower(),
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"validator fail-closed audit failed: {failed}")


if __name__ == "__main__":
    main()
