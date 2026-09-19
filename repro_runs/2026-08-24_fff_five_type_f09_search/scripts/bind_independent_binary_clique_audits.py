#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


F09_GRAPH_SHA = "8ebf555e63f51e0fad9d24f71fc12e47ac057ff55ed22b640f4d7c954f0d878e"
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


def zero_errors(value: dict) -> bool:
    return all(value.get(key) == 0 for key in (
        "latin_errors", "row_not_f_errors", "palette_subset_errors",
    ))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--f09-graph", type=Path, required=True)
    parser.add_argument("--f09-result", type=Path, required=True)
    parser.add_argument("--f18-graph", type=Path, required=True)
    parser.add_argument("--f18-result", type=Path, required=True)
    parser.add_argument("--f18-reference-audit", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    f09 = json.loads(args.f09_result.read_text())
    f18 = json.loads(args.f18_result.read_text())
    f18_reference = json.loads(args.f18_reference_audit.read_text())
    f09_patterns = f09.get("pattern_counts", {})
    checks = {
        "f09_graph_hash": sha256(args.f09_graph) == F09_GRAPH_SHA,
        "f18_graph_hash": sha256(args.f18_graph) == F18_GRAPH_SHA,
        "f09_result_valid": f09.get("valid") is True and zero_errors(f09),
        "f09_complete_task_cover": f09.get("initial_tasks") == 18840,
        "f09_pattern_partition": sum(f09_patterns.values()) == f09.get("clique_count")
        and f09_patterns.get("FFF", 0) == f09.get("fff_count"),
        "f09_no_fff": f09.get("fff_count") == 0,
        "f09_exact_palette_count_bounded": 0 <= f09.get("exact_palette_count", -1)
        <= f09.get("clique_count", -2),
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
        "schema_version": "f09-independent-binary-clique-audit-binding-v1",
        "files": {
            "f09_graph": artifact(args.f09_graph),
            "f09_result": artifact(args.f09_result),
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
            "f09_run": [str(args.binary), str(args.f09_graph),
                "10", "2+2+2+2+2", "4+4+2", "6+4", "8+2", "8"],
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Independent binary clique audit binding", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"f18 control cliques/patterns: {f18.get('clique_count')}/{f18.get('pattern_counts')}",
        f"f09 cliques/patterns: {f09.get('clique_count')}/{f09_patterns}",
        f"f09 exact-palette/FFF: {f09.get('exact_palette_count')}/{f09.get('fff_count')}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"independent binary clique binding failed: {failed}")


if __name__ == "__main__":
    main()
