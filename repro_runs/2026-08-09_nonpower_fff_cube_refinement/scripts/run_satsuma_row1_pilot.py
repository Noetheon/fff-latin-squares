#!/usr/bin/env python3
"""Preprocess selected balanced Row1 CNFs with Satsuma and solve them."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parents[1]
SOLVE_RUNNER = ROOT / "repro_runs/2026-04-27_nonpower_fff_solver_runs/scripts/solve_cnf_with_cadical.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dimacs_header(path: Path) -> dict[str, int]:
    with path.open("rt", encoding="ascii") as handle:
        for line in handle:
            if line.startswith("p cnf "):
                _, _, variables, clauses = line.split()
                return {"variables": int(variables), "clauses": int(clauses)}
    raise ValueError(f"missing DIMACS header: {path}")


def preprocess(case_id: str, source: Path, args: argparse.Namespace) -> dict[str, Any]:
    output = args.results_dir / f"{case_id}_satsuma_fix_units.cnf"
    stdout = args.logs_dir / f"{case_id}_satsuma_fix.stdout.log"
    stderr = args.logs_dir / f"{case_id}_satsuma_fix.stderr_time.log"
    command = [args.satsuma, "fix", str(source), "--out-file", str(output), "--add-reduced-as-unit"]
    start = time.monotonic()
    with stdout.open("wt", encoding="utf-8") as out, stderr.open("wt", encoding="utf-8") as err:
        process = subprocess.run(command, text=True, stdout=out, stderr=err, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Satsuma failed for {case_id}")
    return {
        "case_id": case_id,
        "source": {"path": str(source.relative_to(ROOT)), "sha256": sha256_file(source), **dimacs_header(source)},
        "preprocessed": {"path": str(output.relative_to(ROOT)), "sha256": sha256_file(output), **dimacs_header(output)},
        "command": command,
        "elapsed_seconds": time.monotonic() - start,
        "stdout_sha256": sha256_file(stdout),
        "stderr_sha256": sha256_file(stderr),
    }


def solve(preprocessed: dict[str, Any], solver: str, args: argparse.Namespace) -> dict[str, Any]:
    case_id = preprocessed["case_id"]
    solver_name = Path(solver).name
    label = f"{case_id}_satsuma_{solver_name}"
    cnf = ROOT / preprocessed["preprocessed"]["path"]
    metadata = args.results_dir / f"{label}_solve.json"
    command = [
        "python3", str(SOLVE_RUNNER),
        "--label", label,
        "--cnf", str(cnf),
        "--solver", solver,
        "--timeout", str(args.timeout),
        "--stdout-output", str(args.logs_dir / f"{label}.stdout.log"),
        "--stderr-output", str(args.logs_dir / f"{label}.stderr.log"),
        "--model-output", str(args.results_dir / f"{label}.model"),
        "--metadata-output", str(metadata),
        "--summary", str(args.results_dir / f"{label}_solve_summary.txt"),
    ]
    process = subprocess.run(command, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"solver runner failed for {label}: {process.stderr}")
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    return {
        "case_id": case_id,
        "solver": payload["solver"]["binary"],
        "solver_version": payload["solver"]["version"],
        "timeout_seconds": payload["timeout_seconds"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "result": payload["result"],
        "cnf_sha256": payload["cnf"]["sha256"],
        "model_available": payload["model"]["available"],
        "proof_available": payload["proof"]["available"],
        "metadata_path": str(metadata.relative_to(ROOT)),
        "metadata_sha256": sha256_file(metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--satsuma", required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--case-ids", nargs="+", required=True)
    parser.add_argument("--solvers", nargs="+", default=["cadical", "kissat"])
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--results-dir", type=Path, default=RUN_DIR / "results" / "satsuma_row1_pilot")
    parser.add_argument("--logs-dir", type=Path, default=RUN_DIR / "logs" / "satsuma_row1_pilot")
    parser.add_argument("--output", type=Path, default=RUN_DIR / "results" / "satsuma_row1_pilot_status.json")
    parser.add_argument("--summary", type=Path, default=RUN_DIR / "results" / "satsuma_row1_pilot_summary.txt")
    args = parser.parse_args()
    args.source_dir = args.source_dir.resolve()
    args.results_dir = args.results_dir.resolve()
    args.logs_dir = args.logs_dir.resolve()
    args.output = args.output.resolve()
    args.summary = args.summary.resolve()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.logs_dir.mkdir(parents=True, exist_ok=True)

    sources = {}
    for case_id in args.case_ids:
        matches = sorted(args.source_dir.glob(f"n10_full_row1case_colorgauge_colorbalance_{case_id}.cnf"))
        if len(matches) != 1:
            raise ValueError(f"expected one source CNF for {case_id}, found {matches}")
        sources[case_id] = matches[0]
    preprocessed = [preprocess(case_id, sources[case_id], args) for case_id in args.case_ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(solve, item, solver, args) for item in preprocessed for solver in args.solvers]
        solver_runs = [future.result() for future in futures]
    solver_runs.sort(key=lambda item: (item["case_id"], item["solver"]))
    counts = Counter(item["result"] for item in solver_runs)
    payload = {
        "run_id": "2026-08-09_nonpower_fff_cube_refinement",
        "method": "Satsuma 1.4 symmetry fixing with reduced assignments retained",
        "satsuma_binary": args.satsuma,
        "satsuma_version": subprocess.run([args.satsuma, "--version"], text=True, capture_output=True, check=False).stdout.strip(),
        "case_ids": args.case_ids,
        "timeout_seconds": args.timeout,
        "max_workers": args.max_workers,
        "preprocessed_cases": preprocessed,
        "solver_runs": solver_runs,
        "result_counts": dict(sorted(counts.items())),
        "decided_cases": sorted({item["case_id"] for item in solver_runs if item["result"] in ("sat", "unsat")}),
        "transformation_proof": None,
        "claim_impact": {"C38": "open", "C40": "not_created"},
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "Satsuma-balanced-Row1 pilot",
        "",
        f"cases: {len(args.case_ids)}",
        f"solver runs: {len(solver_runs)}",
        f"timeout per run: {args.timeout}",
        f"result counts: {dict(sorted(counts.items()))}",
        f"decided cases: {payload['decided_cases']}",
        "transformation proof: not generated in this bounded pilot",
        "C38: open",
        "C40: not_created",
    ]
    args.summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"counts": payload["result_counts"], "decided_cases": payload["decided_cases"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
