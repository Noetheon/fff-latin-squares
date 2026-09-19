#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
DATA = RUN_ROOT / "data"
RESULTS = RUN_ROOT / "results"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    delivered_json = DATA / "delivered_latin_trade_results.json"
    fresh_json = RESULTS / "latin_trade_results.json"
    delivered_summary = DATA / "delivered_latin_trade_summary.txt"
    fresh_summary = RESULTS / "latin_trade_summary.txt"

    json_match = json.loads(delivered_json.read_text()) == json.loads(fresh_json.read_text())
    summary_match = delivered_summary.read_bytes() == fresh_summary.read_bytes()
    claims = json.loads((RESULTS / "small_order_claims.json").read_text())
    report = {
        "overall_json_object_match": json_match,
        "overall_summary_exact_match": summary_match,
        "semantic_failure_count": 0 if json_match and all(claims.values()) else 1,
        "delivered": {
            "latin_trade_results.json": sha256(delivered_json),
            "latin_trade_summary.txt": sha256(delivered_summary),
        },
        "fresh": {
            "latin_trade_results.json": sha256(fresh_json),
            "latin_trade_summary.txt": sha256(fresh_summary),
            "small_order_claims.json": sha256(RESULTS / "small_order_claims.json"),
        },
        "claims": claims,
    }
    (RESULTS / "semantic_comparison_to_delivered_latin_trade_artifacts.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "overall_json_object_match": json_match,
        "overall_summary_exact_match": summary_match,
        "semantic_failure_count": report["semantic_failure_count"],
    }, sort_keys=True))
    return 0 if report["semantic_failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
