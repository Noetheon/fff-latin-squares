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
                "e3828b93f302f9f2bfe8ec10e988a9d3e3f34ab8e102855e1789c76bb8bc8a96"),
    "selected": ("FFF_Selected_Research_Dossier.pdf",
                 "874076ee6a2e48a1bbafd922703bb7b502c1291a647a8a11ccd4e5f6d0f9dc3e"),
    "long": ("FFF_Long_Research_Dossier.pdf",
             "48b96fd2f745cd1865fd97e0462599c34c1a1671d86d5c9d3ef2a58c74b1e428"),
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
