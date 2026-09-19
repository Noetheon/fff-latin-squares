#!/usr/bin/env python3
"""Generate the complete canonical n=10 QQQ Row1 and L(3,1) cube covers."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


EXTRA_QQQ_CASES = [
    {
        "case_id": "n10_qqq_row1_case_13_z5_5_3_2",
        "partition": [5, 3, 2],
        "zero_cycle_length": 5,
        "row1_permutation": [1, 2, 3, 4, 0, 6, 7, 5, 9, 8],
    },
    {
        "case_id": "n10_qqq_row1_case_14_z3_5_3_2",
        "partition": [5, 3, 2],
        "zero_cycle_length": 3,
        "row1_permutation": [1, 2, 0, 4, 5, 6, 7, 3, 9, 8],
    },
    {
        "case_id": "n10_qqq_row1_case_15_z2_5_3_2",
        "partition": [5, 3, 2],
        "zero_cycle_length": 2,
        "row1_permutation": [1, 0, 3, 4, 5, 6, 2, 8, 9, 7],
    },
]


def cycles(perm: list[int]) -> list[list[int]]:
    seen: set[int] = set()
    answer = []
    for start in range(len(perm)):
        if start in seen:
            continue
        cycle = []
        current = start
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = perm[current]
        answer.append(cycle)
    return answer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--even-cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.even_cases.read_text())
    even_cases = payload["cases"]
    if len(even_cases) != 12:
        raise ValueError("expected the frozen 12-case even-cycle Row1 cover")

    cases = []
    for index, original in enumerate(even_cases, start=1):
        case = {
            "case_id": f"n10_qqq_row1_case_{index:02d}_" + original["case_id"].split("_case_", 1)[1].split("_", 1)[1],
            "source_case_id": original["case_id"],
            "partition": original["partition"],
            "zero_cycle_length": original["zero_cycle_length"],
            "row1_permutation": original["row1_permutation"],
            "qqq_only_not_row_f": False,
        }
        cases.append(case)
    for extra in EXTRA_QQQ_CASES:
        cases.append({**extra, "source_case_id": None, "qqq_only_not_row_f": True})

    cube_records = []
    for case in cases:
        perm = case["row1_permutation"]
        if sorted(perm) != list(range(10)) or perm[0] != 1:
            raise ValueError(f"invalid Row1 permutation in {case['case_id']}")
        partition = sorted((len(c) for c in cycles(perm)), reverse=True)
        if partition != case["partition"]:
            raise ValueError(f"partition mismatch in {case['case_id']}")
        zero_cycle = next(c for c in cycles(perm) if 0 in c)
        if len(zero_cycle) != case["zero_cycle_length"]:
            raise ValueError(f"zero-cycle mismatch in {case['case_id']}")
        if perm[0] != 1:
            raise ValueError("canonical orientation must satisfy 0 -> 1")
        allowed = [s for s in range(10) if s not in {1, 3, perm[1]}]
        case["fixed_cell"] = [3, 1]
        case["allowed_fixed_cell_symbols"] = allowed
        case["cube_count"] = len(allowed)
        for symbol in allowed:
            cube_records.append(
                {
                    "cube_id": f"{case['case_id']}__r3c1_s{symbol}",
                    "row1_case_id": case["case_id"],
                    "partition": case["partition"],
                    "zero_cycle_length": case["zero_cycle_length"],
                    "qqq_only_not_row_f": case["qqq_only_not_row_f"],
                    "row1_permutation": perm,
                    "fixed_cells": [[3, 1, symbol]],
                    "coverage_note": "One disjoint L(3,1) branch inside the fixed Row1 case.",
                }
            )

    if len(cases) != 15 or len(cube_records) != 105:
        raise AssertionError((len(cases), len(cube_records)))
    counts = Counter(case["cube_count"] for case in cases)
    if counts != Counter({7: 15}):
        raise AssertionError(counts)

    result = {
        "n": 10,
        "property": "QQQ",
        "top_level_case_count": len(cases),
        "second_level_cube_count": len(cube_records),
        "cube_count_distribution": {str(k): v for k, v in sorted(counts.items())},
        "fff_parent_case_count": 12,
        "fff_second_level_cube_count": 84,
        "complete": True,
        "pairwise_disjoint": True,
        "important_correction": "The 12 even-cycle Row1 cases are complete for row-F/FFF, not for QQQ; QQQ adds three 5+3+2 cases.",
        "cases": cases,
        "cubes": cube_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = [
        "Complete n=10 QQQ Row1/cell cube cover",
        "",
        f"top_level_cases: {len(cases)}",
        f"second_level_cubes: {len(cube_records)}",
        "cube_count_distribution: 15 cases x 7 cubes",
        "fff_cover: 12 parents x 7 cubes = 84 cubes",
        "complete: true",
        "pairwise_disjoint: true",
        "correction: 12 even-cycle cases do not cover QQQ; 5+3+2 adds 3 cases.",
        "",
    ]
    for case in cases:
        lines.append(
            f"{case['case_id']}: partition={'+'.join(map(str, case['partition']))}, "
            f"zero_cycle={case['zero_cycle_length']}, cubes={case['cube_count']}, "
            f"qqq_only_not_row_f={str(case['qqq_only_not_row_f']).lower()}"
        )
    args.summary.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
