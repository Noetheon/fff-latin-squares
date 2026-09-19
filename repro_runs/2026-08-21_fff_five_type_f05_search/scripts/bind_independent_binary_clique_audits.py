#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


F05_GRAPH_SHA = "7ac03b6431e39070b334c3d8cfd4a12b58180226f5e0319c175547ebca1ac5c4"
F05_CLIQUE_COUNT = 8832
F05_PATTERN_COUNTS = {"FFT": 2496, "FTF": 2496, "FTT": 3840}
F05_EXACT_PALETTE_COUNT = 8832
F18_GRAPH_SHA = "c4f46131f9a60708b6410502a2765ce85db3f9bbf38efdf5217316fa7d010510"


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
    parser.add_argument("--f05-graph", type=Path, required=True)
    parser.add_argument("--f05-result", type=Path, required=True)
    parser.add_argument("--f18-graph", type=Path, required=True)
    parser.add_argument("--f18-result", type=Path, required=True)
    parser.add_argument("--f18-reference-audit", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    f05 = json.loads(args.f05_result.read_text())
    f18 = json.loads(args.f18_result.read_text())
    f18_reference = json.loads(args.f18_reference_audit.read_text())
    zero_errors = lambda value: all(value.get(key) == 0 for key in (
        "latin_errors", "row_not_f_errors", "palette_subset_errors",
    ))
    checks = {
        "f05_graph_hash": sha256(args.f05_graph) == F05_GRAPH_SHA,
        "f18_graph_hash": sha256(args.f18_graph) == F18_GRAPH_SHA,
        "f05_result_valid": f05.get("valid") is True and zero_errors(f05),
        "f05_complete_counts": f05.get("initial_tasks") == 11892
        and f05.get("clique_count") == F05_CLIQUE_COUNT
        and f05.get("pattern_counts") == F05_PATTERN_COUNTS
        and f05.get("exact_palette_count") == F05_EXACT_PALETTE_COUNT
        and f05.get("fff_count") == 0,
        "f18_control_valid": f18.get("valid") is True and zero_errors(f18),
        "f18_control_counts": f18.get("initial_tasks") == 2520
        and f18.get("clique_count") == 1920
        and f18.get("pattern_counts") == {"FFT": 960, "FTF": 960}
        and f18.get("fff_count") == 0,
        "f18_matches_independent_cliquer_audit":
        f18_reference.get("all_checks_passed") is True
        and f18_reference.get("graph_sha256") == F18_GRAPH_SHA
        and f18_reference.get("unique_clique_count") == f18.get("clique_count")
        and f18_reference.get("pattern_counts") == f18.get("pattern_counts")
        and f18_reference.get("fff_count") == f18.get("fff_count"),
    }
    result = {
        "schema_version": "f05-independent-binary-clique-audit-binding-v1",
        "files": {
            "f05_graph": artifact(args.f05_graph),
            "f05_result": artifact(args.f05_result),
            "f18_graph": artifact(args.f18_graph),
            "f18_result": artifact(args.f18_result),
            "f18_reference_audit": artifact(args.f18_reference_audit),
            "source": artifact(args.source),
            "binary": artifact(args.binary),
        },
        "commands": {
            "compile": [
                "/usr/bin/clang++", "-O3", "-std=c++20", "-pthread",
                "-mcpu=apple-m4", str(args.source), "-o", str(args.binary),
            ],
            "f18_control": [str(args.binary), str(args.f18_graph),
                "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+4", "8+2", "8"],
            "f05_run": [str(args.binary), str(args.f05_graph),
                "10", "2+2+2+2+2", "4+2+2+2", "6+2+2", "8+2", "8"],
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Independent binary clique audit binding", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"f18 control cliques/patterns: {f18.get('clique_count')}/{f18.get('pattern_counts')}",
        f"f05 cliques/patterns: {f05.get('clique_count')}/{f05.get('pattern_counts')}",
        f"f05 exact-palette/FFF: {f05.get('exact_palette_count')}/{f05.get('fff_count')}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"independent binary clique binding failed: {failed}")


if __name__ == "__main__":
    main()
