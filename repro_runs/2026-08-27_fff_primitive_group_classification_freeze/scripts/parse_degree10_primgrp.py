#!/usr/bin/env python3
"""Parse and validate the frozen GAP/PrimGrp degree-10 query."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "results/degree10_primgrp_raw.txt"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    fields: dict[str, str] = {}
    groups = []
    for line in RAW.read_text(encoding="utf-8").splitlines():
        if line.startswith("GROUP\t"):
            _, index, order, structure = line.split("\t", 3)
            groups.append(
                {"catalogue_index": int(index), "order": int(order), "structure": structure}
            )
        elif "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value

    expected_orders = [60, 120, 360, 720, 720, 720, 1440, 1814400, 3628800]
    checks = {
        "gap_version_4_16_0": fields.get("GAP_VERSION") == "4.16.0",
        "primgrp_version_4_0_3": fields.get("PRIMGRP_VERSION") == "4.0.3",
        "degree_is_10": fields.get("DEGREE") == "10",
        "catalogue_count_is_9": fields.get("COUNT") == "9" and len(groups) == 9,
        "indices_are_1_through_9": [item["catalogue_index"] for item in groups]
        == list(range(1, 10)),
        "orders_match_frozen_catalogue": [item["order"] for item in groups]
        == expected_orders,
        "last_two_are_A10_S10": [item["structure"] for item in groups[-2:]]
        == ["A10", "S10"],
    }
    result = {
        "run_id": "2026-08-27_fff_primitive_group_classification_freeze",
        "query": "NrPrimitiveGroups(10) and PrimitiveGroup(10,i)",
        "gap_version": fields.get("GAP_VERSION"),
        "primgrp_version": fields.get("PRIMGRP_VERSION"),
        "degree": int(fields["DEGREE"]),
        "catalogue_count": int(fields["COUNT"]),
        "groups": groups,
        "raw_output_sha256": sha256(RAW),
        "checks": checks,
        "overall_pass": all(checks.values()),
        "evidence_boundary": (
            "Exact query result for GAP 4.16.0/PrimGrp 4.0.3; catalogue correctness "
            "and completeness remain an external classification assumption."
        ),
    }
    output = RUN / "results/degree10_primgrp_result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "Degree-10 PrimGrp classification freeze",
        "========================================",
        f"GAP: {result['gap_version']}",
        f"PrimGrp: {result['primgrp_version']}",
        f"catalogue entries: {result['catalogue_count']}",
        f"overall pass: {result['overall_pass']}",
        f"raw output SHA-256: {result['raw_output_sha256']}",
        "",
    ]
    lines.extend(
        f"- {item['catalogue_index']}: order {item['order']}, {item['structure']}"
        for item in groups
    )
    lines.extend(["", f"Boundary: {result['evidence_boundary']}"])
    (RUN / "results/degree10_primgrp_summary.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if not result["overall_pass"]:
        raise SystemExit("degree-10 PrimGrp freeze failed")


if __name__ == "__main__":
    main()
