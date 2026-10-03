#!/usr/bin/env python3
"""Replay the pinned independent E9 finite controls without mutating sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-10-02_e9_symmetry_review"
SCRIPT_SHA = "7cf0f0939b8b6944f60d7a6f7b9940dbc944b8d342ac58f1b9d67dd7bce52495"
RESULT_SHA = "51b3a9e76f43a59a786f9aea94abda8156de2413fdd27163e52fcc066e11dcd7"
RUNTIME_KEYS = {"python", "elapsed_seconds_before_serialization"}


def scientific(record):
    result = dict(record)
    result["runtime"] = {k: v for k, v in record["runtime"].items() if k not in RUNTIME_KEYS}
    return result


def check(output):
    source = PACKAGE / "scripts/enumerate_s6.py"
    reference = PACKAGE / "results/enumeration_results.json"
    for path, digest in ((source, SCRIPT_SHA), (reference, RESULT_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen control source/result drift: " + path.name)
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / ".audit"):
        raise ValueError("Use a fresh directory under .audit")
    output.mkdir(parents=True, exist_ok=False)
    copied = output / source.name
    shutil.copyfile(source, copied)
    command = [sys.executable, "-I", "-B", str(copied)]
    result = subprocess.run(command, capture_output=True, timeout=10)
    (output / "stdout.txt").write_bytes(result.stdout)
    (output / "stderr.txt").write_bytes(result.stderr)
    actual = json.loads((output / "enumeration_results.json").read_text()) if result.returncode == 0 else None
    expected = json.loads(reference.read_text())
    passed = result.returncode == 0 and actual["status"] == "PASS" and scientific(actual) == scientific(expected)
    receipt = {"passed": passed, "exit_code": result.returncode,
               "source_sha256": SCRIPT_SHA, "reference_sha256": RESULT_SHA,
               "actual_sha256": hashlib.sha256((output / "enumeration_results.json").read_bytes()).hexdigest()
                    if actual is not None else None,
               "ignored_fields": ["runtime." + key for key in sorted(RUNTIME_KEYS)],
               "command_template": "python3 -I -B COPIED_SCRIPT", "timeout_seconds": 10,
               "scope": "Finite controls for the combinatorial and group-theoretic theorem only; no Latin18 enumeration, solver or external peer review"}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = check(args.output)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
