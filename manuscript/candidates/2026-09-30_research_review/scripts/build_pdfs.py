#!/usr/bin/env python3
"""Rebuild the two public PDFs in scratch space and check byte identity."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parents[2]
EPOCH = 1790772857  # Fixed evidence intake, 2026-09-30 12:54:17 UTC.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-only", action="store_true",
                        help="Build a successor for inspection; not a published-byte verification")
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use .audit scratch output")
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for variant, entry in (("long", "main.tex"), ("compact", "main_core.tex")):
        source, build = out / variant / "source", out / variant / "build"
        shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("evidence", "scripts", "results"))
        build.mkdir()
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(EPOCH), FORCE_SOURCE_DATE="1", TZ="UTC", LC_ALL="C")
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        job = f"FFF_Latin_Squares_{variant.title()}_2026-09-30_Research_Review"
        command = ["latexmk", "-norc", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                   "-file-line-error", "-pdflatex=pdflatex -no-shell-escape %O %S",
                   f"-outdir={build}", f"-jobname={job}", entry]
        with (out / variant / "build.log").open("w") as stream:
            subprocess.run(command, cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT,
                           timeout=180, check=True)
        log = (build / f"{job}.log").read_text()
        warnings = [line for line in log.splitlines() if re.search(
            r"LaTeX Warning|Package .* Warning|Overfull|Underfull|undefined", line)]
        pdf = (build / f"{job}.pdf").read_bytes()
        published = ROOT / "papers" / f"FFF_{variant.title()}_Research_Dossier.pdf"
        identical = published.is_file() and pdf == published.read_bytes()
        info = subprocess.check_output(["pdfinfo", str(build / f"{job}.pdf")], text=True)
        pages = int(re.search(r"^Pages:\s+(\d+)$", info, re.M).group(1))
        records.append({"variant": variant, "sha256": hashlib.sha256(pdf).hexdigest(),
                        "pages": pages, "byte_identical": identical, "warnings": warnings})
    result = {"passed": all((r["byte_identical"] or args.candidate_only) and not r["warnings"] for r in records),
              "published_bytes_verified": not args.candidate_only and all(r["byte_identical"] for r in records),
              "candidate_only": args.candidate_only,
              "variants": records, "mathematical_verification": False}
    (out / "pdf_rebuild.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
