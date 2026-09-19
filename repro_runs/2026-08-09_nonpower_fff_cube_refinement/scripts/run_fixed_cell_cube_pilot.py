#!/usr/bin/env python3
"""Run a complete fixed-cell cube pilot for one canonical Row1 case."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
DECODER = ROOT / "repro_runs/2026-04-27_nonpower_fff_solver_runs/scripts/decode_sat_solution.py"
VALIDATOR = ROOT / "repro_runs/2026-04-27_nonpower_fff_obstruction/scripts/validate_fff_table.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_cube_cnf(base_cnf: Path, unit_variable: int, output: Path) -> tuple[int, int]:
    with base_cnf.open("rt", encoding="ascii") as source, output.open("wt", encoding="ascii") as target:
        header_seen = False
        variables = clauses = 0
        for raw in source:
            if raw.startswith("p cnf "):
                _, _, raw_variables, raw_clauses = raw.split()
                variables = int(raw_variables)
                clauses = int(raw_clauses) + 1
                target.write(f"p cnf {variables} {clauses}\n")
                header_seen = True
            else:
                target.write(raw)
        if not header_seen:
            raise ValueError(f"missing DIMACS header in {base_cnf}")
        target.write(f"{unit_variable} 0\n")
    return variables, clauses


def parse_status(text: str) -> str:
    upper = text.upper()
    if "UNSATISFIABLE" in upper:
        return "unsat"
    if "SATISFIABLE" in upper:
        return "sat"
    return "unknown"


def extract_model(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip().startswith("v")]
    return "\n".join(lines) + ("\n" if lines else "")


def solve_cube(
    symbol: int,
    variable: int,
    args: argparse.Namespace,
    var_map: dict[str, Any],
) -> dict[str, Any]:
    label = f"{var_map['fixed_row1_case_id']}_cell_2_1_eq_{symbol}_{Path(args.solver).name}"
    stdout_path = args.logs_dir / f"{label}.stdout.log"
    stderr_path = args.logs_dir / f"{label}.stderr.log"
    model_path = args.results_dir / f"{label}.model"
    with tempfile.TemporaryDirectory(prefix="order8_cube_") as temporary:
        cube_cnf = Path(temporary) / f"{label}.cnf"
        variables, clauses = derive_cube_cnf(args.base_cnf, variable, cube_cnf)
        cube_sha256 = sha256_file(cube_cnf)
        command = [args.solver, str(cube_cnf)]
        start = time.monotonic()
        try:
            process = subprocess.run(command, text=True, capture_output=True, timeout=args.timeout, check=False)
            elapsed = time.monotonic() - start
            stdout = process.stdout
            stderr = process.stderr
            result = parse_status(stdout + "\n" + stderr)
            returncode = process.returncode
        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - start
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
            result = "timeout"
            returncode = None
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        model_path.write_text(extract_model(stdout) if result == "sat" else "", encoding="utf-8")

    validation_result = None
    decoded_table_sha256 = None
    if result == "sat":
        table_path = args.results_dir / f"{label}_decoded_table.json"
        decode_metadata = args.results_dir / f"{label}_decode.json"
        validation_path = args.results_dir / f"{label}_validation.json"
        validation_summary = args.results_dir / f"{label}_validation_summary.txt"
        decode_command = [
            "python3", str(DECODER),
            "--model", str(model_path),
            "--var-map", str(args.var_map),
            "--table-output", str(table_path),
            "--metadata-output", str(decode_metadata),
            "--validator-script", str(VALIDATOR),
            "--validator-output", str(validation_path),
            "--validator-summary", str(validation_summary),
        ]
        decode = subprocess.run(decode_command, text=True, capture_output=True, check=False)
        if decode.returncode != 0:
            raise RuntimeError(f"decode failed for {label}: {decode.stderr}")
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        decoded_table_sha256 = sha256_file(table_path)
        validation_result = {
            "latin": validation["latin"]["latin"],
            "reduced": validation["reduced"],
            "pattern": validation["pattern_name"],
            "fff": validation["fff"],
            "validation_path": str(validation_path.relative_to(ROOT)),
            "validation_sha256": sha256_file(validation_path),
        }
    return {
        "symbol": symbol,
        "unit_variable": variable,
        "cell": [2, 1],
        "derived_cnf": {
            "sha256": cube_sha256,
            "variables": variables,
            "clauses": clauses,
            "reconstruction": f"base CNF plus unit clause {variable} 0",
            "stored": False,
        },
        "solver": str(args.solver),
        "solver_version": subprocess.run([args.solver, "--version"], text=True, capture_output=True, check=False).stdout.strip(),
        "command_template": [str(args.solver), "<deterministically reconstructed cube CNF>"],
        "timeout_seconds": args.timeout,
        "elapsed_seconds": elapsed,
        "returncode": returncode,
        "result": result,
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "stderr_sha256": sha256_file(stderr_path),
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": sha256_file(model_path),
        "decoded_table_sha256": decoded_table_sha256,
        "validation": validation_result,
        "proof_log": False,
        "proof_checked": "not_applicable",
    }


def summary_text(payload: dict[str, Any]) -> str:
    lines = [
        "n=10 fixed-cell complete cube pilot",
        "",
        f"row1_case: {payload['row1_case_id']}",
        f"base_cnf_sha256: {payload['base_cnf']['sha256']}",
        f"fixed_cell: {payload['fixed_cell']}",
        f"allowed_symbols: {payload['allowed_symbols']}",
        f"cube_count: {payload['cube_count']}",
        f"coverage: {payload['coverage']}",
        f"timeout_seconds_per_cube: {payload['timeout_seconds_per_cube']}",
        f"max_workers: {payload['max_workers']}",
        "",
        "Results:",
    ]
    for result, count in sorted(payload["result_counts"].items()):
        lines.append(f"- {result}: {count}")
    lines.extend(
        [
            "",
            f"case_excluded: {str(payload['case_excluded']).lower()}",
            f"validated_full_fff_candidate_found: {str(payload['validated_full_fff_candidate_found']).lower()}",
            "C38: open" if not payload["validated_full_fff_candidate_found"] else "C38: counterexample candidate requires confirmation",
            "C40: not_created",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-cnf", type=Path, required=True)
    parser.add_argument("--var-map", type=Path, required=True)
    parser.add_argument("--solver", default=shutil.which("cadical") or "cadical")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--results-dir", type=Path, default=RUN_DIR / "results" / "fixed_cell_cube_pilot")
    parser.add_argument("--logs-dir", type=Path, default=RUN_DIR / "logs" / "fixed_cell_cube_pilot")
    parser.add_argument("--output", type=Path, default=RUN_DIR / "results" / "fixed_cell_cube_pilot_status.json")
    parser.add_argument("--summary", type=Path, default=RUN_DIR / "results" / "fixed_cell_cube_pilot_summary.txt")
    args = parser.parse_args()
    args.base_cnf = args.base_cnf.resolve()
    args.var_map = args.var_map.resolve()
    args.results_dir = args.results_dir.resolve()
    args.logs_dir = args.logs_dir.resolve()
    args.output = args.output.resolve()
    args.summary = args.summary.resolve()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.logs_dir.mkdir(parents=True, exist_ok=True)

    var_map = json.loads(args.var_map.read_text(encoding="utf-8"))
    if var_map["n"] != 10 or var_map["views"] != ["row", "col", "sym"]:
        raise ValueError("pilot requires the full n=10 row,col,sym model")
    if not var_map.get("color_gauge") or not var_map.get("color_balance"):
        raise ValueError("pilot requires color gauge and balance")
    row1 = var_map["fixed_row1_permutation"]
    excluded = {1, 2, row1[1]}
    allowed = [symbol for symbol in range(10) if symbol not in excluded]
    variables = {symbol: int(var_map["var_names"][f"x_2_1_{symbol}"]) for symbol in allowed}

    start = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(solve_cube, symbol, variables[symbol], args, var_map) for symbol in allowed]
        runs = [future.result() for future in futures]
    runs.sort(key=lambda item: item["symbol"])
    counts = Counter(run["result"] for run in runs)
    case_excluded = counts.get("unsat", 0) == len(runs)
    full_candidates = [run for run in runs if run["validation"] and run["validation"]["fff"]]
    payload = {
        "run_id": "2026-08-09_nonpower_fff_cube_refinement",
        "row1_case_id": var_map["fixed_row1_case_id"],
        "row1_permutation": row1,
        "base_cnf": {
            "path": str(args.base_cnf.relative_to(ROOT)),
            "sha256": sha256_file(args.base_cnf),
        },
        "var_map": {
            "path": str(args.var_map.relative_to(ROOT)),
            "sha256": sha256_file(args.var_map),
        },
        "fixed_cell": [2, 1],
        "excluded_symbols": sorted(excluded),
        "allowed_symbols": allowed,
        "cube_count": len(allowed),
        "coverage": "rigorously complete and pairwise disjoint by proof_notes/fff_fixed_cell_cube_partition.md",
        "timeout_seconds_per_cube": args.timeout,
        "max_workers": args.max_workers,
        "wall_elapsed_seconds": time.monotonic() - start,
        "result_counts": dict(sorted(counts.items())),
        "case_excluded": case_excluded,
        "validated_full_fff_candidate_found": bool(full_candidates),
        "cube_runs": runs,
        "claim_impact": {"C38": "open", "C40": "not_created"},
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(summary_text(payload), encoding="utf-8")
    print(json.dumps({"counts": payload["result_counts"], "case_excluded": case_excluded, "full_candidate": bool(full_candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
