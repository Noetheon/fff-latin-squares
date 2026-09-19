#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRIMARY = load_module(
    "exchange_parity_controls_primary",
    ROOT
    / "repro_runs/2026-08-11_fff_common_mode_trade_lattice/scripts/"
    "audit_common_mode_trade_lattice.py",
)
PARITY = load_module(
    "exchange_parity_controls_parity",
    ROOT
    / "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/scripts/"
    "audit_intrinsic_exchange_parity.py",
)
C97 = load_module(
    "exchange_parity_controls_c97",
    ROOT
    / "repro_runs/2026-08-11_fff_joint_atom_cell_rank/scripts/"
    "audit_joint_atom_cell_rank.py",
)
C98 = load_module(
    "exchange_parity_controls_c98",
    ROOT
    / "repro_runs/2026-08-11_fff_common_mode_gradient/scripts/"
    "audit_common_mode_gradient.py",
)


def table_sha256(table) -> str:
    payload = ";".join(",".join(map(str, row)) for row in table).encode()
    return hashlib.sha256(payload).hexdigest()


def analyze_task(task):
    dataset, source_index, table = task
    table = tuple(tuple(row) for row in table)
    started = time.perf_counter()
    errors = []
    n = len(table)
    width = n * n
    exchanges = PRIMARY.balanced_exchange_vectors(table, 4)
    exchange_masks = [PARITY.parity_mask(vector) for vector in exchanges]
    exchange_basis = PARITY.row_basis(exchange_masks)
    line_masks = PARITY.line_masks(table)
    line_basis = PARITY.row_basis(line_masks)

    nonkernel_exchange_count = sum(
        any(PARITY.dot_parity(mask, line) for line in line_masks)
        for mask in exchange_masks
    )
    if nonkernel_exchange_count:
        errors.append(["nonkernel_exchange_count", nonkernel_exchange_count])

    annihilator_basis = PARITY.nullspace_basis(exchange_basis, width)
    annihilator_row_basis = PARITY.row_basis(annihilator_basis)
    line_covectors_outside_annihilator = sum(
        not PARITY.in_span(line, annihilator_row_basis) for line in line_basis
    )
    if line_covectors_outside_annihilator:
        errors.append(
            [
                "line_covectors_outside_annihilator",
                line_covectors_outside_annihilator,
            ]
        )

    trade_dimension_mod2 = width - len(line_basis)
    quotient_dimension = trade_dimension_mod2 - len(exchange_basis)
    annihilator_mod_lines_dimension = len(annihilator_basis) - len(line_basis)
    if quotient_dimension != annihilator_mod_lines_dimension:
        errors.append(
            [
                "quotient_annihilator_dimension_mismatch",
                quotient_dimension,
                annihilator_mod_lines_dimension,
            ]
        )

    return {
        "dataset": dataset,
        "source_index": source_index,
        "table_sha256": table_sha256(table),
        "order": n,
        "pattern": PARITY.pattern_name(table),
        "group_isotopic": PARITY.is_group_isotopic_reduced(table),
        "balanced_4plus4_exchange_count": len(exchanges),
        "line_rank_mod2": len(line_basis),
        "trade_dimension_mod2": trade_dimension_mod2,
        "exchange_rank_mod2": len(exchange_basis),
        "exchange_quotient_dimension_mod2": quotient_dimension,
        "annihilator_mod_lines_dimension": annihilator_mod_lines_dimension,
        "nonkernel_exchange_count": nonkernel_exchange_count,
        "line_covectors_outside_annihilator": line_covectors_outside_annihilator,
        "elapsed_seconds": time.perf_counter() - started,
        "error_count": len(errors),
        "errors": errors,
    }


def tasks_for(dataset: str, fff_metadata: Path, n10_corpus: Path):
    if dataset == "order8_fff_complete":
        return [
            (dataset, source_index, table)
            for source_index, table in C97.load_n8(fff_metadata)
        ]
    if dataset == "order10_tracked_partial":
        return [
            (dataset, source_index, table)
            for source_index, table, _ in C98.PAIR["FLAG"]["n10_tables"](n10_corpus)
        ]
    raise ValueError(dataset)


def count_map(values) -> dict[str, int]:
    return {str(key): value for key, value in sorted(Counter(values).items())}


def write_summary(path: Path, payload: dict) -> None:
    totals = payload["totals"]
    lines = [
        "Exchange-parity control audit",
        "",
        f"dataset: {payload['dataset']}",
        f"workers: {payload['workers']}",
        f"tables: {totals['table_count']}",
        f"unique tables: {totals['unique_table_count']}",
        f"patterns: {totals['pattern_distribution']}",
        f"group-isotopic: {totals['group_isotopic_distribution']}",
        f"line ranks mod 2: {totals['line_rank_mod2_distribution']}",
        f"E4 ranks mod 2: {totals['exchange_rank_mod2_distribution']}",
        f"quotient dimensions mod 2: {totals['exchange_quotient_dimension_mod2_distribution']}",
        f"exchange-count range: {totals['exchange_count_range']}",
        f"elapsed range seconds: {totals['elapsed_seconds_range']}",
        f"errors: {totals['error_count']}",
        "",
        "Boundary: finite control corpus only; tracked order-10 tables are not exhaustive and do not decide C38.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        choices=("order8_fff_complete", "order10_tracked_partial"),
        required=True,
    )
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    tasks = tasks_for(args.dataset, args.fff_metadata, args.n10_corpus)
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=1))
    records.sort(key=lambda record: record["source_index"])

    payload = {
        "audit_version": "exchange_parity_controls_v1",
        "dataset": args.dataset,
        "workers": args.workers,
        "totals": {
            "table_count": len(records),
            "unique_table_count": len({record["table_sha256"] for record in records}),
            "pattern_distribution": count_map(record["pattern"] for record in records),
            "group_isotopic_distribution": count_map(
                record["group_isotopic"] for record in records
            ),
            "line_rank_mod2_distribution": count_map(
                record["line_rank_mod2"] for record in records
            ),
            "trade_dimension_mod2_distribution": count_map(
                record["trade_dimension_mod2"] for record in records
            ),
            "exchange_rank_mod2_distribution": count_map(
                record["exchange_rank_mod2"] for record in records
            ),
            "exchange_quotient_dimension_mod2_distribution": count_map(
                record["exchange_quotient_dimension_mod2"] for record in records
            ),
            "annihilator_mod_lines_dimension_distribution": count_map(
                record["annihilator_mod_lines_dimension"] for record in records
            ),
            "exchange_count_range": [
                min(record["balanced_4plus4_exchange_count"] for record in records),
                max(record["balanced_4plus4_exchange_count"] for record in records),
            ],
            "elapsed_seconds_range": [
                min(record["elapsed_seconds"] for record in records),
                max(record["elapsed_seconds"] for record in records),
            ],
            "error_count": sum(record["error_count"] for record in records),
        },
        "records": records,
        "claim_boundary": [
            "The order-8 corpus is the complete frozen set of 230 FFF representatives.",
            "The 135 order-10 tables are a partial diagnostic corpus, not FFF examples.",
            "No order-10 existence or non-existence conclusion is inferred.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
