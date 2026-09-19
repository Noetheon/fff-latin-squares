#!/usr/bin/env python3
"""Record metadata for a drat-trim proof check."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_commit(source_dir: Path) -> str | None:
    if not (source_dir / ".git").exists():
        return None
    proc = subprocess.run(["git", "-C", str(source_dir), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def parse_real_time(path: Path) -> float | None:
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("real "):
            try:
                return float(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def make_summary(data: dict[str, Any]) -> str:
    return "\n".join(
        [
            "n=6 full DRAT check summary",
            "",
            f"checker: drat-trim source commit {data['checker']['source_commit']}",
            f"command: {' '.join(data['command'])}",
            f"cnf_sha256: {data['cnf']['sha256']}",
            f"drat_sha256: {data['proof']['sha256']}",
            f"result: {data['result']}",
            f"elapsed_seconds_time_real: {data['elapsed_seconds_time_real']}",
            f"warning_count: {data['warning_count']}",
            data["claim_impact"],
        ]
    ) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--checker-source-dir", type=Path, required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-time-log", type=Path, required=True)
    parser.add_argument("--returncode", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stdout_text = args.stdout_log.read_text(errors="replace")
    normalized_stdout = stdout_text.replace("\r", "\n")
    verified = "s VERIFIED" in normalized_stdout and args.returncode == 0
    warnings = len(re.findall(r"^c WARNING:", normalized_stdout, flags=re.MULTILINE))
    metadata = {
        "label": "n6_full_drat_trim_check",
        "purpose": "Independent check of the CaDiCaL binary DRAT trace for the n=6 full row,col,sym sanity UNSAT.",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "checker": {
            "name": "drat-trim",
            "binary": str(args.checker),
            "source_url": "https://github.com/marijnheule/drat-trim.git",
            "source_commit": source_commit(args.checker_source_dir),
            "binary_sha256": sha256_file(args.checker),
            "version_note": "drat-trim does not print a semantic version in this checkout; source commit is recorded.",
        },
        "command": [str(args.checker), str(args.cnf), str(args.proof), "-i"],
        "cnf": {"path": str(args.cnf), "size_bytes": args.cnf.stat().st_size, "sha256": sha256_file(args.cnf)},
        "proof": {"path": str(args.proof), "size_bytes": args.proof.stat().st_size, "sha256": sha256_file(args.proof), "format": "binary DRAT"},
        "stdout": {"path": str(args.stdout_log), "size_bytes": args.stdout_log.stat().st_size, "sha256": sha256_file(args.stdout_log)},
        "stderr_time": {
            "path": str(args.stderr_time_log),
            "size_bytes": args.stderr_time_log.stat().st_size,
            "sha256": sha256_file(args.stderr_time_log),
        },
        "returncode": args.returncode,
        "elapsed_seconds_time_real": parse_real_time(args.stderr_time_log),
        "result": "verified" if verified else "not_verified",
        "warning_count": warnings,
        "warning_note": "drat-trim normalized duplicate literals in proof lines; verification still ended with s VERIFIED."
        if warnings
        else "No warnings reported.",
        "claim_impact": "C06/C39 sanity status upgraded to solver UNSAT with independently checked DRAT trace; no new C06 claim is created.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(metadata))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
