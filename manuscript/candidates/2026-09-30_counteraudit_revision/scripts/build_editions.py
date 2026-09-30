#!/usr/bin/env python3
"""Build the counteraudit successor; never rewrite a frozen predecessor."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PREVIOUS = PACKAGE.parent / "2026-09-30_three_editions"
SPEC = importlib.util.spec_from_file_location("previous_editions", PREVIOUS / "scripts/build_editions.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
PLAN = OLD.PLAN
EPOCH = OLD.EPOCH


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(destination, edition):
    previous = OLD.assemble(destination, edition)
    changes = []

    def replace(relative, before, after):
        change = OLD.replace_exact(destination / relative, before, after)
        change["file"] = relative
        changes.append(change)

    if edition in {"long", "selected"}:
        replace("sections/00_abstract.tex",
                "disprove the former power-of-two existence conjecture.\nThe order-$10$ exclusion combines a group-theoretic reduction with exact\nfinite computation.",
                "disprove this project's former power-of-two existence conjecture.\nThe order-$10$ exclusion uses a complete cycle-type palette reduction,\nresidual-group orbit covers, and exact finite searches, without a\nprimitive-group filter.")
    else:
        replace("sections/00_abstract.tex", "disproves the former power-of-two-only conjecture.",
                "disproves this project's former power-of-two-only conjecture.")
        replace("sections/00_status_note.tex", "refutes the former power-of-two-only conjecture.",
                "refutes this project's former power-of-two-only conjecture.")
        replace("sections/07_short_order12.tex",
                "is FFF. Thus the conjecture that nontrivial FFF squares exist only\nat powers of two is false.",
                "is FFF. Thus this project's earlier working conjecture that\nnontrivial FFF squares exist only at powers of two is false.")
        replace("sections/08_short_reproducibility.tex",
                "\\begin{center}\\small\n\\texttt{python3 -B tools/build\\_paper\\_editions.py}\\\\\n\\texttt{--output .audit/three-editions-check}\n\\end{center}",
                "\\begin{quote}\\small\n\\begin{verbatim}\npython3 -B tools/build_paper_editions.py \\\n  --output .audit/three-editions-check\n\\end{verbatim}\n\\end{quote}")
        replace("sections/08_short_reproducibility.tex",
                "\\nolinkurl{manuscript/candidates/2026-09-30_three_editions/}.",
                "\\nolinkurl{manuscript/candidates/2026-09-30_counteraudit_revision/}.\nIts finite checker is retained in the three-edition predecessor.")

    if edition == "long":
        replace("sections/00_status_note.tex", "The compact\ncompanion imports",
                "The Selected Results\ncompanion imports")

    replace("sections/07_order10_exclusion.tex",
            "condition simultaneously in all three coordinate views.  The nearby strict\nclassification historically suggested a stronger existence conjecture, now\nknown to be false.",
            "condition simultaneously in all three coordinate views. The nearby strict\nclassification motivated an earlier working conjecture of this project,\nnow known to be false; the weaker FFF assertion is not a theorem or\nconjecture attributed to Kobayashi and Nakamura.")
    replace("sections/07_order10_exclusion.tex",
            "The assertion that FFF Latin squares of order $n>1$ exist exactly at powers\nof two is false.",
            "This project's earlier working conjecture that FFF Latin squares of\norder $n>1$ exist exactly at powers of two is false.")
    replace("references_nonpower.bib", "  eprint        = {2607.09459},",
            "  eprint        = {2607.09459},\n  howpublished  = {Preprint, \\url{https://arxiv.org/abs/2607.09459}},")
    replace("references_nonpower.bib", "@misc{ErskineGriggs2024CycleSwitch,",
            "@article{ErskineGriggs2024CycleSwitch,")
    replace("references_nonpower.bib",
            "  year          = {2024},\n  eprint        = {2405.07750},\n  howpublished  = {Preprint, \\url{https://arxiv.org/abs/2405.07750}},",
            "  year          = {2025},\n  journal       = {Journal of Combinatorial Designs},\n  volume        = {33},\n  number        = {5},\n  pages         = {195--204},\n  doi           = {10.1002/jcd.21975},\n  eprint        = {2405.07750},")
    replace("references_nonpower.bib",
            "  note          = {Section 3.2 prints the 11 rotational starters of the no-6-cycle STS(19)}",
            "  note          = {\\url{https://doi.org/10.1002/jcd.21975}. Preprint arXiv:2405.07750, Section 3.2, prints the 11 rotational starters of the no-6-cycle STS(19)}")
    return {"predecessor": previous, "counteraudit_changes": changes,
            "assembled_sources_sha256": {p.relative_to(destination).as_posix(): sha(p)
                for p in sorted(destination.rglob("*")) if p.suffix in {".tex", ".bib"}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use a new output directory under .audit/")
    out.mkdir(parents=True, exist_ok=False)
    (out / "pdfs").mkdir()
    variants = []
    for edition in PLAN["editions"]:
        name = edition["id"]
        source, build = out / name / "source", out / name / "build"
        source.parent.mkdir()
        record = assemble(source, name)
        build.mkdir()
        job = f"FFF_{name.title()}_2026-09-30_Counteraudit"
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(EPOCH), FORCE_SOURCE_DATE="1", TZ="UTC", LC_ALL="C")
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        command = ["latexmk", "-norc", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                   "-file-line-error", "-pdflatex=pdflatex -no-shell-escape %O %S",
                   f"-outdir={build}", f"-jobname={job}", edition["entry"]]
        with (out / name / "build.log").open("w") as stream:
            subprocess.run(command, cwd=source, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, timeout=180, check=True)
        log = (build / f"{job}.log").read_text()
        warnings = [line for line in log.splitlines() if re.search(
            r"LaTeX Warning|Package .* Warning|Overfull|Underfull|undefined", line)]
        pdf = build / f"{job}.pdf"
        shutil.copyfile(pdf, out / "pdfs" / edition["pdf"])
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        pages = int(re.search(r"^Pages:\s+(\d+)$", info, re.M).group(1))
        variants.append({"id": name, "pages": pages, "pdf": "pdfs/" + edition["pdf"],
                         "sha256": sha(pdf), "page_budget_passed": OLD.check_page_budget(edition, pages),
                         "warnings": warnings, "source_record": record})
    result = {"passed": all(v["page_budget_passed"] and not v["warnings"] for v in variants),
              "evidence_cutoff_utc": PLAN["evidence_cutoff_utc"],
              "new_mathematical_claims": False, "independent_human_peer_review": False,
              "variants": variants,
              "environment": {"source_date_epoch": EPOCH,
                              "pdflatex": subprocess.check_output(["pdflatex", "--version"], text=True).splitlines()[0],
                              "latexmk": subprocess.check_output(["latexmk", "-v"], text=True).strip()}}
    (out / "edition_build.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "editions": [
        {k: v[k] for k in ("id", "pages", "sha256", "warnings")} for v in variants]}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
