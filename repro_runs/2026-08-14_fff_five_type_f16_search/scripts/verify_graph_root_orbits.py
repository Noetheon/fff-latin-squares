#!/usr/bin/env python3
import argparse
import hashlib
import itertools
import json
import struct
from collections import Counter
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * 10
    for point, image in enumerate(permutation):
        result[image] = point
    return tuple(result)


def conjugate(g: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    gi = inverse(g)
    return tuple(g[q[gi[point]]] for point in range(10))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--dimension-record", type=Path, required=True)
    parser.add_argument("--task-ordinals", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    dimension = json.loads(args.dimension_record.read_text())
    expected_palette = ["2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2", "6+4"]
    dimension_checks = {
        "schema": dimension.get("schema_version") == "five-type-root-orbit-dimension-v1",
        "valid": dimension.get("valid") is True,
        "case": dimension.get("case_id") == "f16",
        "palette": dimension.get("palette") == expected_palette,
        "root_type": dimension.get("root_type") == "4+2+2+2",
    }
    if not all(dimension_checks.values()):
        raise SystemExit("invalid f16 dimension record")
    with args.graph.open("rb") as handle:
        magic = handle.read(8)
        n, words = struct.unpack("<II", handle.read(8))
        root = tuple(handle.read(10))
        vertices = [tuple(handle.read(10)) for _ in range(n)]
    if magic != b"O8HTv1\0\0" or args.graph.stat().st_size != 26 + 10*n + 8*n*words:
        raise SystemExit("invalid graph envelope")
    expected_root = (1, 2, 3, 0, 5, 4, 7, 6, 9, 8)
    if root != expected_root:
        raise SystemExit("graph does not contain the canonical f16 root")
    if n != dimension["level1_candidates"]:
        raise SystemExit("graph/dimension candidate-count mismatch")
    buckets = [[] for _ in range(8)]
    for index, vertex in enumerate(vertices):
        buckets[vertex[0] - 2].append(index)
    if [len(bucket) for bucket in buckets] != dimension["bucket_sizes"]:
        raise SystemExit("graph/dimension bucket mismatch")
    initial_bucket = dimension["initial_bucket"]
    initial_image = dimension["initial_image"]
    full_tasks = buckets[initial_bucket]

    group = []
    for value in itertools.permutations(range(10)):
        if value[0] == 0 and value[initial_image] == initial_image:
            if conjugate(value, root) == root:
                group.append(value)
    if len(group) != dimension["residual_group_size"]:
        raise SystemExit("residual group-size mismatch")
    vertex_index = {vertex: index for index, vertex in enumerate(vertices)}
    ordinal_by_vertex = {vertex: ordinal for ordinal, vertex in enumerate(full_tasks)}
    remaining = set(full_tasks)
    orbits = []
    while remaining:
        seed = min(remaining)
        images = {vertex_index[conjugate(g, vertices[seed])] for g in group}
        if not images <= set(full_tasks):
            raise SystemExit("orbit escapes task bucket")
        representative = min(images)
        orbits.append(sorted(images))
        remaining -= images
    orbits.sort(key=lambda orbit: min(ordinal_by_vertex[item] for item in orbit))
    representatives = sorted(
        min(ordinal_by_vertex[item] for item in orbit) for orbit in orbits
    )
    if representatives != dimension["representative_task_ordinals"]:
        raise SystemExit("independent representative list mismatch")
    if len(orbits) != dimension["orbit_count"]:
        raise SystemExit("independent orbit-count mismatch")
    orbit_size_counts = dict(sorted(Counter(map(len, orbits)).items()))
    expected_orbit_size_counts = {12: 6, 24: 2, 48: 30}
    if orbit_size_counts != expected_orbit_size_counts:
        raise SystemExit("unexpected f01 orbit-size distribution")
    args.task_ordinals.write_text("".join(f"{ordinal}\n" for ordinal in representatives))
    selected_vertices = [full_tasks[ordinal] for ordinal in representatives]
    result = {
        "schema_version": "five-type-graph-root-orbit-audit-v1",
        "graph_path": str(args.graph.resolve()),
        "graph_sha256": sha256(args.graph),
        "dimension_record_path": str(args.dimension_record.resolve()),
        "dimension_record_sha256": sha256(args.dimension_record),
        "dimension_checks": dimension_checks,
        "root_permutation": list(root),
        "residual_group_size": len(group),
        "residual_group_sha256": canonical_sha(group),
        "full_initial_bucket": initial_bucket,
        "full_initial_bucket_value": initial_image,
        "full_initial_task_count": len(full_tasks),
        "full_task_vertices_sha256": canonical_sha(full_tasks),
        "orbit_count": len(orbits),
        "orbit_size_counts": orbit_size_counts,
        "covered_task_count": sum(map(len, orbits)),
        "selected_task_ordinals": representatives,
        "selected_task_vertices": sorted(selected_vertices),
        "selected_task_ordinals_sha256": canonical_sha(representatives),
        "selected_task_vertices_sha256": canonical_sha(sorted(selected_vertices)),
        "task_ordinals_path": str(args.task_ordinals.resolve()),
        "task_ordinals_sha256": sha256(args.task_ordinals),
        "checks": {
            "graph_matches_dimension": True,
            "group_matches_dimension": True,
            "representatives_match_dimension": True,
            "canonical_root": root == expected_root,
            "orbit_sizes_exact": orbit_size_counts == expected_orbit_size_counts,
            "all_tasks_covered": sum(map(len, orbits)) == len(full_tasks),
        },
        "valid": sum(map(len, orbits)) == len(full_tasks),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type f16 graph root-orbit audit", "",
        f"graph SHA-256: {result['graph_sha256']}",
        f"group size: {len(group)}",
        f"full tasks/orbits: {len(full_tasks)}/{len(orbits)}",
        f"orbit sizes: {result['orbit_size_counts']}",
        f"covered tasks: {result['covered_task_count']}",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")


if __name__ == "__main__":
    main()
