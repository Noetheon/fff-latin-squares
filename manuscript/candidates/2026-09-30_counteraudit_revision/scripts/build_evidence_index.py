#!/usr/bin/env python3
"""Index compiled statement labels and evidence groups, not certify their proofs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
BASE = PACKAGE.parent / "2026-09-30_research_review"
KINDS = {"thm", "cthm", "prop", "lem", "cor"}


def index(build):
    records = {}
    for edition in ("compact", "selected", "long"):
        source = build / edition / "source"
        aux_files = list((build / edition / "build").glob("*.aux"))
        if len(aux_files) != 1:
            raise ValueError("Expected one final AUX per edition")
        labels = re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]+)\}\{([^}]+)\}", aux_files[0].read_text())
        for label, number, page in labels:
            if label.split(":")[0] not in KINDS:
                continue
            matches = [p for p in (source / "sections").glob("*.tex")
                       if r"\label{" + label + "}" in p.read_text()]
            # The assembler retains non-included alternative sections. Prefer
            # the actual entry's directly included files; compact fragments win.
            entry = {"compact": "main_compact.tex", "selected": "main_core.tex", "long": "main.tex"}[edition]
            included = set(re.findall(r"\\input\{(sections/[^}]+)\}", (source / entry).read_text()))
            matches = [p for p in matches if p.relative_to(source).with_suffix("").as_posix() in included]
            if len(matches) != 1:
                raise ValueError(f"Ambiguous included statement: {edition}/{label}")
            file = matches[0]
            row = records.setdefault(label, {"label": label, "editions": {}})
            row["editions"][edition] = {"number": number, "printed_page": page,
                                         "section": file.name}
    if not records:
        raise ValueError("No compiled mathematical statements found")
    return list(records.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = index(args.build.resolve())
    groups = json.loads((PACKAGE / "evidence_groups.json").read_text())
    lines = ["# Current Theorem-to-Evidence Index", "",
             "Evidence cutoff: **2026-09-30T12:54:17Z, through C280**. "
             "Compact / Selected / Full are overlapping reading editions, not independent papers.", "",
             "The numbers below are read from the final compiled AUX files. Labels are stable; "
             "numbers and printed pages are edition-specific. A dash means the statement is not "
             "in that edition. This index does not turn internal review into external peer review.", "",
             "**Critical boundary:** C38 is disproved by FFF12. C157 is the inherited "
             "order-10 computational exclusion, not a freshly replayed full master search. "
             "Unrestricted order 18 remains open.", "",
             "## Reading the Evidence", "",
             "Written proofs are in the linked source section. Computational theorems additionally "
             "depend on finite enumerations or external catalogues. A fresh finite control is "
             "not a new general proof. Historical computational dependencies remain historical "
             "unless the stated complete domain was actually replayed.", "",
             "The [counteraudit assessment](REVIEW_AND_LIMITATIONS.md) records what was and was not "
             "checked. The [historical public claim map](../2026-09-27_research_snapshot/THEOREM_EVIDENCE.md) "
             "and [new finite-premise report](../2026-09-30_research_review/results/portable_audit.json) "
             "retain their original scope.", ""]
    grouped = {}
    for row in records:
        section = row["editions"].get("long", row["editions"].get("selected", row["editions"].get("compact")))["section"]
        if section not in groups:
            raise ValueError("Unmapped mathematical section: " + section)
        grouped.setdefault(section, []).append(row)
    for section, rows in grouped.items():
        group = groups[section]
        lines += ["## " + group["title"], "", group["evidence"], "",
                  "| Stable statement label | Compact: no. / p. | Selected: no. / p. | Full: no. / p. |",
                  "| --- | --- | --- | --- |"]
        for row in rows:
            cells = []
            for edition in ("compact", "selected", "long"):
                value = row["editions"].get(edition)
                cells.append(f'{value["number"]} / {value["printed_page"]}' if value else "-")
            lines.append("| `" + row["label"] + "` | " + " | ".join(cells) + " |")
        lines.append("")
    lines += [(PACKAGE / "UNNUMBERED_EVIDENCE.md").read_text()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n")
    args.output.with_suffix(".json").write_text(json.dumps({"last_in_scope_claim": "C280",
        "compiled_label_count": len(records), "records": records}, indent=2) + "\n")
    print(json.dumps({"compiled_statements": len(records), "mapped_sections": len(grouped)}))


if __name__ == "__main__":
    main()
