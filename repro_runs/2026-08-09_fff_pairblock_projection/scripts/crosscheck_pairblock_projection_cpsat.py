#!/usr/bin/env python3
"""Independent CP-SAT cross-check of the projection-voltage model."""

from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

from ortools.sat.python import cp_model


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def cycles(permutation: tuple[int, ...]) -> list[tuple[int, ...]]:
    seen = set()
    result = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycle = []
        current = start
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = permutation[current]
        result.append(tuple(cycle))
    return result


def xor_result(model: cp_model.CpModel, variables: list[cp_model.IntVar], name: str) -> cp_model.IntVar:
    current = variables[0]
    for index, variable in enumerate(variables[1:], 1):
        out = model.new_bool_var(f"{name}_{index}")
        model.add_bool_xor([current, variable, out.negated()])
        current = out
    return current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    p = args.p
    permutations = list(itertools.permutations(range(p)))
    identity = permutations.index(tuple(range(p)))
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"y_{index}") for index in range(len(permutations))]
    flips = [
        [model.new_bool_var(f"f_{index}_{source}") for source in range(p)]
        for index in range(len(permutations))
    ]
    model.add(selected[identity] == 1)
    for bit in flips[identity]:
        model.add(bit == 0)
    for index in range(len(permutations)):
        for bit in flips[index]:
            model.add(bit <= selected[index])
    for source in range(p):
        for target in range(p):
            indices = [index for index, phi in enumerate(permutations) if phi[source] == target]
            model.add(sum(selected[index] for index in indices) == 2)
            model.add(sum(flips[index][source] for index in indices) == 1)
    odd_cycle_constraints = 0
    for left in range(len(permutations)):
        for right in range(left + 1, len(permutations)):
            right_inverse = inverse(permutations[right])
            quotient = tuple(right_inverse[permutations[left][source]] for source in range(p))
            for cycle in cycles(quotient):
                if len(cycle) % 2 == 0:
                    continue
                variables = [flips[left][source] for source in cycle] + [
                    flips[right][source] for source in cycle
                ]
                parity = xor_result(model, variables, f"xor_{left}_{right}_{odd_cycle_constraints}")
                model.add(parity == 1).only_enforce_if([selected[left], selected[right]])
                odd_cycle_constraints += 1
    build_variables = len(model.proto.variables)
    build_constraints = len(model.proto.constraints)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.timeout
    solver.parameters.num_search_workers = args.workers
    start = time.perf_counter()
    status = solver.solve(model)
    elapsed = time.perf_counter() - start
    raw = solver.status_name(status).lower()
    result = {"optimal": "sat", "feasible": "sat", "infeasible": "unsat", "unknown": "timeout"}.get(raw, raw)
    payload = {
        "encoding": "independent_pairblock_projection_cpsat_v1",
        "p": p,
        "degree": 2 * p,
        "variables": build_variables,
        "constraints": build_constraints,
        "odd_cycle_voltage_constraints": odd_cycle_constraints,
        "timeout_seconds": args.timeout,
        "workers": args.workers,
        "elapsed_seconds": elapsed,
        "result": result,
        "proof_certificate_available": False,
        "solver_stats": solver.response_stats(),
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Independent pair-block projection CP-SAT cross-check\n\n"
        f"p: {p}\ndegree: {2*p}\nvariables: {build_variables}\n"
        f"constraints: {build_constraints}\nresult: {result}\n"
        f"elapsed_seconds: {elapsed:.6f}\nproof_certificate_available: false\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
