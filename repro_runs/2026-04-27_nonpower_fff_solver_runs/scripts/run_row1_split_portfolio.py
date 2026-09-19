#!/usr/bin/env python3
"""Generate and solve row-1 split CNFs for n=10."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
GENERATOR = RUN_DIR / "scripts" / "generate_fff_cnf.py"
SOLVER_RUNNER = RUN_DIR / "scripts" / "solve_cnf_with_cadical.py"
DECODER = RUN_DIR / "scripts" / "decode_sat_solution.py"
VALIDATOR = ROOT / "repro_runs" / "2026-04-27_nonpower_fff_obstruction" / "scripts" / "validate_fff_table.py"


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


def safe_case_suffix(case: dict[str, Any]) -> str:
    raw = str(case["case_id"])
    return "".join(ch if ch.isalnum() else "_" for ch in raw).strip("_")


def view_label(views: str) -> str:
    if views == "row,col":
        return "rowcol"
    if views == "row,col,sym":
        return "full"
    return views.replace(",", "_")


def run_command(command: list[str], stdout_path: Path | None = None, stderr_path: Path | None = None) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True) if stdout_path else None
    stderr_path.parent.mkdir(parents=True, exist_ok=True) if stderr_path else None
    start = time.time()
    if stdout_path and stderr_path:
        with stdout_path.open("w") as stdout_handle, stderr_path.open("w") as stderr_handle:
            proc = subprocess.run(command, text=True, stdout=stdout_handle, stderr=stderr_handle, check=False)
        stdout = None
        stderr = None
    else:
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
        stdout = proc.stdout
        stderr = proc.stderr
    return {
        "command": command,
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - start,
        "stdout": stdout,
        "stderr": stderr,
    }


def generate_case_cnf(case: dict[str, Any], views: str, args: argparse.Namespace) -> dict[str, Any]:
    suffix = safe_case_suffix(case)
    gauge = "_colorgauge" if args.color_gauge else ""
    balance = "_colorbalance" if args.color_balance else ""
    prefix = f"n10_{view_label(views)}_row1case{gauge}{balance}_{suffix}"
    paths = {
        "cnf": args.results_dir / f"{prefix}.cnf",
        "var_map": args.results_dir / f"{prefix}_var_map.json",
        "metadata": args.results_dir / f"{prefix}_cnf_metadata.json",
        "summary": args.results_dir / f"{prefix}_cnf_summary.txt",
        "generate_stdout": args.logs_dir / f"{prefix}_generate.stdout.log",
        "generate_stderr": args.logs_dir / f"{prefix}_generate.stderr.log",
    }
    command = [
        "python3",
        str(GENERATOR),
        "--n",
        "10",
        "--views",
        views,
        "--fixed-row1-cases-json",
        str(args.cases_json),
        "--fixed-row1-case-id",
        str(case["case_id"]),
        "--cnf-output",
        str(paths["cnf"]),
        "--var-map-output",
        str(paths["var_map"]),
        "--metadata-output",
        str(paths["metadata"]),
        "--summary",
        str(paths["summary"]),
    ]
    if args.color_gauge:
        command.append("--color-gauge")
    if args.color_balance:
        command.append("--color-balance")
    run = run_command(command, paths["generate_stdout"], paths["generate_stderr"])
    if run["returncode"] != 0:
        raise RuntimeError(f"CNF generation failed for {case['case_id']} views={views}")
    meta = read_json(paths["metadata"])
    return {
        "case_id": case["case_id"],
        "row1_case_id": case["case_id"],
        "partition": case["partition"],
        "row1_partition": case["partition"],
        "zero_cycle_length": case["zero_cycle_length"],
        "row1_permutation": case["row1_permutation"],
        "cycle_notation": case["cycle_notation"],
        "views": views.split(","),
        "color_gauge": args.color_gauge,
        "color_balance": args.color_balance,
        "label_prefix": prefix,
        "cnf_path": str(paths["cnf"]),
        "cnf_sha256": meta["cnf"]["sha256"],
        "var_map_path": str(paths["var_map"]),
        "var_map_sha256": meta["var_map"]["sha256"],
        "variables": meta["var_count"],
        "clauses": meta["clause_count"],
        "generation_command": command,
        "generation_elapsed_seconds": run["elapsed_seconds"],
    }


def solve_case(generated: dict[str, Any], solver: str, timeout: float, args: argparse.Namespace) -> dict[str, Any]:
    solver_name = Path(solver).name
    label = f"{generated['label_prefix']}_{solver_name}"
    stdout_path = args.logs_dir / f"{label}.stdout.log"
    stderr_path = args.logs_dir / f"{label}.stderr.log"
    runner_stdout = args.logs_dir / f"{label}_runner.stdout.log"
    runner_stderr = args.logs_dir / f"{label}_runner.stderr.log"
    model_path = args.results_dir / f"{label}.model"
    metadata_path = args.results_dir / f"{label}_solve.json"
    summary_path = args.results_dir / f"{label}_solve_summary.txt"
    proof_path = None
    if args.proof_logs and solver_name == "cadical":
        proof_path = args.results_dir / f"{label}.drat"
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
        str(timeout),
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
    if proof_path is not None:
        command.extend(["--proof", str(proof_path)])
    time_command = ["/usr/bin/time", "-p", *command]
    run = run_command(time_command, runner_stdout, runner_stderr)
    if run["returncode"] != 0:
        raise RuntimeError(f"solver runner failed for {label}")
    solve_meta = read_json(metadata_path)

    decoded_table_sha = None
    validator_result: dict[str, Any] | None = None
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
            raise RuntimeError(f"SAT decode failed for {label}")
        decoded_table_sha = sha256_file(table_path)
        validation = read_json(validation_path)
        validator_result = {
            "validation_path": str(validation_path),
            "validation_sha256": sha256_file(validation_path),
            "latin": validation["latin"]["latin"],
            "reduced": validation["reduced"],
            "pattern_name": validation["pattern_name"],
            "fff": validation["fff"],
            "view_bits": validation["pattern_has_odd_cycle"],
        }

    return {
        "case_id": generated["case_id"],
        "row1_case_id": generated["row1_case_id"],
        "partition": generated["partition"],
        "row1_partition": generated["row1_partition"],
        "zero_cycle_length": generated["zero_cycle_length"],
        "row1_permutation": generated["row1_permutation"],
        "views": generated["views"],
        "color_gauge": generated["color_gauge"],
        "color_balance": generated["color_balance"],
        "cnf_sha256": generated["cnf_sha256"],
        "variables": generated["variables"],
        "clauses": generated["clauses"],
        "solver": solve_meta["solver"]["binary"],
        "solver_version": solve_meta["solver"]["version"],
        "command": solve_meta["solver"]["command"],
        "timeout": solve_meta["timeout_seconds"],
        "result": solve_meta["result"],
        "elapsed": solve_meta["elapsed_seconds"],
        "proof_log": solve_meta["proof"]["available"],
        "proof_log_sha256": solve_meta["proof"]["sha256"],
        "proof_checked": "not_applicable",
        "stdout_sha256": solve_meta["stdout"]["sha256"],
        "stderr_sha256": solve_meta["stderr"]["sha256"],
        "model_sha256": solve_meta["model"]["sha256"],
        "decoded_table_sha256": decoded_table_sha,
        "validator_result": validator_result,
    }


def make_summary(payload: dict[str, Any]) -> str:
    lines = [
        f"n=10 {payload['view_label']} row1 split portfolio",
        "",
        f"case_count: {payload['case_count']}",
        f"solver_count: {len(payload['solvers'])}",
        f"timeout_seconds: {payload['timeout_seconds']}",
        f"max_workers: {payload['max_workers']}",
        f"color_gauge: {payload['color_gauge']}",
        f"color_balance: {payload['color_balance']}",
        f"generated_cnf_count: {len(payload['generated_cases'])}",
        f"solver_run_count: {len(payload['solver_runs'])}",
        "",
        "Result counts:",
    ]
    counts: dict[str, int] = {}
    for entry in payload["solver_runs"]:
        counts[entry["result"]] = counts.get(entry["result"], 0) + 1
    if not counts and payload["generate_only"]:
        lines.append("- not_started: solver execution skipped because generate_only=True")
    elif not counts:
        lines.append("- no solver runs recorded")
    else:
        for key in sorted(counts):
            lines.append(f"- {key}: {counts[key]}")
    sat_entries = [entry for entry in payload["solver_runs"] if entry["result"] == "sat"]
    if sat_entries:
        lines.append("")
        lines.append("SAT decoded validations:")
        for entry in sat_entries:
            validation = entry["validator_result"]
            lines.append(
                "- {case_id} {solver}: Latin={latin}, reduced={reduced}, pattern={pattern}, FFF={fff}".format(
                    case_id=entry["case_id"],
                    solver=Path(entry["solver"]).name,
                    latin=validation["latin"] if validation else None,
                    reduced=validation["reduced"] if validation else None,
                    pattern=validation["pattern_name"] if validation else None,
                    fff=validation["fff"] if validation else None,
                )
            )
    lines.append("")
    lines.append(payload["claim_note"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-json", type=Path, required=True)
    parser.add_argument("--views", required=True, choices=["row,col", "row,col,sym"])
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--solvers", default="cadical,kissat")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--color-gauge", action="store_true")
    parser.add_argument("--color-balance", action="store_true")
    parser.add_argument("--proof-logs", action="store_true")
    parser.add_argument("--case-ids")
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--case-offset", type=int, default=0)
    parser.add_argument("--generate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.logs_dir.mkdir(parents=True, exist_ok=True)
    cases_payload = read_json(args.cases_json)
    cases = cases_payload["cases"]
    if args.case_ids:
        requested = {part.strip() for part in args.case_ids.split(",") if part.strip()}
        cases = [case for case in cases if str(case["case_id"]) in requested]
    if args.case_offset:
        cases = cases[args.case_offset :]
    if args.case_limit is not None:
        cases = cases[: args.case_limit]
    solvers = [solver.strip() for solver in args.solvers.split(",") if solver.strip()]
    missing = [solver for solver in solvers if shutil.which(solver) is None and "/" not in solver]
    if missing:
        raise FileNotFoundError(f"missing solvers: {missing}")

    generated_cases = [generate_case_cnf(case, args.views, args) for case in cases]
    solver_runs: list[dict[str, Any]] = []
    if not args.generate_only:
        jobs = [(generated, solver) for generated in generated_cases for solver in solvers]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = [executor.submit(solve_case, generated, solver, args.timeout, args) for generated, solver in jobs]
            for future in concurrent.futures.as_completed(futures):
                solver_runs.append(future.result())
        solver_runs.sort(key=lambda item: (item["case_id"], Path(item["solver"]).name))

    view = view_label(args.views)
    claim_note = (
        "No C40 claim follows unless every split case is UNSAT in a complete covering family "
        "or a full SAT model independently validates as FFF."
    )
    payload = {
        "run_id": "2026-04-27_nonpower_fff_solver_runs",
        "view_label": view,
        "views": args.views.split(","),
        "cases_json": str(args.cases_json),
        "case_count": len(cases),
        "solvers": solvers,
        "timeout_seconds": args.timeout,
        "max_workers": args.max_workers,
        "color_gauge": args.color_gauge,
        "color_balance": args.color_balance,
        "proof_logs": args.proof_logs,
        "case_filter": {
            "case_ids": [part.strip() for part in args.case_ids.split(",") if part.strip()] if args.case_ids else None,
            "case_offset": args.case_offset,
            "case_limit": args.case_limit,
        },
        "generate_only": args.generate_only,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "elapsed_seconds": time.time() - start,
        "generated_cases": generated_cases,
        "solver_runs": solver_runs,
        "claim_note": claim_note,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
