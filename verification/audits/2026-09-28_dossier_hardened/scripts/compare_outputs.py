"""Compare fresh finite checks to frozen delivered results, without assert gates."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

BYTE_FILES = (
    "results/expanded_representatives.jsonl", "results/corner_parameters.csv",
    "results/exchange_parity.csv", "results/master_inventory.txt",
)
JSON_FILES = (
    "results/expanded_summary.json", "results/verified_certificates.json",
    "results/secondary_verification.json", "results/crt_N9.json",
    "results/crt_N15.json", "results/crt_N45.json", "results/crt_N75.json",
    "results/burnside_and_arithmetic.json", "results/additional_controls.json",
    "results/trade_parity.json",
    "rerun/results/burnside.json", "rerun/results/core_results.json",
    "rerun/results/formulation_scope.json", "rerun/results/norm_and_36.json",
    "rerun/results/order20_rank_certificates.json", "rerun/results/order8_230_checks.json",
    "rerun/results/report_value_checks.json", "rerun/results/smallorders_and_flags.json",
    "rerun/results/threepoint_checks.json", "rerun/results/trade_19_0.json",
)
TIMED_FILES = {
    "results/secondary_verification.json", "results/crt_N9.json",
    "results/crt_N15.json", "results/crt_N45.json", "results/crt_N75.json",
    "results/burnside_and_arithmetic.json", "results/additional_controls.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source_manifest(root):
    seen = set()
    for line in (root / "SOURCE_MANIFEST.sha256").read_text().splitlines():
        digest, sep, name = line.partition("  ")
        path = PurePosixPath(name)
        if (not sep or not re.fullmatch(r"[a-f0-9]{64}", digest) or not name
                or path.is_absolute() or ".." in path.parts or name in seen
                or path.as_posix() != name):
            raise ValueError("Invalid source manifest entry")
        seen.add(name)
        target = root / name
        if not target.resolve().is_relative_to(root.resolve()) or sha(target) != digest:
            raise ValueError(f"Source/reference hash mismatch: {name}")
    actual = {p.relative_to(root).as_posix() for directory in ("scripts", "inputs", "results", "rerun")
              for p in (root / directory).rglob("*") if p.is_file()
              and "__pycache__" not in p.parts}
    if seen != actual:
        raise ValueError("Source manifest does not cover the exact code/input/reference payload")
    return len(seen)


def normalized(path, name):
    value = json.loads(path.read_text())
    if name in TIMED_FILES:
        seconds = value.pop("seconds")
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid $.seconds runtime field")
    # Object key order is immaterial; list order and all scientific fields remain exact.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def compare(reference, fresh):
    records = []
    for name in BYTE_FILES + JSON_FILES:
        row = {"path": name, "comparison": "bytes" if name in BYTE_FILES else "JSON",
               "ignored_fields": ["$.seconds"] if name in TIMED_FILES else [],
               "normalization": [] if name in BYTE_FILES else ["JSON object key order only"]}
        try:
            expected, actual = reference / name, fresh / name
            row.update(reference_sha256=sha(expected), fresh_sha256=sha(actual))
            row["matched"] = (expected.read_bytes() == actual.read_bytes() if name in BYTE_FILES
                              else normalized(expected, name) == normalized(actual, name))
        except (OSError, ValueError, KeyError, TypeError) as error:
            row.update(matched=False, error=type(error).__name__ + ": " + str(error))
        records.append(row)
    return {"passed": all(row["matched"] for row in records), "comparisons": records,
            "scope": "24 fixed finite outputs, not whole-manuscript correctness or human peer review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--fresh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.reference, args.fresh)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "comparisons": len(result["comparisons"])}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
