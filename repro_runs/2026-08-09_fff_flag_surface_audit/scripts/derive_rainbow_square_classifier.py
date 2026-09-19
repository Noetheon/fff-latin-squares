#!/usr/bin/env python3
"""Derive the minimal C70 plus rainbow-square trace order-8 classifier."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


WORD = "012012"


def sha256_json(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    records = []
    joint_groups = defaultdict(list)
    c70_groups = defaultdict(list)
    value_counts = Counter()
    for source in audit["order8_fff_records"]:
        profile = dict(source["mixed_trace_profile"])
        orbit = profile[WORD]
        if len(set(orbit)) != 1:
            raise RuntimeError(
                f"source {source['source_index']}: rainbow-square trace is not color-invariant"
            )
        value = orbit[0]
        beta_fixed = 4 * source["intercalates"]
        if value < beta_fixed or (value - beta_fixed) % 2:
            raise RuntimeError(f"source {source['source_index']}: invalid beta orbit counts")
        beta_two_cycles = (value - beta_fixed) // 2
        c70 = source["c70_incidence_signature_sha256"]
        joint = sha256_json([c70, value])
        c70_groups[c70].append(source["source_index"])
        joint_groups[joint].append(source["source_index"])
        value_counts[value] += 1
        records.append(
            {
                "source_index": source["source_index"],
                "fff_index": source["fff_index"],
                "group_isotopic": source["group_isotopic"],
                "intercalates": source["intercalates"],
                "rainbow_trace_beta_fixed": beta_fixed,
                "rainbow_square_trace_beta2_fixed": value,
                "rainbow_beta_two_cycle_count": beta_two_cycles,
                "c70_incidence_signature_sha256": c70,
                "c70_rainbow_square_joint_sha256": joint,
            }
        )
    old_collisions = sorted(
        sorted(group) for group in c70_groups.values() if len(group) > 1
    )
    remaining = sorted(
        sorted(group) for group in joint_groups.values() if len(group) > 1
    )
    by_source = {record["source_index"]: record for record in records}
    resolutions = [
        {
            "source_indices": group,
            "rainbow_square_values": [
                by_source[source]["rainbow_square_trace_beta2_fixed"]
                for source in group
            ],
        }
        for group in old_collisions
    ]
    payload = {
        "audit_version": "fff_c70_rainbow_square_classifier_v1",
        "word": WORD,
        "definition": "Fix((alpha_R alpha_C alpha_S)^2)",
        "table_count": len(records),
        "c70_distinct_count": len(c70_groups),
        "c70_collision_groups": old_collisions,
        "rainbow_square_value_counts": {
            str(key): value for key, value in sorted(value_counts.items())
        },
        "c70_rainbow_square_joint_distinct_count": len(joint_groups),
        "remaining_joint_collision_groups": remaining,
        "old_collision_resolutions": resolutions,
        "all_color_orbits_constant": True,
        "records": records,
        "claim_boundary": [
            "Exact classifier on the 230 frozen order-8 FFF representatives only.",
            "No injectivity or classification theorem is asserted in higher orders.",
            "C38 remains open and C40 remains absent.",
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "C70 plus rainbow-square trace classifier",
        "",
        f"tables: {len(records)}",
        f"C70 distinct: {len(c70_groups)}",
        f"C70 collision groups: {old_collisions}",
        f"rainbow-square value counts: {dict(sorted(value_counts.items()))}",
        f"joint distinct: {len(joint_groups)}",
        f"remaining joint collisions: {remaining}",
        f"old collision resolutions: {resolutions}",
        "",
        "Conservative conclusion:",
        "- The joint invariant is exact and complete on the frozen 230-class order-8 FFF census.",
        "- It is not a higher-order classification theorem.",
        "- C38 remains open and C40 remains absent.",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    if len(records) != 230 or len(joint_groups) != 230 or remaining:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
