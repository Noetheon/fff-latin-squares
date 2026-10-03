#!/usr/bin/env python3
"""Add the E9 proof to the reviewed three-edition source without editing it."""
import importlib.util
import argparse
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PREVIOUS = PACKAGE.parent / "2026-09-30_counteraudit_revision"
SPEC = importlib.util.spec_from_file_location("e9_predecessor", PREVIOUS / "scripts/build_editions.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)
PLAN = json.loads((PACKAGE / "editions.json").read_text())
ORIGINAL_ASSEMBLE = OLD.assemble


def assemble(destination, edition):
    previous = ORIGINAL_ASSEMBLE(destination, edition)
    changes = []

    def replace(relative, before, after):
        record = OLD.OLD.replace_exact(destination / relative, before, after)
        record["file"] = relative
        changes.append(record)

    entry = next(e["entry"] for e in PLAN["editions"] if e["id"] == edition)
    replace(entry, "30 September 2026", "2 October 2026")
    if edition == "compact":
        replace("sections/00_status_note.tex",
                "use the evidence cutoff of 30 September 2026 at 12:54 UTC.",
                "use the 30 September baseline, with a selected extension of\n"
                "2 October 2026: an order-nine symmetry obstruction proved in\n"
                "Selected Results and the Full Report.")
        replace("sections/08_short_reproducibility.tex",
                "2026-09-30_counteraudit_revision/", "2026-10-02_e9_symmetry_review/")
    else:
        replace("sections/00_status_note.tex",
                "The evidence intake for this edition is 30 September 2026 at 12:54 UTC.",
                "The baseline evidence intake is 30 September 2026 at 12:54 UTC.\n"
                "This edition adds only the completed order-nine symmetry theorem\n"
                "accepted on 2 October 2026 at 14:03 UTC. It does not import all\n"
                "intervening working results or a complete symmetry classification.")
        replace("sections/00_status_note.tex",
                "Work after this\nfixed intake, in particular the unfinished streaming mate-mask campaign,\nis not included.",
                "Other work after this\nfixed baseline, including later search campaigns, is not included.")
        replace(entry, r"\input{sections/15_current_search_boundaries}",
                "\\input{sections/19_e9_free_coordinates}\n"
                "\\input{sections/15_current_search_boundaries}")
        section = PACKAGE / "sections/19_e9_free_coordinates.tex"
        (destination / "sections" / section.name).write_bytes(section.read_bytes())
    return {"predecessor": previous, "e9_changes": changes,
            "new_section_sha256": OLD.sha(PACKAGE / "sections/19_e9_free_coordinates.tex")
                if edition != "compact" else None,
            "assembled_sources_sha256": {p.relative_to(destination).as_posix(): OLD.sha(p)
                for p in sorted(destination.rglob("*")) if p.suffix in {".tex", ".bib"}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    # Reuse the reviewed compiler/diagnostic/page-budget loop; overrides affect
    # this process only. The predecessor's sources remain byte-identical.
    OLD.assemble = assemble
    OLD.PLAN = PLAN
    OLD.EPOCH = 1790953200
    result = OLD.main()
    # Its common builder marks an editorial-only revision; declare our scope
    # in the resulting report, without changing its pass/fail decision.
    output = args.output.resolve()
    path = output / "edition_build.json"
    report = json.loads(path.read_text())
    report["new_mathematical_claims"] = True
    report["scope"] = PLAN["scope"]
    report["baseline_evidence_cutoff_utc"] = PLAN["baseline_evidence_cutoff_utc"]
    path.write_text(json.dumps(report, indent=2) + "\n")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
