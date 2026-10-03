#!/usr/bin/env python3
"""Index the final compiled statements, retaining the predecessor evidence map."""
import argparse
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
PREVIOUS = PACKAGE.parent / "2026-09-30_counteraudit_revision"
SPEC = importlib.util.spec_from_file_location("previous_index", PREVIOUS / "scripts/build_evidence_index.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    args = parser.parse_args()
    rows = OLD.index(args.build.resolve())
    groups = json.loads((PREVIOUS / "evidence_groups.json").read_text())
    groups["19_e9_free_coordinates.tex"] = {
        "title": "Two free coordinates under an order-nine action",
        "evidence": "[Complete analytic proof](sections/19_e9_free_coordinates.tex). "
        "An actual coordinate-preserving E9 action and row-F are necessary hypotheses. "
        "[Independent finite controls](results/enumeration_results.json) are secondary, not a Latin18 census. "
        "[Review and limits](REVIEW_AND_LIMITATIONS.md); unrestricted order 18 remains open."}
    lines = ["# Current Theorem-to-Evidence Index", "",
             "**2 October 2026 selected extension:** the C280 baseline frozen at "
             "2026-09-30T12:54:17Z plus the E9 theorem accepted at 2026-10-02T14:03:38Z. "
             "This is not a complete intake of intervening work.", "",
             "Compact / Selected / Full overlap; numbers and printed pages below "
             "come from their final AUX files. Stable labels identify statements. "
             "A dash means the statement is not included in that edition.", "",
             "C38 is disproved by FFF12. C157 remains a historical computational "
             "order-10 exclusion, not a new master-search rerun. Unrestricted order 18 remains open. "
             "Written proofs, secondary finite controls and external census assumptions are "
             "different evidence. None establishes external peer review or literature priority.", ""]
    grouped = {}
    for row in rows:
        section = next(row["editions"][v]["section"] for v in ("long", "selected", "compact") if v in row["editions"])
        if section not in groups:
            raise ValueError("Unmapped mathematical section: " + section)
        grouped.setdefault(section, []).append(row)
    for section, records in grouped.items():
        group = groups[section]
        lines += ["## " + group["title"], "", group["evidence"], "",
                  "| Stable label | Compact: no. / p. | Selected: no. / p. | Full: no. / p. |",
                  "| --- | --- | --- | --- |"]
        for row in records:
            cells = []
            for edition in ("compact", "selected", "long"):
                value = row["editions"].get(edition)
                cells.append(f'{value["number"]} / {value["printed_page"]}' if value else "-")
            lines.append("| `" + row["label"] + "` | " + " | ".join(cells) + " |")
        lines.append("")
    lines.append((PREVIOUS / "UNNUMBERED_EVIDENCE.md").read_text())
    (PACKAGE / "THEOREM_EVIDENCE.md").write_text("\n".join(lines).rstrip() + "\n")
    (PACKAGE / "THEOREM_EVIDENCE.json").write_text(json.dumps({
        "scope": "C280 baseline plus E9 two-free-coordinate theorem only",
        "compiled_label_count": len(rows), "records": rows}, indent=2) + "\n")
    print(json.dumps({"compiled_statements": len(rows), "mapped_sections": len(grouped)}))


if __name__ == "__main__":
    main()
