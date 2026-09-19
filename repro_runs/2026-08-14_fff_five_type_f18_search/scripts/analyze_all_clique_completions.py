#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path


EXPECTED_PALETTE = {
    (2, 2, 2, 2, 2), (4, 2, 2, 2), (4, 4, 2), (6, 4), (8, 2),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cycle_type(permutation: list[int]) -> tuple[int, ...]:
    seen = [False] * len(permutation)
    lengths = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        current = start
        length = 0
        while not seen[current]:
            seen[current] = True
            current = permutation[current]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def is_f(permutation: list[int]) -> bool:
    return all(length % 2 == 0 for length in cycle_type(permutation))


def inverse(permutation: list[int]) -> list[int]:
    result = [0] * len(permutation)
    for point, image in enumerate(permutation):
        result[image] = point
    return result


def row_relative(left: list[int], right: list[int]) -> list[int]:
    left_inverse = inverse(left)
    return [right[left_inverse[point]] for point in range(len(left))]


def table_pattern(table: list[list[int]]) -> str:
    n = len(table)
    row_f = all(
        is_f(row_relative(table[left], table[right]))
        for left in range(n) for right in range(left + 1, n)
    )
    col_f = True
    for left in range(n):
        for right in range(left + 1, n):
            permutation = [-1] * n
            for row in table:
                permutation[row[left]] = row[right]
            col_f &= is_f(permutation)
    sym_f = True
    positions = [[0] * n for _ in range(n)]
    for row_index, row in enumerate(table):
        for col, symbol in enumerate(row):
            positions[row_index][symbol] = col
    for left in range(n):
        for right in range(left + 1, n):
            permutation = [-1] * n
            for row_index in range(n):
                permutation[positions[row_index][left]] = positions[row_index][right]
            sym_f &= is_f(permutation)
    return "".join("F" if value else "T" for value in (row_f, col_f, sym_f))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--cliques", type=Path, required=True)
    parser.add_argument("--cliquer-stderr", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    with args.graph.open("rb") as handle:
        magic = handle.read(8)
        vertex_count, words = struct.unpack("<II", handle.read(8))
        root = list(handle.read(10))
        vertices = [list(handle.read(10)) for _ in range(vertex_count)]
    expected_size = 26 + vertex_count * 10 + vertex_count * words * 8
    graph_envelope_valid = (
        magic == b"O8HTv1\0\0"
        and words == (vertex_count + 63) // 64
        and args.graph.stat().st_size == expected_size
    )

    line_pattern = re.compile(r"^size=8, weight=8:\s+((?:\d+\s*){8})$")
    parsed = []
    malformed = 0
    for line in args.cliques.read_text().splitlines():
        match = line_pattern.fullmatch(line.strip())
        if not match:
            malformed += 1
            continue
        parsed.append(tuple(sorted(int(value) - 1 for value in match.group(1).split())))

    unique = sorted(set(parsed))
    pattern_counts = Counter()
    palette_counts = Counter()
    exact_palette_count = 0
    palette_subset_errors = 0
    latin_errors = 0
    bucket_errors = 0
    vertex_errors = 0
    examples = {}
    identity = list(range(10))
    for clique in unique:
        if len(clique) != 8 or any(vertex < 0 or vertex >= vertex_count for vertex in clique):
            vertex_errors += 1
            continue
        rows = [identity, root, *(vertices[vertex] for vertex in clique)]
        buckets = sorted(row[0] - 2 for row in rows[2:])
        if buckets != list(range(8)):
            bucket_errors += 1
        latin = (
            all(sorted(row) == identity for row in rows)
            and all(sorted(rows[row][col] for row in range(10)) == identity for col in range(10))
        )
        if not latin:
            latin_errors += 1
            continue
        palette = {
            cycle_type(row_relative(rows[left], rows[right]))
            for left in range(10) for right in range(left + 1, 10)
        }
        palette_subset_errors += not palette <= EXPECTED_PALETTE
        exact_palette_count += palette == EXPECTED_PALETTE
        palette_key = "|".join(
            "+".join(map(str, cycle_type_value))
            for cycle_type_value in sorted(palette, reverse=True)
        )
        palette_counts[palette_key] += 1
        pattern = table_pattern(rows)
        pattern_counts[pattern] += 1
        examples.setdefault(pattern, [vertex + 1 for vertex in clique])

    fff_count = pattern_counts.get("FFF", 0)
    checks = {
        "graph_envelope_valid": graph_envelope_valid,
        "all_lines_parsed": malformed == 0,
        "enumeration_count_exact": len(parsed) == args.expected_count,
        "cliques_unique": len(unique) == len(parsed),
        "vertices_valid": vertex_errors == 0,
        "one_vertex_per_bucket": bucket_errors == 0,
        "all_tables_latin": latin_errors == 0,
        "all_row_palettes_subsets_of_f18": palette_subset_errors == 0,
        "no_exact_f18_row_palette": exact_palette_count == 0,
        "no_fff_completion": fff_count == 0,
    }
    result = {
        "schema_version": "f18-all-clique-completion-audit-v1",
        "graph_sha256": sha256(args.graph),
        "clique_stdout_sha256": sha256(args.cliques),
        "cliquer_stderr_sha256": sha256(args.cliquer_stderr),
        "expected_clique_count": args.expected_count,
        "parsed_clique_count": len(parsed),
        "unique_clique_count": len(unique),
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "row_palette_counts": dict(sorted(palette_counts.items())),
        "exact_f18_palette_count": exact_palette_count,
        "fff_count": fff_count,
        "pattern_examples_one_based_vertices": examples,
        "error_counts": {
            "malformed_lines": malformed,
            "vertex_errors": vertex_errors,
            "bucket_errors": bucket_errors,
            "latin_errors": latin_errors,
            "palette_subset_errors": palette_subset_errors,
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Independent f18 all-clique completion audit", "",
        f"parsed/unique 8-cliques: {len(parsed)}/{len(unique)}",
        f"Latin tables: {len(unique) - latin_errors}",
        f"exact f18 row palettes: {exact_palette_count}",
        f"row palette counts: {dict(sorted(palette_counts.items()))}",
        f"pattern counts: {dict(sorted(pattern_counts.items()))}",
        f"FFF completions: {fff_count}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"all-clique completion audit failed: {failed}")


if __name__ == "__main__":
    main()
