#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
PRIMES = (1000003, 1000033)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C98 = load_module(
    "c98_common_mode",
    ROOT
    / "repro_runs/2026-08-11_fff_common_mode_gradient/scripts/audit_common_mode_gradient.py",
)
C97 = C98.C97
SURFACE = C98.SURFACE
SMALL = C98.SMALL
OPPOSITE_ROLE = C98.OPPOSITE_ROLE
rank_mod = C98.rank_mod
exact_integer_intersection_witnesses = C98.exact_integer_intersection_witnesses


def component_count(adjacency: list[set[int]]) -> int:
    seen = set()
    count = 0
    for start in range(len(adjacency)):
        if start in seen:
            continue
        count += 1
        stack = [start]
        seen.add(start)
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    return count


def line_sums(table: list[list[int]], vector: list[int]) -> dict[str, list[int]]:
    n = len(table)
    rows = [sum(vector[n * row + col] for col in range(n)) for row in range(n)]
    cols = [sum(vector[n * row + col] for row in range(n)) for col in range(n)]
    syms = [
        sum(
            vector[n * row + col]
            for row in range(n)
            for col in range(n)
            if table[row][col] == symbol
        )
        for symbol in range(n)
    ]
    return {"row": rows, "col": cols, "sym": syms}


def matrix_vector(rows: list[list[int]], vector: list[int]) -> list[int]:
    return [sum(value * weight for value, weight in zip(row, vector)) for row in rows]


def analyze_task(task: tuple[str, int, list[list[int]]]) -> dict:
    dataset, source_index, table = task
    n = len(table)
    atoms, point_to_atom, _ = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_groups = SURFACE["build_dual_involutions"](flags)
    errors = [["dual_edge_group", *entry] for entry in bad_groups]

    flag_adjacency = [set() for _ in flags]
    for alpha in alphas:
        for flag, neighbor in enumerate(alpha):
            flag_adjacency[flag].add(neighbor)
    c_value = component_count(flag_adjacency)

    atom_ids = sorted({atom for flag in flags for atom in flag["atoms"]})
    atom_index = {atom: index for index, atom in enumerate(atom_ids)}
    atom_adjacency = [set() for _ in atom_ids]
    atom_rows = []
    cell_rows = []
    joint_rows = []
    for flag in flags:
        atom_row = [0] * len(atom_ids)
        cell_row = [0] * (n * n)
        for atom in flag["atoms"]:
            atom_row[atom_index[atom]] = 1
        for cell in flag["cells"]:
            cell_row[cell] = 1
        atom_rows.append(atom_row)
        cell_rows.append(cell_row)
        joint_rows.append(atom_row + cell_row)

    atom_by_id = {atom["id"]: atom for atom in atoms}
    support_rows = [[0] * len(atom_ids) for _ in range(n * n)]
    for atom_id in atom_ids:
        column = atom_index[atom_id]
        cell_mask = atom_by_id[atom_id]["cell_mask"]
        for cell in range(n * n):
            if (cell_mask >> cell) & 1:
                support_rows[cell][column] = 1

    d_rows = []
    for flag, atom_row in zip(flags, atom_rows):
        d_row = [(n - 3) * value for value in atom_row]
        for cell in flag["cells"]:
            for column, value in enumerate(support_rows[cell]):
                d_row[column] -= value
        d_rows.append(d_row)

    gradient_rows = []
    dual_edge_count = 0
    for colour, alpha in enumerate(alphas):
        role = OPPOSITE_ROLE[colour]
        for flag, neighbor in enumerate(alpha):
            if flag > neighbor:
                continue
            dual_edge_count += 1
            left_atom = atom_index[flags[flag]["atoms"][colour]]
            right_atom = atom_index[flags[neighbor]["atoms"][colour]]
            atom_adjacency[left_atom].add(right_atom)
            atom_adjacency[right_atom].add(left_atom)
            row = [0] * (len(atom_ids) + n * n)
            row[left_atom] += 1
            row[right_atom] -= 1
            row[len(atom_ids) + flags[flag]["cells"][role]] -= 1
            row[len(atom_ids) + flags[neighbor]["cells"][role]] += 1
            gradient_rows.append(row)

    transition_components = component_count(atom_adjacency)
    if transition_components != 3 * c_value:
        errors.append(
            [
                "atom_transition_component_count",
                transition_components,
                3 * c_value,
            ]
        )

    rank_p = len(atom_ids) - 2 * c_value
    joint_r_by_prime = {}
    gradient_r_by_prime = {}
    d_nullity_by_prime = {}
    for prime in PRIMES:
        joint_r_by_prime[str(prime)] = (
            rank_p + n * n - rank_mod(joint_rows, prime)
        )
        gradient_r_by_prime[str(prime)] = (
            len(atom_ids)
            + n * n
            - rank_mod(gradient_rows, prime)
            - transition_components
        )

    observed = set(joint_r_by_prime.values()) | set(gradient_r_by_prime.values())
    if len(observed) != 1:
        errors.append(
            [
                "global_dimension_disagreement",
                joint_r_by_prime,
                gradient_r_by_prime,
            ]
        )
    r_value = joint_r_by_prime[str(PRIMES[0])]
    if r_value < 1:
        errors.append(["missing_constant_mode", r_value])

    predicted_d_nullity = 2 * c_value + r_value - 1
    for prime in PRIMES:
        d_nullity_by_prime[str(prime)] = len(atom_ids) - rank_mod(d_rows, prime)
    if set(d_nullity_by_prime.values()) != {predicted_d_nullity}:
        errors.append(
            ["atom_only_nullity_disagreement", d_nullity_by_prime, predicted_d_nullity]
        )

    row_atom_indicator = [
        int(atom_by_id[atom_id]["view"] == "row") for atom_id in atom_ids
    ]
    constant_atom_vector = [3 * value for value in row_atom_indicator]
    constant_cell_vector = [1] * (n * n)
    constant_q_signal = matrix_vector(support_rows, constant_atom_vector)
    if matrix_vector(atom_rows, constant_atom_vector) != matrix_vector(
        cell_rows, constant_cell_vector
    ):
        errors.append(["constant_common_mode_failure"])
    if constant_q_signal != [3 * (n - 1)] * (n * n):
        errors.append(["constant_endpoint_identity_failure"])

    witnesses = exact_integer_intersection_witnesses(
        atom_rows, cell_rows, r_value
    )
    if len(witnesses) != max(0, r_value - 1):
        errors.append(
            ["rational_intersection_not_certified", r_value, len(witnesses)]
        )

    witness_records = []
    for witness_id, witness in enumerate(witnesses, 1):
        atom_vector = witness["atom_vector"]
        cell_vector = witness["cell_vector"]
        atom_signal = matrix_vector(atom_rows, atom_vector)
        cell_signal = matrix_vector(cell_rows, cell_vector)
        if atom_signal != cell_signal or len(set(atom_signal)) == 1:
            errors.append(["integer_witness_failure", witness_id])
        sums = line_sums(table, cell_vector)
        all_line_sums = sums["row"] + sums["col"] + sums["sym"]
        balanced = len(set(all_line_sums)) == 1
        common_line_sum = all_line_sums[0] if balanced else None
        q_signal = matrix_vector(support_rows, atom_vector)
        endpoint_expected = [
            (n - 3) * value + 2 * common_line_sum for value in cell_vector
        ] if balanced else []
        endpoint_identity = balanced and q_signal == endpoint_expected
        if not endpoint_identity:
            errors.append(["endpoint_identity_failure", witness_id])

        centered_cell_vector = [
            n * value - common_line_sum for value in cell_vector
        ] if balanced else []
        centered_atom_vector = [
            n * value - 3 * common_line_sum * row_atom_indicator[index]
            for index, value in enumerate(atom_vector)
        ] if balanced else []
        centered_sums = line_sums(table, centered_cell_vector) if balanced else {}
        centered_identity = bool(balanced) and (
            matrix_vector(atom_rows, centered_atom_vector)
            == matrix_vector(cell_rows, centered_cell_vector)
            and matrix_vector(support_rows, centered_atom_vector)
            == [(n - 3) * value for value in centered_cell_vector]
            and all(value == 0 for values in centered_sums.values() for value in values)
        )
        if not centered_identity:
            errors.append(["centered_identity_failure", witness_id])
        witness_records.append(
            {
                "witness_id": witness_id,
                "atom_vector": atom_vector,
                "cell_vector": cell_vector,
                "signal_distribution": witness["signal_distribution"],
                "line_sums": sums,
                "line_balanced": balanced,
                "common_line_sum": common_line_sum,
                "endpoint_identity": endpoint_identity,
                "centered_identity": centered_identity,
            }
        )

    return {
        "dataset": dataset,
        "source_index": source_index,
        "order": n,
        "component_count": c_value,
        "atom_count": len(atom_ids),
        "flag_count": len(flags),
        "dual_edge_count": dual_edge_count,
        "transition_component_count": transition_components,
        "joint_r_by_prime": joint_r_by_prime,
        "gradient_r_by_prime": gradient_r_by_prime,
        "d_nullity_by_prime": d_nullity_by_prime,
        "predicted_d_nullity": predicted_d_nullity,
        "r_Q": r_value,
        "kappa_Q": r_value - 1,
        "schur_nullity_Q": 2 * c_value + r_value,
        "integer_witness_count": len(witness_records),
        "integer_witnesses": witness_records,
        "error_count": len(errors),
        "errors": errors,
    }


def table_tasks(fff_metadata: Path, n10_corpus: Path) -> Iterable[tuple]:
    for source_index, table in enumerate(SMALL["reduced_latin_squares"](4), 1):
        yield "order4_complete", source_index, table
    for source_index, table in enumerate(SMALL["reduced_latin_squares"](6), 1):
        yield "order6_complete", source_index, table
    for source_index, table in C97["load_n8"](fff_metadata):
        yield "order8_fff_complete", source_index, table
    for source_index, table, _ in C98.PAIR["FLAG"]["n10_tables"](n10_corpus):
        yield "order10_tracked_partial", source_index, table


def summarize(records: list[dict]) -> dict:
    by_dataset = {}
    for dataset in sorted({record["dataset"] for record in records}):
        current = [record for record in records if record["dataset"] == dataset]
        distribution = Counter(record["r_Q"] for record in current)
        exceptions = [record for record in current if record["r_Q"] > 1]
        witness_count = sum(record["integer_witness_count"] for record in current)
        line_balanced_count = sum(
            witness["line_balanced"]
            for record in exceptions
            for witness in record["integer_witnesses"]
        )
        by_dataset[dataset] = {
            "table_count": len(current),
            "component_count": sum(record["component_count"] for record in current),
            "flag_count": sum(record["flag_count"] for record in current),
            "dual_edge_count": sum(record["dual_edge_count"] for record in current),
            "r_Q_distribution": {
                str(key): value for key, value in sorted(distribution.items())
            },
            "nonconstant_table_count": len(exceptions),
            "integer_witness_count": witness_count,
            "line_balanced_witness_count": line_balanced_count,
            "max_r_Q": max(distribution),
            "error_count": sum(record["error_count"] for record in current),
            "exceptional_tables": exceptions,
        }
    totals = {
        "table_count": len(records),
        "component_count": sum(record["component_count"] for record in records),
        "flag_count": sum(record["flag_count"] for record in records),
        "dual_edge_count": sum(record["dual_edge_count"] for record in records),
        "nonconstant_table_count": sum(
            record["r_Q"] > 1 for record in records
        ),
        "integer_witness_count": sum(
            record["integer_witness_count"] for record in records
        ),
        "line_balanced_witness_count": sum(
            witness["line_balanced"]
            for record in records
            for witness in record["integer_witnesses"]
        ),
        "endpoint_identity_witness_count": sum(
            witness["endpoint_identity"]
            for record in records
            for witness in record["integer_witnesses"]
        ),
        "centered_identity_witness_count": sum(
            witness["centered_identity"]
            for record in records
            for witness in record["integer_witnesses"]
        ),
        "atom_only_nullity_table_count": sum(
            set(record["d_nullity_by_prime"].values())
            == {record["predicted_d_nullity"]}
            for record in records
        ),
        "error_count": sum(record["error_count"] for record in records),
    }
    return {"totals": totals, "datasets": by_dataset}


def write_summary(path: Path, payload: dict) -> None:
    lines = ["Global common-mode audit", ""]
    for key, value in payload["totals"].items():
        lines.append(f"{key.replace('_', ' ')}: {value}")
    lines.append("")
    for dataset, data in payload["datasets"].items():
        lines.extend(
            [
                dataset,
                f"- tables/components/flags: {data['table_count']} / {data['component_count']} / {data['flag_count']}",
                f"- r_Q distribution: {data['r_Q_distribution']}",
                f"- nonconstant tables: {data['nonconstant_table_count']}",
                f"- integer witnesses: {data['integer_witness_count']}",
                f"- line-balanced witnesses: {data['line_balanced_witness_count']} / {data['integer_witness_count']}",
                f"- max r_Q: {data['max_r_Q']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Boundary:",
            "- C99 is a rigorous global intersection/Schur theorem; distributions are frozen-corpus facts.",
            "- The endpoint contraction, line balance, centering, and atom-only kernel formula are rigorous.",
            "- The tracked order-10 corpus is partial; C38 remains open and C40 absent.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    tasks = list(table_tasks(args.fff_metadata, args.n10_corpus))
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(analyze_task, tasks, chunksize=8))
    records.sort(key=lambda record: (record["dataset"], record["source_index"]))
    aggregate = summarize(records)
    payload = {
        "audit_version": "global_common_mode_v2",
        "prime_fields": list(PRIMES),
        "workers": args.workers,
        "totals": aggregate["totals"],
        "datasets": aggregate["datasets"],
        "claim_boundary": [
            "C99 gives an exact global intersection and Schur-nullity formula.",
            "C99 also gives universal line balance, trade-space centering, and an atom-only kernel formula.",
            "Finite dimension distributions and witness shapes are corpus facts.",
            "The tracked order-10 corpus is partial; C38 remains open and C40 absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(args.summary, payload)
    return 1 if payload["totals"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
