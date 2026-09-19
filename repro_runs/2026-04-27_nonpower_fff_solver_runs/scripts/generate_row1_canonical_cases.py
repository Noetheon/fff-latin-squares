#!/usr/bin/env python3
"""Generate canonical row-1 permutations for the n=10 FFF split."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Any


PARTITIONS = [
    [10],
    [8, 2],
    [6, 4],
    [6, 2, 2],
    [4, 4, 2],
    [4, 2, 2, 2],
    [2, 2, 2, 2, 2],
]


def cycles_to_permutation(n: int, cycles: list[list[int]]) -> list[int]:
    perm = list(range(n))
    for cycle in cycles:
        for idx, value in enumerate(cycle):
            perm[value] = cycle[(idx + 1) % len(cycle)]
    return perm


def cycle_notation(cycles: list[list[int]]) -> str:
    return "".join("(" + " ".join(str(value) for value in cycle) + ")" for cycle in cycles)


def build_case(partition: list[int], zero_cycle_length: int, index: int) -> dict[str, Any]:
    remaining_lengths = list(partition)
    remaining_lengths.remove(zero_cycle_length)
    cycles = [list(range(zero_cycle_length))]
    next_value = zero_cycle_length
    for length in sorted(remaining_lengths, reverse=True):
        cycles.append(list(range(next_value, next_value + length)))
        next_value += length
    perm = cycles_to_permutation(sum(partition), cycles)
    return {
        "case_id": f"n10_row1_case_{index:02d}_z{zero_cycle_length}_{'_'.join(str(v) for v in partition)}",
        "partition": partition,
        "zero_cycle_length": zero_cycle_length,
        "row1_permutation": perm,
        "cycle_notation": cycle_notation(cycles),
        "coverage_note": (
            "Canonical representative for reduced row 1 with even cycle partition "
            f"{'+'.join(str(v) for v in partition)} and zero-cycle length {zero_cycle_length}. "
            "The zero cycle is oriented as (0 1 ...), so L(1,0)=1."
        ),
    }


def generate_cases() -> list[dict[str, Any]]:
    cases = []
    for partition in PARTITIONS:
        for zero_cycle_length in sorted(set(partition), reverse=True):
            cases.append(build_case(partition, zero_cycle_length, len(cases) + 1))
    return cases


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_summary(payload: dict[str, Any]) -> str:
    lines = [
        "n=10 canonical row1 split cases",
        "",
        f"case_count: {payload['case_count']}",
        f"partitions: {', '.join(payload['partition_labels'])}",
        "",
    ]
    for case in payload["cases"]:
        lines.append(
            "{case_id}: partition={partition}, zero_cycle_length={zero}, row1={row1}, cycles={cycles}".format(
                case_id=case["case_id"],
                partition="+".join(str(v) for v in case["partition"]),
                zero=case["zero_cycle_length"],
                row1=case["row1_permutation"],
                cycles=case["cycle_notation"],
            )
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    cases = generate_cases()
    payload = {
        "n": 10,
        "case_count": len(cases),
        "partitions": PARTITIONS,
        "partition_labels": ["+".join(str(v) for v in partition) for partition in PARTITIONS],
        "definition": "Canonical fixed row 1 permutations for reduced row-F searches.",
        "proof_note": "proof_notes/fff_reduced_row1_symmetry_breaking.md",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "elapsed_seconds": time.time() - start,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    summary = make_summary(payload)
    summary += f"\njson_sha256: {sha256_file(args.output)}\n"
    args.summary.write_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
