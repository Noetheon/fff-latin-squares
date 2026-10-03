#!/usr/bin/env python3
"""Compare the frozen third-party audit's 18 outputs without executing its code.

The original audit remains outside this public repository. This successor
verifies its pinned manifest and payload before using the reference results.
The comparison is not a mathematical proof or a PDF-validation substitute.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re

SPEC = importlib.util.spec_from_file_location("strict_audit_json", Path(__file__).with_name("audit_json.py"))
STRICT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STRICT)
MANIFEST_SHA256 = "571062bcd9ac17bbd5a2c0f779a3967474b7bdc1059c03933a1aedecfadbd659"
OUTPUTS = {
    "baseline": (
        "binary_lift_checks.json", "binary_mate_checks.json", "core_checks.json",
        "finite_field_checks.json", "minor_certificates.jsonl", "minor_checks.json",
        "near18_checks.json", "order10_inventory_checks.json", "order20_checks.json",
        "order20_representatives.jsonl", "suite_checks.json"),
    "current": (
        "compact_new_controls.json", "e9_independent.json", "eight_pattern_witnesses.json",
        "order36.json", "public_table_checks.json", "source21_physical.json",
        "source21_quotient.json"),
}
VOLATILE = {("baseline", "core_checks.json"), ("current", "e9_independent.json"),
            ("current", "source21_physical.json"), ("current", "source21_quotient.json")}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_file(root, name):
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
        raise ValueError("Unsafe relative path")
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinks are not permitted: " + name)
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing or escaping file: " + name)
    return path


def verify_package(root):
    manifest = regular_file(root, "MANIFEST.sha256")
    if sha(manifest) != MANIFEST_SHA256:
        raise ValueError("External manifest differs from the reviewed frozen package")
    seen = set()
    for line in manifest.read_text().splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or not re.fullmatch("[0-9a-f]{64}", digest) or name in seen:
            raise ValueError("Malformed or repeated manifest entry")
        seen.add(name)
        if sha(regular_file(root, name)) != digest:
            raise ValueError("Frozen external payload changed: " + name)
    if len(seen) != 60:
        raise ValueError("Incomplete external payload")
    for scope, names in OUTPUTS.items():
        references = root / "reference_results" / scope
        if {p.name for p in references.iterdir()} != set(names):
            raise ValueError("Unexpected reference inventory")
        if not all("reference_results/" + scope + "/" + name in seen for name in names):
            raise ValueError("Unsealed reference result")
    return len(seen)


def compare_record(scope, name, expected, actual):
    if scope not in OUTPUTS or name not in OUTPUTS[scope]:
        raise ValueError("Unreviewed output")
    STRICT.validate(expected)
    STRICT.validate(actual)
    ignored = []
    if (scope, name) in VOLATILE:
        for value in (expected, actual):
            if (not isinstance(value, dict) or "seconds" not in value
                    or type(value["seconds"]) not in (int, float) or value["seconds"] < 0):
                raise ValueError("Missing or invalid declared timing")
        expected, actual = dict(expected), dict(actual)
        del expected["seconds"]
        del actual["seconds"]
        ignored.append("seconds")
    if (scope, name) == ("current", "compact_new_controls.json"):
        if (not isinstance(expected, dict) or not isinstance(actual, dict)
                or "displayed_L12_bindings" not in expected
                or "displayed_L12_bindings" not in actual):
            raise ValueError("Optional PDF check status must still be present")
        expected, actual = dict(expected), dict(actual)
        del expected["displayed_L12_bindings"]
        del actual["displayed_L12_bindings"]
        ignored.append("displayed_L12_bindings: excluded, requires separate PDF verification")
    errors = STRICT.differences(expected, actual)
    if errors:
        raise ValueError(scope + "/" + name + ": " + "; ".join(errors[:8]))
    return ignored


def compare(package, actual_root):
    verified = verify_package(package)
    rows = []
    for scope, names in OUTPUTS.items():
        directory = ("replay_earlier_audit/results" if scope == "baseline" else "results")
        for name in names:
            reference = regular_file(package, "reference_results/" + scope + "/" + name)
            actual = regular_file(actual_root, directory + "/" + name)
            ignored = []
            if name.endswith(".json"):
                ignored = compare_record(scope, name, STRICT.read(reference), STRICT.read(actual))
            elif reference.read_bytes() != actual.read_bytes():
                raise ValueError("Byte mismatch: " + scope + "/" + name)
            rows.append({"scope": scope, "file": name, "reference_sha256": sha(reference),
                         "actual_sha256": sha(actual), "ignored_fields": ignored})
    return {"passed": True, "scope": "18 bounded result comparisons only",
            "external_manifest_sha256": MANIFEST_SHA256,
            "sealed_payload_files_checked": verified, "comparisons": rows,
            "optional_pdf_validation": "not certified by this comparator",
            "full_order8_census_replayed": False, "full_order10_master_replayed": False,
            "independent_human_peer_review": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    root = Path(__file__).resolve().parents[1]
    if not output.is_relative_to(root / ".audit") or output.exists():
        parser.error("Use a new output file under .audit")
    try:
        report = compare(args.package.resolve(), args.actual.resolve())
    except (ValueError, OSError) as error:
        report = {"passed": False, "error": str(error)}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"],
                      "comparisons": len(report.get("comparisons", []))}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
