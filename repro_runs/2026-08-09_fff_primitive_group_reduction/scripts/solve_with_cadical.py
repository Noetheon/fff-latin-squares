#!/usr/bin/env python3
"""Run CaDiCaL reproducibly and capture SAT/UNSAT/proof metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_log(text: str) -> str:
    """Normalize progress carriage returns and trailing solver whitespace."""
    lines = [line.rstrip() for line in text.replace("\r", "\n").splitlines()]
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--solver", type=Path, default=Path("/opt/homebrew/bin/cadical"))
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    version = subprocess.run([str(args.solver), "--version"], text=True, capture_output=True, check=False).stdout.strip().splitlines()[0]
    command = [str(args.solver), str(args.cnf)]
    if args.proof:
        args.proof.parent.mkdir(parents=True, exist_ok=True)
        command.append(str(args.proof))
    started = time.time()
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=args.timeout, check=False)
        stdout, stderr = proc.stdout, proc.stderr
        timed_out = False
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True
        returncode = None
    stdout = normalized_log(stdout)
    stderr = normalized_log(stderr)
    elapsed = time.time() - started
    upper = (stdout + stderr).upper()
    result = "timeout" if timed_out else "unsat" if "UNSATISFIABLE" in upper else "sat" if "SATISFIABLE" in upper else "unknown"
    model_lines = [line for line in stdout.splitlines() if line.startswith("v")]
    args.stdout.parent.mkdir(parents=True, exist_ok=True)
    args.stdout.write_text(stdout)
    args.stderr.write_text(stderr)
    args.model.write_text("\n".join(model_lines) + ("\n" if model_lines else ""))
    proof_complete = bool(result == "unsat" and args.proof and args.proof.exists() and args.proof.stat().st_size)
    payload = {
        "cnf": {"path": str(args.cnf), "sha256": sha(args.cnf), "size_bytes": args.cnf.stat().st_size},
        "solver": {"path": str(args.solver), "version": version, "command": command},
        "timeout_seconds": args.timeout,
        "elapsed_seconds": elapsed,
        "result": result,
        "returncode": returncode,
        "proof": {
            "path": str(args.proof) if args.proof else None,
            "complete_unsat_trace": proof_complete,
            "sha256": sha(args.proof) if proof_complete else None,
            "size_bytes": args.proof.stat().st_size if args.proof and args.proof.exists() else None,
            "independently_checked": False,
        },
        "model": {"path": str(args.model), "sha256": sha(args.model), "available": bool(model_lines)},
        "stdout": {"path": str(args.stdout), "sha256": sha(args.stdout)},
        "stderr": {"path": str(args.stderr), "sha256": sha(args.stderr)},
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "Primitive-group F-clique SAT solve\n\n"
        f"result: {result}\nelapsed_seconds: {elapsed:.6f}\ntimeout_seconds: {args.timeout}\n"
        f"solver: {version}\ncnf_sha256: {payload['cnf']['sha256']}\n"
        f"proof_complete_unsat_trace: {proof_complete}\nmodel_available: {bool(model_lines)}\n"
    )


if __name__ == "__main__":
    main()
