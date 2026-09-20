#!/usr/bin/env python3
"""Verify the exact public payload. This is not a mathematical proof checker."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".audit", "__pycache__"}
CENSUS = "repro_runs/2026-04-26_order8_core/data/latin_mc8.txt.gz"
BANNED_SUFFIXES = {".zip", ".gz", ".bin", ".exe", ".dylib", ".so", ".pyc", ".pyo", ".log"}
SECRET = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_" r"pat_|-----BEGIN [A-Z ]*PRIVATE KEY")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if set(rel.parts) & IGNORED or rel.as_posix() in {CENSUS, "PUBLIC_MANIFEST.sha256"}:
            continue
        if path.is_symlink():
            raise ValueError(f"Unexpected symlink: {rel}")
        if path.is_file():
            yield path


def parse_manifest(text: str):
    result = {}
    for line in text.splitlines():
        digest, separator, name = line.partition("  ")
        path = PurePosixPath(name)
        if (not separator or not re.fullmatch(r"[a-f0-9]{64}", digest)
                or not name or path.is_absolute() or ".." in path.parts
                or path.as_posix() != name or name in result):
            raise ValueError("Malformed, duplicate or unsafe manifest entry")
        result[name] = digest
    return result


def verify(root: Path, pdf_text: bool = False):
    expected = parse_manifest((root / "PUBLIC_MANIFEST.sha256").read_text())
    actual, failures = {}, []
    for path in files(root):
        name = path.relative_to(root).as_posix()
        actual[name] = sha(path)
        if path.suffix in BANNED_SUFFIXES or path.name == ".DS_Store":
            failures.append(f"Unexpected artifact: {name}")
        if path.suffix not in {".pdf", ".png"}:
            text = path.read_text(encoding="utf-8")
            if SECRET.search(text):
                failures.append(f"Secret marker: {name}")
        elif pdf_text and path.suffix == ".pdf":
            info = subprocess.check_output(["pdfinfo", str(path)], text=True)
            if re.search(r"^Author:[^\S\r\n]*[^\s]", info, re.M):
                failures.append(f"Unexpected PDF author: {name}")
            if "JavaScript:      yes" in info:
                failures.append(f"Unexpected PDF JavaScript: {name}")
            embedded = subprocess.check_output(["pdfdetach", "-list", str(path)], text=True)
            if not embedded.startswith("0 embedded files"):
                failures.append(f"Unexpected PDF attachment: {name}")
    failures += [f"Missing: {name}" for name in expected.keys() - actual.keys()]
    failures += [f"Unexpected: {name}" for name in actual.keys() - expected.keys()]
    failures += [f"Hash mismatch: {name}" for name in actual.keys() & expected.keys()
                 if actual[name] != expected[name]]
    return {"passed": not failures, "public_files_checked": len(actual),
            "pdf_metadata_checked": pdf_text, "failures": sorted(failures),
            "mathematical_proof_check": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-metadata", action="store_true", help="Requires Poppler tools")
    args = parser.parse_args()
    result = verify(ROOT, args.pdf_metadata)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
