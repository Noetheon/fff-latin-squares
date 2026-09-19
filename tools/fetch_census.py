#!/usr/bin/env python3
"""Fetch the cited order-8 input and require its exact frozen SHA-256."""
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://users.cecs.anu.edu.au/~bdm/data/latin_mc8.txt.gz"
EXPECTED = "e5980ff5bc4ac46cbbefd1f1333258d0905724c42a976c4afe61ea501a4ccf87"
SIZE = 5140393
TARGET = ROOT / "repro_runs/2026-04-26_order8_core/data/latin_mc8.txt.gz"


def main():
    if TARGET.is_symlink():
        raise ValueError("Refusing symlink target")
    if TARGET.exists():
        data = TARGET.read_bytes()
        if len(data) != SIZE or hashlib.sha256(data).hexdigest() != EXPECTED:
            raise ValueError("Existing input differs; refusing replacement")
        print("Existing census matches the frozen size and SHA-256.")
        return
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read(SIZE + 1)
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError("Downloaded census does not match the frozen input")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=TARGET.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        os.link(temporary, TARGET)
    finally:
        temporary.unlink(missing_ok=True)
    print("Fetched census: exact frozen size and SHA-256 verified. See provider terms.")


if __name__ == "__main__":
    main()
