#!/usr/bin/env python3
"""Build exact SAT/CP constraints for reduced Latin-square FFF search."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


ALL_VIEWS = ("row", "col", "sym")


class VarPool:
    def __init__(self) -> None:
        self.next_id = 1
        self.names: dict[str, int] = {}

    def var(self, name: str) -> int:
        if name not in self.names:
            self.names[name] = self.next_id
            self.next_id += 1
        return self.names[name]

    @property
    def count(self) -> int:
        return self.next_id - 1


def exactly_one(clauses: list[list[int]], vars_: list[int]) -> None:
    clauses.append(list(vars_))
    for i, left in enumerate(vars_):
        for right in vars_[i + 1 :]:
            clauses.append([-left, -right])


def add_neq_if_both(clauses: list[list[int]], a: int, b: int, color_left: int, color_right: int) -> None:
    # a and b => color_left != color_right.
    clauses.append([-a, -b, color_left, color_right])
    clauses.append([-a, -b, -color_left, -color_right])


def build_cnf(n: int, views: tuple[str, ...]) -> dict[str, Any]:
    pool = VarPool()
    clauses: list[list[int]] = []
    stats = {
        "latin_clauses": 0,
        "reduced_unit_clauses": 0,
        "row_fff_clauses": 0,
        "col_fff_clauses": 0,
        "sym_fff_clauses": 0,
    }

    def x(r: int, c: int, s: int) -> int:
        return pool.var(f"x_{r}_{c}_{s}")

    def row_color(a: int, b: int, c: int) -> int:
        return pool.var(f"row_color_{a}_{b}_{c}")

    def col_color(c: int, d: int, r: int) -> int:
        return pool.var(f"col_color_{c}_{d}_{r}")

    def sym_color(u: int, v: int, j: int) -> int:
        return pool.var(f"sym_color_{u}_{v}_{j}")

    before = len(clauses)
    for r in range(n):
        for c in range(n):
            exactly_one(clauses, [x(r, c, s) for s in range(n)])
    for r in range(n):
        for s in range(n):
            exactly_one(clauses, [x(r, c, s) for c in range(n)])
    for c in range(n):
        for s in range(n):
            exactly_one(clauses, [x(r, c, s) for r in range(n)])
    stats["latin_clauses"] = len(clauses) - before

    before = len(clauses)
    for j in range(n):
        clauses.append([x(0, j, j)])
    for i in range(n):
        clauses.append([x(i, 0, i)])
    stats["reduced_unit_clauses"] = len(clauses) - before

    if "row" in views:
        before = len(clauses)
        for a in range(n):
            for b in range(a + 1, n):
                for c in range(n):
                    left_color = row_color(a, b, c)
                    for d in range(n):
                        right_color = row_color(a, b, d)
                        for s in range(n):
                            add_neq_if_both(clauses, x(a, c, s), x(b, d, s), left_color, right_color)
        stats["row_fff_clauses"] = len(clauses) - before

    if "col" in views:
        before = len(clauses)
        for c in range(n):
            for d in range(c + 1, n):
                for r in range(n):
                    left_color = col_color(c, d, r)
                    for t in range(n):
                        right_color = col_color(c, d, t)
                        for s in range(n):
                            add_neq_if_both(clauses, x(r, c, s), x(t, d, s), left_color, right_color)
        stats["col_fff_clauses"] = len(clauses) - before

    if "sym" in views:
        before = len(clauses)
        for u in range(n):
            for v in range(u + 1, n):
                for j in range(n):
                    left_color = sym_color(u, v, j)
                    for k in range(n):
                        right_color = sym_color(u, v, k)
                        for r in range(n):
                            add_neq_if_both(clauses, x(r, j, u), x(r, k, v), left_color, right_color)
        stats["sym_fff_clauses"] = len(clauses) - before

    var_prefix_counts = {"cell": 0, "row_color": 0, "col_color": 0, "sym_color": 0}
    for name in pool.names:
        if name.startswith("x_"):
            var_prefix_counts["cell"] += 1
        elif name.startswith("row_color_"):
            var_prefix_counts["row_color"] += 1
        elif name.startswith("col_color_"):
            var_prefix_counts["col_color"] += 1
        elif name.startswith("sym_color_"):
            var_prefix_counts["sym_color"] += 1

    return {
        "n": n,
        "views": list(views),
        "var_count": pool.count,
        "clauses": clauses,
        "clause_count": len(clauses),
        "clause_stats": stats,
        "var_prefix_counts": var_prefix_counts,
        "var_names": pool.names,
    }


def dimacs_text(var_count: int, clauses: list[list[int]]) -> str:
    lines = [f"p cnf {var_count} {len(clauses)}"]
    lines.extend(" ".join(str(lit) for lit in clause) + " 0" for clause in clauses)
    return "\n".join(lines) + "\n"


def available_cli_solver(preferred: str) -> str | None:
    if preferred != "auto":
        return shutil.which(preferred)
    for name in ("kissat", "cadical", "glucose", "minisat"):
        path = shutil.which(name)
        if path:
            return path
    return None


def parse_solver_status(text: str) -> str:
    upper = text.upper()
    if "UNSATISFIABLE" in upper:
        return "unsat"
    if "SATISFIABLE" in upper:
        return "sat"
    if "UNKNOWN" in upper:
        return "unknown"
    return "unknown"


def parse_dimacs_model(text: str) -> set[int]:
    values: set[int] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("c", "s")):
            continue
        if stripped.startswith("v"):
            stripped = stripped[1:].strip()
        for part in stripped.split():
            try:
                value = int(part)
            except ValueError:
                continue
            if value == 0:
                continue
            if value > 0:
                values.add(value)
    return values


def table_from_model(n: int, var_names: dict[str, int], true_vars: set[int]) -> list[list[int]] | None:
    table = [[None for _ in range(n)] for _ in range(n)]
    for name, var_id in var_names.items():
        if not name.startswith("x_") or var_id not in true_vars:
            continue
        _, r, c, s = name.split("_")
        table[int(r)][int(c)] = int(s)
    if any(value is None for row in table for value in row):
        return None
    return [[int(value) for value in row] for row in table]


def run_cli_solver(solver_path: str, cnf_path: Path, timeout: float | None, n: int, var_names: dict[str, int]) -> dict[str, Any]:
    start = time.time()
    name = Path(solver_path).name
    output_model_path = cnf_path.with_suffix(cnf_path.suffix + ".model")
    if name == "minisat":
        command = [solver_path, str(cnf_path), str(output_model_path)]
    else:
        command = [solver_path, str(cnf_path)]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "solver": solver_path,
            "elapsed_seconds": time.time() - start,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    combined = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    if output_model_path.exists():
        combined += "\n" + output_model_path.read_text(errors="replace")
    status = parse_solver_status(combined)
    model_values = parse_dimacs_model(combined) if status == "sat" else set()
    return {
        "status": status,
        "solver": solver_path,
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - start,
        "stdout_excerpt": proc.stdout[:4000],
        "stderr_excerpt": proc.stderr[:4000],
        "solution_table": table_from_model(n, var_names, model_values) if model_values else None,
        "proof_certificate_available": False,
        "proof_certificate_note": "No DRAT/LRAT/FRAT proof logging is configured by this run.",
    }


def run_ortools(cnf: dict[str, Any], timeout: float | None) -> dict[str, Any]:
    start = time.time()
    try:
        from ortools.sat.python import cp_model  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "backend_unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": 0.0,
        }
    model = cp_model.CpModel()
    bools = {i: model.NewBoolVar(f"v_{i}") for i in range(1, cnf["var_count"] + 1)}
    for clause in cnf["clauses"]:
        model.AddBoolOr([bools[abs(lit)].Not() if lit < 0 else bools[lit] for lit in clause])
    solver = cp_model.CpSolver()
    if timeout is not None:
        solver.parameters.max_time_in_seconds = timeout
    status_code = solver.Solve(model)
    status_name = solver.StatusName(status_code).lower()
    status = {
        "optimal": "sat",
        "feasible": "sat",
        "infeasible": "unsat",
        "unknown": "unknown",
        "model_invalid": "unknown",
    }.get(status_name, status_name)
    true_vars = {var_id for var_id, var in bools.items() if status == "sat" and solver.BooleanValue(var)}
    return {
        "status": status,
        "ortools_status": status_name,
        "elapsed_seconds": time.time() - start,
        "solution_table": table_from_model(cnf["n"], cnf["var_names"], true_vars) if true_vars else None,
        "proof_certificate_available": False,
        "proof_certificate_note": "CP-SAT UNSAT is reproducible solver evidence here, not a standalone proof certificate.",
    }


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "FFF constraint model summary",
        "",
        f"n: {result['n']}",
        f"views: {','.join(result['views'])}",
        f"backend: {result['backend']}",
        f"status: {result['status']}",
        f"variables: {result['var_count']}",
        f"clauses: {result['clause_count']}",
        f"cnf_sha256: {result['cnf']['sha256']}",
        f"cnf_written: {result['cnf']['written']}",
        "",
        "Clause stats:",
    ]
    for key, value in result["clause_stats"].items():
        lines.append(f"- {key}: {value}")
    if result.get("solver"):
        lines.extend(["", "Solver:"])
        lines.append(json.dumps(result["solver"], indent=2, sort_keys=True))
    lines.extend(["", f"Claim impact: {result['claim_impact']}"])
    return "\n".join(lines) + "\n"


def parse_views(raw: str) -> tuple[str, ...]:
    views = tuple(part.strip() for part in raw.split(",") if part.strip())
    unknown = sorted(set(views) - set(ALL_VIEWS))
    if unknown:
        raise ValueError(f"unknown views: {unknown}")
    return views


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--views", required=True, help="Comma-separated subset of row,col,sym")
    parser.add_argument("--backend", choices=["cnf", "ortools"], required=True)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--solver", default="auto", help="auto, none, or CLI solver name/path")
    parser.add_argument("--write-cnf", action="store_true")
    parser.add_argument("--cnf-output", type=Path)
    parser.add_argument("--solution-output", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    views = parse_views(args.views)
    if not views:
        raise ValueError("at least one view must be selected")
    start = time.time()
    cnf = build_cnf(args.n, views)
    dimacs = dimacs_text(cnf["var_count"], cnf["clauses"])
    cnf_sha = hashlib.sha256(dimacs.encode("ascii")).hexdigest()
    cnf_path = args.cnf_output or args.output.with_suffix(".cnf")
    cnf_written = False
    solver_result: dict[str, Any] | None = None

    if args.write_cnf:
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf_path.write_text(dimacs)
        cnf_written = True

    status = "model_generated"
    if args.backend == "ortools":
        if args.solve:
            solver_result = run_ortools(cnf, args.timeout)
            status = solver_result["status"]
        else:
            status = "model_generated_not_solved"
    elif args.backend == "cnf":
        if args.solve:
            solver_path = None if args.solver == "none" else available_cli_solver(args.solver)
            if solver_path is None:
                status = "not_solved_no_solver"
                solver_result = {
                    "status": status,
                    "requested_solver": args.solver,
                    "proof_certificate_available": False,
                    "proof_certificate_note": "No local CLI SAT solver was available.",
                }
            else:
                if not cnf_written:
                    cnf_path.parent.mkdir(parents=True, exist_ok=True)
                    cnf_path.write_text(dimacs)
                    cnf_written = True
                solver_result = run_cli_solver(solver_path, cnf_path, args.timeout, args.n, cnf["var_names"])
                status = solver_result["status"]
        else:
            status = "model_generated_not_solved"

    if solver_result and solver_result.get("solution_table") and args.solution_output:
        args.solution_output.parent.mkdir(parents=True, exist_ok=True)
        args.solution_output.write_text(
            json.dumps(
                {
                    "n": args.n,
                    "views": list(views),
                    "table": solver_result["solution_table"],
                    "source": str(args.output),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    result = {
        "n": args.n,
        "views": list(views),
        "backend": args.backend,
        "status": status,
        "timeout_seconds": args.timeout,
        "solve_requested": args.solve,
        "elapsed_seconds": time.time() - start,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "var_count": cnf["var_count"],
        "var_prefix_counts": cnf["var_prefix_counts"],
        "clause_count": cnf["clause_count"],
        "clause_stats": cnf["clause_stats"],
        "cnf": {
            "sha256": cnf_sha,
            "written": cnf_written,
            "path": str(cnf_path) if cnf_written else None,
            "size_bytes": cnf_path.stat().st_size if cnf_written else None,
        },
        "solver": solver_result,
        "solution_output": str(args.solution_output) if args.solution_output else None,
        "claim_impact": (
            "No C38 upgrade unless status is sat with independently validated table, or unsat with "
            "documented solver details and preferably a proof certificate."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
