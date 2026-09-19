#!/usr/bin/env python3
import argparse
import csv
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
    parser.add_argument("--products", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text())
    records = inventory["records"]
    products = {}
    with args.products.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            products[(row["alpha"], row["beta"], row["gamma"])] = int(
                row["count_for_fixed_alpha_representative"]
            )

    expected_palettes = {
        f"f{number:02d}": palette
        for number, palette in enumerate(itertools.combinations(TYPES, 5), 1)
    }
    errors = []
    checks = []
    for record in records:
        case_id = record["case_id"]
        palette = tuple(record["palette"])
        root = record["root_type"]
        expected = sum(
            products.get((root, left, right), 0)
            for left in palette
            for right in palette
        )
        record_checks = {
            "canonical_palette": palette == expected_palettes.get(case_id),
            "root_in_palette": root in palette,
            "class_product_count": expected == record["unfiltered_candidates"],
            "level1_not_larger_than_unfiltered":
                record["level1_candidates"] <= record["unfiltered_candidates"],
            "bucket_sum": sum(record["bucket_sizes"]) == record["level1_candidates"],
            "task_bucket":
                record["bucket_sizes"][record["initial_bucket"]]
                == record["full_initial_tasks"],
            "minimal_bucket_selected":
                record["full_initial_tasks"] == min(record["bucket_sizes"]),
            "orbit_partition":
                record["covered_tasks"]
                == record["orbit_union_total"]
                == record["full_initial_tasks"],
            "orbit_size_sum": sum(
                int(size) * count
                for size, count in record["orbit_size_counts"].items()
            ) == record["full_initial_tasks"],
            "no_orbit_escape": record["orbit_escape"] is False,
            "valid": record["valid"] is True,
        }
        if not all(record_checks.values()):
            errors.append({
                "case_id": case_id,
                "root_type": root,
                "expected_unfiltered": expected,
                "observed_unfiltered": record["unfiltered_candidates"],
                "checks": record_checks,
            })
        checks.append({"case_id": case_id, "root_type": root, "checks": record_checks})

    roots = {
        case_id: {r["root_type"] for r in records if r["case_id"] == case_id}
        for case_id in expected_palettes
    }
    global_checks = {
        "palette_count": len(expected_palettes) == inventory["palette_count"] == 21,
        "record_count": len(records) == inventory["record_count"] == 105,
        "five_roots_per_palette": all(
            roots[case_id] == set(palette)
            for case_id, palette in expected_palettes.items()
        ),
        "all_record_checks": not errors,
    }
    result = {
        "schema_version": "five-type-inventory-independent-audit-v1",
        "inputs": {
            "inventory_sha256": sha256(args.inventory),
            "class_products_sha256": sha256(args.products),
        },
        "counts": {
            "palettes": len(expected_palettes),
            "root_records": len(records),
            "record_errors": len(errors),
        },
        "global_checks": global_checks,
        "record_checks": checks,
        "errors": errors,
        "all_checks_passed": all(global_checks.values()),
        "claim_boundary": (
            "independent dimension and orbit-bookkeeping audit only; "
            "no five-type palette exclusion"
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Five-type inventory independent audit\n\n"
        f"palettes: {len(expected_palettes)}/21\n"
        f"root records: {len(records)}/105\n"
        f"class-product/bookkeeping errors: {len(errors)}\n"
        f"all checks passed: {str(result['all_checks_passed']).lower()}\n"
        "claim boundary: no five-type palette excluded\n"
    )
    if not result["all_checks_passed"]:
        raise SystemExit("five-type independent audit failed")


if __name__ == "__main__":
    main()
