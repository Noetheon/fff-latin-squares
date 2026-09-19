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
    result = [0] * len(permutation)
    for point, image in enumerate(permutation):
        result[image] = point
    return tuple(result)


def conjugate(g: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    gi = inverse(g)
    return tuple(g[q[gi[point]]] for point in range(10))


def centralizer_stabilizer() -> list[tuple[int, ...]]:
    pairs = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9))
    group = []
    for targets in itertools.permutations((2, 3, 4)):
        for flips in itertools.product((0, 1), repeat=3):
            g = list(range(10))
            for source_index, target_index, flip in zip((2, 3, 4), targets, flips):
                source = pairs[source_index]
                target = pairs[target_index]
                g[source[0]] = target[flip]
                g[source[1]] = target[1 - flip]
            group.append(tuple(g))
    return sorted(group)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--task-ordinals", type=Path, required=True)
    args = parser.parse_args()

    with args.graph.open("rb") as handle:
        magic = handle.read(8)
        n, words = struct.unpack("<II", handle.read(8))
        root = tuple(handle.read(10))
        vertices = [tuple(handle.read(10)) for _ in range(n)]
    expected_root = (1, 0, 3, 2, 5, 4, 7, 6, 9, 8)
    if magic != b"O8HTv1\0\0" or root != expected_root:
        raise SystemExit("not the expected strict p09 involution-root graph")
    if args.graph.stat().st_size != 26 + 10 * n + 8 * n * words:
        raise SystemExit("graph size mismatch")

    group = centralizer_stabilizer()
    identity = tuple(range(10))
    group_checks = {
        "size_48": len(group) == 48,
        "unique": len(set(group)) == len(group),
        "fixes_0": all(g[0] == 0 for g in group),
        "fixes_2": all(g[2] == 2 for g in group),
        "centralizes_root": all(conjugate(g, root) == root for g in group),
        "contains_identity": identity in group,
    }
    if not all(group_checks.values()):
        raise SystemExit("residual group construction failed")

    vertex_index = {vertex: index for index, vertex in enumerate(vertices)}
    if len(vertex_index) != len(vertices):
        raise SystemExit("duplicate graph vertices")
    full_tasks = [index for index, vertex in enumerate(vertices) if vertex[0] == 2]
    task_set = set(full_tasks)
    remaining = set(full_tasks)
    orbits = []
    while remaining:
        seed = min(remaining)
        images = {vertex_index[conjugate(g, vertices[seed])] for g in group}
        if not images <= task_set:
            raise SystemExit("orbit escapes the initial bucket")
        representative = min(images, key=lambda index: vertices[index])
        orbits.append({
            "representative_vertex": representative,
            "representative_permutation": list(vertices[representative]),
            "orbit_size": len(images),
            "orbit_vertices_sha256": canonical_sha(sorted(images)),
        })
        remaining -= images
    orbits.sort(key=lambda row: row["representative_permutation"])
    selected_vertices = [row["representative_vertex"] for row in orbits]
    ordinal_by_vertex = {vertex: ordinal for ordinal, vertex in enumerate(full_tasks)}
    selected_ordinals = sorted(ordinal_by_vertex[vertex] for vertex in selected_vertices)
    covered = sum(row["orbit_size"] for row in orbits)
    orbit_size_counts = dict(sorted(Counter(row["orbit_size"] for row in orbits).items()))
    checks = {
        "all_tasks_covered": covered == len(full_tasks),
        "all_orbits_size_48": orbit_size_counts == {48: len(orbits)},
        "representative_count_260": len(orbits) == 260,
        "selected_ordinals_unique": len(set(selected_ordinals)) == len(selected_ordinals),
        "selected_vertices_are_orbit_representatives": set(selected_vertices)
        == {row["representative_vertex"] for row in orbits},
    }
    if not all(checks.values()):
        raise SystemExit("orbit coverage audit failed")

    args.task_ordinals.write_text("".join(f"{ordinal}\n" for ordinal in selected_ordinals))
    result = {
        "schema_version": "p09-involution-root-orbit-audit-v1",
        "graph_path": str(args.graph.resolve()),
        "graph_sha256": sha256(args.graph),
        "root_permutation": list(root),
        "residual_group_definition": "centralizer(root) fixing 0 and 2",
        "residual_group_size": len(group),
        "residual_group_sha256": canonical_sha(group),
        "group_checks": group_checks,
        "full_initial_bucket": 0,
        "full_initial_bucket_value": 2,
        "full_initial_task_count": len(full_tasks),
        "full_task_vertices_sha256": canonical_sha(full_tasks),
        "orbit_count": len(orbits),
        "orbit_size_counts": orbit_size_counts,
        "covered_task_count": covered,
        "selected_task_vertices": sorted(selected_vertices),
        "selected_task_ordinals": selected_ordinals,
        "selected_task_vertices_sha256": canonical_sha(sorted(selected_vertices)),
        "selected_task_ordinals_sha256": canonical_sha(selected_ordinals),
        "task_ordinals_path": str(args.task_ordinals.resolve()),
        "task_ordinals_sha256": sha256(args.task_ordinals),
        "orbits": orbits,
        "checks": checks,
        "valid": all(group_checks.values()) and all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "p09 involution-root orbit audit",
        "",
        f"graph SHA-256: {result['graph_sha256']}",
        f"residual group size: {len(group)}",
        f"full initial tasks: {len(full_tasks)}",
        f"orbit representatives: {len(orbits)}",
        f"orbit sizes: {orbit_size_counts}",
        f"covered tasks: {covered}",
        f"root-task reduction factor: {len(full_tasks) / len(orbits):.6f}",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")


if __name__ == "__main__":
    main()
