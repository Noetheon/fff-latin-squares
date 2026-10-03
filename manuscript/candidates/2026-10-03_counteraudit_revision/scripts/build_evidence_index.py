#!/usr/bin/env python3
"""Index actual compiled statements while preserving the predecessor ledger."""
import argparse
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
BASE = PACKAGE.parent / "2026-09-30_counteraudit_revision"
SPEC = importlib.util.spec_from_file_location("index_predecessor", BASE / "scripts/build_evidence_index.py")
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    args = parser.parse_args()
    records = OLD.index(args.build.resolve())
    groups = json.loads((BASE / "evidence_groups.json").read_text())
    groups["19_e9_free_coordinates.tex"] = {
        "title": "Two free coordinates under an order-nine action",
        "evidence": "[Frozen E9 proof](../2026-10-02_e9_symmetry_review/sections/19_e9_free_coordinates.tex), "
        "with the [current wording/literature amendments](scripts/build_editions.py). "
        "Actual E9 action, row-F and two free coordinates remain required. "
        "[Targeted literature comparison](LITERATURE_SCOPE.md) is not a priority certificate. "
        "[Finite controls](../2026-10-02_e9_symmetry_review/results/enumeration_results.json) "
        "remain secondary; unrestricted order 18 is open."}
    groups["02_definitions.tex"]["evidence"] += (
        " The [current amendment](scripts/build_editions.py) specifies k selected "
        "cycle positions and 2k changed cells; the sign formula is unchanged.")
    groups["05_computational_results.tex"]["evidence"] += (
        " The all-pattern existence corollary now uses [eight explicit witnesses]"
        "(evidence/pattern_witnesses.json), not census completeness. "
        "The 230 and 5/225 counts retain their census dependency.")
    lines = ["# Current Theorem-to-Evidence Index", "",
             "**3 October 2026 counterreview revision.** Research cutoff unchanged: "
             "C280 baseline (2026-09-30T12:54:17Z) plus the selected E9 theorem "
             "(2026-10-02T14:03:38Z). No later working campaigns are imported.", "",
             "Numbers and printed pages come from the final AUX files. Compact, "
             "Selected Results and Full Report overlap; they are not independent studies. "
             "The [counted amendments](scripts/build_editions.py) apply to assembled copies "
             "only; every predecessor source stays frozen.", "",
             "**Boundary:** C38 is disproved by FFF12. Unrestricted order 18 remains open. "
             "C157 retains its historical computational dependencies. This revision is "
             "not a full census/master replay, external peer review or novelty certificate.", ""]
    grouped = {}
    for record in records:
        section = next(record["editions"][v]["section"] for v in ("long", "selected", "compact")
                       if v in record["editions"])
        if section not in groups:
            raise ValueError("Unmapped section: " + section)
        grouped.setdefault(section, []).append(record)
    for section, rows in grouped.items():
        group = groups[section]
        lines += ["## " + group["title"], "", group["evidence"], "",
                  "| Stable label | Compact: no. / p. | Selected: no. / p. | Full: no. / p. |",
                  "| --- | --- | --- | --- |"]
        for row in rows:
            cells = []
            for variant in ("compact", "selected", "long"):
                value = row["editions"].get(variant)
                cells.append(f'{value["number"]} / {value["printed_page"]}' if value else "-")
            lines.append("| " + row["label"] + " | " + " | ".join(cells) + " |")
        lines.append("")
    lines.append((BASE / "UNNUMBERED_EVIDENCE.md").read_text())
    (PACKAGE / "THEOREM_EVIDENCE.md").write_text("\n".join(lines).rstrip() + "\n")
    (PACKAGE / "THEOREM_EVIDENCE.json").write_text(json.dumps({
        "scope": "Unchanged C280 plus selected E9 research cutoff; counterreview amendments",
        "compiled_label_count": len(records), "records": records}, indent=2) + "\n")
    print(json.dumps({"compiled_labels": len(records), "mapped_sections": len(grouped)}))


if __name__ == "__main__":
    main()
