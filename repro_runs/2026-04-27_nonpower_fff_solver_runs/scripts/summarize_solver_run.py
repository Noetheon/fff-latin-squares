#!/usr/bin/env python3
"""Create aggregate status files for the nonpower FFF solver run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    labels = ["n6_full", "n6_full_color_gauge", "n10_row", "n10_row_col", "n10_full"]
    statuses = {}
    for label in labels:
        path = args.results_dir / f"{label}_cadical_solve.json"
        if not path.exists():
            continue
        data = read_json(path)
        statuses[label] = {
            "cnf_sha256": data["cnf"]["sha256"],
            "solver": data["solver"]["binary"],
            "solver_version": data["solver"]["version"],
            "command": data["solver"]["command"],
            "timeout_seconds": data["timeout_seconds"],
            "result": data["result"],
            "elapsed_seconds": data["elapsed_seconds"],
            "proof_log_available": data["proof"]["available"],
            "proof_log_sha256": data["proof"]["sha256"],
            "stdout_sha256": data["stdout"]["sha256"],
            "stderr_sha256": data["stderr"]["sha256"],
            "model_available": data["model"]["available"],
            "model_sha256": data["model"]["sha256"],
        }
    inventory = read_json(args.results_dir / "solver_inventory_after_install.json")["summary"]
    validation = read_json(args.results_dir / "n10_row_decoded_validation.json")
    drat_check_path = args.results_dir / "n6_full_drat_trim_check.json"
    drat_check = read_json(drat_check_path) if drat_check_path.exists() else None
    color_gauge_drat_check_path = args.results_dir / "n6_full_color_gauge_drat_trim_check.json"
    color_gauge_drat_check = read_json(color_gauge_drat_check_path) if color_gauge_drat_check_path.exists() else None
    row1_rowcol_path = args.results_dir / "n10_rowcol_row1split_portfolio_status.json"
    row1_rowcol = read_json(row1_rowcol_path) if row1_rowcol_path.exists() else None
    row1_full_path = args.results_dir / "n10_full_row1split_portfolio_status.json"
    row1_full = read_json(row1_full_path) if row1_full_path.exists() else None
    row1_full_colorgauge_path = args.results_dir / "n10_full_row1split_colorgauge_portfolio_status.json"
    row1_full_colorgauge = read_json(row1_full_colorgauge_path) if row1_full_colorgauge_path.exists() else None
    row1_col1_cases_path = args.results_dir / "n10_row1_col1_canonical_cases.json"
    row1_col1_cases = read_json(row1_col1_cases_path) if row1_col1_cases_path.exists() else None
    row1_col1_case_summary = None
    if row1_col1_cases:
        row1_col1_case_summary = {
            "n": row1_col1_cases["n"],
            "case_count": row1_col1_cases["case_count"],
            "row1_case_count": row1_col1_cases["row1_case_count"],
            "counts_by_row1_case": row1_col1_cases["counts_by_row1_case"],
            "source_row1_cases_json": row1_col1_cases["source_row1_cases_json"],
            "coverage_note": row1_col1_cases["coverage_note"],
        }
    row1_col1_portfolio_path = args.results_dir / "n10_rowcol_row1col1split_portfolio_status.json"
    row1_col1_portfolio = read_json(row1_col1_portfolio_path) if row1_col1_portfolio_path.exists() else None
    row1_col1_full_pilot_path = args.results_dir / "n10_full_row1col1_pilot_status.json"
    row1_col1_full_pilot = read_json(row1_col1_full_pilot_path) if row1_col1_full_pilot_path.exists() else None
    symbol01_path = args.results_dir / "n10_symbol01_canonical_cases.json"
    symbol01 = read_json(symbol01_path) if symbol01_path.exists() else None
    result = {
        "run_id": "2026-04-27_nonpower_fff_solver_runs",
        "claim_impact": {
            "C38": "remains open",
            "C39": "solver-run infrastructure exercises the encoding",
            "C40": "not created because n10 is not decided and no full FFF table was validated",
        },
        "solver_inventory": inventory,
        "statuses": statuses,
        "n10_row_decoded_validation": {
            "latin": validation["latin"]["latin"],
            "reduced": validation["reduced"],
            "pattern_name": validation["pattern_name"],
            "fff": validation["fff"],
            "view_bits": validation["pattern_has_odd_cycle"],
        },
        "n12_started": False,
        "n12_reason": "n10 was not decided; row+col and full runs timed out",
        "n6_drat_check": drat_check,
        "n6_color_gauge_drat_check": color_gauge_drat_check,
        "n10_row1_rowcol_split": row1_rowcol,
        "n10_row1_full_split": row1_full,
        "n10_row1_full_colorgauge_split": row1_full_colorgauge,
        "n10_row1_col1_cases": row1_col1_case_summary,
        "n10_row1_col1_rowcol_split": row1_col1_portfolio,
        "n10_row1_col1_full_pilot": row1_col1_full_pilot,
        "n10_symbol01_split_counts": symbol01,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = ["Nonpower FFF solver run status", ""]
    lines.append(f"Strong solver available: {inventory['strong_solver_available']}")
    lines.append(f"Available strong solvers: {inventory['available_strong_solvers']}")
    lines.append("")
    for label, data in statuses.items():
        lines.append(
            "- {label}: result={result}, timeout={timeout}, elapsed={elapsed:.3f}s, "
            "proof_log={proof}, cnf_sha256={sha}".format(
                label=label,
                result=data["result"],
                timeout=data["timeout_seconds"],
                elapsed=data["elapsed_seconds"],
                proof=data["proof_log_available"],
                sha=data["cnf_sha256"],
            )
        )
    lines.append("")
    lines.append(
        "n10 row decoded validation: Latin={latin}, reduced={reduced}, pattern={pattern}, FFF={fff}".format(
            latin=result["n10_row_decoded_validation"]["latin"],
            reduced=result["n10_row_decoded_validation"]["reduced"],
            pattern=result["n10_row_decoded_validation"]["pattern_name"],
            fff=result["n10_row_decoded_validation"]["fff"],
        )
    )
    lines.append("n10 status: not decided; no C40 claim created.")
    if drat_check:
        lines.append(f"n6 DRAT check: {drat_check['result']} by drat-trim source commit {drat_check['checker']['source_commit']}.")
    if color_gauge_drat_check:
        lines.append(
            "n6 color-gauge DRAT check: {result} by drat-trim source commit {commit}.".format(
                result=color_gauge_drat_check["result"],
                commit=color_gauge_drat_check["checker"]["source_commit"],
            )
        )
    if row1_rowcol:
        counts: dict[str, int] = {}
        for entry in row1_rowcol["solver_runs"]:
            counts[entry["result"]] = counts.get(entry["result"], 0) + 1
        lines.append(
            "n10 row1 row+col split: {cases} cases, {runs} solver jobs, counts={counts}.".format(
                cases=row1_rowcol["case_count"],
                runs=len(row1_rowcol["solver_runs"]),
                counts=counts,
            )
        )
    if row1_full:
        lines.append(
            "n10 row1 full split: {cases} CNFs generated, solver jobs started={runs}.".format(
                cases=row1_full["case_count"],
                runs=len(row1_full["solver_runs"]),
            )
        )
    if row1_full_colorgauge:
        counts = {}
        for entry in row1_full_colorgauge["solver_runs"]:
            counts[entry["result"]] = counts.get(entry["result"], 0) + 1
        lines.append(
            "n10 row1 full color-gauge split: {cases} cases, {runs} solver jobs, timeout={timeout}, max_workers={workers}, counts={counts}.".format(
                cases=row1_full_colorgauge["case_count"],
                runs=len(row1_full_colorgauge["solver_runs"]),
                timeout=row1_full_colorgauge["timeout_seconds"],
                workers=row1_full_colorgauge["max_workers"],
                counts=counts,
            )
        )
    if row1_col1_case_summary:
        lines.append(f"n10 row1+col1 canonical split: {row1_col1_case_summary['case_count']} complete cases.")
    if row1_col1_portfolio:
        counts = {}
        for entry in row1_col1_portfolio["solver_runs"]:
            counts[entry["result"]] = counts.get(entry["result"], 0) + 1
        sat_validations = [
            entry["validator_result"]["pattern_name"]
            for entry in row1_col1_portfolio["solver_runs"]
            if entry["result"] == "sat" and entry.get("validator_result")
        ]
        lines.append(
            "n10 row1+col1 row+col pilot: selected={selected}/{full}, complete={complete}, solver_jobs={runs}, counts={counts}, SAT_patterns={patterns}.".format(
                selected=row1_col1_portfolio["selected_case_count"],
                full=row1_col1_portfolio["full_case_count"],
                complete=row1_col1_portfolio["complete_portfolio"],
                runs=len(row1_col1_portfolio["solver_runs"]),
                counts=counts,
                patterns=sorted(set(sat_validations)),
            )
        )
    if row1_col1_full_pilot:
        counts = {}
        for entry in row1_col1_full_pilot["solver_runs"]:
            counts[entry["result"]] = counts.get(entry["result"], 0) + 1
        lines.append(
            "n10 row1+col1 full pilot: selected={selected}/{full}, complete={complete}, solver_jobs={runs}, timeout={timeout}, counts={counts}.".format(
                selected=row1_col1_full_pilot["selected_case_count"],
                full=row1_col1_full_pilot["full_case_count"],
                complete=row1_col1_full_pilot["complete_portfolio"],
                runs=len(row1_col1_full_pilot["solver_runs"]),
                timeout=row1_col1_full_pilot["timeout_seconds"],
                counts=counts,
            )
        )
    if symbol01:
        estimate = symbol01.get("row1_col1_estimates") or {}
        lines.append(
            "n10 symbol01 split counts: row1_orbit_total={row1_total}, row1_col1_cases={row1_col1_cases}, weighted_pre_orbit_upper_bound={upper}, weighted_row1_orbit_lower_bound={lower}.".format(
                row1_total=symbol01["row1_symbol01_orbit_total"],
                row1_col1_cases=symbol01["row1_col1_case_count"],
                upper=estimate.get("weighted_pre_orbit_upper_bound"),
                lower=estimate.get("weighted_row1_orbit_lower_bound"),
            )
        )
    lines.append("n12: not started because n10 was not decided.")
    args.summary.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
