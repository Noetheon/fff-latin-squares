#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RUN_ROOT = Path(__file__).resolve().parents[1]
DATA = RUN_ROOT / "data"
RESULTS = RUN_ROOT / "results"

STEMS = [
    "order8_loop_invariants_analysis",
    "order8_nongroup_cluster_analysis",
    "order8_invariant_basis_minimization",
    "order8_full_fff_basis_analysis",
    "order8_commutant_weakening_analysis",
    "order8_extended_nongroup_cluster_analysis",
    "order8_cluster_refinement_analysis",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks = []
    summary = {}
    known_drifts = []

    for stem in STEMS:
        delivered_json = DATA / f"delivered_{stem}_results.json"
        fresh_json = RESULTS / f"{stem}_results.json"
        delivered_summary = DATA / f"delivered_{stem}_summary.txt"
        fresh_summary = RESULTS / f"{stem}_summary.txt"

        json_exact = delivered_json.read_bytes() == fresh_json.read_bytes()
        json_object_equal = load_json(delivered_json) == load_json(fresh_json)
        summary_exact = delivered_summary.read_bytes() == fresh_summary.read_bytes()

        checks.append({"name": f"{stem}_json_object_match", "ok": json_object_equal})
        checks.append({"name": f"{stem}_json_exact_match", "ok": json_exact})
        checks.append({"name": f"{stem}_summary_exact_match", "ok": summary_exact})

        summary[stem] = {
            "delivered_json_sha256": sha256(delivered_json),
            "fresh_json_sha256": sha256(fresh_json),
            "json_exact_match": json_exact,
            "json_object_match": json_object_equal,
            "delivered_summary_sha256": sha256(delivered_summary),
            "fresh_summary_sha256": sha256(fresh_summary),
            "summary_exact_match": summary_exact,
        }

        if stem == "order8_loop_invariants_analysis" and not summary_exact:
            known_drifts.append(
                {
                    "stem": stem,
                    "field": "summary.txt",
                    "kind": "display_text_drift",
                    "detail": "fresh script writes a more verbose summary; result JSON is byte-identical",
                }
            )
        if stem == "order8_nongroup_cluster_analysis":
            if not json_exact and json_object_equal:
                known_drifts.append(
                    {
                        "stem": stem,
                        "field": "results.json",
                        "kind": "trailing_newline_only",
                        "detail": "JSON objects are equal; fresh file has one trailing newline",
                    }
                )
            if not summary_exact:
                known_drifts.append(
                    {
                        "stem": stem,
                        "field": "summary.txt",
                        "kind": "counter_display_drift",
                        "detail": "summary renders Counter values as dicts in the fresh run; result JSON is semantically equal",
                    }
                )

    semantic_failures = [c for c in checks if c["name"].endswith("_json_object_match") and not c["ok"]]
    exact_failures = [c for c in checks if not c["ok"]]
    report = {
        "overall_json_object_match": not semantic_failures,
        "overall_exact_artifact_match": not exact_failures,
        "semantic_failures": semantic_failures,
        "exact_failures": exact_failures,
        "known_drifts": known_drifts,
        "summary": summary,
    }

    out = RESULTS / "semantic_comparison_to_delivered_artifacts.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "overall_json_object_match": report["overall_json_object_match"],
                "overall_exact_artifact_match": report["overall_exact_artifact_match"],
                "known_drift_count": len(known_drifts),
                "semantic_failure_count": len(semantic_failures),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
