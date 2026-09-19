#!/usr/bin/env python3
"""Record an independent drat-trim check of a CaDiCaL proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_log(path: Path) -> None:
    text = path.read_text(errors="replace")
    lines = [line.rstrip() for line in text.replace("\r", "\n").splitlines()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--checker-source", type=Path, required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--returncode", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    normalize_log(args.stdout)
    normalize_log(args.stderr)
    commit = subprocess.run(["git", "-C", str(args.checker_source), "rev-parse", "HEAD"], text=True, capture_output=True, check=False).stdout.strip()
    verified = args.returncode == 0 and "s VERIFIED" in args.stdout.read_text(errors="replace").replace("\r", "\n")
    payload = {
        "result": "verified" if verified else "not_verified",
        "checker": {"path": str(args.checker), "binary_sha256": sha(args.checker), "source_commit": commit},
        "cnf": {"path": str(args.cnf), "sha256": sha(args.cnf)},
        "proof": {"path": str(args.proof), "sha256": sha(args.proof), "size_bytes": args.proof.stat().st_size},
        "stdout": {"path": str(args.stdout), "sha256": sha(args.stdout)},
        "stderr": {"path": str(args.stderr), "sha256": sha(args.stderr)},
        "returncode": args.returncode,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Primitive-group F-clique DRAT proof check\n\n"
        f"result: {payload['result']}\nchecker_source_commit: {commit}\n"
        f"cnf_sha256: {payload['cnf']['sha256']}\nproof_sha256: {payload['proof']['sha256']}\n"
    )
    if not verified:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
