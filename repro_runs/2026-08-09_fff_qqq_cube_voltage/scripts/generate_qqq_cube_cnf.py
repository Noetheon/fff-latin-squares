#!/usr/bin/env python3
"""Generate a QQQ CNF with Row1 and optional fixed-cell cube units.

The frozen upstream QQQ generator is invoked first. This wrapper then appends
unit clauses using its documented cell-variable formula and records both the
upstream and final hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fixed_cell(raw: str, n: int) -> tuple[int, int, int]:
    values = tuple(int(part) for part in raw.split(","))
    if len(values) != 3 or any(value < 0 or value >= n for value in values):
        raise ValueError(f"invalid fixed cell {raw!r}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-generator", type=Path, required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--views", default="row,col,sym")
    parser.add_argument("--fixed-row1-permutation", required=True)
    parser.add_argument("--fixed-cell", action="append", default=[])
    parser.add_argument("--cnf-output", type=Path, required=True)
    parser.add_argument("--mapping-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    n = args.n
    row1 = [int(value) for value in args.fixed_row1_permutation.split(",")]
    if len(row1) != n or sorted(row1) != list(range(n)) or row1[0] != 1:
        raise ValueError("invalid fixed Row1 permutation")
    fixed_cells = [parse_fixed_cell(raw, n) for raw in args.fixed_cell]
    assignments: dict[tuple[int, int], int] = {}
    for row, col, symbol in fixed_cells:
        previous = assignments.setdefault((row, col), symbol)
        if previous != symbol:
            raise ValueError("conflicting fixed-cell assignments")
        if row == 0 and symbol != col:
            raise ValueError("fixed cell conflicts with reduced first row")
        if col == 0 and symbol != row:
            raise ValueError("fixed cell conflicts with reduced first column")
        if row == 1 and symbol != row1[col]:
            raise ValueError("fixed cell conflicts with fixed Row1")

    args.cnf_output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="order8_qqq_cube_") as temporary:
        temp = Path(temporary)
        base_cnf = temp / "base.cnf"
        base_mapping = temp / "base_mapping.json"
        base_metadata = temp / "base_metadata.json"
        base_summary = temp / "base_summary.txt"
        command = [
            "python3", str(args.upstream_generator), "--n", str(n),
            "--views", args.views, "--power-encoding", "guarded_transition",
            "--fixed-row1-permutation", args.fixed_row1_permutation,
            "--cnf-output", str(base_cnf), "--mapping-output", str(base_mapping),
            "--metadata-output", str(base_metadata), "--summary-output", str(base_summary),
        ]
        subprocess.run(command, check=True)
        base_meta = json.loads(base_metadata.read_text())
        first, *body = base_cnf.read_text(encoding="ascii").splitlines()
        marker, kind, variable_count, clause_count = first.split()
        if (marker, kind) != ("p", "cnf"):
            raise ValueError("upstream output is not DIMACS CNF")
        units = []
        for row, col, symbol in fixed_cells:
            variable = 1 + (row * n + col) * n + symbol
            units.append(f"{variable} 0")
        final_lines = [f"p cnf {variable_count} {int(clause_count) + len(units)}", *body, *units]
        args.cnf_output.write_text("\n".join(final_lines) + "\n", encoding="ascii")
        args.mapping_output.write_text(base_mapping.read_text())

    metadata = {
        "encoding_version": "qqq_power_fixedpoint_v2_guarded_transition_fixed_cell_cube_v1",
        "n": n,
        "views": args.views.split(","),
        "reduced": True,
        "fixed_row1_permutation": row1,
        "fixed_cells": [list(cell) for cell in fixed_cells],
        "variables": int(variable_count),
        "clauses": int(clause_count) + len(units),
        "upstream_generator": {
            "path": str(args.upstream_generator),
            "sha256": sha256(args.upstream_generator),
        },
        "upstream_base_cnf_sha256": base_meta["cnf"]["sha256"],
        "cnf": {
            "path": str(args.cnf_output),
            "sha256": sha256(args.cnf_output),
            "size_bytes": args.cnf_output.stat().st_size,
        },
        "mapping": {
            "path": str(args.mapping_output),
            "sha256": sha256(args.mapping_output),
        },
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary_output.write_text(
        "QQQ fixed-cell cube CNF\n\n"
        f"n: {n}\nviews: {args.views}\nfixed_row1: {row1}\n"
        f"fixed_cells: {metadata['fixed_cells']}\nvariables: {metadata['variables']}\n"
        f"clauses: {metadata['clauses']}\ncnf_sha256: {metadata['cnf']['sha256']}\n"
        f"upstream_generator_sha256: {metadata['upstream_generator']['sha256']}\n"
    )


if __name__ == "__main__":
    main()
