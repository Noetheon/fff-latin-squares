#!/usr/bin/env python3
"""Optional layout/metadata checks for the three locally built reading editions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-09-30_three_editions"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata_errors(reader):
    errors, fonts = [], {}
    catalog = reader.trailer["/Root"]
    if reader.metadata.author:
        errors.append("Unexpected author metadata")
    if reader.attachments:
        errors.append("Unexpected attachments")
    for key in ("/AA", "/AcroForm"):
        if key in catalog:
            errors.append(key)
    if "/OpenAction" in catalog:
        action = catalog["/OpenAction"]
        dest = action.get("/D")
        if not (set(action) == {"/S", "/D"} and action["/S"] == "/GoTo"
                and isinstance(dest, list) and len(dest) == 2 and dest[1] == "/Fit"
                and dest[0] == reader.pages[0].indirect_reference):
            errors.append("Unexpected opening action")
    names = catalog.get("/Names", {})
    names = names.get_object() if hasattr(names, "get_object") else names
    if "/JavaScript" in names or "/EmbeddedFiles" in names:
        errors.append("Active or attached content")
    for page in reader.pages:
        if "/AA" in page:
            errors.append("Page action")
        for annotation in page.get("/Annots", []):
            item = annotation.get_object()
            action = item.get("/A", {})
            action = action.get_object() if hasattr(action, "get_object") else action
            if action.get("/S") in {"/JavaScript", "/Launch"} or "/AA" in item:
                errors.append("Active annotation")
        resources = page.get("/Resources", {}).get_object()
        for value in resources.get("/Font", {}).get_object().values():
            font = value.get_object()
            descriptor = font.get("/FontDescriptor", {})
            descriptor = descriptor.get_object() if hasattr(descriptor, "get_object") else descriptor
            fonts[str(font.get("/BaseFont"))] = any(
                key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    if not fonts or not all(fonts.values()):
        errors.append("Unembedded font")
    return errors, fonts


def main():
    from pypdf import PdfReader
    import pypdfium2 as pdfium

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    build = args.build.resolve()
    if not build.is_relative_to(ROOT / ".audit"):
        parser.error("Use a built .audit directory")
    summary = json.loads((build / "edition_build.json").read_text())
    if not summary["passed"]:
        raise ValueError("Edition build has not passed")
    layout = load("paper_layout", ROOT / "tools/check_paper_layout.py")
    examples = load("edition_examples", PACKAGE / "scripts/check_compact_examples.py")
    example_report = examples.check(build / "compact/source")
    (build / "compact_examples.json").write_text(json.dumps(example_report, indent=2) + "\n")
    records = []
    for variant in summary["variants"]:
        path = build / variant["pdf"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != variant["sha256"]:
            raise ValueError("Built PDF changed")
        report = layout.audit_pdf(path)
        reader = PdfReader(path)
        errors, fonts = metadata_errors(reader)
        report.update({"id": variant["id"], "metadata_errors": errors,
                       "embedded_fonts": fonts, "passed": report["passed"] and not errors})
        records.append(report)
        if args.render:
            # Inspect all new compact pages; changed selected pages and a long sample.
            selected = {0, 1, 2, 3, 4, 39, 40, 41, 42, 43}
            pages = (range(len(reader.pages)) if variant["id"] == "compact" else
                     sorted(selected) if variant["id"] == "selected" else [0, 1, 2, 3, 14, 61, 87, 88])
            out = build / "rendered" / variant["id"]
            out.mkdir(parents=True, exist_ok=True)
            with pdfium.PdfDocument(path) as document:
                for index in pages:
                    page = document[index]
                    bitmap = page.render(scale=1.65)
                    bitmap.to_pil().save(out / f"page-{index + 1:02}.png")
                    bitmap.close()
                    page.close()
    result = {"passed": all(r["passed"] for r in records) and example_report["passed"], "records": records,
              "finite_examples_passed": example_report["passed"],
              "visual_review_still_required": True,
              "not_external_peer_review": True}
    (build / "edition_checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "editions": len(records),
                      "finite_examples_passed": result["finite_examples_passed"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
