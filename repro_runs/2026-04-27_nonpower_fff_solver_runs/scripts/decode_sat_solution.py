#!/usr/bin/env python3
"""Decode a SAT assignment into a Latin table using a variable map."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_model(path: Path) -> set[int]:
    values: set[int] = set()
    for raw in path.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(("c", "s")):
            continue
        if stripped.startswith("v"):
            stripped = stripped[1:].strip()
        for part in stripped.split():
            try:
                value = int(part)
            except ValueError:
                continue
            if value > 0:
                values.add(value)
    return values


def decode_table(var_map: dict[str, Any], true_vars: set[int]) -> tuple[list[list[int | None]], dict[str, Any]]:
    n = int(var_map["n"])
    table: list[list[int | None]] = [[None for _ in range(n)] for _ in range(n)]
    positive_cell_vars = 0
    color_true_counts = {"row_color": 0, "col_color": 0, "sym_color": 0}
    for name, var_id in var_map["var_names"].items():
        if int(var_id) not in true_vars:
            continue
        if name.startswith("x_"):
            positive_cell_vars += 1
            _, r, c, s = name.split("_")
            table[int(r)][int(c)] = int(s)
        elif name.startswith("row_color_"):
            color_true_counts["row_color"] += 1
        elif name.startswith("col_color_"):
            color_true_counts["col_color"] += 1
        elif name.startswith("sym_color_"):
            color_true_counts["sym_color"] += 1
    complete = all(value is not None for row in table for value in row)
    return table, {
        "positive_cell_vars": positive_cell_vars,
        "complete_table": complete,
        "true_color_var_counts": color_true_counts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--var-map", type=Path, required=True)
    parser.add_argument("--table-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--validator-script", type=Path)
    parser.add_argument("--validator-output", type=Path)
    parser.add_argument("--validator-summary", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    var_map = json.loads(args.var_map.read_text())
    true_vars = parse_model(args.model)
    table, decode_summary = decode_table(var_map, true_vars)
    table_payload = {
        "n": var_map["n"],
        "views": var_map["views"],
        "reduced": var_map["reduced"],
        "encoding_version": var_map["encoding_version"],
        "table": table,
        "source_model": str(args.model),
        "source_var_map": str(args.var_map),
    }
    args.table_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.table_output.write_text(json.dumps(table_payload, indent=2, sort_keys=True) + "\n")

    validator_result: dict[str, Any] | None = None
    if args.validator_script and args.validator_output and args.validator_summary:
        args.validator_output.parent.mkdir(parents=True, exist_ok=True)
        args.validator_summary.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                "python3",
                str(args.validator_script),
                "--input",
                str(args.table_output),
                "--expect-reduced",
                "--output",
                str(args.validator_output),
                "--summary",
                str(args.validator_summary),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        validator_result = {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "output": str(args.validator_output),
            "output_sha256": sha256_file(args.validator_output) if args.validator_output.exists() else None,
            "summary": str(args.validator_summary),
            "summary_sha256": sha256_file(args.validator_summary) if args.validator_summary.exists() else None,
        }

    metadata = {
        "model": {
            "path": str(args.model),
            "size_bytes": args.model.stat().st_size,
            "sha256": sha256_file(args.model),
        },
        "var_map": {
            "path": str(args.var_map),
            "size_bytes": args.var_map.stat().st_size,
            "sha256": sha256_file(args.var_map),
        },
        "table_output": {
            "path": str(args.table_output),
            "size_bytes": args.table_output.stat().st_size,
            "sha256": sha256_file(args.table_output),
        },
        "decode_summary": decode_summary,
        "validator": validator_result,
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return 0 if decode_summary["complete_table"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
