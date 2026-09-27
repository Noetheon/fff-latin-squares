#!/usr/bin/env python3
"""Fresh bounded controls for the C251 edition, with exact scientific comparison."""
import argparse
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript/candidates/2026-09-27_research_snapshot"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".audit") or output.exists():
        parser.error("Use a new file under .audit; frozen reference outputs are read-only")
    namespace = runpy.run_path(str(SOURCE / "scripts/audit_snapshot.py"))
    start = time.monotonic()
    sources = namespace["audit_sources"]()
    actual = namespace["run_finite_checks"]()
    expected = json.loads((ROOT / "verification/snapshot_2026-09-27_reference.json").read_text())
    matched = actual == expected["finite_checks"]
    report = {"passed": matched, "sources": sources, "finite_checks": actual,
              "exact_scientific_result_match": matched,
              "not_compared": ["elapsed_seconds", "source inventory of the larger original capture"],
              "heavy_solvers_run": False, "historical_unsat_proofs_rechecked": False,
              "elapsed_seconds": round(time.monotonic() - start, 3)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "finite_checks"}))
    return 0 if matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
