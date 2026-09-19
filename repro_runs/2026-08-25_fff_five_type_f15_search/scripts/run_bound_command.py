#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, action="append", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise SystemExit("missing bound command")

    before = {
        "source": artifact(args.source),
        "binary": artifact(args.binary),
        "inputs": [artifact(path) for path in args.input],
    }
    started = dt.datetime.now(dt.timezone.utc)
    process = subprocess.run(command, check=False)
    finished = dt.datetime.now(dt.timezone.utc)
    outputs = [artifact(path) for path in args.output if path.is_file()]
    record = {
        "schema_version": "bound-command-execution-v1",
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_seconds": (finished - started).total_seconds(),
        "command": command,
        "exit_code": process.returncode,
        **before,
        "outputs": outputs,
        "complete": process.returncode == 0 and len(outputs) == len(args.output),
    }
    args.record.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    if not record["complete"]:
        raise SystemExit(f"bound command failed with exit code {process.returncode}")


if __name__ == "__main__":
    main()
