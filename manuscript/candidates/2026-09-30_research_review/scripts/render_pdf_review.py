#!/usr/bin/env python3
"""Optional all-page layout renders; requires pypdfium2 and Pillow."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw, ImageStat
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[4]
    out = args.output.resolve()
    if not out.is_relative_to(root / ".audit"):
        ap.error("Use fresh .audit output")
    out.mkdir(parents=True, exist_ok=False)
    records, sheets = [], []
    with pdfium.PdfDocument(args.pdf) as document:
        sheet = None
        for index, page in enumerate(document):
            bitmap = page.render(scale=1.4)
            picture = bitmap.to_pil().convert("RGB")
            picture.save(out / f"page-{index + 1:03d}.png")
            spread = sum(ImageStat.Stat(picture.convert("L")).stddev)
            if spread < 1:
                raise ValueError(f"Blank page {index + 1}")
            if index % 20 == 0:
                sheet = Image.new("RGB", (920, 1660), "#d7d7d7")
            thumb = picture.copy()
            thumb.thumbnail((220, 305))
            x, y = (index % 4) * 230 + 5, ((index % 20) // 4) * 332 + 22
            sheet.paste(thumb, (x, y))
            ImageDraw.Draw(sheet).text((x, y - 17), f"Page {index + 1}", fill="black")
            records.append({"page": index + 1, "width": picture.width,
                            "height": picture.height, "nonblank_stddev": round(spread, 4)})
            if index % 20 == 19 or index == len(document) - 1:
                filename = f"contact-{index // 20 + 1:02d}.png"
                sheet.save(out / filename)
                sheets.append(filename)
            bitmap.close()
            page.close()
    report = {"source_sha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
              "pages": records, "contact_sheets": sheets,
              "all_pages_rendered": True,
              "automated_render_is_not_human_review": True}
    (out / "render_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pages_rendered": len(records), "contact_sheets": sheets}))


if __name__ == "__main__":
    main()
