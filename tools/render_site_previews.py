#!/usr/bin/env python3
"""Render complete PDF pages for the website; optional pypdfium2 dependency.

This does not edit the PDFs. The default public verification gate is still
standard-library-only and does not invoke this rendering tool.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "compact": ("FFF_Compact_Research_Dossier.pdf",
                "f51d47b9adb9546307a7ef4ae678956208c42acba376eaf0ff605b0600a53dd9"),
    "selected": ("FFF_Selected_Research_Dossier.pdf",
                 "78e438894d072bdbf2b7dd25376f237c2e6620e650ac59229cb9d6ed41b0bab1"),
    "long": ("FFF_Long_Research_Dossier.pdf",
             "74e499f82ab636bee6a55159ba3c6fe5e6b3bb71683e17bcec148c9370c91209"),
}


def main():
    import pypdfium2 as pdfium

    records = []
    for edition, (filename, expected) in SOURCES.items():
        source = ROOT / "papers" / filename
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Unexpected source PDF hash: {filename}")
        with pdfium.PdfDocument(source) as document:
            # Preserve the legacy asset name; the second image shows Introduction.
            for label, index, width in (("cover", 0, 536), ("abstract", 3, 720)):
                page = document[index]
                try:
                    bitmap = page.render(scale=width / page.get_width())
                    destination = ROOT / "assets" / f"{edition}-{label}.png"
                    bitmap.to_pil().save(destination, optimize=True)
                    records.append({"asset": destination.relative_to(ROOT).as_posix(),
                                    "source": source.relative_to(ROOT).as_posix(),
                                    "source_sha256": expected, "page": index + 1,
                                    "width": bitmap.width, "height": bitmap.height,
                                    "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
                    bitmap.close()
                finally:
                    page.close()
    (ROOT / "verification/site-preview-sources.json").write_text(
        json.dumps({"pdfium_version": pdfium.PDFIUM_INFO.version,
                    "pypdfium2_version": pdfium.PYPDFIUM_INFO.version,
                    "full_pages_no_crop": True, "records": records}, indent=2) + "\n")


if __name__ == "__main__":
    main()
