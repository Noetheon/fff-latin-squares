#!/usr/bin/env python3
"""Audit C70 cell-local cycle incidences on complete n=6/n=8 data."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import runpy
import time
from collections import Counter
from itertools import permutations
from pathlib import Path
from typing import Iterable


VIEWS = ("row", "col", "sym")
VIEW_PAIRS = (("row", "col"), ("row", "sym"), ("col", "sym"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_table(table: list[list[int]]) -> str:
    return "".join(str(value) for row in table for value in row)


def parse_compact(compact: str, n: int) -> list[list[int]]:
    if len(compact) != n * n:
        raise ValueError(f"expected {n*n} digits, found {len(compact)}")
    return [
        [int(value) for value in compact[n * row : n * (row + 1)]]
        for row in range(n)
    ]


def validate_latin(table: list[list[int]]) -> bool:
    n = len(table)
    target = list(range(n))
    return all(sorted(row) == target for row in table) and all(
        sorted(table[row][column] for row in range(n)) == target
        for column in range(n)
    )


def inverse(permutation: list[int]) -> list[int]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return result


def view_lines(table: list[list[int]]) -> dict[str, list[list[int]]]:
    n = len(table)
    symbol_lines = [[0] * n for _ in range(n)]
    for row, entries in enumerate(table):
        for column, symbol in enumerate(entries):
            symbol_lines[symbol][column] = row
    return {
        "row": table,
        "col": [[table[row][column] for row in range(n)] for column in range(n)],
        "sym": symbol_lines,
    }


def cycles_with_support(permutation: list[int]) -> list[tuple[int, tuple[int, ...]]]:
    seen = [False] * len(permutation)
    result = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        support = []
        point = start
        while not seen[point]:
            seen[point] = True
            support.append(point)
            point = permutation[point]
        result.append((len(support), tuple(support)))
    return result


def add_cycle_to_cells(
    local: dict[str, list[list[list[int]]]],
    view: str,
    first: int,
    second: int,
    length: int,
    support: tuple[int, ...],
    lines: dict[str, list[list[int]]],
) -> None:
    if view == "row":
        for column in support:
            local[view][first][column][length] += 1
            local[view][second][column][length] += 1
    elif view == "col":
        for row in support:
            local[view][row][first][length] += 1
            local[view][row][second][length] += 1
    else:
        for column in support:
            local[view][lines[view][first][column]][column][length] += 1
            local[view][lines[view][second][column]][column][length] += 1


def table_incidence(table: list[list[int]], tensor_patterns: set[str]) -> dict:
    if not validate_latin(table):
        raise ValueError("input is not Latin")
    n = len(table)
    lines = view_lines(table)
    local = {
        view: [[[0] * (n + 1) for _ in range(n)] for _ in range(n)]
        for view in VIEWS
    }
    cycle_counts = {view: [0] * (n + 1) for view in VIEWS}
    failed_pairs = {view: 0 for view in VIEWS}
    negative_edges = {view: [] for view in VIEWS}
    sign_class_sizes = {}
    sign_cut_errors = []

    for view in VIEWS:
        inverses = [inverse(line) for line in lines[view]]
        line_signs = []
        for line in lines[view]:
            cycle_count = len(cycles_with_support(line))
            line_signs.append(-1 if (n - cycle_count) % 2 else 1)
        negative_line_count = sum(sign < 0 for sign in line_signs)
        sign_class_sizes[view] = min(negative_line_count, n - negative_line_count)
        for first in range(n):
            for second in range(first):
                permutation = [
                    inverses[second][value] for value in lines[view][first]
                ]
                cycles = cycles_with_support(permutation)
                if any(length % 2 for length, _ in cycles):
                    failed_pairs[view] += 1
                induced_sign = -1 if (n - len(cycles)) % 2 else 1
                expected_sign = line_signs[first] * line_signs[second]
                if induced_sign != expected_sign:
                    sign_cut_errors.append([view, first, second])
                if induced_sign < 0:
                    negative_edges[view].append([second, first])
                for length, support in cycles:
                    cycle_counts[view][length] += 1
                    add_cycle_to_cells(
                        local, view, first, second, length, support, lines
                    )

    pattern = "".join(
        "T" if failed_pairs[view] else "F" for view in VIEWS
    )
    include_tensors = pattern in tensor_patterns
    identity_errors = []
    local_histogram: Counter[str] = Counter()
    a2_histogram: Counter[int] = Counter()
    for row in range(n):
        for column in range(n):
            profiles = {
                view: tuple(local[view][row][column][2:]) for view in VIEWS
            }
            for view, profile in profiles.items():
                if sum(profile) != n - 1:
                    identity_errors.append(["partition", row, column, view])
            a2 = [local[view][row][column][2] for view in VIEWS]
            if len(set(a2)) != 1:
                identity_errors.append(["intercalate", row, column, a2])
            a2_histogram[a2[0]] += 1
            if include_tensors:
                key = "|".join(
                    ",".join(map(str, profiles[view])) for view in VIEWS
                )
                local_histogram[key] += 1

    marginal_errors = []
    for view in VIEWS:
        for length in range(2, n + 1):
            observed = sum(
                local[view][row][column][length]
                for row in range(n)
                for column in range(n)
            )
            expected = 2 * length * cycle_counts[view][length]
            if observed != expected:
                marginal_errors.append([view, length, observed, expected])

    pair_tensors = {}
    triple_tensor = []
    incidence_signature = None
    if include_tensors:
        for left, right in VIEW_PAIRS:
            tensor = []
            for first_length in range(2, n + 1):
                for second_length in range(2, n + 1):
                    tensor.append(
                        sum(
                            local[left][row][column][first_length]
                            * local[right][row][column][second_length]
                            for row in range(n)
                            for column in range(n)
                        )
                    )
            pair_tensors[f"{left}_{right}"] = tensor

        for row_length in range(2, n + 1):
            for col_length in range(2, n + 1):
                for sym_length in range(2, n + 1):
                    triple_tensor.append(
                        sum(
                            local["row"][row][column][row_length]
                            * local["col"][row][column][col_length]
                            * local["sym"][row][column][sym_length]
                            for row in range(n)
                            for column in range(n)
                        )
                    )
        canonical_forms = []
        for axis_order in permutations(range(3)):
            transformed = []
            for key, count in local_histogram.items():
                profiles = key.split("|")
                transformed.append(
                    ("|".join(profiles[index] for index in axis_order), count)
                )
            canonical_forms.append(sorted(transformed))
        canonical_payload = min(canonical_forms)
        canonical_bytes = json.dumps(
            canonical_payload, separators=(",", ":")
        ).encode("ascii")
        incidence_signature = sha256_bytes(canonical_bytes)
    return {
        "pattern": pattern,
        "failed_pair_counts": failed_pairs,
        "cycle_counts": {view: values[2:] for view, values in cycle_counts.items()},
        "negative_edge_counts": {
            view: len(edges) for view, edges in negative_edges.items()
        },
        "sign_class_sizes": sign_class_sizes,
        "sign_cut_errors": sign_cut_errors,
        "identity_errors": identity_errors,
        "marginal_errors": marginal_errors,
        "a2_histogram": {str(key): value for key, value in sorted(a2_histogram.items())},
        "local_histogram": dict(sorted(local_histogram.items())),
        "pair_tensors": pair_tensors,
        "triple_tensor": triple_tensor,
        "incidence_signature_sha256": incidence_signature,
    }


def analyze_dataset(
    name: str,
    tables: Iterable[list[list[int]]],
    expected_count: int,
    keep_patterns: set[str],
) -> dict:
    started = time.perf_counter()
    pattern_counts: Counter[str] = Counter()
    a2_histogram_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    sign_class_profile_counts: Counter[str] = Counter()
    pan_hamiltonian_view_count = 0
    kept_table_summaries = []
    detailed_examples = []
    detailed_per_pattern: Counter[str] = Counter()
    kept_count = 0
    total_identity_errors = 0
    total_sign_cut_errors = 0
    for index, table in enumerate(tables, start=1):
        result = table_incidence(table, keep_patterns)
        pattern = result["pattern"]
        pattern_counts[pattern] += 1
        total_identity_errors += len(result["identity_errors"]) + len(
            result["marginal_errors"]
        )
        total_sign_cut_errors += len(result["sign_cut_errors"])
        for view in VIEWS:
            cycles = result["cycle_counts"][view]
            if cycles[-1] == len(table) * (len(table) - 1) // 2 and sum(cycles[:-1]) == 0:
                pan_hamiltonian_view_count += 1
        if pattern in keep_patterns:
            kept_count += 1
            a2_key = json.dumps(result["a2_histogram"], sort_keys=True)
            a2_histogram_counts[a2_key] += 1
            signature_counts[result["incidence_signature_sha256"]] += 1
            sign_key = ",".join(
                map(str, sorted(result["sign_class_sizes"].values()))
            )
            sign_class_profile_counts[sign_key] += 1
            kept_table_summaries.append(
                {
                    "source_index": index,
                    "compact_table": compact_table(table),
                    "pattern": pattern,
                    "failed_pair_counts": result["failed_pair_counts"],
                    "cycle_counts": result["cycle_counts"],
                    "sign_class_sizes": result["sign_class_sizes"],
                    "a2_histogram": result["a2_histogram"],
                    "incidence_signature_sha256": result[
                        "incidence_signature_sha256"
                    ],
                }
            )
            if detailed_per_pattern[pattern] < 3:
                detailed_examples.append(
                    {
                        "source_index": index,
                        "compact_table": compact_table(table),
                        **result,
                    }
                )
                detailed_per_pattern[pattern] += 1
    if index != expected_count:
        raise RuntimeError(f"{name}: expected {expected_count}, found {index}")
    return {
        "name": name,
        "table_count": index,
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "identity_error_count": total_identity_errors,
        "sign_cut_error_count": total_sign_cut_errors,
        "pan_hamiltonian_view_count": pan_hamiltonian_view_count,
        "kept_patterns": sorted(keep_patterns),
        "kept_table_count": kept_count,
        "distinct_incidence_signatures": len(signature_counts),
        "incidence_signature_counts": dict(sorted(signature_counts.items())),
        "a2_histogram_counts": dict(sorted(a2_histogram_counts.items())),
        "sign_class_profile_counts": dict(sorted(sign_class_profile_counts.items())),
        "kept_table_summaries": kept_table_summaries,
        "detailed_examples": detailed_examples,
        "elapsed_seconds": time.perf_counter() - started,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n6-generator", type=Path, required=True)
    parser.add_argument("--n8-census", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--n8-limit", type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    generator = runpy.run_path(str(args.n6_generator))
    n6 = analyze_dataset(
        "all reduced order-6 Latin squares",
        generator["reduced_latin_squares"](6),
        9408,
        {"FFT", "FTF", "TFF"},
    )

    def n8_tables():
        with gzip.open(args.n8_census, "rt", encoding="ascii") as handle:
            for index, line in enumerate(handle, start=1):
                if args.n8_limit is not None and index > args.n8_limit:
                    break
                compact = line.strip()
                if compact:
                    yield parse_compact(compact, 8)

    n8_expected = args.n8_limit if args.n8_limit is not None else 283657
    n8 = analyze_dataset(
        "ANU order-8 main-class representatives",
        n8_tables(),
        n8_expected,
        {"FFF"},
    )

    corpus = json.loads(args.n10_corpus.read_text())
    compacts = sorted(corpus["tracked_order10_source_paths"])
    n10 = analyze_dataset(
        "tracked distinct order-10 Latin tables",
        (parse_compact(compact, 10) for compact in compacts),
        len(compacts),
        {"FFF", "FFT", "FTF", "TFF"},
    )

    payload = {
        "run_id": "2026-08-09_fff_cell_local_incidence_census",
        "scope": "C70 cell-local incidence and C71 sign-cut audit",
        "inputs": {
            "n6_generator": str(args.n6_generator),
            "n8_census": str(args.n8_census),
            "n10_corpus": str(args.n10_corpus),
        },
        "orders": {"6": n6, "8": n8, "10_tracked": n10},
        "claim_effect": {
            "C38": "open",
            "C40": "absent",
            "order10_decided": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "FFF cell-local cycle-incidence census",
        "",
        "Exact audits:",
        f"- n=6: {n6['table_count']} tables, patterns={n6['pattern_counts']}, identity_errors={n6['identity_error_count']}, sign_cut_errors={n6['sign_cut_error_count']}.",
        f"- n=8: {n8['table_count']} tables, patterns={n8['pattern_counts']}, FFF={n8['kept_table_count']}, distinct_FFF_incidence_signatures={n8['distinct_incidence_signatures']}, identity_errors={n8['identity_error_count']}, sign_cut_errors={n8['sign_cut_error_count']}.",
        f"- tracked n=10: {n10['table_count']} tables, patterns={n10['pattern_counts']}, kept={n10['kept_table_count']}, distinct_kept_incidence_signatures={n10['distinct_incidence_signatures']}, identity_errors={n10['identity_error_count']}, sign_cut_errors={n10['sign_cut_error_count']}.",
        "",
        "Conservative conclusion:",
        "- C70 identities and the full line-pair sign cut hold on every scanned table.",
        "- Finite incidence-signature variation is census evidence, not an order-10 theorem.",
        "- C38 remains open and C40 remains absent.",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    if any(
        dataset["identity_error_count"] or dataset["sign_cut_error_count"]
        for dataset in (n6, n8, n10)
    ):
        raise SystemExit("incidence or sign-cut audit failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
