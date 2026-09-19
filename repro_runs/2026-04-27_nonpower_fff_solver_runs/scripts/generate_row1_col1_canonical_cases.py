#!/usr/bin/env python3
"""Generate complete n=10 row1+col1 canonical split cases."""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


N = 10


def cycles_of_perm(perm: list[int] | tuple[int, ...]) -> list[list[int]]:
    seen = [False] * len(perm)
    cycles: list[list[int]] = []
    for start in range(len(perm)):
        if seen[start]:
            continue
        cycle = []
        value = start
        while not seen[value]:
            seen[value] = True
            cycle.append(value)
            value = perm[value]
        cycles.append(cycle)
    return cycles


def cycle_notation(perm: list[int] | tuple[int, ...]) -> str:
    cycles = cycles_of_perm(perm)
    parts = ["(" + " ".join(str(value) for value in cycle) + ")" for cycle in cycles if len(cycle) > 1]
    return "".join(parts) if parts else "()"


def partition(perm: list[int] | tuple[int, ...]) -> list[int]:
    return sorted((len(cycle) for cycle in cycles_of_perm(perm)), reverse=True)


def zero_cycle_length(perm: list[int] | tuple[int, ...]) -> int:
    for cycle in cycles_of_perm(perm):
        if 0 in cycle:
            return len(cycle)
    raise AssertionError("0 missing from permutation")


def invert(perm: tuple[int, ...]) -> tuple[int, ...]:
    inv = [0] * len(perm)
    for idx, value in enumerate(perm):
        inv[value] = idx
    return tuple(inv)


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[right[idx]] for idx in range(len(left)))


def conjugate_tau(pi: tuple[int, ...], tau: tuple[int, ...]) -> tuple[int, ...]:
    return compose(compose(pi, tau), invert(pi))


def commutes_with_sigma(pi: tuple[int, ...], sigma: tuple[int, ...]) -> bool:
    return compose(pi, sigma) == compose(sigma, pi)


def residual_group_for_sigma(sigma: list[int]) -> list[tuple[int, ...]]:
    sigma_tuple = tuple(sigma)
    cycles = cycles_of_perm(sigma)
    zero_cycle = next(cycle for cycle in cycles if 0 in cycle)
    nonzero_by_length: dict[int, list[list[int]]] = defaultdict(list)
    for cycle in cycles:
        if cycle is zero_cycle:
            continue
        nonzero_by_length[len(cycle)].append(cycle)

    base_map = {value: value for value in zero_cycle}
    partial_maps = [base_map]

    for length in sorted(nonzero_by_length):
        group_cycles = nonzero_by_length[length]
        additions: list[dict[int, int]] = []
        for cycle_perm in itertools.permutations(range(len(group_cycles))):
            for rotations in itertools.product(range(length), repeat=len(group_cycles)):
                mapping: dict[int, int] = {}
                for source_index, target_index in enumerate(cycle_perm):
                    source = group_cycles[source_index]
                    target = group_cycles[target_index]
                    rotation = rotations[source_index]
                    for pos, source_value in enumerate(source):
                        mapping[source_value] = target[(pos + rotation) % length]
                additions.append(mapping)
        combined: list[dict[int, int]] = []
        for partial in partial_maps:
            for addition in additions:
                merged = dict(partial)
                merged.update(addition)
                combined.append(merged)
        partial_maps = combined

    group: set[tuple[int, ...]] = set()
    for mapping in partial_maps:
        pi = tuple(mapping[idx] for idx in range(N))
        if pi[0] != 0:
            raise AssertionError("residual group generator did not fix 0")
        if not commutes_with_sigma(pi, sigma_tuple):
            raise AssertionError("residual group generator produced non-centralizer element")
        group.add(pi)
    return sorted(group)


def compatible_tau_permutations(sigma: list[int]) -> list[tuple[int, ...]]:
    fixed_0 = 1
    fixed_1 = sigma[1]
    used = {fixed_0, fixed_1}
    if len(used) != 2:
        return []
    positions = list(range(2, N))
    values = [value for value in range(N) if value not in used]
    compatible: list[tuple[int, ...]] = []
    for tail in itertools.permutations(values):
        tau = [None] * N
        tau[0] = fixed_0
        tau[1] = fixed_1
        for pos, value in zip(positions, tail):
            tau[pos] = value
        tau_int = tuple(int(value) for value in tau if value is not None)
        if len(tau_int) != N:
            raise AssertionError("incomplete tau")
        if any(tau_int[idx] == idx for idx in range(N)):
            continue
        if any(len(cycle) % 2 for cycle in cycles_of_perm(tau_int)):
            continue
        compatible.append(tau_int)
    return compatible


def orbit_representatives(taus: list[tuple[int, ...]], group: list[tuple[int, ...]]) -> list[dict[str, Any]]:
    unseen = set(taus)
    representatives: list[dict[str, Any]] = []
    while unseen:
        tau = min(unseen)
        orbit = {conjugate_tau(pi, tau) for pi in group}
        rep = min(orbit)
        representatives.append({"representative": rep, "orbit_size": len(orbit)})
        unseen.difference_update(orbit)
    representatives.sort(key=lambda item: item["representative"])
    return representatives


def read_row1_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    cases = payload["cases"] if isinstance(payload, dict) and "cases" in payload else payload
    return list(cases)


def make_summary(payload: dict[str, Any]) -> str:
    lines = [
        "n=10 row1+col1 canonical split cases",
        "",
        f"row1_case_count: {payload['row1_case_count']}",
        f"total_row1_col1_cases: {payload['case_count']}",
        "",
        "Counts by row1 case:",
    ]
    for entry in payload["counts_by_row1_case"]:
        lines.append(
            "- {row1_case_id}: residual_group_size={residual_group_size}, compatible_tau_count={compatible_tau_count}, orbit_case_count={orbit_case_count}".format(
                **entry
            )
        )
    lines.extend(
        [
            "",
            "Coverage:",
            "For each fixed row1 permutation sigma, the cases are lexicographically minimal representatives of all compatible col1 permutations tau under the residual centralizer G_sigma. This is the complete row1+col1 split for reduced row+column-F and FFF searches.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row1-cases-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    row1_cases = read_row1_cases(args.row1_cases_json)
    output_cases: list[dict[str, Any]] = []
    counts: list[dict[str, Any]] = []
    global_case_index = 1

    for row1_case in row1_cases:
        sigma = [int(value) for value in row1_case["row1_permutation"]]
        if sigma[0] != 1:
            raise ValueError(f"row1 case {row1_case['case_id']} does not have sigma(0)=1")
        group = residual_group_for_sigma(sigma)
        taus = compatible_tau_permutations(sigma)
        reps = orbit_representatives(taus, group)
        counts.append(
            {
                "row1_case_id": row1_case["case_id"],
                "row1_partition": row1_case["partition"],
                "row1_zero_cycle_length": row1_case["zero_cycle_length"],
                "residual_group_size": len(group),
                "compatible_tau_count": len(taus),
                "orbit_case_count": len(reps),
            }
        )
        for local_index, rep_entry in enumerate(reps, start=1):
            tau = list(rep_entry["representative"])
            case_id = f"n10_row1col1_case_{global_case_index:04d}__{row1_case['case_id']}__c{local_index:03d}"
            output_cases.append(
                {
                    "case_id": case_id,
                    "row1_case_id": row1_case["case_id"],
                    "row1_partition": row1_case["partition"],
                    "row1_zero_cycle_length": row1_case["zero_cycle_length"],
                    "row1_permutation": sigma,
                    "row1_cycle_notation": row1_case["cycle_notation"],
                    "col1_case_id": f"{row1_case['case_id']}__col1_orbit_{local_index:03d}",
                    "col1_partition": partition(tau),
                    "col1_zero_cycle_length": zero_cycle_length(tau),
                    "col1_permutation": tau,
                    "col1_cycle_notation": cycle_notation(tau),
                    "residual_group_size": len(group),
                    "orbit_size": rep_entry["orbit_size"],
                    "compatibility_checks": {
                        "col1_is_permutation": sorted(tau) == list(range(N)),
                        "col1_0_equals_1": tau[0] == 1,
                        "col1_1_equals_row1_1": tau[1] == sigma[1],
                        "col1_fixed_point_free": all(tau[idx] != idx for idx in range(N)),
                        "col1_all_cycles_even": all(len(cycle) % 2 == 0 for cycle in cycles_of_perm(tau)),
                    },
                    "coverage_note": (
                        "Lexicographically minimal representative of a compatible col1 orbit under "
                        f"the residual centralizer of row1 case {row1_case['case_id']}."
                    ),
                }
            )
            global_case_index += 1

    payload = {
        "n": N,
        "source_row1_cases_json": str(args.row1_cases_json),
        "row1_case_count": len(row1_cases),
        "case_count": len(output_cases),
        "counts_by_row1_case": counts,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "elapsed_seconds": time.time() - start,
        "coverage_note": (
            "Complete row1+col1 split: all compatible fixed-point-free even-cycle col1 permutations "
            "are quotient by the residual centralizer of each fixed row1 case."
        ),
        "cases": output_cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
