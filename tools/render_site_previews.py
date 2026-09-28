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
                "bd8c4c132565a72b3c7f1205b248773090a9417ef9fb474172842c587eea1366"),
    "long": ("FFF_Long_Research_Dossier.pdf",
             "5986a4008e2227f37c2d8b494872fa19f450f7dc74f7ed00ba0543a357bae868"),
}


def main():
    import pypdfium2 as pdfium

    records = []
    for edition, (filename, expected) in SOURCES.items():
        source = ROOT / "papers" / filename
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
        with pdfium.PdfDocument(source) as document:
            for label, index, width in (("cover", 0, 536), ("abstract", 2, 720)):
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
