#!/usr/bin/env python3
"""Audit prime-field line dependencies and their cyclic quotient fibres."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]
PRIMES = (2, 3, 5, 7, 11)
VIEWS = ("row", "col", "sym")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SMALL = load_module(
    "prime_field_small",
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
    return tuple(tuple(int(x) for x in compact[r * n : (r + 1) * n]) for r in range(n))


def validate_latin(table) -> bool:
    n = len(table)
    target = list(range(n))
    return all(sorted(row) == target for row in table) and all(
        sorted(table[r][c] for r in range(n)) == target for c in range(n)
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


def has_odd_cycle(lines) -> bool:
    n = len(lines)
    inverses = []
    for line in lines:
        inverse = [0] * n
        for i, value in enumerate(line):
            inverse[value] = i
        inverses.append(inverse)
    for first in range(n):
        for second in range(first + 1, n):
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
                if length % 2:
                    return True
    return False


def pattern(table) -> str:
    return "".join("T" if has_odd_cycle(view_lines(table, view)) else "F" for view in VIEWS)


def equations(table):
    n = len(table)
    rows = []
    for r in range(n):
        for c in range(n):
            row = [0] * (3 * n)
            row[r] = row[n + c] = row[2 * n + table[r][c]] = 1
            rows.append(row)
    return rows


def rref_mod(rows, width: int, prime: int):
    matrix = [[value % prime for value in row] for row in rows]
    rank = 0
    pivots = []
    for column in range(width):
        pivot = next((i for i in range(rank, len(matrix)) if matrix[i][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inverse = pow(matrix[rank][column], -1, prime)
        matrix[rank] = [(value * inverse) % prime for value in matrix[rank]]
        for i in range(len(matrix)):
            if i == rank or not matrix[i][column]:
                continue
            factor = matrix[i][column]
            matrix[i] = [
                (left - factor * right) % prime
                for left, right in zip(matrix[i], matrix[rank])
            ]
        pivots.append(column)
        rank += 1
        if rank == len(matrix):
            break
    return matrix[:rank], pivots


def nullspace_basis(rows, width: int, prime: int):
    reduced, pivots = rref_mod(rows, width, prime)
    pivot_set = set(pivots)
    basis = []
    for free in (column for column in range(width) if column not in pivot_set):
        vector = [0] * width
        vector[free] = 1
        for row, pivot in zip(reduced, pivots):
            vector[pivot] = (-row[free]) % prime
        basis.append(tuple(vector))
    return basis, len(pivots)


def span(basis, prime: int):
    if not basis:
        return [tuple()]
    width = len(basis[0])
    return [
        tuple(sum(coeff * vector[i] for coeff, vector in zip(coeffs, basis)) % prime for i in range(width))
        for coeffs in product(range(prime), repeat=len(basis))
    ]


def constants(n: int, prime: int):
    return [
        tuple([alpha] * n + [beta] * n + [(-alpha - beta) % prime] * n)
        for alpha in range(prime)
        for beta in range(prime)
    ]


def add_vectors(left, right, prime: int):
    return tuple((a + b) % prime for a, b in zip(left, right))


def quotient_representatives(basis, n: int, prime: int):
    universal = constants(n, prime)
    representatives = {
        min(add_vectors(vector, constant, prime) for constant in universal)
        for vector in span(basis, prime)
    }
    representatives.discard(tuple([0] * (3 * n)))
    return sorted(representatives)


def line_family(table, view: str):
    n = len(table)
    if view == "row":
        return [list(row) for row in table]
    if view == "col":
        return [[table[r][c] for r in range(n)] for c in range(n)]
    return [
        [next(r for r in range(n) if table[r][c] == symbol) for c in range(n)]
        for symbol in range(n)
    ]


def quotient_check(table, vector, prime: int):
    n = len(table)
    a = vector[:n]
    b = vector[n : 2 * n]
    c = vector[2 * n :]
    expected = n // prime
    errors = []
    for name, values in (("row", a), ("col", b), ("sym", c)):
        counts = Counter(values)
        if set(counts) != set(range(prime)) or set(counts.values()) != {expected}:
            errors.append(["unbalanced", name, dict(sorted(counts.items())), expected])
    for r in range(n):
        for j in range(n):
            if (a[r] + b[j] + c[table[r][j]]) % prime:
                errors.append(["cell_equation", r, j])
                break
    view_values = {
        "row": (a, b),
        "col": (b, a),
        "sym": (c, b),
    }
    for view in VIEWS:
        line_values, domain_values = view_values[view]
        lines = line_family(table, view)
        inverse_base = [0] * n
        for domain, value in enumerate(lines[0]):
            inverse_base[value] = domain
        for line_id, line in enumerate(lines):
            shift = (line_values[line_id] - line_values[0]) % prime
            for domain, value in enumerate(line):
                image = inverse_base[value]
                if domain_values[image] != (domain_values[domain] + shift) % prime:
                    errors.append(["block_transport", view, line_id, domain])
                    break
    return errors


def analyze_task(task):
    dataset, source_index, raw_table = task
    table = tuple(tuple(row) for row in raw_table)
    n = len(table)
    errors = []
    if not validate_latin(table):
        errors.append("not_latin")
    eqs = equations(table)
    prime_records = {}
    total_quotient_checks = 0
    for prime in PRIMES:
        basis, rank = nullspace_basis(eqs, 3 * n, prime)
        delta = len(basis) - 2
        if delta < 0:
            errors.append(["rank_above_universal", prime, rank])
        representatives = quotient_representatives(basis, n, prime) if delta else []
        expected_classes = prime**delta - 1
        if len(representatives) != expected_classes:
            errors.append(["quotient_class_count", prime, len(representatives), expected_classes])
        if delta and n % prime:
            errors.append(["prime_does_not_divide_order", prime, delta])
        quotient_errors = []
        for representative in representatives:
            quotient_errors.extend(quotient_check(table, representative, prime))
        if quotient_errors:
            errors.append(["quotient_checks", prime, quotient_errors[:10]])
        total_quotient_checks += len(representatives)
        prime_records[str(prime)] = {
            "rank": rank,
            "left_kernel_dimension": len(basis),
            "delta": delta,
            "nonuniversal_quotient_class_count": len(representatives),
            "quotient_checks_ok": not quotient_errors,
        }
    return {
        "dataset": dataset,
        "source_index": source_index,
        "order": n,
        "table_sha256": table_sha256(table),
        "pattern": pattern(table),
        "primes": prime_records,
        "quotient_class_checks": total_quotient_checks,
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


def summarize(records):
    summary = {
        "table_count": len(records),
        "unique_table_count": len({record["table_sha256"] for record in records}),
        "pattern_distribution": count_map(record["pattern"] for record in records),
        "quotient_class_checks": sum(record["quotient_class_checks"] for record in records),
        "error_count": sum(record["error_count"] for record in records),
        "primes": {},
    }
    for prime in PRIMES:
        key = str(prime)
        summary["primes"][key] = {
            "rank_distribution": count_map(record["primes"][key]["rank"] for record in records),
            "delta_distribution": count_map(record["primes"][key]["delta"] for record in records),
            "defect_table_count": sum(record["primes"][key]["delta"] > 0 for record in records),
            "nonuniversal_quotient_class_count": sum(
                record["primes"][key]["nonuniversal_quotient_class_count"] for record in records
            ),
            "defect_pattern_distribution": count_map(
                record["pattern"] for record in records if record["primes"][key]["delta"] > 0
            ),
        }
    return summary


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
        dataset: summarize([record for record in records if record["dataset"] == dataset])
        for dataset in sorted({record["dataset"] for record in records})
    }
    totals = {
        "table_count": len(records),
        "quotient_class_checks": sum(record["quotient_class_checks"] for record in records),
        "error_count": sum(record["error_count"] for record in records),
    }
    payload = {
        "audit_version": "prime_field_line_quotients_v1",
        "workers": args.workers,
        "primes": list(PRIMES),
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
            "The prime-field quotient theorem is proved independently of this audit.",
            "The order-10 corpus is partial and contains no FFF table.",
            "Torsion-free line incidence is necessary, not sufficient, for order-10 FFF.",
            "C38 remains open and C40 is absent.",
        ],
        "overall_ok": totals["error_count"] == 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    elapsed = time.perf_counter() - started
    lines = [
        "Prime-field line quotient audit",
        "",
        f"overall_ok: {payload['overall_ok']}",
        f"workers: {args.workers}",
        f"tables: {totals['table_count']}",
        f"nonuniversal quotient classes checked: {totals['quotient_class_checks']}",
        f"errors: {totals['error_count']}",
        f"elapsed seconds: {elapsed:.6f}",
        "",
    ]
    for dataset, dataset_summary in datasets.items():
        lines.extend([f"{dataset}:", f"- tables: {dataset_summary['table_count']}", f"- patterns: {dataset_summary['pattern_distribution']}"])
        for prime in PRIMES:
            info = dataset_summary["primes"][str(prime)]
            lines.append(
                f"- p={prime}: ranks {info['rank_distribution']}; deltas {info['delta_distribution']}; "
                f"defect tables/classes {info['defect_table_count']}/{info['nonuniversal_quotient_class_count']}; "
                f"defect patterns {info['defect_pattern_distribution']}"
            )
        lines.append("")
    lines.extend(
        [
            "Boundary:",
            "- The order-10 dataset is diagnostic only.",
            "- Saturated line incidence does not imply FFF.",
            "- C38 remains open and C40 is absent.",
        ]
    )
    args.summary.write_text("\n".join(lines) + "\n")
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
