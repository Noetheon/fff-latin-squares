#!/usr/bin/env python3
"""Recheck numerical theorem records without claiming a complete archive rerun."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "repro_runs/2026-08-10_paper_symbol_sign_audit/scripts/audit_manuscript_computational_claims.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".audit"):
        parser.error("Use an output directory under .audit")
    output.mkdir(parents=True, exist_ok=False)
    namespace = runpy.run_path(str(SCRIPT), run_name="_public_record_audit")
    entry = namespace["main"]
    entry.__globals__["RESULTS"] = output
    historical_exit = None
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            entry()
        except SystemExit as exc:
            historical_exit = str(exc)
    source = output / "manuscript_computational_claim_audit.json"
    report = json.loads(source.read_text())
    checks_pass = (report["expected_theorem_count"] == 13
                   and report["manuscript_computational_theorem_count"] == 13
                   and report["all_theorem_counts_match"] is True
                   and report["all_theorem_relevant_checks_pass"] is True
                   and len(report["claims"]) == 13
                   and all(c["all_theorem_relevant_checks_pass"] is True
                           and all(c["theorem_relevant_checks"].values()) for c in report["claims"]))
    # The historical all-package-layout gate is deliberately NOT made to pass.
    result = {"passed": checks_pass, "theorem_records": len(report["claims"]),
              "all_theorem_relevant_checks_pass": checks_pass,
              "historical_package_layout_complete": report["all_package_files_present"],
              "historical_audit_overall_pass": report["overall_pass"],
              "historical_exit": historical_exit,
              "scope": "Numerical/status record consistency only; historical package completeness is not a public export requirement.",
              "exhaustive_search_rerun": False, "claims": report["claims"]}
    (output / "public_record_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "claims"}, indent=2))
    return 0 if checks_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
