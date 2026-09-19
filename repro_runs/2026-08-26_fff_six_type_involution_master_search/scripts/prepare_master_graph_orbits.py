#!/usr/bin/env python3
import argparse
import hashlib
import itertools
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path


MAGIC = b"O8HTv1\0\0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for point, image in enumerate(permutation):
        result[image] = point
    return tuple(result)


def conjugate(
    relabelling: tuple[int, ...], permutation: tuple[int, ...]
) -> tuple[int, ...]:
    inverse_relabelling = inverse(relabelling)
    return tuple(
        relabelling[permutation[inverse_relabelling[point]]]
        for point in range(len(permutation))
    )


def cycles(permutation: tuple[int, ...]) -> list[tuple[int, ...]]:
    seen = set()
    result = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycle = []
        point = start
        while point not in seen:
            seen.add(point)
            cycle.append(point)
            point = permutation[point]
        result.append(tuple(cycle))
    return result


def centralizer(permutation: tuple[int, ...]) -> list[tuple[int, ...]]:
    by_length: dict[int, list[tuple[int, ...]]] = defaultdict(list)
    for cycle in cycles(permutation):
        by_length[len(cycle)].append(cycle)

    blocks = []
    for length in sorted(by_length):
        source_cycles = by_length[length]
        choices = []
        for target_order in itertools.permutations(range(len(source_cycles))):
            for rotations in itertools.product(range(length), repeat=len(source_cycles)):
                mapping = {}
                for source_index, source_cycle in enumerate(source_cycles):
                    target_cycle = source_cycles[target_order[source_index]]
                    rotation = rotations[source_index]
                    for offset, point in enumerate(source_cycle):
                        mapping[point] = target_cycle[(offset + rotation) % length]
                choices.append(mapping)
        blocks.append(choices)

    result = []
    for choices in itertools.product(*blocks):
        mapping = {}
        for choice in choices:
            mapping.update(choice)
        result.append(tuple(mapping[point] for point in range(len(permutation))))
    return result


def load_graph_vertices(path: Path) -> tuple[tuple[int, ...], list[tuple[int, ...]], int]:
    with path.open("rb") as handle:
        magic = handle.read(8)
        count, words = struct.unpack("<II", handle.read(8))
        root = tuple(handle.read(10))
        vertices = [tuple(handle.read(10)) for _ in range(count)]
    expected_size = 26 + count * 10 + count * words * 8
    if magic != MAGIC or words != (count + 63) // 64:
        raise SystemExit("invalid graph header")
    if path.stat().st_size != expected_size:
        raise SystemExit("graph size does not match its header")
    return root, vertices, words


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--task-ordinals", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text())
    cases = {case["case_id"]: case for case in inventory["cases"]}
    if args.case_id not in cases:
        raise SystemExit("case is absent from the independent inventory")
    expected = cases[args.case_id]
    binding = json.loads(args.binding.read_text())
    if binding.get("all_checks_passed") is not True:
        raise SystemExit("master inventory binding is not valid")
    if args.case_id not in binding.get("cases", {}):
        raise SystemExit("case is absent from the master inventory binding")
    bound_expected = binding["cases"][args.case_id]

    root, vertices, words = load_graph_vertices(args.graph)
    if list(root) != expected["root"]:
        raise SystemExit("graph root differs from the independently frozen root")
    if len(vertices) != expected["triple_filtered_candidates"]:
        raise SystemExit("graph vertex count differs from the independent inventory")

    buckets = [[] for _ in range(8)]
    for index, vertex in enumerate(vertices):
        bucket = vertex[0] - 2
        if not 0 <= bucket < 8:
            raise SystemExit(f"invalid first-image bucket at vertex {index}")
        buckets[bucket].append(index)
    bucket_sizes = [len(bucket) for bucket in buckets]
    nonempty = [index for index, bucket in enumerate(buckets) if bucket]
    initial_bucket = min(nonempty, key=lambda index: (len(buckets[index]), index))
    initial_image = initial_bucket + 2
    full_tasks = buckets[initial_bucket]
    if len(full_tasks) != expected["root_task_count"]:
        raise SystemExit("initial task count differs from the independent inventory")

    residual_group = [
        relabelling
        for relabelling in centralizer(root)
        if relabelling[0] == 0 and relabelling[initial_image] == initial_image
    ]
    if len(residual_group) != expected["residual_group_size"]:
        raise SystemExit("residual group size differs from the independent inventory")

    vertex_index = {vertex: index for index, vertex in enumerate(vertices)}
    full_task_set = set(full_tasks)
    ordinal_by_vertex = {
        vertex: ordinal for ordinal, vertex in enumerate(full_tasks)
    }
    remaining = set(full_tasks)
    orbits = []
    while remaining:
        seed = min(remaining)
        images = {
            vertex_index[conjugate(relabelling, vertices[seed])]
            for relabelling in residual_group
        }
        if not images <= full_task_set:
            raise SystemExit("residual-group orbit escapes the initial task bucket")
        orbits.append(sorted(images))
        remaining -= images
    representatives = sorted(
        min(ordinal_by_vertex[vertex] for vertex in orbit) for orbit in orbits
    )
    orbit_size_counts = dict(sorted(Counter(map(len, orbits)).items()))
    expected_orbit_sizes = {
        int(size): count for size, count in expected["orbit_size_counts"].items()
    }

    task_text = "".join(f"{ordinal}\n" for ordinal in representatives)
    if args.task_ordinals.is_file():
        if args.task_ordinals.read_text() != task_text:
            raise SystemExit("existing task-ordinal file differs from reconstruction")
    else:
        args.task_ordinals.parent.mkdir(parents=True, exist_ok=True)
        args.task_ordinals.write_text(task_text)

    checks = {
        "inventory_binding_current": sha256(args.inventory)
        == binding["files"]["python_output"]["sha256"],
        "graph_root_frozen": list(root) == expected["root"],
        "graph_vertices_frozen": len(vertices) == expected["triple_filtered_candidates"],
        "bucket_counts_frozen": [0, 0, *bucket_sizes]
        == expected["bucket_counts"],
        "bound_bucket_counts_frozen": [0, 0, *bucket_sizes]
        == bound_expected["bucket_counts"],
        "residual_group_frozen": len(residual_group) == expected["residual_group_size"],
        "orbit_count_frozen": len(orbits) == expected["orbit_count"],
        "orbit_sizes_frozen": orbit_size_counts == expected_orbit_sizes,
        "exact_orbit_cover": sum(map(len, orbits)) == len(full_tasks),
        "representatives_unique": len(representatives) == len(set(representatives)),
    }
    result = {
        "schema_version": "six-type-master-graph-root-orbit-audit-v1",
        "case_id": args.case_id,
        "graph_path": str(args.graph.resolve()),
        "graph_sha256": sha256(args.graph),
        "graph_vertices": len(vertices),
        "graph_words": words,
        "root": list(root),
        "bucket_sizes_for_images_2_to_9": bucket_sizes,
        "initial_bucket": initial_bucket,
        "initial_image": initial_image,
        "full_initial_tasks": len(full_tasks),
        "full_task_vertices_sha256": canonical_sha(full_tasks),
        "residual_group_size": len(residual_group),
        "residual_group_sha256": canonical_sha(residual_group),
        "orbit_count": len(orbits),
        "orbit_size_counts": orbit_size_counts,
        "covered_task_count": sum(map(len, orbits)),
        "selected_task_ordinals": representatives,
        "selected_task_ordinals_sha256": canonical_sha(representatives),
        "selected_task_vertices": [full_tasks[ordinal] for ordinal in representatives],
        "task_ordinals_path": str(args.task_ordinals.resolve()),
        "task_ordinals_sha256": sha256(args.task_ordinals),
        "checks": checks,
        "valid": all(checks.values()),
        "evidence_boundary": (
            "Graph-bound root-orbit cover only; no completion search result."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Six-type master graph root-orbit audit",
        "",
        f"case: {args.case_id}",
        f"graph vertices: {len(vertices)}",
        f"full tasks/orbits: {len(full_tasks)}/{len(orbits)}",
        f"residual group: {len(residual_group)}",
        f"orbit sizes: {orbit_size_counts}",
        f"covered tasks: {sum(map(len, orbits))}",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")
    if not result["valid"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"master graph orbit audit failed: {failed}")


if __name__ == "__main__":
    main()
