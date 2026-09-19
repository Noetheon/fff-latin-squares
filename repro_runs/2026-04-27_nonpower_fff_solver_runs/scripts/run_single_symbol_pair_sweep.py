#!/usr/bin/env python3
"""Run row+col plus one symbol-pair sweeps for a fixed row1+col1 context."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import platform
import shutil
import subprocess
import time
from itertools import combinations
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
GENERATOR = RUN_DIR / "scripts" / "generate_fff_cnf.py"
SOLVER_RUNNER = RUN_DIR / "scripts" / "solve_cnf_with_cadical.py"
DECODER = RUN_DIR / "scripts" / "decode_sat_solution.py"
VALIDATOR = ROOT / "repro_runs" / "2026-04-27_nonpower_fff_obstruction" / "scripts" / "validate_fff_table.py"
ANALYZER = RUN_DIR / "scripts" / "analyze_symbol_pair_failures.py"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def run_command(command: list[str], stdout_path: Path | None = None, stderr_path: Path | None = None) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True) if stdout_path else None
    stderr_path.parent.mkdir(parents=True, exist_ok=True) if stderr_path else None
    start = time.time()
    if stdout_path and stderr_path:
        with stdout_path.open("w") as stdout_handle, stderr_path.open("w") as stderr_handle:
            proc = subprocess.run(command, text=True, stdout=stdout_handle, stderr=stderr_handle, check=False)
    else:
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return {"returncode": proc.returncode, "elapsed_seconds": time.time() - start}


def sanitize(raw: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in raw).strip("_")


def analyze_table(input_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    command = [
        "python3",
        str(ANALYZER),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--summary",
        str(summary_path),
    ]
    run = run_command(command, summary_path.with_suffix(".analyze.stdout.log"), summary_path.with_suffix(".analyze.stderr.log"))
    if run["returncode"] != 0:
        raise RuntimeError(f"symbol-pair analysis failed for {input_path}")
    return read_json(output_path)


def generate_case(pair: tuple[int, int], args: argparse.Namespace) -> dict[str, Any]:
    case_suffix = sanitize(args.case_id)
    pair_suffix = f"s{pair[0]}_{pair[1]}"
    prefix = f"n10_rowcol_plus_{pair_suffix}_{case_suffix}"
    cnf_path = args.results_dir / f"{prefix}.cnf"
    var_map_path = args.results_dir / f"{prefix}_var_map.json"
    metadata_path = args.results_dir / f"{prefix}_cnf_metadata.json"
    summary_path = args.results_dir / f"{prefix}_cnf_summary.txt"
    command = [
        "python3",
        str(GENERATOR),
        "--n",
        "10",
        "--views",
        "row,col",
        "--fixed-row1-col1-cases-json",
        str(args.cases_json),
        "--fixed-row1-col1-case-id",
        args.case_id,
        "--cnf-output",
        str(cnf_path),
        "--var-map-output",
        str(var_map_path),
        "--metadata-output",
        str(metadata_path),
        "--summary",
        str(summary_path),
        "--sym-pairs",
        f"{pair[0]},{pair[1]}",
    ]
    if args.color_gauge:
        command.append("--color-gauge")
    if args.color_balance:
        command.append("--color-balance")
    run = run_command(
        command,
        args.logs_dir / f"{prefix}_generate.stdout.log",
        args.logs_dir / f"{prefix}_generate.stderr.log",
    )
    if run["returncode"] != 0:
        raise RuntimeError(f"CNF generation failed for pair {pair}")
    meta = read_json(metadata_path)
    return {
        "pair": list(pair),
        "cnf_path": str(cnf_path),
        "cnf_sha256": meta["cnf"]["sha256"],
        "var_map_path": str(var_map_path),
        "variables": meta["var_count"],
        "clauses": meta["clause_count"],
    }


def solve_case(generated: dict[str, Any], solver: str, args: argparse.Namespace) -> dict[str, Any]:
    pair = generated["pair"]
    solver_name = Path(solver).name
    label = f"{Path(generated['cnf_path']).stem}_{solver_name}"
    stdout_path = args.logs_dir / f"{label}.stdout.log"
    stderr_path = args.logs_dir / f"{label}.stderr.log"
    runner_stdout = args.logs_dir / f"{label}_runner.stdout.log"
    runner_stderr = args.logs_dir / f"{label}_runner.stderr_time.log"
    model_path = args.results_dir / f"{label}.model"
    metadata_path = args.results_dir / f"{label}_solve.json"
    summary_path = args.results_dir / f"{label}_solve_summary.txt"
    command = [
        "python3",
        str(SOLVER_RUNNER),
        "--label",
        label,
        "--cnf",
        generated["cnf_path"],
        "--solver",
        solver,
        "--timeout",
        str(args.timeout),
        "--stdout-output",
        str(stdout_path),
        "--stderr-output",
        str(stderr_path),
        "--model-output",
        str(model_path),
        "--metadata-output",
        str(metadata_path),
        "--summary",
        str(summary_path),
    ]
    run = run_command(time_command := ["/usr/bin/time", "-p", *command], runner_stdout, runner_stderr)
    if run["returncode"] != 0:
        raise RuntimeError(f"solver runner failed for {label}")
    solve_meta = read_json(metadata_path)
    validator_result = None
    symbol_profile = None
    decoded_table_sha = None
    if solve_meta["result"] == "sat" and solve_meta["model"]["available"]:
        table_path = args.results_dir / f"{label}_decoded_table.json"
        decode_path = args.results_dir / f"{label}_decode.json"
        validation_path = args.results_dir / f"{label}_decoded_validation.json"
        validation_summary_path = args.results_dir / f"{label}_decoded_validation_summary.txt"
        decode_command = [
            "python3",
            str(DECODER),
            "--model",
            str(model_path),
            "--var-map",
            generated["var_map_path"],
            "--table-output",
            str(table_path),
            "--metadata-output",
            str(decode_path),
            "--validator-script",
            str(VALIDATOR),
            "--validator-output",
            str(validation_path),
            "--validator-summary",
            str(validation_summary_path),
        ]
        decode_run = run_command(
            decode_command,
            args.logs_dir / f"{label}_decode.stdout.log",
            args.logs_dir / f"{label}_decode.stderr.log",
        )
        if decode_run["returncode"] != 0:
            raise RuntimeError(f"decode failed for {label}")
        decoded_table_sha = sha256_file(table_path)
        validation = read_json(validation_path)
        profile_path = args.results_dir / f"{label}_symbol_failure_profile.json"
        profile_summary = args.results_dir / f"{label}_symbol_failure_profile_summary.txt"
        profile = analyze_table(table_path, profile_path, profile_summary)
        validator_result = {
            "latin": validation["latin"]["latin"],
            "reduced": validation["reduced"],
            "pattern_name": validation["pattern_name"],
            "fff": validation["fff"],
        }
        symbol_profile = {
            "path": str(profile_path),
            "sha256": sha256_file(profile_path),
            "failing_symbol_pair_count": profile["failing_symbol_pair_count"],
        }
    return {
        "pair": pair,
        "solver": solve_meta["solver"]["binary"],
        "solver_version": solve_meta["solver"]["version"],
        "command": solve_meta["solver"]["command"],
        "timeout": solve_meta["timeout_seconds"],
        "result": solve_meta["result"],
        "elapsed": solve_meta["elapsed_seconds"],
        "cnf_sha256": generated["cnf_sha256"],
        "variables": generated["variables"],
        "clauses": generated["clauses"],
        "decoded_table_sha256": decoded_table_sha,
        "validator_result": validator_result,
        "symbol_profile": symbol_profile,
    }


def make_summary(payload: dict[str, Any]) -> str:
    lines = [
        "n=10 row+col plus one-symbol-pair sweep",
        "",
        f"case_id: {payload['case_id']}",
        f"pair_count: {payload['pair_count']}",
        f"solver_count: {len(payload['solvers'])}",
        f"timeout_seconds: {payload['timeout_seconds']}",
        f"color_gauge: {payload['color_gauge']}",
        f"color_balance: {payload['color_balance']}",
        "",
        "Result counts:",
    ]
    counts: dict[str, int] = {}
    for run in payload["solver_runs"]:
        counts[run["result"]] = counts.get(run["result"], 0) + 1
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    sat = [run for run in payload["solver_runs"] if run["result"] == "sat"]
    if sat:
        lines.append("")
        lines.append("SAT highlights:")
        for run in sat[:12]:
            validation = run["validator_result"]
            lines.append(
                "- pair={pair} {solver}: pattern={pattern}, FFF={fff}, remaining_failing_pairs={remain}".format(
                    pair=tuple(run["pair"]),
                    solver=Path(run["solver"]).name,
                    pattern=validation["pattern_name"] if validation else None,
                    fff=validation["fff"] if validation else None,
                    remain=run["symbol_profile"]["failing_symbol_pair_count"] if run["symbol_profile"] else None,
                )
            )
    lines.append("")
    lines.append("No claim update follows from this sweep alone.")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-json", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--solvers", default="cadical,kissat")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--color-gauge", action="store_true")
    parser.add_argument("--color-balance", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.logs_dir.mkdir(parents=True, exist_ok=True)
    solvers = [solver.strip() for solver in args.solvers.split(",") if solver.strip()]
    missing = [solver for solver in solvers if shutil.which(solver) is None and "/" not in solver]
    if missing:
        raise FileNotFoundError(f"missing solvers: {missing}")
    pairs = list(combinations(range(10), 2))
    generated_cases = [generate_case(pair, args) for pair in pairs]
    jobs = [(generated, solver) for generated in generated_cases for solver in solvers]
    solver_runs: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(solve_case, generated, solver, args) for generated, solver in jobs]
        for future in concurrent.futures.as_completed(futures):
            solver_runs.append(future.result())
    solver_runs.sort(key=lambda item: (tuple(item["pair"]), Path(item["solver"]).name))
    payload = {
        "run_id": "2026-04-27_nonpower_fff_solver_runs",
        "case_id": args.case_id,
        "pair_count": len(pairs),
        "solvers": solvers,
        "timeout_seconds": args.timeout,
        "max_workers": args.max_workers,
        "color_gauge": args.color_gauge,
        "color_balance": args.color_balance,
        "generated_cases": generated_cases,
        "solver_runs": solver_runs,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
