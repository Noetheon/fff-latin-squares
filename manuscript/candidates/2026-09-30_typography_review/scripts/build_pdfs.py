#!/usr/bin/env python3
"""Build a layout-only successor without rewriting the frozen C280 sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parents[2]
BASE = SOURCE.parent / "2026-09-30_research_review"
EPOCH = 1790772857
OVERRIDES = frozenset({
    "main.tex", "main_core.tex", "paper_setup.tex", "sections/00_abstract.tex",
})


def assemble(destination: Path) -> dict:
    overrides = {p.relative_to(SOURCE).as_posix()
                 for p in SOURCE.rglob("*.tex")}
    if overrides != OVERRIDES:
        raise ValueError("Unexpected or missing typography override")
    shutil.copytree(BASE, destination,
                    ignore=shutil.ignore_patterns("evidence", "scripts", "results"))
    preserved = {}
    for relative in sorted(OVERRIDES):
        shutil.copyfile(SOURCE / relative, destination / relative)
    for original in sorted(BASE.rglob("*")):
        relative = original.relative_to(BASE).as_posix()
        if original.suffix not in {".tex", ".bib"} or relative in OVERRIDES:
            continue
        if original.read_bytes() != (destination / relative).read_bytes():
            raise ValueError("Scientific text changed: " + relative)
        preserved[relative] = hashlib.sha256(original.read_bytes()).hexdigest()
    if not preserved:
        raise ValueError("No preserved scientific sources")
    return {"body_and_bibliography_byte_preserved": True,
            "preserved_sources_sha256": preserved,
            "editorial_overrides": sorted(OVERRIDES)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-only", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use fresh .audit scratch output")
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for variant, entry in (("long", "main.tex"), ("compact", "main_core.tex")):
        source, build = out / variant / "source", out / variant / "build"
        source.parent.mkdir()
        preservation = assemble(source)
        build.mkdir()
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(EPOCH),
                   FORCE_SOURCE_DATE="1", TZ="UTC", LC_ALL="C")
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        job = f"FFF_Latin_Squares_{variant.title()}_2026-09-30_Typography_Review"
        command = ["latexmk", "-norc", "-pdf", "-interaction=nonstopmode",
                   "-halt-on-error", "-file-line-error",
                   "-pdflatex=pdflatex -no-shell-escape %O %S",
                   f"-outdir={build}", f"-jobname={job}", entry]
        with (out / variant / "build.log").open("w") as stream:
            subprocess.run(command, cwd=source, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, timeout=180, check=True)
        log = (build / f"{job}.log").read_text()
        warnings = [line for line in log.splitlines() if re.search(
            r"LaTeX Warning|Package .* Warning|Overfull|Underfull|undefined", line)]
        pdf = (build / f"{job}.pdf").read_bytes()
        published = ROOT / "papers" / f"FFF_{variant.title()}_Research_Dossier.pdf"
        info = subprocess.check_output(["pdfinfo", str(build / f"{job}.pdf")], text=True)
        records.append({"variant": variant,
                        "sha256": hashlib.sha256(pdf).hexdigest(),
                        "pages": int(re.search(r"^Pages:\s+(\d+)$", info, re.M).group(1)),
                        "byte_identical": published.is_file() and pdf == published.read_bytes(),
                        "warnings": warnings, "source_preservation": preservation})
    result = {
        "passed": all((r["byte_identical"] or args.candidate_only)
                      and not r["warnings"] for r in records),
        "candidate_only": args.candidate_only,
        "published_bytes_verified": not args.candidate_only and
                                    all(r["byte_identical"] for r in records),
        "variants": records, "mathematical_claims_changed": False,
        "independent_human_peer_review": False,
    }
    (out / "pdf_rebuild.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
