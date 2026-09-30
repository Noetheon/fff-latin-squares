#!/usr/bin/env python3
"""Optional PDF safety/font check with pypdf; not a mathematical validator."""
import argparse
import hashlib
import json
from pathlib import Path


def local_first_page_fit(action, first_page_ref):
    if hasattr(action, "get_object"):
        action = action.get_object()
    if not isinstance(action, dict) or set(action) != {"/S", "/D"}:
        return False
    dest = action["/D"]
    return (action["/S"] == "/GoTo" and isinstance(dest, list)
            and len(dest) == 2 and dest[1] == "/Fit"
            and getattr(dest[0], "idnum", None) == first_page_ref.idnum
            and getattr(dest[0], "generation", None) == first_page_ref.generation)


def main():
    from pypdf import PdfReader
    import pypdf
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(root / ".audit") or out.exists():
        ap.error("Use a new .audit output")
    records = []
    for variant in ("Compact", "Selected", "Long"):
        path = root / "papers" / f"FFF_{variant}_Research_Dossier.pdf"
        reader = PdfReader(path)
        catalog = reader.trailer["/Root"]
        names = catalog.get("/Names", {})
        names = names.get_object() if hasattr(names, "get_object") else names
        forbidden = [key for key in ("/AA", "/AcroForm") if key in catalog]
        open_action_safe = ("/OpenAction" not in catalog or local_first_page_fit(
            catalog["/OpenAction"], reader.pages[0].indirect_reference))
        if not open_action_safe:
            forbidden.append("nonlocal or active /OpenAction")
        forbidden += [key for key in ("/JavaScript", "/EmbeddedFiles") if key in names]
        fonts = {}
        for page in reader.pages:
            if "/AA" in page:
                forbidden.append("page /AA")
            for annotation in page.get("/Annots", []):
                item = annotation.get_object()
                action = item.get("/A", {})
                if hasattr(action, "get_object"):
                    action = action.get_object()
                if action.get("/S") in ("/JavaScript", "/Launch") or "/AA" in item:
                    forbidden.append("active annotation")
            resources = page.get("/Resources", {}).get_object()
            for value in resources.get("/Font", {}).get_object().values():
                font = value.get_object()
                descriptor = font.get("/FontDescriptor", {})
                if hasattr(descriptor, "get_object"):
                    descriptor = descriptor.get_object()
                fonts[str(font.get("/BaseFont"))] = any(
                    key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
        record = {"path": path.relative_to(root).as_posix(), "pages": len(reader.pages),
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "author_empty": not reader.metadata.author,
                  "open_action_absent_or_local_first_page_fit": open_action_safe,
                  "attachments": len(reader.attachments), "forbidden_active_entries": forbidden,
                  "embedded_fonts": fonts}
        record["passed"] = (record["author_empty"] and not record["attachments"]
                            and not forbidden and bool(fonts) and all(fonts.values()))
        records.append(record)
    report = {"passed": all(row["passed"] for row in records), "pypdf": pypdf.__version__,
              "scope": "Current generated PDFs; metadata, attachments, active entries, embedding",
              "records": records}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "pdfs_checked": len(records)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
