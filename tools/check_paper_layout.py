#!/usr/bin/env python3
"""Optional PDF page-flow check; not a mathematical or PDF/UA certification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def structure_errors(texts, labels, introduction_page, reference_page):
    errors = []
    if len(texts) < 5 or len(labels) != len(texts):
        return ["Missing document pages or page labels"]
    normalized = [" ".join(text.split()) for text in texts]
    if not all(term in normalized[0] for term in
               ("Abstract", "Keywords.", "Mathematics Subject Classification")):
        errors.append("Title/abstract/keywords/MSC do not share the first page")
    if "Contents" in normalized[0] or "1 Introduction" in normalized[0]:
        errors.append("First page contains contents or introduction")
    if not normalized[1].startswith("Status, attribution, and evidence boundary"):
        errors.append("Status declaration does not start on its own page")
    if "Contents" in normalized[1] or "1 Introduction" in normalized[1]:
        errors.append("Status declaration shares a page with contents or introduction")
    if not normalized[2].startswith("Contents"):
        errors.append("Contents do not start on the third page")
    if introduction_page != 3 or not normalized[3].startswith("1 Introduction"):
        errors.append("Introduction is not on its own fourth PDF page")
    if labels[:4] != ["i", "ii", "iii", "1"]:
        errors.append("Front matter / Arabic body page numbering differs")
    if not isinstance(reference_page, int) or reference_page <= 3:
        errors.append("Missing separate references destination")
    elif not normalized[reference_page].startswith("References"):
        errors.append("References do not start on a new page")
    if any(not text.strip() for text in texts):
        errors.append("Blank page")
    if any("??" in text for text in texts):
        errors.append("Possible unresolved reference")
    return errors


def flatten_outline(outline):
    for item in outline:
        if isinstance(item, list):
            yield from flatten_outline(item)
        else:
            yield item


def audit_pdf(path):
    from pypdf import PdfReader
    import pypdfium2 as pdfium

    reader = PdfReader(path)
    texts = [page.extract_text() for page in reader.pages]
    destinations = {
        str(item.title): reader.get_destination_page_number(item)
        for item in flatten_outline(reader.outline)
    }
    introduction = next((page for title, page in destinations.items()
                         if re.fullmatch(r"(?:1\s+)?Introduction", title)), None)
    references = destinations.get("References")
    errors = structure_errors(texts, reader.page_labels, introduction, references)
    clipped = []
    with pdfium.PdfDocument(path) as document:
        for index, page in enumerate(document):
            width, height = page.get_size()
            if abs(width - 595.276) > 1 or abs(height - 841.89) > 1:
                errors.append(f"Non-A4 page: {index + 1}")
            textpage = page.get_textpage()
            try:
                for char_index in range(textpage.count_chars()):
                    char = textpage.get_text_range(char_index, 1)
                    if not char.strip():
                        continue
                    left, bottom, right, top = textpage.get_charbox(char_index)
                    if left < 20 or bottom < 20 or right > width - 20 or top > height - 20:
                        clipped.append({"page": index + 1, "character": char,
                                        "box": [round(v, 3) for v in (left, bottom, right, top)]})
            finally:
                textpage.close()
                page.close()
    if clipped:
        errors.append("Glyphs intrude into the outer 20-point page safety margin")
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pages": len(reader.pages),
        "introduction_pdf_page": None if introduction is None else introduction + 1,
        "introduction_printed_page": None if introduction is None else reader.page_labels[introduction],
        "references_pdf_page": None if references is None else references + 1,
        "front_matter_page_labels": reader.page_labels[:4],
        "contents_is_separate_page": not errors,
        "outline_destinations": destinations,
        "glyph_margin_failures": clipped,
        "errors": errors, "passed": not errors,
        "visual_review_still_required": True,
        "mathematical_verification": False, "pdf_ua_certification": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / ".audit"):
        parser.error("Use .audit output")
    out.parent.mkdir(parents=True, exist_ok=True)
    result = audit_pdf(args.pdf)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
