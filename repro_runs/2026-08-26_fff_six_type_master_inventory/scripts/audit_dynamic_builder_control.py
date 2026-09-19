#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_SHA256 = "c4f46131f9a60708b6410502a2765ce85db3f9bbf38efdf5217316fa7d010510"
EXPECTED_SIZE = 51004826
EXPECTED_VERTICES = 20160
EXPECTED_WORDS = 315
EXPECTED_ROOT = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def envelope(path: Path) -> dict:
    with path.open("rb") as handle:
        magic = handle.read(8)
        vertices, words = struct.unpack("<II", handle.read(8))
        root = list(handle.read(10))
    return {
        "magic_hex": magic.hex(),
        "vertices": vertices,
        "words": words,
        "root": root,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--semantic-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    generated_sha = sha256(args.generated)
    reference_sha = sha256(args.reference)
    generated_envelope = envelope(args.generated)
    reference_envelope = envelope(args.reference)
    semantic_audit = json.loads(args.semantic_audit.read_text())
    checks = {
        "generated_hash_frozen": generated_sha == EXPECTED_SHA256,
        "reference_hash_frozen": reference_sha == EXPECTED_SHA256,
        "byte_sizes_frozen": args.generated.stat().st_size
        == args.reference.stat().st_size
        == EXPECTED_SIZE,
        "files_byte_identical": args.generated.read_bytes() == args.reference.read_bytes(),
        "envelopes_equal": generated_envelope == reference_envelope,
        "envelope_dimensions_frozen": generated_envelope["vertices"] == EXPECTED_VERTICES
        and generated_envelope["words"] == EXPECTED_WORDS,
        "canonical_root_frozen": generated_envelope["root"] == EXPECTED_ROOT,
        "semantic_vertices_frozen": semantic_audit.get("stored_vertices")
        == semantic_audit.get("independently_enumerated_vertices")
        == EXPECTED_VERTICES,
        "semantic_pairs_frozen": semantic_audit.get("pairs_checked") == 203202720,
        "semantic_edges_frozen": semantic_audit.get("edges") == 11689920,
        "semantic_error_counters_zero": all(
            semantic_audit.get(name) == 0
            for name in (
                "candidate_list_errors",
                "edge_errors",
                "reverse_edge_errors",
                "format_errors",
                "diagonal_errors",
                "padding_errors",
                "canonical_root_errors",
            )
        ),
        "semantic_audit_valid": semantic_audit.get("valid") is True,
    }
    result = {
        "schema_version": "dynamic-master-builder-f18-control-v1",
        "generated": {
            "path": str(args.generated.resolve()),
            "sha256": generated_sha,
            "size_bytes": args.generated.stat().st_size,
            "envelope": generated_envelope,
        },
        "reference": {
            "path": str(args.reference.resolve()),
            "sha256": reference_sha,
            "size_bytes": args.reference.stat().st_size,
            "envelope": reference_envelope,
        },
        "semantic_audit": {
            "path": str(args.semantic_audit.resolve()),
            "sha256": sha256(args.semantic_audit),
            "result": semantic_audit,
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "evidence_boundary": "Builder generalization control only; no six-/seven-type graph was built.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Dynamic master graph-builder f18 control",
        "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"generated/reference SHA-256: {generated_sha}/{reference_sha}",
        f"vertices/words: {generated_envelope['vertices']}/{generated_envelope['words']}",
        f"byte-identical: {str(checks['files_byte_identical']).lower()}",
        f"complete semantic pairs/edges: {semantic_audit.get('pairs_checked')}/{semantic_audit.get('edges')}",
        f"complete semantic audit valid: {str(checks['semantic_audit_valid']).lower()}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("dynamic builder f18 control failed")


if __name__ == "__main__":
    main()
