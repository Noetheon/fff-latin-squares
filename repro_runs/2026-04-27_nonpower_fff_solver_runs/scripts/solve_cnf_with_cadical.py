#!/usr/bin/env python3
"""Run CaDiCaL on a CNF and capture solver output/proof metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def solver_version(binary: str) -> str:
    proc = subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=10, check=False)
    return (proc.stdout or proc.stderr).strip().splitlines()[0]


def parse_status(text: str) -> str:
    upper = text.upper()
    if "UNSATISFIABLE" in upper:
        return "unsat"
    if "SATISFIABLE" in upper:
        return "sat"
    if "UNKNOWN" in upper:
        return "unknown"
    return "unknown"


def extract_model(stdout: str) -> str:
    lines = []
    for raw in stdout.splitlines():
        stripped = raw.strip()
        if stripped.startswith("v ") or stripped == "v":
            lines.append(stripped)
    return "\n".join(lines) + ("\n" if lines else "")


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "CaDiCaL solve summary",
        "",
        f"label: {result['label']}",
        f"cnf: {result['cnf']['path']}",
        f"cnf_sha256: {result['cnf']['sha256']}",
        f"solver: {result['solver']['binary']}",
        f"solver_version: {result['solver']['version']}",
        f"command: {' '.join(result['solver']['command'])}",
        f"timeout_seconds: {result['timeout_seconds']}",
        f"result: {result['result']}",
        f"elapsed_seconds: {result['elapsed_seconds']:.6f}",
        f"proof_log_available: {result['proof']['available']}",
        f"proof_log_sha256: {result['proof']['sha256']}",
        f"model_available: {result['model']['available']}",
        f"model_sha256: {result['model']['sha256']}",
        f"stdout_sha256: {result['stdout']['sha256']}",
        f"stderr_sha256: {result['stderr']['sha256']}",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--solver", default="cadical")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--stdout-output", type=Path, required=True)
    parser.add_argument("--stderr-output", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--ascii-proof", action="store_true")
    parser.add_argument("--lrat", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    binary = shutil.which(args.solver) if "/" not in args.solver else args.solver
    if binary is None:
        raise FileNotFoundError(f"solver not found: {args.solver}")
    command = [binary]
    if args.ascii_proof:
        command.append("--no-binary")
    if args.lrat:
        command.append("--lrat")
    command.append(str(args.cnf))
    if args.proof is not None:
        args.proof.parent.mkdir(parents=True, exist_ok=True)
        command.append(str(args.proof))

    args.stdout_output.parent.mkdir(parents=True, exist_ok=True)
    args.stderr_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=args.timeout, check=False)
        elapsed = time.time() - start
        stdout = proc.stdout
        stderr = proc.stderr
        result = parse_status(stdout + "\n" + stderr)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - start
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        result = "timeout"
        timed_out = True
        proc = None  # type: ignore[assignment]

    model_text = extract_model(stdout) if result == "sat" else ""
    args.stdout_output.write_text(stdout)
    args.stderr_output.write_text(stderr)
    args.model_output.write_text(model_text)

    proof_available = bool(args.proof and args.proof.exists() and args.proof.stat().st_size > 0 and result == "unsat")
    metadata: dict[str, Any] = {
        "label": args.label,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "cnf": {
            "path": str(args.cnf),
            "size_bytes": args.cnf.stat().st_size,
            "sha256": sha256_file(args.cnf),
        },
        "solver": {
            "binary": binary,
            "version": solver_version(binary),
            "command": command,
            "returncode": None if timed_out else proc.returncode,
        },
        "timeout_seconds": args.timeout,
        "timed_out": timed_out,
        "result": result,
        "elapsed_seconds": elapsed,
        "proof": {
            "requested": args.proof is not None,
            "available": proof_available,
            "path": str(args.proof) if args.proof else None,
            "size_bytes": args.proof.stat().st_size if args.proof and args.proof.exists() else None,
            "sha256": sha256_file(args.proof) if args.proof and args.proof.exists() else None,
            "format_note": "CaDiCaL proof trace; binary DRAT by default unless options changed.",
            "formal_certificate_status": "proof_log_present_not_independently_checked" if proof_available else "no_formal_proof_certificate",
        },
        "stdout": {
            "path": str(args.stdout_output),
            "size_bytes": args.stdout_output.stat().st_size,
            "sha256": sha256_file(args.stdout_output),
        },
        "stderr": {
            "path": str(args.stderr_output),
            "size_bytes": args.stderr_output.stat().st_size,
            "sha256": sha256_file(args.stderr_output),
        },
        "model": {
            "available": bool(model_text),
            "path": str(args.model_output),
            "size_bytes": args.model_output.stat().st_size,
            "sha256": sha256_file(args.model_output),
        },
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(metadata))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
