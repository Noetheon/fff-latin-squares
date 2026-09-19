#!/usr/bin/env python3
"""Incrementally block concrete odd row/column/symbol cycles."""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

from pysat.solvers import Solver


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "repro_runs/2026-04-27_nonpower_fff_obstruction/scripts/validate_fff_table.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xvar(n: int, row: int, col: int, symbol: int) -> int:
    return row * n * n + col * n + symbol + 1


def exactly_one(literals: list[int]) -> list[list[int]]:
    clauses = [literals]
    clauses.extend([-left, -right] for left, right in combinations(literals, 2))
    return clauses


def base_latin_clauses(n: int, row1: list[int]) -> list[list[int]]:
    clauses: list[list[int]] = []
    for row in range(n):
        for col in range(n):
            clauses.extend(exactly_one([xvar(n, row, col, symbol) for symbol in range(n)]))
    for row in range(n):
        for symbol in range(n):
            clauses.extend(exactly_one([xvar(n, row, col, symbol) for col in range(n)]))
    for col in range(n):
        for symbol in range(n):
            clauses.extend(exactly_one([xvar(n, row, col, symbol) for row in range(n)]))
    for index in range(n):
        clauses.append([xvar(n, 0, index, index)])
        clauses.append([xvar(n, index, 0, index)])
        clauses.append([xvar(n, 1, index, row1[index])])
    return clauses


def decode_table(model: list[int], n: int) -> list[list[int]]:
    positive = {literal for literal in model if literal > 0}
    table = []
    for row in range(n):
        decoded_row = []
        for col in range(n):
            values = [symbol for symbol in range(n) if xvar(n, row, col, symbol) in positive]
            if len(values) != 1:
                raise ValueError(f"cell ({row},{col}) has values {values}")
            decoded_row.append(values[0])
        table.append(decoded_row)
    return table


def view_lines(table: list[list[int]], view: str) -> list[list[int]]:
    n = len(table)
    if view == "row":
        return table
    if view == "col":
        return [[table[row][col] for row in range(n)] for col in range(n)]
    return [
        [next(row for row in range(n) if table[row][col] == symbol) for col in range(n)]
        for symbol in range(n)
    ]


def induced_permutation(lines: list[list[int]], first: int, second: int) -> list[int]:
    inverse = [0] * len(lines)
    for index, value in enumerate(lines[second]):
        inverse[value] = index
    return [inverse[value] for value in lines[first]]


def cycles(permutation: list[int]) -> list[list[int]]:
    seen = [False] * len(permutation)
    result = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        cycle = []
        cursor = start
        while not seen[cursor]:
            seen[cursor] = True
            cycle.append(cursor)
            cursor = permutation[cursor]
        result.append(cycle)
    return result


class LazyEncoder:
    def __init__(self, n: int, solver: Solver, clauses: list[list[int]]) -> None:
        self.n = n
        self.solver = solver
        self.clauses = clauses
        self.next_variable = n**3 + 1
        self.equality_variables: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
        self.same_row_variables: dict[tuple[int, int, int, int], int] = {}
        self.blockers: set[tuple[int, ...]] = set()

    def equality_variable(self, left: tuple[int, int], right: tuple[int, int]) -> int:
        key = tuple(sorted((left, right)))
        if key in self.equality_variables:
            return self.equality_variables[key]
        variable = self.next_variable
        self.next_variable += 1
        self.equality_variables[key] = variable
        for symbol in range(self.n):
            equality_implies_aux = [-xvar(self.n, *left, symbol), -xvar(self.n, *right, symbol), variable]
            aux_implies_equality = [-variable, -xvar(self.n, *left, symbol), xvar(self.n, *right, symbol)]
            self.solver.add_clause(equality_implies_aux)
            self.solver.add_clause(aux_implies_equality)
            self.clauses.append(equality_implies_aux)
            self.clauses.append(aux_implies_equality)
        return variable

    def same_row_variable(self, first_symbol: int, first_col: int, second_symbol: int, second_col: int) -> int:
        key = (first_symbol, first_col, second_symbol, second_col)
        if key in self.same_row_variables:
            return self.same_row_variables[key]
        variable = self.next_variable
        self.next_variable += 1
        self.same_row_variables[key] = variable
        for row in range(self.n):
            incidence_implies_aux = [
                -xvar(self.n, row, first_col, first_symbol),
                -xvar(self.n, row, second_col, second_symbol),
                variable,
            ]
            aux_implies_incidence = [
                -variable,
                -xvar(self.n, row, first_col, first_symbol),
                xvar(self.n, row, second_col, second_symbol),
            ]
            self.solver.add_clause(incidence_implies_aux)
            self.solver.add_clause(aux_implies_incidence)
            self.clauses.append(incidence_implies_aux)
            self.clauses.append(aux_implies_incidence)
        return variable

    def add_blocker(self, clause: list[int]) -> bool:
        normalized = tuple(sorted(set(clause)))
        if normalized in self.blockers:
            return False
        self.blockers.add(normalized)
        materialized = list(normalized)
        self.solver.add_clause(materialized)
        self.clauses.append(materialized)
        return True

    def block_odd_cycles(self, table: list[list[int]]) -> dict[str, int]:
        added = Counter()
        n = self.n
        for view in ("row", "col", "sym"):
            lines = view_lines(table, view)
            for first, second in combinations(range(n), 2):
                permutation = induced_permutation(lines, first, second)
                for cycle in cycles(permutation):
                    if len(cycle) % 2 == 0:
                        continue
                    if view == "row":
                        clause = []
                        for index, point in enumerate(cycle):
                            successor = cycle[(index + 1) % len(cycle)]
                            clause.append(-self.equality_variable((first, point), (second, successor)))
                    elif view == "col":
                        clause = []
                        for index, point in enumerate(cycle):
                            successor = cycle[(index + 1) % len(cycle)]
                            clause.append(-self.equality_variable((point, first), (successor, second)))
                    else:
                        clause = []
                        for index, col in enumerate(cycle):
                            successor_col = cycle[(index + 1) % len(cycle)]
                            clause.append(
                                -self.same_row_variable(first, col, second, successor_col)
                            )
                    if self.add_blocker(clause):
                        added[view] += 1
        return dict(added)


def solve_with_deadline(solver: Solver, seconds: float) -> bool | None:
    timer = threading.Timer(seconds, solver.interrupt)
    timer.start()
    try:
        result = solver.solve_limited(expect_interrupt=True)
    finally:
        timer.cancel()
        solver.clear_interrupt()
    return result


def write_dimacs(path: Path, variables: int, clauses: list[list[int]]) -> None:
    with path.open("wt", encoding="ascii") as handle:
        handle.write(f"p cnf {variables} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row1-cases", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--progress-every", type=int, default=100)
    args = parser.parse_args()
    args.row1_cases = args.row1_cases.resolve()
    args.output_prefix = args.output_prefix.resolve()
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)

    cases_payload = json.loads(args.row1_cases.read_text(encoding="utf-8"))
    case = next(case for case in cases_payload["cases"] if case["case_id"] == args.case_id)
    row1 = [int(value) for value in case["row1_permutation"]]
    n = 10
    clauses = base_latin_clauses(n, row1)
    start = time.monotonic()
    deadline = start + args.timeout
    iteration = 0
    best: dict[str, Any] | None = None
    status = "unknown"
    with Solver(name=args.solver, bootstrap_with=clauses) as solver:
        encoder = LazyEncoder(n, solver, clauses)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                status = "timeout"
                break
            solved = solve_with_deadline(solver, remaining)
            if solved is None:
                status = "timeout"
                break
            if solved is False:
                status = "unsat"
                break
            iteration += 1
            table = decode_table(solver.get_model(), n)
            profile_counts = {}
            total_failures = 0
            for view in ("row", "col", "sym"):
                lines = view_lines(table, view)
                failed = 0
                odd_cycles = 0
                for first, second in combinations(range(n), 2):
                    odd = [cycle for cycle in cycles(induced_permutation(lines, first, second)) if len(cycle) % 2]
                    if odd:
                        failed += 1
                        odd_cycles += len(odd)
                profile_counts[view] = {"failed_pairs": failed, "odd_cycles": odd_cycles}
                total_failures += failed
            if best is None or total_failures < best["total_failed_pairs"]:
                best = {
                    "iteration": iteration,
                    "total_failed_pairs": total_failures,
                    "profile": profile_counts,
                    "table": table,
                }
                args.output_prefix.with_name(args.output_prefix.name + "_best_table.json").write_text(
                    json.dumps({"table": table}, indent=2) + "\n", encoding="utf-8"
                )
            if total_failures == 0:
                status = "sat"
                break
            added = encoder.block_odd_cycles(table)
            if not added:
                raise RuntimeError("non-FFF model produced no new odd-cycle blocker")
            if iteration % args.progress_every == 0:
                print(
                    json.dumps(
                        {
                            "iteration": iteration,
                            "best_failed_pairs": best["total_failed_pairs"],
                            "blockers": len(encoder.blockers),
                            "equalities": len(encoder.equality_variables),
                            "elapsed": round(time.monotonic() - start, 3),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        variable_count = encoder.next_variable - 1
        blocker_count = len(encoder.blockers)
        equality_count = len(encoder.equality_variables)
        same_row_count = len(encoder.same_row_variables)

    cnf_path = args.output_prefix.with_suffix(".cnf")
    write_dimacs(cnf_path, variable_count, clauses)
    best_table_path = args.output_prefix.with_name(args.output_prefix.name + "_best_table.json")
    validation = None
    if best_table_path.exists():
        validation_path = args.output_prefix.with_name(args.output_prefix.name + "_best_validation.json")
        validation_summary = args.output_prefix.with_name(args.output_prefix.name + "_best_validation_summary.txt")
        import subprocess
        run = subprocess.run(
            ["python3", str(VALIDATOR), "--input", str(best_table_path), "--expect-reduced", "--output", str(validation_path), "--summary", str(validation_summary)],
            text=True, capture_output=True, check=False,
        )
        if run.returncode != 0:
            raise RuntimeError(f"independent validation failed: {run.stderr}")
        checked = json.loads(validation_path.read_text(encoding="utf-8"))
        validation = {
            "latin": checked["latin"]["latin"],
            "reduced": checked["reduced"],
            "pattern": checked["pattern_name"],
            "fff": checked["fff"],
            "sha256": sha256_file(validation_path),
        }
    payload = {
        "run_id": "2026-08-09_nonpower_fff_cube_refinement",
        "method": "incremental lazy concrete odd-cycle blocking",
        "encoding_proof": "proof_notes/fff_lazy_odd_cycle_blocking.md",
        "row1_case_id": args.case_id,
        "row1_permutation": row1,
        "solver": args.solver,
        "timeout_seconds": args.timeout,
        "elapsed_seconds": time.monotonic() - start,
        "status": status,
        "iterations": iteration,
        "base_clause_count": len(base_latin_clauses(n, row1)),
        "final_clause_count": len(clauses),
        "final_variable_count": variable_count,
        "equality_variable_count": equality_count,
        "same_row_variable_count": same_row_count,
        "odd_cycle_blocker_count": blocker_count,
        "best": best,
        "independent_validation": validation,
        "final_cnf": {"path": str(cnf_path.relative_to(ROOT)), "sha256": sha256_file(cnf_path)},
        "proof_certificate": None,
        "claim_impact": {"C38": "open", "C40": "not_created"},
    }
    status_path = args.output_prefix.with_name(args.output_prefix.name + "_status.json")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.txt")
    status_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(
        "\n".join(
            [
                "Lazy odd-cycle CEGAR summary",
                "",
                f"row1_case: {args.case_id}",
                f"solver: {args.solver}",
                f"timeout_seconds: {args.timeout}",
                f"status: {status}",
                f"iterations: {iteration}",
                f"odd_cycle_blockers: {blocker_count}",
                f"equality_variables: {equality_count}",
                f"same_row_variables: {same_row_count}",
                f"best_failed_pairs: {best['total_failed_pairs'] if best else None}",
                f"best_profile: {best['profile'] if best else None}",
                f"best_validation: {validation}",
                f"final_cnf_sha256: {payload['final_cnf']['sha256']}",
                "C38: open" if status != "sat" else "C38: potential counterexample requires confirmation",
                "C40: not_created",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "iterations": iteration, "best": best["total_failed_pairs"] if best else None}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
