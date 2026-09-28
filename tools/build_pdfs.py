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

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 1790591089  # Frozen 2026-09-28 C271 paper edition.
SOURCE = ROOT / "manuscript/candidates/2026-09-28_research_review"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use .audit scratch output")
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for variant, entry in (("long", "main.tex"), ("compact", "main_core.tex")):
        source, build = out / variant / "source", out / variant / "build"
        shutil.copytree(SOURCE, source)
        build.mkdir()
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(EPOCH), FORCE_SOURCE_DATE="1", TZ="UTC", LC_ALL="C")
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        job = f"FFF_Latin_Squares_{variant.title()}_2026-09-28_Research_Review"
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
        identical = pdf == (ROOT / "papers" / f"FFF_{variant.title()}_Research_Dossier.pdf").read_bytes()
        records.append({"variant": variant, "sha256": hashlib.sha256(pdf).hexdigest(),
                        "byte_identical": identical, "warnings": warnings})
    result = {"passed": all(r["byte_identical"] and not r["warnings"] for r in records),
              "variants": records, "mathematical_verification": False}
    (out / "pdf_rebuild.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
