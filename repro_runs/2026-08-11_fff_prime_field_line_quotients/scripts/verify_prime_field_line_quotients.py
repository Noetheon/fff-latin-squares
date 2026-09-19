#!/usr/bin/env python3
"""Independent modular-rank verifier for the prime-field quotient audit."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRIMES = (2, 3, 5, 7, 11)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SMALL = load_module(
    "prime_field_verify_small",
    ROOT / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py",
)


def parse_compact(compact: str, n: int):
    return tuple(tuple(int(x) for x in compact[r * n : (r + 1) * n]) for r in range(n))


def table_sha256(table) -> str:
    raw = ";".join(",".join(map(str, row)) for row in table).encode()
    return hashlib.sha256(raw).hexdigest()


def independent_rank(table, prime: int) -> int:
    n = len(table)
    basis = {}
    for r in range(n):
        for c in range(n):
            vector = {r: 1, n + c: 1, 2 * n + table[r][c]: 1}
            while vector:
                pivot = min(vector)
                if pivot not in basis:
                    inverse = pow(vector[pivot], -1, prime)
                    basis[pivot] = {key: value * inverse % prime for key, value in vector.items() if value % prime}
                    break
                factor = vector[pivot]
                row = basis[pivot]
                keys = set(vector) | set(row)
                vector = {
                    key: (vector.get(key, 0) - factor * row.get(key, 0)) % prime
                    for key in keys
                    if (vector.get(key, 0) - factor * row.get(key, 0)) % prime
                }
    return len(basis)


def load_tables(fff_metadata: Path, n10_corpus: Path):
    tables = []
    for n in (2, 4, 6):
        tables.extend(
            (f"order{n}_reduced_complete", index, tuple(tuple(row) for row in table))
            for index, table in enumerate(SMALL.reduced_latin_squares(n), 1)
        )
    with fff_metadata.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            tables.append(("order8_fff_complete", int(row["line_number"]), parse_compact(row["square"], 8)))
    corpus = json.loads(n10_corpus.read_text())
    tables.extend(
        ("order10_tracked_partial", index, parse_compact(compact, 10))
        for index, compact in enumerate(sorted(corpus["tracked_order10_source_paths"]), 1)
    )
    return tables


def count_map(values):
    return {str(key): value for key, value in sorted(Counter(values).items())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    indexed = {(record["dataset"], record["source_index"]): record for record in audit["records"]}
    errors = []
    checks = 0
    rebuilt = {}
    for dataset, source_index, table in load_tables(args.fff_metadata, args.n10_corpus):
        key = (dataset, source_index)
        record = indexed.get(key)
        if record is None:
            errors.append(["missing_record", *key])
            continue
        if record["table_sha256"] != table_sha256(table):
            errors.append(["table_hash", *key])
        for prime in PRIMES:
            rank = independent_rank(table, prime)
            checks += 1
            if rank != record["primes"][str(prime)]["rank"]:
                errors.append(["rank", *key, prime, rank, record["primes"][str(prime)]["rank"]])
            delta = 3 * len(table) - 2 - rank
            expected_classes = prime**delta - 1
            if expected_classes != record["primes"][str(prime)]["nonuniversal_quotient_class_count"]:
                errors.append(["class_count", *key, prime, expected_classes])
            if delta and len(table) % prime:
                errors.append(["nondividing_prime_defect", *key, prime, delta])
        rebuilt[key] = record
    if len(rebuilt) != audit["totals"]["table_count"]:
        errors.append(["table_count", len(rebuilt), audit["totals"]["table_count"]])

    expected_distributions = {
        "order2_reduced_complete": {2: {1: 1}},
        "order4_reduced_complete": {2: {1: 3, 2: 1}},
        "order6_reduced_complete": {2: {0: 8928, 1: 480}, 3: {0: 9168, 1: 240}},
        "order8_fff_complete": {2: {0: 63, 1: 156, 2: 10, 3: 1}},
        "order10_tracked_partial": {2: {0: 135}, 5: {0: 135}},
    }
    distribution_checks = 0
    for dataset, prime_data in expected_distributions.items():
        records = [record for record in rebuilt.values() if record["dataset"] == dataset]
        for prime, expected in prime_data.items():
            observed = Counter(record["primes"][str(prime)]["delta"] for record in records)
            distribution_checks += 1
            if dict(observed) != expected:
                errors.append(["distribution", dataset, prime, dict(observed), expected])

    n6_p3 = [
        record
        for record in rebuilt.values()
        if record["dataset"] == "order6_reduced_complete" and record["primes"]["3"]["delta"]
    ]
    if len(n6_p3) != 240 or Counter(record["pattern"] for record in n6_p3) != {"TTT": 240}:
        errors.append(["order6_p3_controls", len(n6_p3), count_map(record["pattern"] for record in n6_p3)])

    payload = {
        "verification_version": "prime_field_line_quotients_independent_v1",
        "audit_sha256": hashlib.sha256(args.audit.read_bytes()).hexdigest(),
        "table_count": len(rebuilt),
        "independent_rank_checks": checks,
        "distribution_checks": distribution_checks,
        "order6_p3_defect_count": len(n6_p3),
        "order6_p3_defect_patterns": count_map(record["pattern"] for record in n6_p3),
        "error_count": len(errors),
        "errors": errors,
        "overall_ok": not errors,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(
            [
                "Prime-field line quotient independent verification",
                "",
                f"overall_ok: {payload['overall_ok']}",
                f"tables: {payload['table_count']}",
                f"independent modular-rank checks: {checks}",
                f"distribution checks: {distribution_checks}",
                f"order-6 p=3 defects/patterns: {len(n6_p3)} / {payload['order6_p3_defect_patterns']}",
                f"errors: {len(errors)}",
            ]
        )
        + "\n"
    )
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
