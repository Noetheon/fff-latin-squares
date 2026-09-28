#!/usr/bin/env python3
"""Fresh bounded C271 checks with explicit scientific comparison rules."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript/candidates/2026-09-28_research_review"
CHECKS = (
    ("audit_snapshot.py", "snapshot_audit.json", ("elapsed_seconds", "sources")),
    ("audit_update.py", "update_audit.json", ("elapsed_seconds", "captured_update_files_verified")),
    ("audit_crt_update.py", "crt_update_audit.json", ("runtime_seconds",)),
)


def scientific(record, ignored):
    return {key: value for key, value in record.items() if key not in ignored}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".audit") or output.exists():
        parser.error("Use a new file under .audit; frozen reports are read-only")
    scratch = output.with_suffix("")
    scratch.mkdir(parents=True, exist_ok=False)
    start, records = time.monotonic(), []
    for script, filename, ignored in CHECKS:
        report_path = scratch / filename
        subprocess.run([sys.executable, "-B", str(SOURCE / "scripts" / script),
                        "--output", str(report_path)], check=True, timeout=240)
        actual = json.loads(report_path.read_text())
        expected = json.loads((SOURCE / "results" / filename).read_text())
        match = scientific(actual, ignored) == scientific(expected, ignored)
        records.append({"script": script, "scientific_fields_match": match,
                        "ignored_fields": list(ignored),
                        "inventory_policy": "Selected public source hashes are checked independently by each auditor; private capture counts are not mathematical results."})
    result = {"passed": all(row["scientific_fields_match"] for row in records),
              "cutoff": "C271", "checks": records,
              "heavy_solvers_run": False, "historical_unsat_proofs_rechecked": False,
              "elapsed_seconds": round(time.monotonic()-start, 3)}
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
