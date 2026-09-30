#!/usr/bin/env python3
"""Record local edition checks and seal this new candidate, never an old one."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", type=Path, required=True)
    ap.add_argument("--repeat-build", type=Path, required=True)
    args = ap.parse_args()
    build, repeat = args.build.resolve(), args.repeat_build.resolve()
    if not all(path.is_relative_to(ROOT / ".audit") for path in (build, repeat)):
        ap.error("Use .audit build paths")
    records = {}
    for name in ("edition_build", "edition_checks", "compact_examples"):
        records[name] = json.loads((build / f"{name}.json").read_text())
        if not records[name]["passed"]:
            raise ValueError(f"Failed {name}")
    repeated = json.loads((repeat / "edition_build.json").read_text())
    if not repeated["passed"]:
        raise ValueError("Second build failed")
    hashes = lambda d: {v["id"]: v["sha256"] for v in d["variants"]}
    if hashes(records["edition_build"]) != hashes(repeated):
        raise ValueError("PDF rebuilds differ")
    repository = json.loads((ROOT / ".audit/latest.json").read_text())
    if not repository["passed"]:
        raise ValueError("Repository audit has not passed")
    out = PACKAGE / "results"
    out.mkdir(exist_ok=False)
    for name in records:
        shutil.copyfile(build / f"{name}.json", out / f"{name}.json")
    # Retain a portable summary, not machine-specific argv or personal paths.
    portable = {
        "source_report_sha256": digest(ROOT / ".audit/latest.json"),
        "passed": repository["passed"], "timestamp_utc": repository["timestamp_utc"],
        "publication_ready": repository["publication_ready"],
        "paper_currency_status": repository["paper_currency"]["status"],
        "checks": [{k: c[k] for k in ("name", "passed", "exit_code", "elapsed_seconds") if k in c}
                   for c in repository["checks"]],
        "fresh_build_pdf_hashes_agree": True, "pdf_sha256": hashes(repeated),
    }
    (out / "repository_and_rebuild_summary.json").write_text(json.dumps(portable, indent=2) + "\n")
    inputs = {}
    for candidate in ("2026-09-30_research_review", "2026-09-30_typography_review"):
        for path in (PACKAGE.parent / candidate).rglob("*"):
            if path.suffix in {".tex", ".bib"} or path.relative_to(PACKAGE.parent / candidate).as_posix() == "scripts/build_pdfs.py":
                inputs[path.relative_to(ROOT).as_posix()] = digest(path)
    for path, sha in records["compact_examples"]["inputs_sha256"].items():
        if not path.startswith(".audit/"):
            inputs[path] = sha
    (PACKAGE / "INPUTS.sha256").write_text("".join(
        f"{sha}  {path}\n" for path, sha in sorted(inputs.items())))
    (PACKAGE / "OUTPUTS.sha256").write_text("".join(
        f"{variant['sha256']}  {Path(variant['pdf']).name}\n"
        for variant in records["edition_build"]["variants"]))
    files = [p for p in sorted(PACKAGE.rglob("*")) if p.is_file() and p.name != "MANIFEST.sha256"]
    (PACKAGE / "MANIFEST.sha256").write_text("".join(
        f"{digest(path)}  {path.relative_to(PACKAGE).as_posix()}\n" for path in files))
    print(f"Recorded {len(files)} new-package files and {len(inputs)} immutable input hashes; PDFs identical on rebuild.")


if __name__ == "__main__":
    main()
