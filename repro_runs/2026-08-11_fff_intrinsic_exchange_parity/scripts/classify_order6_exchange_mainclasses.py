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


PARITY = load_module("intrinsic_parity_mainclass_helper", PARITY_PATH)
SMALL = PARITY.SMALL


def classify_task(task):
    source_index, table, lattice_record = task
    representative = PARITY.canonical_mainclass_representative(table)
    return {
        "source_index": source_index,
        "mainclass_id": PARITY.hashlib.sha256(bytes(representative)).hexdigest(),
        "mainclass_representative": "".join(str(value) for value in representative),
        "pattern": PARITY.pattern_name(table),
        "group_isotopic": PARITY.is_group_isotopic_reduced(table),
        "r_Q": lattice_record["r_Q"],
        "E4_rank": lattice_record["elementary_rank"],
        "four_exchange_count": lattice_record["four_exchange_count"],
    }


def write_summary(path: Path, payload: dict) -> None:
    lines = [
        "Order-6 exchange-lattice main-class classification",
        "",
        f"reduced tables: {payload['totals']['table_count']}",
        f"main classes: {payload['totals']['mainclass_count']}",
        f"main-class sizes: {payload['totals']['mainclass_size_distribution']}",
        f"rank-19/r_Q=3 exceptional main classes: {payload['totals']['rank19_r3_mainclass_count']}",
        f"errors: {payload['totals']['error_count']}",
        "",
        "Per-main-class profile:",
    ]
    for record in payload["mainclasses"]:
        lines.append(
            "- {id}: size={size}, representative={rep}, patterns={patterns}, "
            "group={group}, r_Q={rq}, E4_rank={rank}".format(
                id=record["mainclass_id"][:12],
                size=record["reduced_table_count"],
                rep=record["mainclass_representative"],
                patterns=record["pattern_distribution"],
                group=record["group_isotopy_distribution"],
                rq=record["r_Q_distribution"],
                rank=record["E4_rank_distribution"],
            )
        )
    lines += [
        "",
        "Boundary: this is a complete order-6 main-class classification of the frozen census, not an order-10 result.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    primary = json.loads(args.primary.read_text())
    by_index = {record["source_index"]: record for record in primary["records"]}
    tasks = [
        (source_index, table, by_index[source_index])
        for source_index, table in enumerate(SMALL.reduced_latin_squares(6), 1)
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(classify_task, tasks, chunksize=4))
    records.sort(key=lambda record: record["source_index"])

    grouped = defaultdict(list)
    for record in records:
        grouped[record["mainclass_id"]].append(record)
    mainclasses = []
    errors = []
    for mainclass_id, group in sorted(grouped.items()):
        representatives = {record["mainclass_representative"] for record in group}
        if len(representatives) != 1:
            errors.append(["representative_collision", mainclass_id, len(representatives)])
        mainclasses.append(
            {
                "mainclass_id": mainclass_id,
                "mainclass_representative": min(representatives),
                "reduced_table_count": len(group),
                "source_indices": [record["source_index"] for record in group],
                "pattern_distribution": dict(sorted(Counter(record["pattern"] for record in group).items())),
                "group_isotopy_distribution": {
                    str(status): count
                    for status, count in sorted(Counter(record["group_isotopic"] for record in group).items())
                },
                "r_Q_distribution": dict(sorted(Counter(record["r_Q"] for record in group).items())),
                "E4_rank_distribution": dict(sorted(Counter(record["E4_rank"] for record in group).items())),
                "four_exchange_count_distribution": dict(
                    sorted(Counter(record["four_exchange_count"] for record in group).items())
                ),
            }
        )

    payload = {
        "audit_version": "order6_exchange_mainclass_v1",
        "workers": args.workers,
        "totals": {
            "table_count": len(records),
            "mainclass_count": len(mainclasses),
            "mainclass_size_distribution": dict(
                sorted(Counter(record["reduced_table_count"] for record in mainclasses).items())
            ),
            "rank19_r3_mainclass_count": sum(
                record["r_Q_distribution"] == {3: record["reduced_table_count"]}
                and record["E4_rank_distribution"] == {19: record["reduced_table_count"]}
                for record in mainclasses
            ),
            "error_count": len(errors),
        },
        "mainclasses": mainclasses,
        "errors": errors,
        "claim_boundary": [
            "Complete for all 9,408 reduced order-6 squares.",
            "No order-10 conclusion is inferred.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
