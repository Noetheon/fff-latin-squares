#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PARITY_PATH = (
    ROOT
    / "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/scripts/"
    "audit_intrinsic_exchange_parity.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PARITY = load_module("intrinsic_parity_rank19_helper", PARITY_PATH)
PRIMARY = PARITY.PRIMARY
SMALL = PARITY.SMALL


def analyze_task(task):
    source_index, table, primary_record, mainclass_id = task
    errors = []
    width = len(table) ** 2
    exchanges = PRIMARY.balanced_exchange_vectors(table, 4)
    exchange_basis = PARITY.row_basis([PARITY.parity_mask(vector) for vector in exchanges])
    annihilator_basis = PARITY.nullspace_basis(exchange_basis, width)
    annihilator_row_basis = PARITY.row_basis(annihilator_basis)
    line_basis = PARITY.row_basis(PARITY.line_masks(table))

    if len(exchange_basis) != 19:
        errors.append(["exchange_mod2_rank", len(exchange_basis), 19])
    if len(annihilator_basis) - len(line_basis) != 1:
        errors.append(
            [
                "parity_class_dimension_mod_lines",
                len(annihilator_basis) - len(line_basis),
                1,
            ]
        )
    if any(not PARITY.in_span(line, annihilator_row_basis) for line in line_basis):
        errors.append("line_covectors_not_in_annihilator")

    parity_class = next(
        vector for vector in annihilator_basis if not PARITY.in_span(vector, line_basis)
    )
    coset = [parity_class ^ line for line in PARITY.span_elements(line_basis)]
    weights = Counter(mask.bit_count() for mask in coset)
    minimum_weight = min(weights)
    minimum_masks = [mask for mask in coset if mask.bit_count() == minimum_weight]
    profiles = Counter(PARITY.line_degree_profile(table, mask) for mask in minimum_masks)

    completion = primary_record["six_exchange_completion"]
    completion_parity = None
    if completion is not None:
        completion_parity = PARITY.dot_parity(
            parity_class, PARITY.parity_mask(completion["vector"])
        )
        if completion_parity != 1:
            errors.append(["completion_parity", completion_parity, 1])

    return {
        "source_index": source_index,
        "mainclass_id": mainclass_id,
        "r_Q": primary_record["r_Q"],
        "exchange_mod2_rank": len(exchange_basis),
        "line_covector_rank": len(line_basis),
        "parity_class_dimension_mod_lines": len(annihilator_basis) - len(line_basis),
        "minimum_covector_weight": minimum_weight,
        "minimum_covector_count": len(minimum_masks),
        "covector_coset_weight_distribution": {
            str(weight): count for weight, count in sorted(weights.items())
        },
        "minimum_line_degree_profiles": {
            str(profile): count for profile, count in sorted(profiles.items())
        },
        "six_exchange_completion_parity": completion_parity,
        "error_count": len(errors),
        "errors": errors,
    }


def signature(record: dict) -> tuple:
    return (
        record["minimum_covector_weight"],
        record["minimum_covector_count"],
        tuple(sorted(record["covector_coset_weight_distribution"].items())),
        tuple(sorted(record["minimum_line_degree_profiles"].items())),
    )


def write_summary(path: Path, payload: dict) -> None:
    totals = payload["totals"]
    lines = [
        "All rank-19 order-6 exchange-parity audit",
        "",
        f"tables: {totals['table_count']}",
        f"main classes: {totals['mainclass_count']}",
        f"parity signatures: {totals['parity_signature_count']}",
        f"minimum weights: {totals['minimum_weight_distribution']}",
        f"errors: {totals['error_count']}",
        "",
        "Per-main-class signatures:",
    ]
    for record in payload["mainclasses"]:
        lines.append(
            f"- {record['mainclass_id'][:12]}: tables={record['table_count']}, "
            f"r_Q={record['r_Q_distribution']}, signatures={record['parity_signature_count']}, "
            f"min_weights={record['minimum_weight_distribution']}, "
            f"min_counts={record['minimum_count_distribution']}"
        )
    lines += [
        "",
        "Boundary: complete for the three rank-19 main classes of order 6; no order-10 conclusion.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--mainclasses", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    rank19 = {
        record["source_index"]: record
        for record in primary["records"]
        if record["elementary_rank"] == 19
    }
    classification = json.loads(args.mainclasses.read_text())
    mainclass_by_source = {}
    for mainclass in classification["mainclasses"]:
        for source_index in mainclass["source_indices"]:
            mainclass_by_source[source_index] = mainclass["mainclass_id"]

    tasks = [
        (source_index, table, rank19[source_index], mainclass_by_source[source_index])
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
        if source_index in rank19
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=4))
    records.sort(key=lambda record: record["source_index"])

    grouped = defaultdict(list)
    for record in records:
        grouped[record["mainclass_id"]].append(record)
    mainclasses = []
    for mainclass_id, group in sorted(grouped.items()):
        mainclasses.append(
            {
                "mainclass_id": mainclass_id,
                "table_count": len(group),
                "r_Q_distribution": dict(sorted(Counter(record["r_Q"] for record in group).items())),
                "parity_signature_count": len({signature(record) for record in group}),
                "minimum_weight_distribution": dict(
                    sorted(Counter(record["minimum_covector_weight"] for record in group).items())
                ),
                "minimum_count_distribution": dict(
                    sorted(Counter(record["minimum_covector_count"] for record in group).items())
                ),
                "representative_signature": {
                    "covector_coset_weight_distribution": group[0]["covector_coset_weight_distribution"],
                    "minimum_line_degree_profiles": group[0]["minimum_line_degree_profiles"],
                },
            }
        )

    payload = {
        "audit_version": "all_rank19_exchange_parity_v1",
        "workers": args.workers,
        "totals": {
            "table_count": len(records),
            "mainclass_count": len(grouped),
            "parity_signature_count": len({signature(record) for record in records}),
            "minimum_weight_distribution": dict(
                sorted(Counter(record["minimum_covector_weight"] for record in records).items())
            ),
            "error_count": sum(record["error_count"] for record in records),
        },
        "mainclasses": mainclasses,
        "records": records,
        "claim_boundary": [
            "Complete for all 3,960 rank-19 reduced order-6 squares.",
            "No order-10 conclusion is inferred.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
