#!/usr/bin/env python3
import itertools
import json
from collections import Counter


N = 10
IDENTITY = tuple(range(N))
ALL_F = {
    (10,), (2, 2, 2, 2, 2), (4, 2, 2, 2), (4, 4, 2),
    (6, 2, 2), (6, 4), (8, 2),
}


def inverse(p):
    result = [0] * N
    for point, image in enumerate(p):
        result[image] = point
    return tuple(result)


def compose(left, right):
    return tuple(left[right[point]] for point in range(N))


def conjugate(g, p):
    return compose(compose(g, p), inverse(g))


def cycle_type(p):
    seen = [False] * N
    lengths = []
    for start in range(N):
        if seen[start]:
            continue
        current = start
        length = 0
        while not seen[current]:
            seen[current] = True
            current = p[current]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def partial_has_odd_cycle(mapping):
    for start in range(N):
        current = start
        seen_at = {}
        step = 0
        while current >= 0 and current not in seen_at:
            seen_at[current] = step
            step += 1
            current = mapping[current]
        if current >= 0 and current in seen_at:
            length = step - seen_at[current]
            if length > 1 and length % 2:
                return True
    return False


def creates_crossview_odd_cycle(rows):
    for left in range(N):
        for right in range(left + 1, N):
            mapping = [-1] * N
            for row in rows:
                mapping[row[left]] = row[right]
            if partial_has_odd_cycle(mapping):
                return True
    positions = [[0] * N for _ in rows]
    for row_index, row in enumerate(rows):
        for column, symbol in enumerate(row):
            positions[row_index][symbol] = column
    for left in range(N):
        for right in range(left + 1, N):
            mapping = [-1] * N
            for position in positions:
                mapping[position[left]] = position[right]
            if partial_has_odd_cycle(mapping):
                return True
    return False


def analyze(case_id, root, allowed):
    root_inverse = inverse(root)
    class_allowed = 0
    candidates = []
    buckets = Counter()
    for candidate in itertools.permutations(range(N)):
        if cycle_type(candidate) not in allowed:
            continue
        if cycle_type(compose(candidate, root_inverse)) not in allowed:
            continue
        class_allowed += 1
        if creates_crossview_odd_cycle((IDENTITY, root, candidate)):
            continue
        candidates.append(candidate)
        buckets[candidate[0]] += 1

    group = [
        g for g in itertools.permutations(range(N))
        if g[0] == 0 and g[2] == 2 and conjugate(g, root) == root
    ]
    index = {candidate: position for position, candidate in enumerate(candidates)}
    remaining = {index[candidate] for candidate in candidates if candidate[0] == 2}
    orbit_sizes = Counter()
    while remaining:
        seed = min(remaining)
        orbit = {index[conjugate(g, candidates[seed])] for g in group}
        if any(candidates[position][0] != 2 for position in orbit):
            raise RuntimeError("orbit escaped root bucket")
        orbit_sizes[len(orbit)] += 1
        remaining.difference_update(orbit)
    n = len(candidates)
    words = (n + 63) // 64
    return {
        "case_id": case_id,
        "root": list(root),
        "allowed_types": [list(item) for item in sorted(allowed)],
        "class_allowed_candidates": class_allowed,
        "triple_filtered_candidates": n,
        "bucket_counts": [buckets[value] for value in range(N)],
        "residual_group_size": len(group),
        "root_task_count": buckets[2],
        "orbit_size_counts": dict(sorted(orbit_sizes.items())),
        "orbit_count": sum(orbit_sizes.values()),
        "dense_graph_size_bytes": 26 + 10 * n + 8 * n * words,
    }


def main():
    cases = [
        analyze(
            "involution_master_all_7_types",
            (1, 0, 3, 2, 5, 4, 7, 6, 9, 8),
            ALL_F,
        ),
        analyze(
            "noninvolution_master_6_types",
            (1, 2, 3, 0, 5, 4, 7, 6, 9, 8),
            ALL_F - {(2, 2, 2, 2, 2)},
        ),
    ]
    result = {"schema_version": "six-type-master-inventory-independent-audit-v1", "cases": cases}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
