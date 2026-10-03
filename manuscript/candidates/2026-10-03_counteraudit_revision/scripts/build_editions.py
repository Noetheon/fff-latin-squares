#!/usr/bin/env python3
"""Apply counted counterreview amendments to the frozen E9 successor."""
import argparse
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PREVIOUS = PACKAGE.parent / "2026-10-02_e9_symmetry_review"
SPEC = importlib.util.spec_from_file_location("october_predecessor", PREVIOUS / "scripts/build_editions.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
PLAN = json.loads((PACKAGE / "editions.json").read_text())
SHA = OLD.OLD.sha


def assemble(destination, edition):
    previous = OLD.assemble(destination, edition)
    changes = []

    def replace(relative, before, after):
        record = OLD.OLD.OLD.replace_exact(destination / relative, before, after)
        record["file"] = relative
        changes.append(record)

    entry = next(e["entry"] for e in PLAN["editions"] if e["id"] == edition)
    replace(entry, "2 October 2026", "3 October 2026")
    replace("sections/01_introduction.tex",
            "only the realization of all eight patterns uses the census.",
            "the realization of all eight patterns uses eight explicit witnesses,\n"
            "not census completeness.")
    replace("sections/02_definitions.tex",
            "are its parastrophic companions.  If a trade has support size $k$ and\n"
            "$\\delta=(-1)^k$, then its sign ratios are",
            "are its parastrophic companions. For a two-line trade, let $k=|C|$\n"
            "be the number of positions in the selected cycle union, so the trade\n"
            "changes $2k$ cells. Use the same convention in each coordinate view.\n"
            "Put $\\delta=(-1)^k$. Then its sign ratios are")
    if edition == "compact":
        replace("sections/08_short_reproducibility.tex",
                "The companion\n\\nolinkurl{scripts/check_compact_examples.py} runs the finite checks above.",
                "Run the companion\n"
                "\\nolinkurl{tools/check_paper_editions.py} with\n"
                "\\texttt{--build .audit/three-editions-check} to invoke the finite\n"
                "example checks and optional PDF layout checks.")
        replace("sections/08_short_reproducibility.tex",
                "2026-10-02_e9_symmetry_review/", "2026-10-03_counteraudit_revision/")
        replace("sections/00_status_note.tex",
                "Selected Results and the Full Report.",
                "Selected Results and the Full Report. The 3 October revision clarifies\n"
                "wording and uses eight explicit pattern witnesses; its research cutoff\n"
                "and open order-$18$ boundary are unchanged.")
        computational = "sections/06_short_computational.tex"
    else:
        replace("sections/00_status_note.tex",
                "accepted on 2 October 2026 at 14:03 UTC. It does not import all",
                "included in the internal evidence snapshot on 2 October 2026 at\n"
                "14:03 UTC. The 3 October revision corrects wording and reproduction\n"
                "guidance without extending that research cutoff. It does not import all")
        computational = ("sections/05_computational_core.tex" if edition == "selected"
                         else "sections/05_computational_results.tex")
        replace("sections/06_snapshot_evidence.tex",
                "The preceding dated source package",
                "The current edition's build and evidence map are in\n"
                "\\nolinkurl{manuscript/candidates/2026-10-03_counteraudit_revision/}.\n"
                "It adds counterreview corrections and explicit pattern witnesses to\n"
                "the selected E9 extension of 2 October. The theorem and its finite\n"
                "control are retained in\n"
                "\\nolinkurl{manuscript/candidates/2026-10-02_e9_symmetry_review/}.\n"
                "This is internal evidence review, not journal acceptance.\n\n"
                "The preceding dated source package")
        replace("sections/06_snapshot_evidence.tex",
                "The present successor is", "The September baseline successor is")
        replace("sections/06_snapshot_evidence.tex",
                "The two PDF variants have the same evidence boundary and overlapping\ncontent;",
                "The three reading editions share this evidence boundary and have\n"
                "overlapping selections of results;")
        replace("sections/19_e9_free_coordinates.tex",
                "The proofs above are analytic.",
                "The proofs above are combinatorial and group-theoretic.")
        replace("sections/19_e9_free_coordinates.tex",
                "\\paragraph{Evidence and remaining scope.}",
                "\\paragraph{Relation to prior work.}\n"
                "Stones, Vojt\\v{e}chovsk\\'y and Wanless study general autotopism\n"
                "cycle structures, including fixed points, cycle divisibility and\n"
                "subsquares~\\cite{StonesVojtechovskyWanless2012}. The present argument\n"
                "uses a whole order-nine action and the additional row-F hypothesis.\n"
                "This difference of hypotheses is not a proof of novelty or of\n"
                "nonderivability from earlier results. The cited work must not be\n"
                "read as an FFF18 exclusion.\n\n"
                "\\paragraph{Evidence and remaining scope.}")
        bib = PACKAGE / "references_review.bib"
        existing = (destination / "references_nonpower.bib").read_text()
        replace("references_nonpower.bib", existing, existing.rstrip() + "\n\n" + bib.read_text())

    witness = (PACKAGE / "sections/pattern_witnesses.tex").read_text()
    marker = "\\begin{corollary}\\label{cor:all-patterns}"
    replace(computational, marker, witness + "\n\n" + marker)
    replace(computational,
            "Computational Theorem~\\ref{cthm:order8} supplies one order-$8$ square of each\npattern.",
            "The eight explicit witnesses above supply one order-$8$ square of each\n"
            "pattern, independently of the completeness or counts of the census.")
    return {"predecessor": previous, "counterreview_changes": changes,
            "shared_witness_source_sha256": SHA(PACKAGE / "sections/pattern_witnesses.tex"),
            "assembled_sources_sha256": {
                p.relative_to(destination).as_posix(): SHA(p)
                for p in sorted(destination.rglob("*")) if p.suffix in {".tex", ".bib"}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    # Reuse the established compiler, warning gates and page limits. Overrides
    # affect only this process, never the frozen predecessor's files.
    OLD.OLD.assemble = assemble
    OLD.OLD.PLAN = PLAN
    OLD.OLD.EPOCH = 1791028800
    result = OLD.OLD.main()
    path = args.output.resolve() / "edition_build.json"
    report = json.loads(path.read_text())
    report.update({"scope": PLAN["scope"], "proof_dependencies_changed": True,
                   "baseline_evidence_cutoff_utc": PLAN["baseline_evidence_cutoff_utc"]})
    path.write_text(json.dumps(report, indent=2) + "\n")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
