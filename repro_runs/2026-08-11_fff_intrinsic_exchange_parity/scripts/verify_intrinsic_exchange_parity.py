#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path


def gf2_basis(vectors: list[int]) -> dict[int, int]:
    basis: dict[int, int] = {}
    for original in vectors:
        vector = original
        while vector:
            pivot = (vector & -vector).bit_length() - 1
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return basis


def gf2_contains(vector: int, basis: dict[int, int]) -> bool:
    while vector:
        pivot = (vector & -vector).bit_length() - 1
        if pivot not in basis:
            return False
        vector ^= basis[pivot]
    return True


def orthogonal_basis(equations: list[int], width: int) -> list[int]:
    rows = list(gf2_basis(equations).values())
    pivot_rows: dict[int, int] = {}
    for row in rows:
        pivot = (row & -row).bit_length() - 1
        pivot_rows[pivot] = row
    pivots = set(pivot_rows)
    result = []
    for free in range(width):
        if free in pivots:
            continue
        vector = 1 << free
        for pivot in sorted(pivots, reverse=True):
            row = pivot_rows[pivot]
            if (row & vector).bit_count() & 1:
                vector |= 1 << pivot
        result.append(vector)
    return result


def independent_balanced_four_masks(table) -> list[int]:
    n = len(table)
    groups = defaultdict(list)
    for cells in itertools.combinations(range(n * n), 4):
        profile = [0] * (3 * n)
        mask = 0
        for cell in cells:
            row, column = divmod(cell, n)
            symbol = table[row][column]
            profile[row] += 1
            profile[n + column] += 1
            profile[2 * n + symbol] += 1
            mask |= 1 << cell
        groups[tuple(profile)].append(mask)
    vectors = []
    for masks in groups.values():
        for left, right in itertools.combinations(masks, 2):
            if not left & right:
                vectors.append(left | right)
    return list(gf2_basis(vectors).values())


def line_basis(table) -> dict[int, int]:
    n = len(table)
    masks = []
    for kind in range(3):
        for line in range(n):
            mask = 0
            for row in range(n):
                for column in range(n):
                    if (row, column, table[row][column])[kind] == line:
                        mask |= 1 << (n * row + column)
            masks.append(mask)
    return gf2_basis(masks)


def span_values(basis: dict[int, int]) -> list[int]:
    values = [0]
    for vector in basis.values():
        values += [value ^ vector for value in values]
    return values


def line_profile(table, mask: int) -> tuple[tuple[int, ...], ...]:
    n = len(table)
    families = []
    for kind in range(3):
        degrees = []
        for line in range(n):
            degrees.append(
                sum(
                    bool(mask >> (n * row + column) & 1)
                    and (row, column, table[row][column])[kind] == line
                    for row in range(n)
                    for column in range(n)
                )
            )
        families.append(tuple(sorted(degrees)))
    return tuple(sorted(families))


def parity_signature(table) -> dict:
    exchange_basis = independent_balanced_four_masks(table)
    annihilator = orthogonal_basis(exchange_basis, len(table) ** 2)
    lines = line_basis(table)
    annihilator_span = gf2_basis(annihilator)
    if any(not gf2_contains(line, annihilator_span) for line in lines.values()):
        raise ValueError("line covector outside exchange annihilator")
    nontrivial = next(vector for vector in annihilator if not gf2_contains(vector, lines))
    coset = [nontrivial ^ value for value in span_values(lines)]
    weights = Counter(value.bit_count() for value in coset)
    minimum = min(weights)
    profiles = Counter(line_profile(table, value) for value in coset if value.bit_count() == minimum)
    return {
        "exchange_mod2_rank": len(exchange_basis),
        "line_covector_rank": len(lines),
        "parity_class_dimension_mod_lines": len(annihilator) - len(lines),
        "minimum_covector_weight": minimum,
        "minimum_covector_count": weights[minimum],
        "covector_coset_weight_distribution": {
            str(weight): count for weight, count in sorted(weights.items())
        },
        "minimum_line_degree_profiles": {
            str(profile): count for profile, count in sorted(profiles.items())
        },
    }


def parse_table(compact: str):
    n = int(len(compact) ** 0.5)
    if n * n != len(compact):
        raise ValueError(compact)
    return tuple(
        tuple(int(value) for value in compact[n * row : n * (row + 1)])
        for row in range(n)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--exceptional", type=Path, required=True)
    parser.add_argument("--mainclasses", type=Path, required=True)
    parser.add_argument("--rank19", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    exceptional = json.loads(args.exceptional.read_text())
    mainclasses = json.loads(args.mainclasses.read_text())
    rank19 = json.loads(args.rank19.read_text())
    errors = []

    primary_by_source = {record["source_index"]: record for record in primary["records"]}
    classified_sources = [
        source
        for mainclass in mainclasses["mainclasses"]
        for source in mainclass["source_indices"]
    ]
    if sorted(classified_sources) != list(range(1, 9409)):
        errors.append("mainclass_source_partition")
    if len(mainclasses["mainclasses"]) != 12:
        errors.append(["mainclass_count", len(mainclasses["mainclasses"]), 12])

    rank19_sources = {
        source
        for mainclass in mainclasses["mainclasses"]
        if mainclass["E4_rank_distribution"] == {"19": mainclass["reduced_table_count"]}
        for source in mainclass["source_indices"]
    }
    expected_rank19 = {
        source for source, record in primary_by_source.items() if record["elementary_rank"] == 19
    }
    if rank19_sources != expected_rank19:
        errors.append("rank19_source_partition")

    independent_signatures = []
    for mainclass in rank19["mainclasses"]:
        class_record = next(
            record
            for record in mainclasses["mainclasses"]
            if record["mainclass_id"] == mainclass["mainclass_id"]
        )
        representative = class_record["mainclass_representative"]
        if hashlib.sha256(bytes(map(int, representative))).hexdigest() != mainclass["mainclass_id"]:
            errors.append(["mainclass_hash", mainclass["mainclass_id"]])
        actual = parity_signature(parse_table(representative))
        expected = {
            "covector_coset_weight_distribution": mainclass["representative_signature"]["covector_coset_weight_distribution"],
            "minimum_line_degree_profiles": mainclass["representative_signature"]["minimum_line_degree_profiles"],
        }
        for key, value in expected.items():
            if actual[key] != value:
                errors.append(["signature", mainclass["mainclass_id"], key])
        independent_signatures.append(
            {
                "mainclass_id": mainclass["mainclass_id"],
                **actual,
                "matches_stored_signature": all(actual[key] == value for key, value in expected.items()),
            }
        )

    exceptional_records = exceptional["records"]
    if len(exceptional_records) != 180:
        errors.append(["exceptional_count", len(exceptional_records), 180])
    if len({record["mainclass_id"] for record in exceptional_records}) != 1:
        errors.append("exceptional_mainclass_count")
    if any(any(record["saturated_common_mode_parities"]) for record in exceptional_records):
        errors.append("exceptional_common_mode_parity")
    if any(record["six_exchange_completion_parity"] != 1 for record in exceptional_records):
        errors.append("exceptional_completion_parity")

    payload = {
        "verification_version": "intrinsic_exchange_parity_independent_v1",
        "checks": {
            "mainclass_count": len(mainclasses["mainclasses"]),
            "classified_source_count": len(classified_sources),
            "rank19_source_count": len(rank19_sources),
            "rank19_mainclass_count": len(independent_signatures),
            "exceptional_source_count": len(exceptional_records),
            "independent_signatures": independent_signatures,
        },
        "error_count": len(errors),
        "errors": errors,
        "overall_pass": not errors,
        "claim_boundary": "Independent finite verification only; no order-10 conclusion.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join(
            [
                "Independent intrinsic exchange-parity verification",
                "",
                f"main classes: {payload['checks']['mainclass_count']}",
                f"classified sources: {payload['checks']['classified_source_count']}",
                f"rank-19 sources: {payload['checks']['rank19_source_count']}",
                f"rank-19 main classes independently checked: {payload['checks']['rank19_mainclass_count']}",
                f"exceptional sources: {payload['checks']['exceptional_source_count']}",
                f"errors: {payload['error_count']}",
                f"overall pass: {payload['overall_pass']}",
                "",
                "No order-10 conclusion is inferred.",
            ]
        )
        + "\n"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
