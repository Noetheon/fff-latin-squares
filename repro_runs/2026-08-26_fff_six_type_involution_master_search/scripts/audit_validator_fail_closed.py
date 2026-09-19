#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("validate_involution", path)
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
    tasks, nodes, prunes = 506, 123456789, 98765432
    baseline = {
        "status": "complete_negative", "negative_search_complete": True,
        "complete_disjoint_cover": True, "completed_tasks": tasks,
        "total_initial_tasks": tasks, "search_nodes": nodes,
        "crossview_odd_cycle_prunes": prunes, "fff_found": False, "errors": [],
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
        "recorded_error_rejects": ("errors", ["synthetic"], False),
    }
    checks, observations = {}, {}
    for name, (field, value, expected) in cases.items():
        candidate = dict(baseline)
        if field is not None:
            candidate[field] = value
        actual = validator.complete_negative(candidate, tasks, nodes, prunes)
        checks[name] = actual is expected
        observations[name] = {"field": field, "value": value, "expected": expected, "actual": actual}
    comparison = {
        "all_checks_passed": True,
        "checks": {"synthetic": True},
        "values": {
            "completed_tasks": tasks, "total_initial_tasks": tasks,
            "search_nodes": nodes, "crossview_odd_cycle_prunes": prunes,
            "fff_found": False, "negative_search_complete": True,
            "complete_disjoint_cover": True, "status": "complete_negative",
        },
    }
    checks["comparison_baseline_accepts"] = validator.merge_comparison_valid(
        comparison, tasks, nodes, prunes
    )
    mutated = json.loads(json.dumps(comparison))
    mutated["values"]["search_nodes"] += 1
    checks["comparison_wrong_nodes_rejects"] = not validator.merge_comparison_valid(
        mutated, tasks, nodes, prunes
    )
    mutated = json.loads(json.dumps(comparison))
    mutated["checks"]["synthetic"] = False
    checks["comparison_failed_field_rejects"] = not validator.merge_comparison_valid(
        mutated, tasks, nodes, prunes
    )
    result = {
        "schema_version": "involution-master-validator-fail-closed-v1",
        "checks": checks, "observations": observations,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Involution master validator fail-closed audit\n\n"
        f"checks passed: {sum(checks.values())}/{len(checks)}\n"
        f"all checks passed: {str(result['all_checks_passed']).lower()}\n"
    )
    if not result["all_checks_passed"]:
        raise SystemExit("validator fail-closed audit failed")


if __name__ == "__main__":
    main()
