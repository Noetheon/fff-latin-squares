#!/usr/bin/env python3
"""Enumerate n=10 symbol01 canonical split counts after row1/row1+col1 fixing."""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import time
from collections import Counter, defaultdict
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
    parts = ["(" + " ".join(str(value) for value in cycle) + ")" for cycle in cycles_of_perm(perm) if len(cycle) > 1]
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


def conjugate(pi: tuple[int, ...], perm: tuple[int, ...]) -> tuple[int, ...]:
    return compose(compose(pi, perm), invert(pi))


def commutes(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    return compose(left, right) == compose(right, left)


def residual_group_for_sigma(sigma: list[int]) -> list[tuple[int, ...]]:
    sigma_tuple = tuple(sigma)
    cycles = cycles_of_perm(sigma)
    zero_cycle = next(cycle for cycle in cycles if 0 in cycle)
    nonzero_by_length: dict[int, list[list[int]]] = defaultdict(list)
    for cycle in cycles:
        if cycle is zero_cycle:
            continue
        nonzero_by_length[len(cycle)].append(cycle)

    partial_maps: list[dict[int, int]] = [{value: value for value in zero_cycle}]
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
            raise AssertionError("residual group element did not fix 0")
        if not commutes(pi, sigma_tuple):
            raise AssertionError("residual group element does not commute with sigma")
        group.add(pi)
    return sorted(group)


def residual_group_for_sigma_tau(sigma: list[int], tau: list[int]) -> list[tuple[int, ...]]:
    tau_tuple = tuple(tau)
    return [pi for pi in residual_group_for_sigma(sigma) if conjugate(pi, tau_tuple) == tau_tuple]


def compatible_symbol01_permutations(sigma: list[int]) -> list[tuple[int, ...]]:
    pred_zero = sigma.index(0)
    forced = {0: 1, pred_zero: 0}
    if len(set(forced)) != len(set(forced.values())):
        return []
    positions = [idx for idx in range(N) if idx not in forced]
    values = [value for value in range(N) if value not in set(forced.values())]
    compatible: list[tuple[int, ...]] = []
    for tail in itertools.permutations(values):
        nu = [None] * N
        for pos, value in forced.items():
            nu[pos] = value
        for pos, value in zip(positions, tail):
            nu[pos] = value
        nu_tuple = tuple(int(value) for value in nu if value is not None)
        if len(nu_tuple) != N:
            raise AssertionError("incomplete symbol01 permutation")
        if any(nu_tuple[idx] == idx for idx in range(N)):
            continue
        if any(len(cycle) % 2 for cycle in cycles_of_perm(nu_tuple)):
            continue
        compatible.append(nu_tuple)
    return compatible


def orbit_representatives(perms: list[tuple[int, ...]], group: list[tuple[int, ...]]) -> list[dict[str, Any]]:
    unseen = set(perms)
    representatives: list[dict[str, Any]] = []
    while unseen:
        perm = min(unseen)
        orbit = {conjugate(pi, perm) for pi in group}
        rep = min(orbit)
        representatives.append({"representative": rep, "orbit_size": len(orbit)})
        unseen.difference_update(orbit)
    representatives.sort(key=lambda item: item["representative"])
    return representatives


def load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text())
    cases = payload["cases"] if isinstance(payload, dict) and "cases" in payload else payload
    return (payload if isinstance(payload, dict) else {}, list(cases))


def sample_representatives(reps: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    samples = []
    for entry in reps[:limit]:
        perm = list(entry["representative"])
        samples.append(
            {
                "symbol01_permutation": perm,
                "symbol01_partition": partition(perm),
                "symbol01_zero_cycle_length": zero_cycle_length(perm),
                "symbol01_cycle_notation": cycle_notation(perm),
                "orbit_size": entry["orbit_size"],
            }
        )
    return samples


def select_row1_col1_samples(cases: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.row1_col1_sample_case_ids:
        wanted = {case_id.strip() for case_id in args.row1_col1_sample_case_ids.split(",") if case_id.strip()}
        return [case for case in cases if case["case_id"] in wanted]
    return cases[: args.row1_col1_sample_limit]


def make_summary(payload: dict[str, Any]) -> str:
    lines = [
        "n=10 symbol01 canonical split counts",
        "",
        f"row1_case_count: {payload['row1_case_count']}",
        f"row1_symbol01_orbit_total: {payload['row1_symbol01_orbit_total']}",
        f"row1_col1_case_count: {payload['row1_col1_case_count']}",
        "",
        "Counts by row1 case:",
    ]
    for entry in payload["row1_counts"]:
        lines.append(
            "- {row1_case_id}: residual_group_size={residual_group_size}, "
            "compatible_symbol01_count={compatible_symbol01_count}, "
            "symbol01_orbit_count={symbol01_orbit_count}".format(**entry)
        )
    if payload["row1_col1_estimates"]:
        estimate = payload["row1_col1_estimates"]
        lines.extend(
            [
                "",
                "Complete row1+col1+symbol01 size estimates:",
                f"- weighted_pre_orbit_upper_bound: {estimate['weighted_pre_orbit_upper_bound']}",
                f"- weighted_row1_orbit_lower_bound: {estimate['weighted_row1_orbit_lower_bound']}",
                f"- interpretation: {estimate['interpretation']}",
            ]
        )
    if payload["row1_col1_sample_counts"]:
        lines.extend(["", "Sample row1+col1 residual counts:"])
        for entry in payload["row1_col1_sample_counts"]:
            lines.append(
                "- {case_id}: residual_group_size={residual_group_size}, "
                "symbol01_orbit_count={symbol01_orbit_count}, "
                "compatible_symbol01_count={compatible_symbol01_count}".format(**entry)
            )
    lines.extend(
        [
            "",
            "Conclusion:",
            payload["conclusion"],
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row1-cases-json", type=Path, required=True)
    parser.add_argument("--row1-col1-cases-json", type=Path)
    parser.add_argument("--row1-col1-sample-case-ids")
    parser.add_argument("--row1-col1-sample-limit", type=int, default=12)
    parser.add_argument("--representative-sample-limit", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    row1_payload, row1_cases = load_cases(args.row1_cases_json)
    row1_counts: list[dict[str, Any]] = []
    row1_lookup: dict[str, dict[str, Any]] = {}
    row1_symbol01_orbit_total = 0

    for row1_case in row1_cases:
        sigma = [int(value) for value in row1_case["row1_permutation"]]
        group = residual_group_for_sigma(sigma)
        compatible = compatible_symbol01_permutations(sigma)
        reps = orbit_representatives(compatible, group)
        pred_zero = sigma.index(0)
        entry = {
            "row1_case_id": row1_case["case_id"],
            "row1_partition": row1_case["partition"],
            "row1_zero_cycle_length": row1_case["zero_cycle_length"],
            "row1_permutation": sigma,
            "forced_symbol01_values": {"0": 1, str(pred_zero): 0},
            "residual_group_size": len(group),
            "compatible_symbol01_count": len(compatible),
            "symbol01_orbit_count": len(reps),
            "representative_samples": sample_representatives(reps, args.representative_sample_limit),
        }
        row1_counts.append(entry)
        row1_lookup[row1_case["case_id"]] = entry
        row1_symbol01_orbit_total += len(reps)

    row1_col1_payload: dict[str, Any] = {}
    row1_col1_cases: list[dict[str, Any]] = []
    sample_counts: list[dict[str, Any]] = []
    estimates: dict[str, Any] | None = None
    if args.row1_col1_cases_json:
        row1_col1_payload, row1_col1_cases = load_cases(args.row1_col1_cases_json)
        selected = select_row1_col1_samples(row1_col1_cases, args)
        for case in selected:
            sigma = [int(value) for value in case["row1_permutation"]]
            tau = [int(value) for value in case["col1_permutation"]]
            group = residual_group_for_sigma_tau(sigma, tau)
            compatible = compatible_symbol01_permutations(sigma)
            reps = orbit_representatives(compatible, group)
            sample_counts.append(
                {
                    "case_id": case["case_id"],
                    "row1_case_id": case["row1_case_id"],
                    "col1_case_id": case["col1_case_id"],
                    "row1_permutation": sigma,
                    "col1_permutation": tau,
                    "residual_group_size": len(group),
                    "compatible_symbol01_count": len(compatible),
                    "symbol01_orbit_count": len(reps),
                    "representative_samples": sample_representatives(reps, args.representative_sample_limit),
                }
            )

        row1_col1_counts = Counter(case["row1_case_id"] for case in row1_col1_cases)
        weighted_upper = 0
        weighted_lower = 0
        for row1_case_id, case_count in row1_col1_counts.items():
            row1_entry = row1_lookup[row1_case_id]
            weighted_upper += case_count * int(row1_entry["compatible_symbol01_count"])
            weighted_lower += case_count * int(row1_entry["symbol01_orbit_count"])
        estimates = {
            "weighted_pre_orbit_upper_bound": weighted_upper,
            "weighted_row1_orbit_lower_bound": weighted_lower,
            "row1_col1_count_by_row1_case": dict(sorted(row1_col1_counts.items())),
            "interpretation": (
                "The upper bound counts compatible symbol01 permutations before quotienting by the "
                "row1+col1 residual subgroup. The lower bound repeats the coarser row1-level orbit "
                "count for each row1+col1 case. The exact complete row1+col1+symbol01 split was not "
                "enumerated because it is expected to be very large."
            ),
        }

    conclusion = (
        "A complete naive row1+col1+symbol01 split is not a practical next full portfolio target. "
        "The symbol01 split should first be used selectively or combined with additional propagation, "
        "because the weighted pre-orbit upper bound is large."
        if estimates
        else "Only row1-level symbol01 counts were generated."
    )
    payload = {
        "n": N,
        "source_row1_cases_json": str(args.row1_cases_json),
        "source_row1_cases_sha256": row1_payload.get("source_sha256"),
        "source_row1_col1_cases_json": str(args.row1_col1_cases_json) if args.row1_col1_cases_json else None,
        "row1_case_count": len(row1_cases),
        "row1_symbol01_orbit_total": row1_symbol01_orbit_total,
        "row1_counts": row1_counts,
        "row1_col1_case_count": len(row1_col1_cases),
        "row1_col1_estimates": estimates,
        "row1_col1_sample_counts": sample_counts,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "elapsed_seconds": time.time() - start,
        "conclusion": conclusion,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
