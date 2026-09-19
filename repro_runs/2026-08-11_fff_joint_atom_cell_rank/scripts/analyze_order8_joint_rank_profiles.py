#!/usr/bin/env python3
"""Compute the finite C97 joint-rank profile on the 230 order-8 FFF inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path


AUDIT = runpy.run_path(
    str(Path(__file__).with_name("audit_joint_atom_cell_rank.py"))
)
analyze_table = AUDIT["analyze_table"]
load_n8 = AUDIT["load_n8"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def component_tuple(component: dict) -> tuple[int, int, int, int, int]:
    return (
        component["flag_count"],
        component["atom_count"],
        component["normalized_vertex_count"],
        component["q"],
        component["s_Q"],
    )


def signature_key(signature: list[tuple[int, ...]]) -> str:
    return ";".join(",".join(map(str, entry)) for entry in signature)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--holonomy-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    holonomy_payload = json.loads(args.holonomy_audit.read_text())
    holonomy_groups = holonomy_payload["datasets"]["order8_fff_complete"][
        "fff_holonomy_signature_groups"
    ]
    holonomy_by_source = {
        int(source): signature
        for signature, sources in holonomy_groups.items()
        for source in sources
    }
    profiles = []
    errors = []
    groups: dict[str, list[int]] = defaultdict(list)
    for source_index, table in load_n8(args.fff_metadata):
        record = analyze_table(table, source_index)
        errors.extend(
            {"source_index": source_index, "error": error}
            for error in record["errors"]
        )
        signature = sorted(component_tuple(component) for component in record["components"])
        key = signature_key(signature)
        groups[key].append(source_index)
        holonomy_signature = holonomy_by_source.get(source_index)
        if holonomy_signature is None:
            errors.append(
                {"source_index": source_index, "error": "missing C86 holonomy signature"}
            )
        profiles.append(
            {
                "source_index": source_index,
                "component_count": record["component_count"],
                "joint_rank_signature": signature,
                "c86_holonomy_signature_sha256": holonomy_signature,
                "exceptional_components": [
                    {
                        "component_id": component["component_id"],
                        "flag_count": component["flag_count"],
                        "atom_count": component["atom_count"],
                        "normalized_vertex_count": component["normalized_vertex_count"],
                        "q": component["q"],
                        "s_Q": component["s_Q"],
                        "epsilon_Q": component["epsilon_Q"],
                    }
                    for component in record["components"]
                    if component["s_Q"] > 1
                ],
            }
        )

    collision_histogram = Counter(len(sources) for sources in groups.values())
    combined_groups: dict[str, list[int]] = defaultdict(list)
    for profile in profiles:
        combined_groups[
            json.dumps(
                [
                    profile["joint_rank_signature"],
                    profile["c86_holonomy_signature_sha256"],
                ],
                separators=(",", ":"),
            )
        ].append(profile["source_index"])
    combined_collision_histogram = Counter(
        len(sources) for sources in combined_groups.values()
    )
    exceptional_profiles = [
        profile for profile in profiles if profile["exceptional_components"]
    ]
    payload = {
        "audit_version": "order8_joint_rank_profile_v1",
        "input": {
            "path": str(args.fff_metadata),
            "sha256": sha256(args.fff_metadata),
        },
        "c86_holonomy_input": {
            "path": str(args.holonomy_audit),
            "sha256": sha256(args.holonomy_audit),
        },
        "signature_definition": (
            "sorted multiset of (flag_count, atom_count, normalized_vertex_count, q, s_Q)"
        ),
        "table_count": len(profiles),
        "distinct_signature_count": len(groups),
        "singleton_signature_count": collision_histogram[1],
        "maximum_signature_collision_size": max(collision_histogram, default=0),
        "collision_size_histogram": dict(sorted(collision_histogram.items())),
        "combined_c86_c97_signature_count": len(combined_groups),
        "combined_c86_c97_singleton_count": combined_collision_histogram[1],
        "combined_c86_c97_maximum_collision_size": max(
            combined_collision_histogram, default=0
        ),
        "combined_c86_c97_collision_size_histogram": dict(
            sorted(combined_collision_histogram.items())
        ),
        "exceptional_table_count": len(exceptional_profiles),
        "exceptional_source_indices": [
            profile["source_index"] for profile in exceptional_profiles
        ],
        "signature_groups": [
            {
                "joint_rank_signature": [
                    tuple(map(int, entry.split(","))) for entry in key.split(";")
                ],
                "source_indices": sorted(sources),
            }
            for key, sources in sorted(groups.items())
        ],
        "combined_c86_c97_signature_groups": [
            {
                "joint_rank_signature": json.loads(key)[0],
                "c86_holonomy_signature_sha256": json.loads(key)[1],
                "source_indices": sorted(sources),
            }
            for key, sources in sorted(combined_groups.items())
        ],
        "profiles": profiles,
        "error_count": len(errors),
        "errors": errors,
        "claim_boundary": [
            "This is an exact finite profile on the frozen 230 order-8 FFF representatives.",
            "Profile collisions are not main-class or isotopy classifications.",
            "The combined C86/C97 profile is likewise only a frozen-corpus invariant.",
            "No universal bound on s_Q or epsilon_Q is inferred.",
            "This does not decide order 10; C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "Order-8 C97 joint-rank profile audit",
        "",
        f"tables: {payload['table_count']}",
        f"distinct signatures: {payload['distinct_signature_count']}",
        f"singleton signatures: {payload['singleton_signature_count']}",
        f"maximum collision size: {payload['maximum_signature_collision_size']}",
        f"collision histogram: {payload['collision_size_histogram']}",
        f"combined C86/C97 signatures: {payload['combined_c86_c97_signature_count']}",
        f"combined C86/C97 singleton signatures: {payload['combined_c86_c97_singleton_count']}",
        f"combined C86/C97 maximum collision size: {payload['combined_c86_c97_maximum_collision_size']}",
        f"combined C86/C97 collision histogram: {payload['combined_c86_c97_collision_size_histogram']}",
        f"tables with epsilon_Q > 0: {payload['exceptional_table_count']}",
        f"exceptional source indices: {payload['exceptional_source_indices']}",
        f"errors: {payload['error_count']}",
        "",
        "Boundary:",
        "- Exact finite invariant only; no main-class or isotopy classification is claimed.",
        "- Combining C86 and C97 remains a frozen-corpus statement only.",
        "- No universal upper bound on s_Q is claimed.",
        "- C38 remains open and C40 absent.",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    return len(errors)


if __name__ == "__main__":
    raise SystemExit(main())
