#!/usr/bin/env python3
"""Check PDF-extracted witness cells; optional pypdf, not a visual review."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-10-03_counteraudit_revision"
ORDER12 = ROOT / "manuscript/candidates/2026-09-28_research_review/evidence/data/order12_first.json"
ORDER12_SHA256 = "8b71d6ecaa6ab86a806a0660529b404d8f3667db2b58b82bf5c72fed010fa416"


def check_texts(texts, table, patterns):
    matches = []
    table_pages = []
    pattern_pages = []
    for index, text in enumerate(texts, 1):
        encoded = re.findall(r"([FT]{3})\s*([0-7]{64})(?![0-9])", text)
        if encoded:
            matches.extend(encoded)
            pattern_pages.append(index)
        rows = [list(map(int, line.split())) for line in text.splitlines()
                if re.fullmatch(r"\s*\d+(?:\s+\d+){12}\s*", line)]
        if rows:
            expected = [[i, *row] for i, row in enumerate(table)]
            if rows != expected:
                raise ValueError("Printed order-12 cells/row labels differ")
            table_pages.append(index)
    if len(table_pages) != 1:
        raise ValueError("Expected exactly one complete printed order-12 table")
    if len(matches) != 8 or dict(matches) != patterns:
        raise ValueError("Printed pattern witnesses differ, are missing or duplicated")
    return {"order12_cells_checked": 144, "order12_page": table_pages[0],
            "pattern_witnesses_checked": 8, "pattern_pages": pattern_pages}


def main():
    from pypdf import PdfReader

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / ".audit") or output.exists():
        parser.error("Use a fresh .audit output file")
    if hashlib.sha256(ORDER12.read_bytes()).hexdigest() != ORDER12_SHA256:
        raise ValueError("Frozen order-12 input changed")
    patterns_path = PACKAGE / "evidence/pattern_witnesses.json"
    patterns = json.loads(patterns_path.read_text())
    table = json.loads(ORDER12.read_text())["table"]
    records = []
    for edition in ("Compact", "Selected", "Long"):
        path = ROOT / "papers" / f"FFF_{edition}_Research_Dossier.pdf"
        reader = PdfReader(path)
        records.append({"path": path.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "pages": len(reader.pages),
                        **check_texts([page.extract_text() for page in reader.pages], table, patterns)})
    report = {"passed": True, "records": records,
              "order12_input_sha256": ORDER12_SHA256,
              "pattern_input_sha256": hashlib.sha256(patterns_path.read_bytes()).hexdigest(),
              "scope": "Extracted cell identity only; separate semantic and visual checks required"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "editions": len(records)}))


if __name__ == "__main__":
    main()
