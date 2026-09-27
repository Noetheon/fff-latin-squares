#!/usr/bin/env python3
"""Refresh the derived public byte manifest after reviewing a publication diff."""
from pathlib import Path
from verify_public_release import BANNED_SUFFIXES, files, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    payload = list(files(ROOT))
    for path in payload:
        if path.suffix in BANNED_SUFFIXES or path.name == ".DS_Store":
            raise ValueError(f"Forbidden payload: {path.relative_to(ROOT)}")
    (ROOT / "PUBLIC_MANIFEST.sha256").write_text("".join(
        f"{sha(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in payload))
    print(f"Sealed {len(payload)} public files; run verification and review before committing.")


if __name__ == "__main__":
    main()
