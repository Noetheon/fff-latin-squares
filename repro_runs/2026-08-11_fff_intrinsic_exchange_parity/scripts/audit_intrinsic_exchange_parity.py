#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRIMARY_PATH = (
    ROOT
    / "repro_runs/2026-08-11_fff_common_mode_trade_lattice/scripts/"
    "audit_common_mode_trade_lattice.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRIMARY = load_module("primary_intrinsic_exchange_parity", PRIMARY_PATH)
SMALL = PRIMARY.SMALL


def parity_mask(vector: list[int]) -> int:
    mask = 0
    for index, value in enumerate(vector):
        if value & 1:
            mask |= 1 << index
    return mask


def dot_parity(left: int, right: int) -> int:
    return (left & right).bit_count() & 1


def row_basis(vectors: list[int]) -> list[int]:
    pivots: dict[int, int] = {}
    for original in vectors:
        vector = original
        while vector:
            pivot = vector.bit_length() - 1
            if pivot in pivots:
                vector ^= pivots[pivot]
            else:
                pivots[pivot] = vector
                break
    return [pivots[pivot] for pivot in sorted(pivots, reverse=True)]


def in_span(vector: int, basis: list[int]) -> bool:
    for base in basis:
        pivot = base.bit_length() - 1
        if vector & (1 << pivot):
            vector ^= base
    return vector == 0


def nullspace_basis(equations: list[int], width: int) -> list[int]:
    rows = [row for row in equations if row]
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(width):
        selected = next(
            (index for index in range(pivot_row, len(rows)) if rows[index] >> column & 1),
            None,
        )
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        for index in range(len(rows)):
            if index != pivot_row and rows[index] >> column & 1:
                rows[index] ^= rows[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break

    pivot_set = set(pivot_columns)
    basis = []
    for free in range(width):
        if free in pivot_set:
            continue
        vector = 1 << free
        for row_index, pivot in enumerate(pivot_columns):
            if rows[row_index] >> free & 1:
                vector |= 1 << pivot
        basis.append(vector)
    return basis


def line_masks(table: tuple[tuple[int, ...], ...]) -> list[int]:
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
    return masks


def span_elements(basis: list[int]) -> list[int]:
    values = [0]
    for vector in basis:
        values += [value ^ vector for value in values]
    return values


def line_degree_profile(table, mask: int) -> tuple[tuple[int, ...], ...]:
    n = len(table)
    families = []
    for kind in range(3):
        degrees = []
        for line in range(n):
            count = 0
            for row in range(n):
                for column in range(n):
                    cell = n * row + column
                    if mask >> cell & 1 and (row, column, table[row][column])[kind] == line:
                        count += 1
            degrees.append(count)
        families.append(tuple(sorted(degrees)))
    return tuple(sorted(families))


def parastrophe(table, coordinate_order: tuple[int, int, int]):
    n = len(table)
    transformed = [[None] * n for _ in range(n)]
    for row in range(n):
        for column in range(n):
            triple = (row, column, table[row][column])
            first, second, value = (triple[index] for index in coordinate_order)
            transformed[first][second] = value
    return tuple(tuple(int(value) for value in row) for row in transformed)


def canonical_isotopy_representative(table) -> tuple[int, ...]:
    n = len(table)
    best = None
    for first_row in range(n):
        for first_column in range(n):
            remaining_columns = [column for column in range(n) if column != first_column]
            for tail in itertools.permutations(remaining_columns):
                columns = (first_column,) + tail
                symbol_map = [None] * n
                for new_column, old_column in enumerate(columns):
                    symbol_map[table[first_row][old_column]] = new_column
                rows = [None] * n
                for old_row in range(n):
                    rows[symbol_map[table[old_row][first_column]]] = old_row
                candidate = tuple(
                    symbol_map[table[old_row][old_column]]
                    for old_row in rows
                    for old_column in columns
                )
                if best is None or candidate < best:
                    best = candidate
    if best is None:
        raise ValueError("missing isotopy representative")
    return best


def canonical_mainclass_representative(table) -> tuple[int, ...]:
    return min(
        canonical_isotopy_representative(parastrophe(table, coordinate_order))
        for coordinate_order in itertools.permutations(range(3))
    )


def compose(first, second):
    return tuple(first[second[index]] for index in range(len(first)))


def is_group_isotopic_reduced(table) -> bool:
    family = set(table)
    return all(compose(first, second) in family for first in family for second in family)


def cycle_lengths(permutation):
    seen = [False] * len(permutation)
    lengths = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        cursor = start
        length = 0
        while not seen[cursor]:
            seen[cursor] = True
            cursor = permutation[cursor]
            length += 1
        lengths.append(length)
    return lengths


def view_lines(table, view: str):
    n = len(table)
    if view == "row":
        return table
    if view == "col":
        return tuple(tuple(table[row][column] for row in range(n)) for column in range(n))
    if view == "sym":
        lines = [[None] * n for _ in range(n)]
        for row in range(n):
            for column in range(n):
                lines[table[row][column]][column] = row
        return tuple(tuple(int(value) for value in line) for line in lines)
    raise ValueError(view)


def view_has_odd_cycle(table, view: str) -> bool:
    lines = view_lines(table, view)
    positions = []
    for line in lines:
        inverse = [None] * len(line)
        for index, value in enumerate(line):
            inverse[value] = index
        positions.append(inverse)
    for first, second in itertools.combinations(range(len(lines)), 2):
        permutation = tuple(positions[second][value] for value in lines[first])
        if any(length > 1 and length & 1 for length in cycle_lengths(permutation)):
            return True
    return False


def pattern_name(table) -> str:
    return "".join("T" if view_has_odd_cycle(table, view) else "F" for view in ("row", "col", "sym"))


def analyze_task(task):
    source_index, table, primary_record, saturation_record = task
    errors = []
    n = len(table)
    width = n * n

    exchanges = PRIMARY.balanced_exchange_vectors(table, 4)
    exchange_masks = [parity_mask(vector) for vector in exchanges]
    exchange_basis = row_basis(exchange_masks)
    annihilator_basis = nullspace_basis(exchange_basis, width)
    annihilator_row_basis = row_basis(annihilator_basis)

    line_basis = row_basis(line_masks(table))
    if any(not in_span(line, annihilator_row_basis) for line in line_basis):
        errors.append("line_covectors_not_in_exchange_annihilator")
    if len(exchange_basis) != 19:
        errors.append(["exchange_mod2_rank", len(exchange_basis), 19])
    if len(line_basis) != 16:
        errors.append(["line_covector_rank", len(line_basis), 16])
    if len(annihilator_basis) != 17:
        errors.append(["exchange_annihilator_dimension", len(annihilator_basis), 17])

    parity_class = next(
        (vector for vector in annihilator_basis if not in_span(vector, line_basis)),
        None,
    )
    if parity_class is None:
        errors.append("missing_nontrivial_parity_class")
        parity_class = 0

    line_space = span_elements(line_basis)
    coset = [parity_class ^ line for line in line_space]
    weight_distribution = Counter(mask.bit_count() for mask in coset)
    minimum_weight = min(weight_distribution)
    minimum_masks = sorted(mask for mask in coset if mask.bit_count() == minimum_weight)
    minimum_profiles = Counter(line_degree_profile(table, mask) for mask in minimum_masks)

    saturated_modes = saturation_record["saturated_common_mode_cell_basis"]
    mode_parities = [dot_parity(parity_class, parity_mask(mode)) for mode in saturated_modes]
    if any(mode_parities):
        errors.append(["common_mode_parity", mode_parities, [0] * len(mode_parities)])

    completion = primary_record["six_exchange_completion"]
    completion_parity = dot_parity(parity_class, parity_mask(completion["vector"]))
    if completion_parity != 1:
        errors.append(["completion_parity", completion_parity, 1])

    mainclass_representative = canonical_mainclass_representative(table)
    mainclass_id = hashlib.sha256(bytes(mainclass_representative)).hexdigest()

    return {
        "source_index": source_index,
        "mainclass_id": mainclass_id,
        "mainclass_representative": "".join(str(value) for value in mainclass_representative),
        "pattern": pattern_name(table),
        "group_isotopic": is_group_isotopic_reduced(table),
        "exchange_count": len(exchanges),
        "exchange_mod2_rank": len(exchange_basis),
        "line_covector_rank": len(line_basis),
        "exchange_annihilator_dimension": len(annihilator_basis),
        "parity_class_dimension_mod_lines": len(annihilator_basis) - len(line_basis),
        "minimum_covector_weight": minimum_weight,
        "minimum_covector_count": len(minimum_masks),
        "minimum_covector_masks": minimum_masks,
        "minimum_line_degree_profiles": {
            str(profile): count for profile, count in sorted(minimum_profiles.items())
        },
        "covector_coset_weight_distribution": {
            str(weight): count for weight, count in sorted(weight_distribution.items())
        },
        "saturated_common_mode_parities": mode_parities,
        "six_exchange_completion_parity": completion_parity,
        "error_count": len(errors),
        "errors": errors,
    }


def summarize(records: list[dict]) -> dict:
    return {
        "table_count": len(records),
        "exchange_mod2_rank_distribution": dict(
            sorted(Counter(record["exchange_mod2_rank"] for record in records).items())
        ),
        "parity_class_dimension_distribution": dict(
            sorted(
                Counter(
                    record["parity_class_dimension_mod_lines"] for record in records
                ).items()
            )
        ),
        "minimum_covector_weight_distribution": dict(
            sorted(Counter(record["minimum_covector_weight"] for record in records).items())
        ),
        "minimum_covector_count_distribution": dict(
            sorted(Counter(record["minimum_covector_count"] for record in records).items())
        ),
        "mainclass_distribution": dict(
            sorted(Counter(record["mainclass_id"] for record in records).items())
        ),
        "pattern_distribution": dict(
            sorted(Counter(record["pattern"] for record in records).items())
        ),
        "group_isotopy_distribution": {
            str(status): count
            for status, count in sorted(
                Counter(record["group_isotopic"] for record in records).items()
            )
        },
        "common_mode_even_count": sum(
            not any(record["saturated_common_mode_parities"]) for record in records
        ),
        "completion_odd_count": sum(
            record["six_exchange_completion_parity"] == 1 for record in records
        ),
        "error_count": sum(record["error_count"] for record in records),
    }


def write_summary(path: Path, payload: dict) -> None:
    totals = payload["totals"]
    lines = [
        "Intrinsic exchange-parity audit",
        "",
        f"tables: {totals['table_count']}",
        f"E4 mod-2 ranks: {totals['exchange_mod2_rank_distribution']}",
        f"parity-class dimensions modulo lines: {totals['parity_class_dimension_distribution']}",
        f"minimum covector weights: {totals['minimum_covector_weight_distribution']}",
        f"minimum covector counts: {totals['minimum_covector_count_distribution']}",
        f"main classes: {len(totals['mainclass_distribution'])}",
        f"main-class sizes in this reduced corpus: {sorted(totals['mainclass_distribution'].values())}",
        f"patterns: {totals['pattern_distribution']}",
        f"group-isotopy flags: {totals['group_isotopy_distribution']}",
        f"common-mode lattices parity-even: {totals['common_mode_even_count']}",
        f"6+6 completions parity-odd: {totals['completion_odd_count']}",
        f"errors: {totals['error_count']}",
        "",
        "The nonzero class is intrinsic in Ann(E4)/LineCovectors and is relabelling-covariant.",
        "This is a complete audit of the 180 order-6 rank-19 cases, not an order-10 obstruction.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--saturation", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    exceptional = {
        record["source_index"]: record
        for record in primary["records"]
        if record["r_Q"] == 3 and record["elementary_rank"] == 19
    }
    saturation = json.loads(args.saturation.read_text())
    saturation_by_index = {
        record["source_index"]: record for record in saturation["records"]
    }
    tasks = [
        (source_index, table, exceptional[source_index], saturation_by_index[source_index])
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
        if source_index in exceptional
    ]

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=2))
    records.sort(key=lambda record: record["source_index"])
    payload = {
        "audit_version": "intrinsic_exchange_parity_v1",
        "workers": args.workers,
        "definitions": {
            "parity_class": "the unique nonzero class in Ann_F2(E4 mod 2) modulo the span of row, column, and symbol line covectors",
            "evaluation": "dot product modulo 2 with any representative of the parity class",
        },
        "totals": summarize(records),
        "records": records,
        "claim_boundary": [
            "Complete only for the 180 reduced order-6 rank-19 cases.",
            "No universal FFF or order-10 conclusion is inferred.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
