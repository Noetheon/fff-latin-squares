#!/usr/bin/env python3
"""Build three reading editions from one frozen scientific source."""
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
PLAN = json.loads((PACKAGE / "editions.json").read_text())
BASE = PACKAGE.parent / PLAN["scientific_source"]
LAYOUT = PACKAGE.parent / PLAN["layout_source"]
EPOCH = 1790772857
LONG_SHA256 = "836864560ee69c4bbfce14ebbcb848c983f39d0f006c1454c5c22eb58d7be81a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def excerpt(text: str, start: str, end: str | None = None,
            include_end: bool = False) -> str:
    """Select a unique, complete source span; never guess at moved markers."""
    if text.count(start) != 1:
        raise ValueError(f"Non-unique start marker: {start!r}")
    first = text.index(start)
    if end is None:
        return text[first:]
    if text.count(end) != 1 or text.index(end) <= first:
        raise ValueError(f"Non-unique or out-of-order end marker: {end!r}")
    last = text.index(end) + (len(end) if include_end else 0)
    return text[first:last]


def compact_fragments() -> tuple[dict[str, str], list[dict]]:
    records = []

    def take(relative: str, start: str, end: str | None = None,
             include_end: bool = False) -> str:
        path = BASE / "sections" / relative
        value = excerpt(path.read_text(), start, end, include_end)
        records.append({"source": path.relative_to(ROOT).as_posix(),
                        "source_sha256": sha(path), "start": start, "end": end,
                        "include_end": include_end,
                        "excerpt_sha256": hashlib.sha256(value.encode()).hexdigest()})
        return value

    definitions = take("02_definitions.tex", r"\section{Definitions and invariance}",
                       "\\begin{definition}\nFix two rows")
    definitions += take("02_definitions.tex", r"An \emph{isotopy}")
    congruences = (
        "\\section{Binary congruences and a nongroup example}\n\n"
        "A Latin operation is a quasigroup operation: each equation $a*x=b$\n"
        "or $y*a=b$ has a unique solution. The two solution operations are\n"
        "left and right division. A congruence is an equivalence relation\n"
        "preserved by multiplication and both divisions.\n\n"
    )
    congruences += take("04_congruence_obstructions.tex",
                        "We next use congruences", "\\begin{corollary}[Order-$2p$ simplicity]")
    congruences += take("04_congruence_obstructions.tex",
                        "The same theorem also gives a census-free nongroup example.")
    computational = take("05_computational_core.tex", r"\section{Computational results}",
                         "\\begin{computationaltheorem}[Subsquare census of the FFF classes]")
    # Keep the census heading and its small table together without shrinking text.
    census_start = computational.index(r"\begin{computationaltheorem}[Order-$8$ pattern census]")
    computational = (computational[:census_start] + "\\begin{samepage}\n" +
                     computational[census_start:].rstrip() + "\n\\end{samepage}\n\n")
    computational += take("05_computational_core.tex", "The ordered non-symmetric labels")
    order12 = (
        "\\section{An explicit order-12 counterexample}\n"
        "The following statement is a direct finite verification, not an\n"
        "inference from an incomplete search or a solver timeout.\n\n"
        "\\begin{computationaltheorem}[An order-$12$ FFF square]\n"
        "\\label{cthm:nonpower-witnesses}\n"
        "The reduced Latin square displayed in Table~\\ref{tab:order12-witness}\n"
        "is FFF. Thus the conjecture that nontrivial FFF squares exist only\n"
        "at powers of two is false.\n"
        "\\end{computationaltheorem}\n\n"
    )
    table = take("08_nonpower_fff.tex", r"\begin{table}[ht]", r"\end{table}", True)
    if table.count(r"\scriptsize") != 1:
        raise ValueError("Unexpected order-12 table typography")
    order12 += table.replace(r"\scriptsize", r"\small")
    order12 += (
        "\n\nThe check verifies every row and column and constructs the\n"
        "relative permutations for all $3\\binom{12}{2}=198$ line pairs.\n"
        "It rejects fixed points and odd cycles explicitly. The exact table\n"
        "is supplied so that this positive existence statement can be\n"
        "rechecked without an external census. This does not decide order $18$.\n"
    )
    return {
        "02_short_definitions.tex": definitions,
        "05_short_congruences.tex": congruences,
        "06_short_computational.tex": computational,
        "07_short_order12.tex": order12,
    }, records


def replace_exact(path: Path, before: str, after: str, count: int = 1) -> dict:
    text = path.read_text()
    if text.count(before) != count:
        raise ValueError(f"Editorial replacement count changed in {path.name}: {before!r}")
    path.write_text(text.replace(before, after))
    return {"file": path.name, "before": before, "after": after, "count": count}


def assemble(destination: Path, edition: str) -> dict:
    if edition not in {e["id"] for e in PLAN["editions"]}:
        raise ValueError("Unknown edition")
    spec = importlib.util.spec_from_file_location("frozen_layout_builder",
                                                   LAYOUT / "scripts/build_pdfs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inherited = module.assemble(destination)
    records = {"frozen_layout": inherited, "editorial_changes": [],
               "excerpts": [], "new_source_sha256": {}}
    if edition == "selected":
        changes = records["editorial_changes"]
        changes.append(replace_exact(destination / "main_core.tex",
                                     "Research dossier: compact companion",
                                     "Research dossier: Selected Results"))
        for name in ("00_status_note.tex", "01_introduction_core.tex",
                     "06_reproducibility_core.tex"):
            path = destination / "sections" / name
            # Only reader-facing edition names change; theorem/proof blocks do not.
            count = path.read_text().count("compact")
            changes.append(replace_exact(path, "compact", "selected-results", count))
    elif edition == "compact":
        for original in sorted(PACKAGE.rglob("*.tex")):
            target = destination / original.relative_to(PACKAGE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            records["new_source_sha256"][original.relative_to(ROOT).as_posix()] = sha(original)
        fragments, records["excerpts"] = compact_fragments()
        records["presentation_adjustments"] = [
            "Keep the order-8 census statement and table on one page with samepage",
            "Enlarge order-12 table from scriptsize to small; retain all entries",
        ]
        for name, text in fragments.items():
            (destination / "sections" / name).write_text(text)
    # The historical source package is never written or resealed by this builder.
    records["assembled_sources_sha256"] = {
        p.relative_to(destination).as_posix(): sha(p)
        for p in sorted(destination.rglob("*")) if p.suffix in {".tex", ".bib"}
    }
    return records


def check_page_budget(edition: dict, pages: int) -> bool:
    bounds = edition["page_range_including_front_matter_and_references"]
    return bounds is None or bounds[0] <= pages <= bounds[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use a fresh output directory below .audit/")
    out.mkdir(parents=True, exist_ok=False)
    (out / "pdfs").mkdir()
    variants = []
    for edition in PLAN["editions"]:
        variant = edition["id"]
        source, build = out / variant / "source", out / variant / "build"
        source.parent.mkdir()
        sources = assemble(source, variant)
        build.mkdir()
        # Preserve the old long job name, epoch and sources for exact byte comparison.
        job = ("FFF_Latin_Squares_Long_2026-09-30_Typography_Review" if variant == "long"
               else f"FFF_Latin_Squares_{variant.title()}_2026-09-30_Three_Editions")
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(EPOCH), FORCE_SOURCE_DATE="1",
                   TZ="UTC", LC_ALL="C")
        for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS", "TEXMFOUTPUT"):
            env.pop(key, None)
        command = ["latexmk", "-norc", "-pdf", "-interaction=nonstopmode",
                   "-halt-on-error", "-file-line-error",
                   "-pdflatex=pdflatex -no-shell-escape %O %S",
                   f"-outdir={build}", f"-jobname={job}", edition["entry"]]
        with (out / variant / "build.log").open("w") as stream:
            subprocess.run(command, cwd=source, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, timeout=180, check=True)
        log = (build / f"{job}.log").read_text()
        warnings = [line for line in log.splitlines() if re.search(
            r"LaTeX Warning|Package .* Warning|Overfull|Underfull|undefined", line)]
        pdf = build / f"{job}.pdf"
        shutil.copyfile(pdf, out / "pdfs" / edition["pdf"])
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        pages = int(re.search(r"^Pages:\s+(\d+)$", info, re.M).group(1))
        variants.append({"id": variant, "pages": pages,
                         "pdf": f"pdfs/{edition['pdf']}", "sha256": sha(pdf),
                         "page_budget_passed": check_page_budget(edition, pages),
                         "warnings": warnings, "source_record": sources,
                         "long_unchanged": sha(pdf) == LONG_SHA256 if variant == "long" else None})
    result = {
        "passed": all(not v["warnings"] and v["page_budget_passed"] and
                      v["long_unchanged"] is not False for v in variants),
        "evidence_cutoff_utc": PLAN["evidence_cutoff_utc"],
        "new_mathematical_claims": False, "published": False,
        "independent_human_peer_review": False, "variants": variants,
        "environment": {
            "source_date_epoch": EPOCH,
            "pdflatex": subprocess.check_output(["pdflatex", "--version"], text=True).splitlines()[0],
            "latexmk": subprocess.check_output(["latexmk", "-v"], text=True).strip(),
        },
    }
    (out / "edition_build.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"],
                      "variants": [{k: v[k] for k in ("id", "pages", "sha256", "warnings",
                                                       "page_budget_passed", "long_unchanged")}
                                   for v in variants]}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
