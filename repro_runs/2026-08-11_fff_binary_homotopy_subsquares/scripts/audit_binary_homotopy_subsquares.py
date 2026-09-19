#!/usr/bin/env python3
"""Audit the F2 line-kernel / half-order-subsquare correspondence."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
VIEWS = ("row", "col", "sym")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SMALL = load_module(
    "binary_homotopy_small",
    ROOT / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_sha256(table) -> str:
    payload = ";".join(",".join(map(str, row)) for row in table).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_compact(compact: str, n: int):
    if len(compact) != n * n:
        raise ValueError((n, len(compact)))
    return tuple(tuple(int(value) for value in compact[r * n : (r + 1) * n]) for r in range(n))


def validate_latin(table) -> bool:
    n = len(table)
    expected = list(range(n))
    return all(sorted(row) == expected for row in table) and all(
        sorted(table[r][c] for r in range(n)) == expected for c in range(n)
    )


def view_lines(table, view: str):
    n = len(table)
    if view == "row":
        return table
    if view == "col":
        return tuple(tuple(table[r][c] for r in range(n)) for c in range(n))
    return tuple(
        tuple(next(r for r in range(n) if table[r][c] == s) for c in range(n))
        for s in range(n)
    )


def view_has_odd_cycle(lines) -> bool:
    n = len(lines)
    inverses = []
    for line in lines:
        inverse = [0] * n
        for index, value in enumerate(line):
            inverse[value] = index
        inverses.append(inverse)
    for first, second in combinations(range(n), 2):
        permutation = [inverses[second][value] for value in lines[first]]
        seen = [False] * n
        for start in range(n):
            if seen[start]:
                continue
            cursor = start
            length = 0
            while not seen[cursor]:
                seen[cursor] = True
                cursor = permutation[cursor]
                length += 1
            if length > 1 and length % 2:
                return True
    return False


def pattern(table) -> str:
    return "".join("T" if view_has_odd_cycle(view_lines(table, view)) else "F" for view in VIEWS)


def rref_masks(rows, width: int):
    matrix = [int(row) for row in rows if row]
    rank = 0
    pivots = []
    for column in range(width):
        pivot = next((i for i in range(rank, len(matrix)) if (matrix[i] >> column) & 1), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        for i in range(len(matrix)):
            if i != rank and ((matrix[i] >> column) & 1):
                matrix[i] ^= matrix[rank]
        pivots.append(column)
        rank += 1
        if rank == len(matrix):
            break
    return matrix[:rank], pivots


def nullspace_basis(rows, width: int):
    reduced, pivots = rref_masks(rows, width)
    pivot_set = set(pivots)
    basis = []
    for free in (column for column in range(width) if column not in pivot_set):
        vector = 1 << free
        for row, pivot in zip(reduced, pivots):
            if (row >> free) & 1:
                vector |= 1 << pivot
        basis.append(vector)
    return basis


def span(basis):
    values = [0]
    for vector in basis:
        values += [value ^ vector for value in values]
    return values


def line_equations(table):
    n = len(table)
    return [
        (1 << r) | (1 << (n + c)) | (1 << (2 * n + table[r][c]))
        for r in range(n)
        for c in range(n)
    ]


def universal_constant_space(n: int):
    rows = sum(1 << index for index in range(n))
    cols = sum(1 << (n + index) for index in range(n))
    syms = sum(1 << (2 * n + index) for index in range(n))
    return (0, rows ^ cols, rows ^ syms, cols ^ syms)


def fibres(vector: int, offset: int, n: int):
    return tuple(
        tuple(index for index in range(n) if ((vector >> (offset + index)) & 1) == bit)
        for bit in (0, 1)
    )


def predicted_subsquares(table, kernel_basis):
    n = len(table)
    if n % 2:
        return set(), 0
    constants = universal_constant_space(n)
    classes = {min(value ^ constant for constant in constants) for value in span(kernel_basis)}
    classes.discard(0)
    found = set()
    for representative in classes:
        row_fibres = fibres(representative, 0, n)
        col_fibres = fibres(representative, n, n)
        sym_fibres = fibres(representative, 2 * n, n)
        if len({len(part) for part in (*row_fibres, *col_fibres, *sym_fibres)}) != 1:
            raise AssertionError("nontrivial kernel class is not balanced")
        for x in (0, 1):
            for y in (0, 1):
                found.add((row_fibres[x], col_fibres[y], sym_fibres[x ^ y]))
    return found, len(classes)


def direct_half_subsquares(table):
    n = len(table)
    if n % 2:
        return set()
    m = n // 2
    found = set()
    for rows in combinations(range(n), m):
        for cols in combinations(range(n), m):
            symbols = tuple(sorted({table[r][c] for r in rows for c in cols}))
            if len(symbols) == m:
                found.add((rows, cols, symbols))
    return found


def analyze_task(task):
    dataset, source_index, table = task
    table = tuple(tuple(row) for row in table)
    n = len(table)
    errors = []
    if not validate_latin(table):
        errors.append("not_latin")
    equations = line_equations(table)
    reduced, pivots = rref_masks(equations, 3 * n)
    kernel_basis = nullspace_basis(equations, 3 * n)
    line_rank = len(pivots)
    delta = len(kernel_basis) - 2
    predicted, quotient_nonzero_count = predicted_subsquares(table, kernel_basis)
    direct = direct_half_subsquares(table)
    expected_count = 4 * ((1 << delta) - 1)
    if predicted != direct:
        errors.append(
            {
                "set_mismatch": {
                    "predicted_only": [list(map(list, item)) for item in sorted(predicted - direct)[:5]],
                    "direct_only": [list(map(list, item)) for item in sorted(direct - predicted)[:5]],
                }
            }
        )
    if len(direct) != expected_count:
        errors.append({"count_formula": [len(direct), expected_count]})
    if quotient_nonzero_count != (1 << delta) - 1:
        errors.append({"quotient_count": [quotient_nonzero_count, (1 << delta) - 1]})
    pat = pattern(table)
    if n % 4 == 2 and n > 2 and pat == "FFF" and delta != 0:
        errors.append({"fff_rank_corollary": delta})
    return {
        "dataset": dataset,
        "source_index": source_index,
        "order": n,
        "table_sha256": table_sha256(table),
        "pattern": pat,
        "line_rank_mod2": line_rank,
        "left_kernel_dimension": len(kernel_basis),
        "delta_2": delta,
        "quotient_nonzero_class_count": quotient_nonzero_count,
        "direct_half_order_subsquare_count": len(direct),
        "predicted_half_order_subsquare_count": len(predicted),
        "formula_half_order_subsquare_count": expected_count,
        "set_match": predicted == direct,
        "error_count": len(errors),
        "errors": errors,
    }


def count_map(values):
    return {str(key): value for key, value in sorted(Counter(values).items())}


def load_tasks(args):
    tasks = []
    for n in (2, 4, 6):
        tasks.extend(
            (f"order{n}_reduced_complete", index, table)
            for index, table in enumerate(SMALL.reduced_latin_squares(n), 1)
        )
    with args.fff_metadata.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            tasks.append(("order8_fff_complete", int(row["line_number"]), parse_compact(row["square"], 8)))
    corpus = json.loads(args.n10_corpus.read_text())
    for index, compact in enumerate(sorted(corpus["tracked_order10_source_paths"]), 1):
        tasks.append(("order10_tracked_partial", index, parse_compact(compact, 10)))
    return tasks


def summarize_dataset(records):
    return {
        "table_count": len(records),
        "unique_table_count": len({record["table_sha256"] for record in records}),
        "pattern_distribution": count_map(record["pattern"] for record in records),
        "line_rank_mod2_distribution": count_map(record["line_rank_mod2"] for record in records),
        "delta_2_distribution": count_map(record["delta_2"] for record in records),
        "half_order_subsquare_count_distribution": count_map(
            record["direct_half_order_subsquare_count"] for record in records
        ),
        "set_match_count": sum(record["set_match"] for record in records),
        "error_count": sum(record["error_count"] for record in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    tasks = load_tasks(args)
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=8))
    records.sort(key=lambda record: (record["order"], record["dataset"], record["source_index"]))
    datasets = {
        dataset: summarize_dataset([record for record in records if record["dataset"] == dataset])
        for dataset in sorted({record["dataset"] for record in records})
    }
    elapsed_seconds = time.perf_counter() - started
    totals = {
        "table_count": len(records),
        "set_match_count": sum(record["set_match"] for record in records),
        "error_count": sum(record["error_count"] for record in records),
    }
    payload = {
        "audit_version": "binary_homotopy_subsquares_v1",
        "theorem": "h(L)=4*(2^delta_2(L)-1), delta_2=(3n-2)-rank_F2(N_L)",
        "workers": args.workers,
        "inputs": {
            "fff_metadata": {"path": str(args.fff_metadata), "sha256": sha256_file(args.fff_metadata)},
            "n10_corpus": {"path": str(args.n10_corpus), "sha256": sha256_file(args.n10_corpus)},
            "small_order_generator": {
                "path": str(Path(SMALL.__file__)),
                "sha256": sha256_file(Path(SMALL.__file__)),
            },
        },
        "datasets": datasets,
        "totals": totals,
        "records": records,
        "claim_boundary": [
            "The correspondence theorem is proved independently of the finite audit.",
            "The order-8 dataset is the complete frozen FFF representative corpus.",
            "The order-10 dataset is partial, contains no FFF table, and does not decide C38.",
        ],
        "overall_ok": totals["error_count"] == 0 and totals["set_match_count"] == totals["table_count"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        "Binary line-kernel / half-order-subsquare audit",
        "",
        f"overall_ok: {payload['overall_ok']}",
        f"workers: {args.workers}",
        f"tables: {totals['table_count']}",
        f"exact set matches: {totals['set_match_count']}",
        f"errors: {totals['error_count']}",
        f"elapsed seconds: {elapsed_seconds:.6f}",
        "",
    ]
    for dataset, summary in datasets.items():
        lines.extend(
            [
                f"{dataset}:",
                f"- tables: {summary['table_count']}",
                f"- patterns: {summary['pattern_distribution']}",
                f"- line ranks mod 2: {summary['line_rank_mod2_distribution']}",
                f"- delta_2: {summary['delta_2_distribution']}",
                f"- half-order subsquares: {summary['half_order_subsquare_count_distribution']}",
                f"- set matches/errors: {summary['set_match_count']}/{summary['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C38 remains open and C40 is absent.",
            "- The tracked order-10 corpus is diagnostic only.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
