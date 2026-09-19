#!/usr/bin/env python3
"""Audit exact line-pair labels on the C73 flag incidence."""

from __future__ import annotations

import argparse
import csv
import json
import runpy
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FLAG = runpy.run_path(
    str(ROOT / "repro_runs/2026-08-09_fff_flag_surface_audit/scripts/audit_flag_surface.py")
)
SMALL = runpy.run_path(
    str(ROOT / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py")
)
VIEWS = ("row", "col", "sym")
PAIR_NAMES = ("row_col", "row_sym", "col_sym")
PRIME = 1_000_003


def pair_data(n: int) -> tuple[list[tuple[int, int]], dict[tuple[int, int], int]]:
    pairs = [(low, high) for high in range(n) for low in range(high)]
    return pairs, {pair: index for index, pair in enumerate(pairs)}


def is_latin(table: list[list[int]]) -> bool:
    n = len(table)
    target = list(range(n))
    return all(sorted(row) == target for row in table) and all(
        sorted(table[row][column] for row in range(n)) == target
        for column in range(n)
    )


def pattern(table: list[list[int]]) -> str:
    return "".join(
        "T" if SMALL["has_odd_cycle_view"](table, view) else "F"
        for view in VIEWS
    )


def intercalate_count(table: list[list[int]]) -> int:
    n = len(table)
    total = 0
    for row_a in range(n):
        for row_b in range(row_a):
            for col_a in range(n):
                for col_b in range(col_a):
                    if (
                        table[row_a][col_a] == table[row_b][col_b]
                        and table[row_a][col_b] == table[row_b][col_a]
                    ):
                        total += 1
    return total


def view_cycle_profiles(table: list[list[int]]) -> dict[str, list[tuple[int, ...]]]:
    lines = FLAG["view_lines"](table)
    result = {}
    for view in VIEWS:
        inverses = [FLAG["inverse"](line) for line in lines[view]]
        profiles = []
        for high in range(len(table)):
            for low in range(high):
                permutation = [inverses[low][value] for value in lines[view][high]]
                profiles.append(tuple(sorted(len(cycle) for cycle in FLAG["cycles"](permutation))))
        result[view] = profiles
    return result


def flag_label_triples(table: list[list[int]]) -> list[tuple[int, int, int]]:
    n = len(table)
    _pairs, pair_index = pair_data(n)
    inverses = [FLAG["inverse"](row) for row in table]
    triples = []
    for row in range(n):
        for other_row in range(n):
            if row == other_row:
                continue
            for column in range(n):
                symbol = table[row][column]
                other_column = inverses[other_row][symbol]
                other_symbol = table[row][other_column]
                triples.append(
                    (
                        pair_index[tuple(sorted((row, other_row)))],
                        pair_index[tuple(sorted((column, other_column)))],
                        pair_index[tuple(sorted((symbol, other_symbol)))],
                    )
                )
    return triples


def pair_matrices(
    triples: list[tuple[int, int, int]], m: int
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    raw = [[[0] * m for _ in range(m)] for _ in PAIR_NAMES]
    for row_pair, col_pair, sym_pair in triples:
        raw[0][row_pair][col_pair] += 1
        raw[1][row_pair][sym_pair] += 1
        raw[2][col_pair][sym_pair] += 1
    if any(value % 2 for matrix in raw for row in matrix for value in row):
        raise AssertionError("pair-label flag codegree is not even")
    return raw, [
        [[value // 2 for value in row] for row in matrix] for matrix in raw
    ]


def edge_lift_matrices(table: list[list[int]]) -> list[list[list[int]]]:
    n = len(table)
    pairs, pair_index = pair_data(n)
    m = len(pairs)
    matrices = [[[0] * m for _ in range(m)] for _ in PAIR_NAMES]
    symbol_positions = [[0] * n for _ in range(n)]
    for row in range(n):
        for column, symbol in enumerate(table[row]):
            symbol_positions[symbol][row] = column
    for symbol in range(n):
        matching = symbol_positions[symbol]
        for edge_index, (low, high) in enumerate(pairs):
            image = tuple(sorted((matching[low], matching[high])))
            matrices[0][edge_index][pair_index[image]] += 1
    for column in range(n):
        matching = [table[row][column] for row in range(n)]
        for edge_index, (low, high) in enumerate(pairs):
            image = tuple(sorted((matching[low], matching[high])))
            matrices[1][edge_index][pair_index[image]] += 1
    for row in range(n):
        matching = table[row]
        for edge_index, (low, high) in enumerate(pairs):
            image = tuple(sorted((matching[low], matching[high])))
            matrices[2][edge_index][pair_index[image]] += 1
    return matrices


def weighted_components(
    weights: list[int], pairs: list[tuple[int, int]], n: int
) -> tuple[int, ...]:
    adjacency = [set() for _ in range(n)]
    degrees = [0] * n
    for weight, (low, high) in zip(weights, pairs):
        if weight:
            adjacency[low].add(high)
            adjacency[high].add(low)
            degrees[low] += weight
            degrees[high] += weight
    if any(degree != 2 for degree in degrees):
        raise AssertionError(["weighted_degree", degrees])
    unseen = set(range(n))
    sizes = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        component = []
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(len(component))
    return tuple(sorted(sizes))


def transpose(matrix: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*matrix)]


def block_gram_half(matrices: list[list[list[int]]], n: int) -> list[list[int]]:
    m = len(matrices[0])
    result = [[0] * (3 * m) for _ in range(3 * m)]
    for index in range(3 * m):
        result[index][index] = n
    for left in range(m):
        for right in range(m):
            result[left][m + right] = result[m + right][left] = matrices[0][left][right]
            result[left][2 * m + right] = result[2 * m + right][left] = matrices[1][left][right]
            result[m + left][2 * m + right] = result[2 * m + right][m + left] = matrices[2][left][right]
    return result


def triangle_trace(matrices: list[list[list[int]]]) -> int:
    row_col, row_sym, col_sym = matrices
    m = len(row_col)
    return sum(
        row_col[row_pair][col_pair]
        * col_sym[col_pair][sym_pair]
        * row_sym[row_pair][sym_pair]
        for row_pair in range(m)
        for col_pair in range(m)
        if row_col[row_pair][col_pair]
        for sym_pair in range(m)
        if col_sym[col_pair][sym_pair] and row_sym[row_pair][sym_pair]
    )


def trace_cube_symmetric(matrix: list[list[int]]) -> int:
    size = len(matrix)
    square = [[0] * size for _ in range(size)]
    for row in range(size):
        for middle, left in enumerate(matrix[row]):
            if not left:
                continue
            for column, right in enumerate(matrix[middle]):
                if right:
                    square[row][column] += left * right
    return sum(square[row][column] * matrix[row][column] for row in range(size) for column in range(size))


def coarse_sigma_mod(
    matrices: list[list[list[int]]], n: int, pairs: list[tuple[int, int]], prime: int = PRIME
) -> list[list[int]]:
    """Build the exact C75 pair-label Schur projection over a prime field."""
    m = len(pairs)
    denominator = (5 * n - 9) % prime
    endpoint_coefficient = (-9 * n * pow(denominator, prime - 2, prime)) % prime
    all_one_coefficient = (
        16
        * n
        * pow(((n - 1) * (5 * n - 9)) % prime, prime - 2, prime)
    ) % prime
    cross_all_one = (-4 * pow((n - 1) % prime, prime - 2, prime)) % prime
    endpoint_gram = [
        [len(set(left) & set(right)) for right in pairs]
        for left in pairs
    ]
    result = [[0] * (3 * m) for _ in range(3 * m)]
    for color in range(3):
        offset = color * m
        for row in range(m):
            for column in range(m):
                value = endpoint_coefficient * endpoint_gram[row][column] + all_one_coefficient
                if row == column:
                    value += 2 * n
                result[offset + row][offset + column] = value % prime
    block_positions = ((0, 1, matrices[0]), (0, 2, matrices[1]), (1, 2, matrices[2]))
    for left_color, right_color, matrix in block_positions:
        for row in range(m):
            for column in range(m):
                value = (2 * matrix[row][column] + cross_all_one) % prime
                result[left_color * m + row][right_color * m + column] = value
                result[right_color * m + column][left_color * m + row] = value
    return result


def rank_mod(matrix: list[list[int]], prime: int = PRIME) -> int:
    data = [[value % prime for value in row] for row in matrix]
    rows = len(data)
    columns = len(data[0]) if data else 0
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if data[row][column]), None)
        if pivot is None:
            continue
        data[rank], data[pivot] = data[pivot], data[rank]
        inverse = pow(data[rank][column], prime - 2, prime)
        data[rank] = [(value * inverse) % prime for value in data[rank]]
        for row in range(rank + 1, rows):
            if data[row][column]:
                factor = data[row][column]
                data[row] = [
                    (value - factor * pivot_value) % prime
                    for value, pivot_value in zip(data[row], data[rank])
                ]
        rank += 1
        if rank == rows:
            break
    return rank


def hypergraph_components(triples: list[tuple[int, int, int]], m: int) -> int:
    parent = list(range(3 * m))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for row_pair, col_pair, sym_pair in triples:
        col_pair += m
        sym_pair += 2 * m
        union(row_pair, col_pair)
        union(row_pair, sym_pair)
    return len({find(vertex) for vertex in range(3 * m)})


def analyze_table(
    table: list[list[int]], source: int, rank_control: bool, c70_signature: str | None = None
) -> dict:
    n = len(table)
    pairs, _pair_index = pair_data(n)
    m = len(pairs)
    errors = []
    if not is_latin(table):
        errors.append(["not_latin"])
    triples = flag_label_triples(table)
    if len(triples) != n * n * (n - 1):
        errors.append(["flag_count", len(triples), n * n * (n - 1)])
    raw, matrices = pair_matrices(triples, m)
    lifted_matrices = edge_lift_matrices(table)
    profiles = view_cycle_profiles(table)
    intercalates = intercalate_count(table)
    expected_pairs = (("row", "col"), ("row", "sym"), ("col", "sym"))
    profile_checks = 0
    entry_checks = 0
    edge_lift_checks = 0
    for matrix_index, matrix in enumerate(matrices):
        left_view, right_view = expected_pairs[matrix_index]
        if any(value not in (0, 1, 2) for row in matrix for value in row):
            errors.append(["entry_range", PAIR_NAMES[matrix_index]])
        entry_checks += m * m
        edge_lift_checks += m * m
        if matrix != lifted_matrices[matrix_index]:
            errors.append(["edge_lift_decomposition", PAIR_NAMES[matrix_index]])
        if sum(value for row in matrix for value in row) != n * m:
            errors.append(["entry_sum", PAIR_NAMES[matrix_index]])
        if sum(value == 2 for row in matrix for value in row) != intercalates:
            errors.append(["intercalates", PAIR_NAMES[matrix_index]])
        if sum(value * value for row in matrix for value in row) != n * m + 2 * intercalates:
            errors.append(["frobenius", PAIR_NAMES[matrix_index]])
        for row_index, row in enumerate(matrix):
            try:
                observed = weighted_components(row, pairs, n)
            except AssertionError as error:
                errors.append(["row_two_factor", PAIR_NAMES[matrix_index], row_index, error.args])
                continue
            profile_checks += 1
            if observed != profiles[left_view][row_index]:
                errors.append(["row_profile", PAIR_NAMES[matrix_index], row_index, observed, profiles[left_view][row_index]])
        for col_index, column in enumerate(transpose(matrix)):
            try:
                observed = weighted_components(column, pairs, n)
            except AssertionError as error:
                errors.append(["column_two_factor", PAIR_NAMES[matrix_index], col_index, error.args])
                continue
            profile_checks += 1
            if observed != profiles[right_view][col_index]:
                errors.append(["column_profile", PAIR_NAMES[matrix_index], col_index, observed, profiles[right_view][col_index]])
    indicators = [
        [[int(value == 2) for value in row] for row in matrix]
        for matrix in matrices
    ]
    indicator_row_degrees = [[sum(row) for row in matrix] for matrix in indicators]
    indicator_column_degrees = [
        [sum(column) for column in transpose(matrix)] for matrix in indicators
    ]
    if indicator_row_degrees[0] != indicator_row_degrees[1]:
        errors.append(["intercalate_row_pair_degrees"])
    if indicator_column_degrees[0] != indicator_row_degrees[2]:
        errors.append(["intercalate_col_pair_degrees"])
    if indicator_column_degrees[1] != indicator_column_degrees[2]:
        errors.append(["intercalate_sym_pair_degrees"])
    label_degrees = [[0] * m for _ in VIEWS]
    for triple in triples:
        for view_index, label in enumerate(triple):
            label_degrees[view_index][label] += 1
    if any(degree != 2 * n for degrees in label_degrees for degree in degrees):
        errors.append(["label_degree"])
    for raw_matrix, matrix in zip(raw, matrices):
        if any(raw_matrix[i][j] != 2 * matrix[i][j] for i in range(m) for j in range(m)):
            errors.append(["cross_gram"])
    components = hypergraph_components(triples, m)
    gram = block_gram_half(matrices, n)
    triangle = triangle_trace(matrices)
    edge_lift_triangle = triangle_trace(lifted_matrices)
    if edge_lift_triangle != triangle:
        errors.append(["edge_lift_triangle_trace", edge_lift_triangle, triangle])
    record = {
        "source_index": source,
        "pattern": pattern(table),
        "intercalates": intercalates,
        "triangle_trace": triangle,
        "independent_edge_lift_triangle_trace": edge_lift_triangle,
        "label_hypergraph_components": components,
        "entry_checks": entry_checks,
        "edge_lift_entry_checks": edge_lift_checks,
        "two_factor_profile_checks": profile_checks,
        "errors": errors,
    }
    if c70_signature is not None:
        record["c70_incidence_signature_sha256"] = c70_signature
    if rank_control:
        rank = rank_mod(gram)
        sigma = coarse_sigma_mod(matrices, n, pairs)
        sigma_rank = rank_mod(sigma)
        if sigma_rank != rank - 1:
            errors.append(["coarse_sigma_rank", sigma_rank, rank - 1])
        full_gram = [[2 * value for value in row] for row in gram]
        trace_1 = sum(full_gram[index][index] for index in range(3 * m))
        trace_2 = sum(value * value for row in full_gram for value in row)
        trace_3 = trace_cube_symmetric(full_gram)
        expected_trace_1 = 6 * m * n
        expected_trace_2 = 12 * m * n * (n + 2) + 48 * intercalates
        expected_trace_3 = 8 * (
            3 * m * n**3 + 18 * n * (n * m + 2 * intercalates) + 6 * triangle
        )
        if trace_1 != expected_trace_1:
            errors.append(["gram_trace_1", trace_1, expected_trace_1])
        if trace_2 != expected_trace_2:
            errors.append(["gram_trace_2", trace_2, expected_trace_2])
        if trace_3 != expected_trace_3:
            errors.append(["gram_trace_3", trace_3, expected_trace_3])
        record["block_gram_rank_mod_1000003"] = rank
        record["cycle_space_block_rank_mod_1000003"] = rank - (3 * n - 2)
        record["coarse_sigma_rank_mod_1000003"] = sigma_rank
        record["coarse_sigma_rank_difference"] = rank - sigma_rank
        record["gram_trace_controls"] = {
            "trace_1": trace_1,
            "trace_2": trace_2,
            "trace_3": trace_3,
            "expected_trace_1": expected_trace_1,
            "expected_trace_2": expected_trace_2,
            "expected_trace_3": expected_trace_3,
        }
        record["kernel_lower_bound"] = 2 * components
        record["extra_modular_nullity_beyond_component_constants"] = (
            3 * m - rank - 2 * components
        )
        record["pair_matrix_ranks_mod_1000003"] = [rank_mod(matrix) for matrix in matrices]
    return record


def dataset_summary(name: str, records: list[dict]) -> dict:
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    rank_records = [record for record in records if "block_gram_rank_mod_1000003" in record]
    summary = {
        "name": name,
        "table_count": len(records),
        "pattern_counts": dict(sorted(Counter(record["pattern"] for record in records).items())),
        "intercalate_range": [min(record["intercalates"] for record in records), max(record["intercalates"] for record in records)],
        "triangle_trace_range": [
            min(record["triangle_trace"] for record in records),
            max(record["triangle_trace"] for record in records),
        ],
        "triangle_trace_distinct_count": len({record["triangle_trace"] for record in records}),
        "intercalate_triangle_trace_distinct_count": len(
            {(record["intercalates"], record["triangle_trace"]) for record in records}
        ),
        "label_component_histogram": {
            str(key): value
            for key, value in sorted(Counter(record["label_hypergraph_components"] for record in records).items())
        },
        "entry_checks": sum(record["entry_checks"] for record in records),
        "edge_lift_entry_checks": sum(record["edge_lift_entry_checks"] for record in records),
        "two_factor_profile_checks": sum(record["two_factor_profile_checks"] for record in records),
        "error_count": len(errors),
        "errors": errors[:100],
        "rank_controls": rank_records,
    }
    if records and all("c70_incidence_signature_sha256" in record for record in records):
        joint_groups: dict[tuple[str, int], list[int]] = {}
        for record in records:
            key = (record["c70_incidence_signature_sha256"], record["triangle_trace"])
            joint_groups.setdefault(key, []).append(record["source_index"])
        c70_groups: dict[str, list[dict]] = {}
        for record in records:
            c70_groups.setdefault(record["c70_incidence_signature_sha256"], []).append(record)
        summary["c70_distinct_count"] = len(c70_groups)
        summary["c70_triangle_trace_joint_distinct_count"] = len(joint_groups)
        summary["c70_triangle_trace_collision_groups"] = [
            sources for sources in joint_groups.values() if len(sources) > 1
        ]
        summary["c70_collision_triangle_traces"] = [
            {
                "sources": [record["source_index"] for record in group],
                "triangle_traces": [record["triangle_trace"] for record in group],
            }
            for group in c70_groups.values()
            if len(group) > 1
        ]
        summary["triangle_trace_records"] = [
            {
                "source_index": record["source_index"],
                "intercalates": record["intercalates"],
                "triangle_trace": record["triangle_trace"],
                "c70_incidence_signature_sha256": record["c70_incidence_signature_sha256"],
            }
            for record in records
        ]
    return summary


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), FLAG["parse_compact"](row["square"], 8)


def write_summary(payload: dict, path: Path) -> None:
    lines = [
        "Labelled flag-incidence audit",
        "",
        f"audit version: {payload['audit_version']}",
        f"total tables: {payload['totals']['tables']}",
        f"total flag-label triples: {payload['totals']['flag_label_triples']}",
        f"pair-matrix entry checks: {payload['totals']['entry_checks']}",
        f"independent edge-lift entry checks: {payload['totals']['edge_lift_entry_checks']}",
        f"two-factor profile checks: {payload['totals']['two_factor_profile_checks']}",
        f"errors: {payload['totals']['errors']}",
        "",
    ]
    for name, data in payload["datasets"].items():
        lines.extend(
            [
                name,
                f"- tables: {data['table_count']}",
                f"- patterns: {data['pattern_counts']}",
                f"- intercalate range: {data['intercalate_range']}",
                f"- triangle-trace range: {data['triangle_trace_range']}",
                f"- distinct triangle traces: {data['triangle_trace_distinct_count']}",
                f"- distinct (intercalates, triangle trace): {data['intercalate_triangle_trace_distinct_count']}",
                f"- label-hypergraph components: {data['label_component_histogram']}",
                f"- pair-matrix entries checked: {data['entry_checks']}",
                f"- independent edge-lift entries checked: {data['edge_lift_entry_checks']}",
                f"- two-factor profiles checked: {data['two_factor_profile_checks']}",
                f"- errors: {data['error_count']}",
                f"- modular rank controls: {len(data['rank_controls'])}",
                "",
            ]
        )
        if "c70_triangle_trace_joint_distinct_count" in data:
            lines.extend(
                [
                    f"- C70 distinct signatures: {data['c70_distinct_count']}",
                    f"- distinct (C70, triangle trace): {data['c70_triangle_trace_joint_distinct_count']}",
                    f"- remaining (C70, triangle trace) collisions: {data['c70_triangle_trace_collision_groups']}",
                    f"- old C70 collision triangle traces: {data['c70_collision_triangle_traces']}",
                    "",
                ]
            )
    lines.extend(
        [
            "Evidence boundary:",
            "- The matrix identities and two-factor formulation are rigorous.",
            "- The cycle-space reduction and coarse-C75 Schur collapse are rigorous.",
            "- The triangle trace is a rigorous main-class invariant; its order-8 separation count is exactly computed.",
            "- Prime-field ranks are exact only over GF(1000003) and are secondary diagnostics.",
            "- The audit does not construct or exclude an order-10 FFF Latin square.",
            "- C38 remains open and C40 remains absent.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n6-generator", type=Path, required=True)
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--flag-audit", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    datasets = {}
    n4_records = [
        analyze_table(table, source, True)
        for source, table in enumerate(SMALL["reduced_latin_squares"](4), start=1)
    ]
    datasets["order4_complete"] = dataset_summary("order4_complete", n4_records)

    n6_records = []
    rank_patterns = Counter()
    for source, table in enumerate(SMALL["reduced_latin_squares"](6), start=1):
        table_pattern = pattern(table)
        rank_control = rank_patterns[table_pattern] < 2
        rank_patterns[table_pattern] += int(rank_control)
        n6_records.append(analyze_table(table, source, rank_control))
    datasets["order6_complete"] = dataset_summary("order6_complete", n6_records)

    flag_payload = json.loads(args.flag_audit.read_text())
    c70_by_source = {
        int(record["source_index"]): record["c70_incidence_signature_sha256"]
        for record in flag_payload["order8_fff_records"]
    }
    n8_records = [
        analyze_table(table, source, index < 10, c70_by_source[source])
        for index, (source, table) in enumerate(load_n8(args.fff_metadata))
    ]
    datasets["order8_fff_complete"] = dataset_summary("order8_fff_complete", n8_records)

    n10_records = [
        analyze_table(table, source, source <= 5)
        for source, table, _metadata in FLAG["n10_tables"](args.n10_corpus)
    ]
    datasets["order10_tracked_partial"] = dataset_summary("order10_tracked_partial", n10_records)

    all_data = list(datasets.values())
    payload = {
        "audit_version": "labelled_flag_incidence_v2",
        "prime": PRIME,
        "datasets": datasets,
        "totals": {
            "tables": sum(data["table_count"] for data in all_data),
            "flag_label_triples": 4 * 4 * 4 * 3 + 9408 * 6 * 6 * 5 + 230 * 8 * 8 * 7 + 135 * 10 * 10 * 9,
            "entry_checks": sum(data["entry_checks"] for data in all_data),
            "edge_lift_entry_checks": sum(data["edge_lift_entry_checks"] for data in all_data),
            "two_factor_profile_checks": sum(data["two_factor_profile_checks"] for data in all_data),
            "errors": sum(data["error_count"] for data in all_data),
        },
        "claim_boundary": [
            "C76 identities are rigorous and this audit is exact sanity evidence.",
            "C77 is an exact classifier only on the frozen 230-class order-8 FFF census.",
            "The labelled pair matrices are necessary but not sufficient for Latin realizability.",
            "No order-10 FFF table or complete exclusion is claimed.",
            "C38 remains open and C40 remains absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(payload, args.summary)
    return int(payload["totals"]["errors"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
