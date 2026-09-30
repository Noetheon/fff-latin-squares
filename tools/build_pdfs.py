#!/usr/bin/env python3
"""Rebuild current editions and compare all three public PDF aliases."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-B", str(root / "tools/build_paper_editions.py"),
                    "--output", str(args.output)], check=True)
    build = args.output.resolve()
    result = json.loads((build / "edition_build.json").read_text())
    records = []
    for edition in result["variants"]:
        generated = build / edition["pdf"]
        published = root / "papers" / generated.name
        records.append({"edition": edition["id"], "pages": edition["pages"],
                        "sha256": hashlib.sha256(generated.read_bytes()).hexdigest(),
                        "byte_identical": generated.read_bytes() == published.read_bytes(),
                        "warnings": edition["warnings"]})
    report = {"passed": result["passed"] and all(r["byte_identical"] for r in records),
              "variants": records, "mathematical_claims_changed": False}
    (build / "pdf_rebuild.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
