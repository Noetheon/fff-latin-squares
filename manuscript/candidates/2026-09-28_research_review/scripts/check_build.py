#!/usr/bin/env python3
"""Check final TeX logs, PDF bytes, and optional repeat-build equality."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def check(directory, other=None):
    records = []
    for kind in ("Long", "Compact"):
        stem = f"FFF_Latin_Squares_{kind}_2026-09-28_Research_Review"
        pdf = directory / (stem + ".pdf")
        log = (directory / f"build-{kind}" / (stem + ".log")).read_text()
        failures = re.findall(
            r"(?im)^(?:LaTeX Warning:|Package .+ Warning:|Class .+ Warning:|"
            r"Overfull|Underfull|!|.*Undefined control sequence).*$", log)
        if failures:
            raise ValueError(f"TeX diagnostics in {kind}: {failures}")
        bibliography = (directory / f"build-{kind}" / (stem + ".bbl")).read_text()
        identifiers = ["2405.07750"] + (["2212.12823v1"] if kind == "Long" else [])
        for identifier in identifiers:
            if "Preprint, \\url{https://arxiv.org/abs/" + identifier + "}" not in bibliography:
                raise ValueError(f"Missing rendered preprint identifier: {identifier}")
        content = pdf.read_bytes()
        if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-1024:]:
            raise ValueError(f"Invalid PDF envelope: {pdf}")
        same = None if other is None else content == (other / pdf.name).read_bytes()
        if same is False:
            raise ValueError(f"Non-deterministic PDF: {pdf.name}")
        records.append({"name": pdf.name, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "final_tex_warnings": failures, "repeat_build_byte_identical": same})
    semantic = None
    if other is not None:
        first = json.loads((directory / "snapshot_audit.json").read_text())
        second = json.loads((other / "snapshot_audit.json").read_text())
        first.pop("elapsed_seconds")
        second.pop("elapsed_seconds")
        semantic = first == second
        if not semantic:
            raise ValueError("Repeat finite audit differs beyond elapsed_seconds")
        updates = [json.loads((path / "update_audit.json").read_text())
                   for path in (directory, other)]
        for item in updates:
            item.pop("elapsed_seconds")
        if updates[0] != updates[1]:
            raise ValueError("Repeat update audit differs beyond elapsed_seconds")
        crt = [json.loads((path / "crt_update_audit.json").read_text())
               for path in (directory, other)]
        for item in crt:
            item.pop("runtime_seconds")
        if crt[0] != crt[1]:
            raise ValueError("Repeat CRT audit differs beyond runtime_seconds")
    result = {"passed": True, "pdfs": records,
              "finite_repeat_semantic_match": semantic,
              "finite_comparison_ignored_fields": {
                  "snapshot_audit.json": ["elapsed_seconds"],
                  "update_audit.json": ["elapsed_seconds"],
                  "crt_update_audit.json": ["runtime_seconds"]},
              "scope": "Build diagnostics and byte reproducibility; visual and mathematical review separate."}
    (directory / "pdf_build_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.output_directory, args.compare), indent=2))
