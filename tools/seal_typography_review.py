#!/usr/bin/env python3
"""Record one new typography receipt; never rewrite a previous release receipt."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-09-30_typography_review"
RECEIPT = ROOT / "PUBLIC_SNAPSHOT_2026-09-30_TYPOGRAPHY.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if RECEIPT.exists():
        raise FileExistsError("Receipt already frozen; create a dated successor")
    paths = sorted(p for p in PACKAGE.rglob("*")
                   if p.is_file() and p.name != "MANIFEST.sha256")
    if not paths or any(p.is_symlink() or "__pycache__" in p.parts for p in paths):
        raise ValueError("Unsafe or missing typography sources")
    (PACKAGE / "MANIFEST.sha256").write_text("".join(
        f"{sha(p)}  {p.relative_to(PACKAGE).as_posix()}\n" for p in paths))
    previous = ROOT / "PUBLIC_SNAPSHOT_2026-09-30.json"
    prior = json.loads(previous.read_text())
    payloads = sorted(p for p in PACKAGE.rglob("*") if p.is_file())
    payloads += [ROOT / p for p in ("tools/check_paper_layout.py", "tests/test_paper_layout.py")]
    record = {
        "edition": "2026-09-30 typography correction",
        "public_base_commit": "76d33e078f49c12153954b7c7831ac82e4e64346",
        "previous_receipt_sha256": sha(previous),
        "evidence_cutoff_utc": prior["evidence_cutoff_utc"],
        "last_in_scope_claim": "C280",
        "mathematical_claims_changed": False,
        "historical_receipts_modified": False,
        "private_history_imported": False,
        "superseded_aliases": [
            {"path": row["path"], "previous_sha256": row["public_sha256"],
             "public_sha256": sha(ROOT / row["path"])}
            for row in prior["superseded_aliases"]],
        "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                   "sha256": sha(p)} for p in payloads],
    }
    RECEIPT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("New typography receipt recorded; scientific predecessors preserved")


if __name__ == "__main__":
    main()
