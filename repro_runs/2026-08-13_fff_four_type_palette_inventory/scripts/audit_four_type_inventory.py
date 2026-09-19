#!/usr/bin/env python3
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

TYPES = ["10", "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2"]
ODD = {"10", "2+2+2+2+2", "4+4+2", "6+2+2"}
INVOLUTION = "2+2+2+2+2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimensions", type=Path, required=True)
    parser.add_argument("--products", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.dimensions.read_text())
    records = data["records"]
    by_case = {}
    for record in records:
        by_case.setdefault(record["case_id"], []).append(record)

    products = {}
    with args.products.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            products[(row["alpha"], row["beta"], row["gamma"])] = int(
                row["count_for_fixed_alpha_representative"]
            )

    count_errors = []
    cases = []
    for number, palette_tuple in enumerate(itertools.combinations(TYPES, 4), 1):
        case_id = f"p{number:02d}"
        palette = list(palette_tuple)
        roots = by_case.get(case_id, [])
        for record in roots:
            expected_total = 0
            root = record["root_type"]
            for left in palette:
                for right in palette:
                    expected_total += products.get((root, left, right), 0)
            if expected_total != record["candidate_vertices"]:
                count_errors.append(
                    {"case_id": case_id, "root": root,
                     "expected": expected_total,
                     "observed": record["candidate_vertices"]}
                )
        best = min(roots, key=lambda item: (item["candidate_vertices"], item["root_type"]))
        rigorous_exclusion = None
        if set(palette) <= ODD:
            rigorous_exclusion = "all_four_types_odd_sign_contradicts_sign_cut_triangles"
        elif set(palette) & ODD == {INVOLUTION}:
            rigorous_exclusion = "involution_only_odd_type_contradicts_sign_cut_plus_C109_matching"
        cases.append(
            {
                "case_id": case_id,
                "palette": palette,
                "recommended_root": best["root_type"],
                "candidate_vertices": best["candidate_vertices"],
                "bucket_counts": best["bucket_counts"],
                "rigorous_exclusion": rigorous_exclusion,
            }
        )

    checks = {
        "case_count_35": len(cases) == 35,
        "root_record_count_140": len(records) == 140,
        "four_roots_per_case": all(len(value) == 4 for value in by_case.values()),
        "class_product_candidate_counts_match": not count_errors,
    }
    output = {
        "result_version": "degree10-four-type-palette-inventory-v1",
        "inputs": {
            "dimensions_sha256": sha256(args.dimensions),
            "class_products_sha256": sha256(args.products),
        },
        "counts": {
            "palettes": len(cases),
            "root_records": len(records),
            "rigorous_exclusions": sum(case["rigorous_exclusion"] is not None for case in cases),
        },
        "candidate_count_errors": count_errors,
        "cases": cases,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "claim_boundary": "dimensioning and rigorous abstract exclusions only; no FFF existence decision",
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    lines = [
        "Degree-10 four-type palette inventory",
        "",
        f"palettes/root records: {len(cases)}/{len(records)}",
        f"rigorous sign/matching exclusions: {output['counts']['rigorous_exclusions']}",
        f"candidate count errors: {len(count_errors)}",
        f"all checks passed: {output['all_checks_passed']}",
        "",
    ]
    lines += [
        f"{case['case_id']} {' + '.join(case['palette'])} "
        f"root={case['recommended_root']} candidates={case['candidate_vertices']} "
        f"status={case['rigorous_exclusion'] or 'open'}"
        for case in cases
    ]
    lines += ["", "C38 open; C40 absent"]
    args.summary.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
