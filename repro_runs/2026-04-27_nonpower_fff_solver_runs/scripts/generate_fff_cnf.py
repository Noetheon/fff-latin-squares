#!/usr/bin/env python3
"""Generate reduced Latin-square FFF CNFs with variable maps."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from itertools import combinations
from pathlib import Path
from typing import Any


ALL_VIEWS = ("row", "col", "sym")
ENCODING_VERSION = "fff_even_cycle_coloring_v1"


class VarPool:
    def __init__(self) -> None:
        self.next_id = 1
        self.names: dict[str, int] = {}

    def var(self, name: str) -> int:
        if name not in self.names:
            self.names[name] = self.next_id
            self.next_id += 1
        return self.names[name]

    @property
    def count(self) -> int:
        return self.next_id - 1


def exactly_one(clauses: list[list[int]], vars_: list[int]) -> None:
    clauses.append(list(vars_))
    for i, left in enumerate(vars_):
        for right in vars_[i + 1 :]:
            clauses.append([-left, -right])


def exactly_k(clauses: list[list[int]], vars_: list[int], k: int) -> None:
    n = len(vars_)
    if k < 0 or k > n:
        clauses.append([])
        return
    for subset in combinations(vars_, k + 1):
        clauses.append([-lit for lit in subset])
    for subset in combinations(vars_, n - k + 1):
        clauses.append(list(subset))


def add_neq_if_both(clauses: list[list[int]], left_cell: int, right_cell: int, left_color: int, right_color: int) -> None:
    clauses.append([-left_cell, -right_cell, left_color, right_color])
    clauses.append([-left_cell, -right_cell, -left_color, -right_color])


def validate_fixed_row1(n: int, row1: list[int]) -> None:
    if n < 2:
        raise ValueError("fixed row 1 requires n >= 2")
    if len(row1) != n:
        raise ValueError(f"fixed row 1 has length {len(row1)}, expected {n}")
    if sorted(row1) != list(range(n)):
        raise ValueError("fixed row 1 is not a permutation of 0..n-1")
    if row1[0] != 1:
        raise ValueError("fixed row 1 must satisfy L(1,0)=1, so row1_permutation[0] must be 1")
    fixed_points = [idx for idx, value in enumerate(row1) if idx == value]
    if fixed_points:
        raise ValueError(f"fixed row 1 collides with reduced row 0 at columns {fixed_points}")


def validate_fixed_col1(n: int, col1: list[int], fixed_row1: list[int] | None = None) -> None:
    if n < 2:
        raise ValueError("fixed column 1 requires n >= 2")
    if len(col1) != n:
        raise ValueError(f"fixed column 1 has length {len(col1)}, expected {n}")
    if sorted(col1) != list(range(n)):
        raise ValueError("fixed column 1 is not a permutation of 0..n-1")
    if col1[0] != 1:
        raise ValueError("fixed column 1 must satisfy L(0,1)=1, so col1_permutation[0] must be 1")
    fixed_points = [idx for idx, value in enumerate(col1) if idx == value]
    if fixed_points:
        raise ValueError(f"fixed column 1 collides with reduced column 0 at rows {fixed_points}")
    if fixed_row1 is not None and col1[1] != fixed_row1[1]:
        raise ValueError(
            "fixed row 1 and fixed column 1 disagree at L(1,1): "
            f"row1[1]={fixed_row1[1]}, col1[1]={col1[1]}"
        )


def parse_row1_permutation(raw: str, n: int) -> list[int]:
    try:
        row1 = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise ValueError(f"invalid fixed row 1 permutation: {raw}") from exc
    validate_fixed_row1(n, row1)
    return row1


def parse_col1_permutation(raw: str, n: int, fixed_row1: list[int] | None = None) -> list[int]:
    try:
        col1 = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise ValueError(f"invalid fixed column 1 permutation: {raw}") from exc
    validate_fixed_col1(n, col1, fixed_row1=fixed_row1)
    return col1


def parse_compact_square(compact: str) -> list[list[int]]:
    compact = compact.strip()
    side = int(len(compact) ** 0.5)
    if side * side != len(compact):
        raise ValueError(f"compact square length is not a square: {len(compact)}")
    return [[int(compact[row * side + col]) for col in range(side)] for row in range(side)]


def normalize_table(raw: Any) -> list[list[int]]:
    if isinstance(raw, str):
        return parse_compact_square(raw)
    if isinstance(raw, list):
        return [[int(value) for value in row] for row in raw]
    raise ValueError(f"cannot parse table from object of type {type(raw).__name__}")


def validate_fixed_table(n: int, table: list[list[int]]) -> None:
    if len(table) != n or any(len(row) != n for row in table):
        raise ValueError(f"fixed table has shape {len(table)}x{len(table[0]) if table else 0}, expected {n}x{n}")
    expected = list(range(n))
    for row in table:
        if sorted(row) != expected:
            raise ValueError("fixed table row is not a permutation of 0..n-1")
    for col in range(n):
        if sorted(table[row][col] for row in range(n)) != expected:
            raise ValueError("fixed table column is not a permutation of 0..n-1")
    if table[0] != expected or [table[i][0] for i in range(n)] != expected:
        raise ValueError("fixed table is not reduced")


def load_fixed_table(path: Path, n: int, counterexample_index: int | None) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "counterexamples" in payload:
        index = 0 if counterexample_index is None else counterexample_index
        entry = payload["counterexamples"][index]
        table = normalize_table(entry.get("square") or entry.get("compact_square"))
        validate_fixed_table(n, table)
        return {
            "path": str(path),
            "counterexample_index": index,
            "source_line_number": entry.get("line_number"),
            "source_index": entry.get("index"),
            "table": table,
        }
    for key in ("table", "latin_square", "square_table", "square", "compact_square"):
        if isinstance(payload, dict) and key in payload:
            table = normalize_table(payload[key])
            validate_fixed_table(n, table)
            return {"path": str(path), "counterexample_index": None, "source_line_number": None, "source_index": None, "table": table}
    table = normalize_table(payload)
    validate_fixed_table(n, table)
    return {"path": str(path), "counterexample_index": None, "source_line_number": None, "source_index": None, "table": table}


def load_row1_case(path: Path, case_id: str, n: int) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    cases = payload["cases"] if isinstance(payload, dict) and "cases" in payload else payload
    for case in cases:
        if str(case.get("case_id")) == case_id:
            row1 = [int(value) for value in case["row1_permutation"]]
            validate_fixed_row1(n, row1)
            return dict(case, row1_permutation=row1)
    raise ValueError(f"case_id {case_id!r} not found in {path}")


def load_row1_col1_case(path: Path, case_id: str, n: int) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    cases = payload["cases"] if isinstance(payload, dict) and "cases" in payload else payload
    for case in cases:
        if str(case.get("case_id")) == case_id:
            row1 = [int(value) for value in case["row1_permutation"]]
            col1 = [int(value) for value in case["col1_permutation"]]
            validate_fixed_row1(n, row1)
            validate_fixed_col1(n, col1, fixed_row1=row1)
            return dict(case, row1_permutation=row1, col1_permutation=col1)
    raise ValueError(f"row1+col1 case_id {case_id!r} not found in {path}")


def build_cnf(
    n: int,
    views: tuple[str, ...],
    active_row_pairs: list[tuple[int, int]] | None = None,
    active_col_pairs: list[tuple[int, int]] | None = None,
    active_sym_pairs: list[tuple[int, int]] | None = None,
    fixed_row1: list[int] | None = None,
    fixed_col1: list[int] | None = None,
    color_gauge: bool = False,
    color_balance: bool = False,
    fixed_table: list[list[int]] | None = None,
) -> dict[str, Any]:
    pool = VarPool()
    clauses: list[list[int]] = []
    stats = {
        "latin_clauses": 0,
        "reduced_unit_clauses": 0,
        "fixed_row1_unit_clauses": 0,
        "fixed_col1_unit_clauses": 0,
        "fixed_table_unit_clauses": 0,
        "color_gauge_unit_clauses": 0,
        "color_balance_clauses": 0,
        "row_fff_clauses": 0,
        "col_fff_clauses": 0,
        "sym_fff_clauses": 0,
    }

    def x(r: int, c: int, s: int) -> int:
        return pool.var(f"x_{r}_{c}_{s}")

    def row_color(a: int, b: int, c: int) -> int:
        return pool.var(f"row_color_{a}_{b}_{c}")

    def col_color(c: int, d: int, r: int) -> int:
        return pool.var(f"col_color_{c}_{d}_{r}")

    def sym_color(u: int, v: int, j: int) -> int:
        return pool.var(f"sym_color_{u}_{v}_{j}")

    if active_row_pairs is None:
        active_row_pairs = [(a, b) for a in range(n) for b in range(a + 1, n)] if "row" in views else []
    if active_col_pairs is None:
        active_col_pairs = [(c, d) for c in range(n) for d in range(c + 1, n)] if "col" in views else []
    if active_sym_pairs is None:
        active_sym_pairs = [(u, v) for u in range(n) for v in range(u + 1, n)] if "sym" in views else []

    before = len(clauses)
    for r in range(n):
        for c in range(n):
            exactly_one(clauses, [x(r, c, s) for s in range(n)])
    for r in range(n):
        for s in range(n):
            exactly_one(clauses, [x(r, c, s) for c in range(n)])
    for c in range(n):
        for s in range(n):
            exactly_one(clauses, [x(r, c, s) for r in range(n)])
    stats["latin_clauses"] = len(clauses) - before

    before = len(clauses)
    for j in range(n):
        clauses.append([x(0, j, j)])
    for i in range(n):
        clauses.append([x(i, 0, i)])
    stats["reduced_unit_clauses"] = len(clauses) - before

    if fixed_row1 is not None:
        validate_fixed_row1(n, fixed_row1)
        before = len(clauses)
        for c, symbol in enumerate(fixed_row1):
            clauses.append([x(1, c, symbol)])
        stats["fixed_row1_unit_clauses"] = len(clauses) - before

    if fixed_col1 is not None:
        validate_fixed_col1(n, fixed_col1, fixed_row1=fixed_row1)
        before = len(clauses)
        for r, symbol in enumerate(fixed_col1):
            clauses.append([x(r, 1, symbol)])
        stats["fixed_col1_unit_clauses"] = len(clauses) - before

    if fixed_table is not None:
        validate_fixed_table(n, fixed_table)
        before = len(clauses)
        for r, row in enumerate(fixed_table):
            for c, symbol in enumerate(row):
                clauses.append([x(r, c, symbol)])
        stats["fixed_table_unit_clauses"] = len(clauses) - before

    if active_row_pairs:
        before = len(clauses)
        for a, b in active_row_pairs:
            for c in range(n):
                left_color = row_color(a, b, c)
                for d in range(n):
                    right_color = row_color(a, b, d)
                    for s in range(n):
                        add_neq_if_both(clauses, x(a, c, s), x(b, d, s), left_color, right_color)
        stats["row_fff_clauses"] = len(clauses) - before

    if active_col_pairs:
        before = len(clauses)
        for c, d in active_col_pairs:
            for r in range(n):
                left_color = col_color(c, d, r)
                for t in range(n):
                    right_color = col_color(c, d, t)
                    for s in range(n):
                        add_neq_if_both(clauses, x(r, c, s), x(t, d, s), left_color, right_color)
        stats["col_fff_clauses"] = len(clauses) - before

    if active_sym_pairs:
        before = len(clauses)
        for u, v in active_sym_pairs:
            for j in range(n):
                left_color = sym_color(u, v, j)
                for k in range(n):
                    right_color = sym_color(u, v, k)
                    for r in range(n):
                        add_neq_if_both(clauses, x(r, j, u), x(r, k, v), left_color, right_color)
        stats["sym_fff_clauses"] = len(clauses) - before

    if color_gauge:
        before = len(clauses)
        for a, b in active_row_pairs:
            clauses.append([-row_color(a, b, 0)])
        for c, d in active_col_pairs:
            clauses.append([-col_color(c, d, 0)])
        for u, v in active_sym_pairs:
            clauses.append([-sym_color(u, v, 0)])
        stats["color_gauge_unit_clauses"] = len(clauses) - before

    if color_balance:
        if n % 2 == 1:
            raise ValueError("color balance is only supported for even n")
        before = len(clauses)
        target = n // 2
        for a, b in active_row_pairs:
            exactly_k(clauses, [row_color(a, b, c) for c in range(n)], target)
        for c, d in active_col_pairs:
            exactly_k(clauses, [col_color(c, d, r) for r in range(n)], target)
        for u, v in active_sym_pairs:
            exactly_k(clauses, [sym_color(u, v, j) for j in range(n)], target)
        stats["color_balance_clauses"] = len(clauses) - before

    prefix_counts = {"cell": 0, "row_color": 0, "col_color": 0, "sym_color": 0}
    for name in pool.names:
        if name.startswith("x_"):
            prefix_counts["cell"] += 1
        elif name.startswith("row_color_"):
            prefix_counts["row_color"] += 1
        elif name.startswith("col_color_"):
            prefix_counts["col_color"] += 1
        elif name.startswith("sym_color_"):
            prefix_counts["sym_color"] += 1

    return {
        "n": n,
        "views": list(views),
        "reduced": True,
        "encoding_version": ENCODING_VERSION,
        "fixed_row1_permutation": fixed_row1,
        "fixed_col1_permutation": fixed_col1,
        "color_gauge": color_gauge,
        "color_balance": color_balance,
        "active_row_pairs": active_row_pairs,
        "active_col_pairs": active_col_pairs,
        "active_sym_pairs": active_sym_pairs,
        "var_count": pool.count,
        "clauses": clauses,
        "clause_count": len(clauses),
        "clause_stats": stats,
        "var_prefix_counts": prefix_counts,
        "var_names": pool.names,
    }


def dimacs_text(var_count: int, clauses: list[list[int]]) -> str:
    lines = [f"p cnf {var_count} {len(clauses)}"]
    lines.extend(" ".join(str(lit) for lit in clause) + " 0" for clause in clauses)
    return "\n".join(lines) + "\n"


def parse_views(raw: str) -> tuple[str, ...]:
    views = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not views:
        raise ValueError("at least one view is required")
    unknown = sorted(set(views) - set(ALL_VIEWS))
    if unknown:
        raise ValueError(f"unknown views: {unknown}")
    return views


def normalize_pair(pair: tuple[int, int], n: int, *, label: str) -> tuple[int, int]:
    left, right = pair
    if not (0 <= left < n and 0 <= right < n):
        raise ValueError(f"{label} pair {pair} is outside 0..{n - 1}")
    if left == right:
        raise ValueError(f"{label} pair {pair} must have distinct entries")
    return (left, right) if left < right else (right, left)


def parse_pair_token(raw: str, n: int, *, label: str) -> tuple[int, int]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"invalid {label} pair token {raw!r}; expected 'u,v'")
    try:
        pair = (int(parts[0]), int(parts[1]))
    except ValueError as exc:
        raise ValueError(f"invalid {label} pair token {raw!r}; expected integers") from exc
    return normalize_pair(pair, n, label=label)


def load_pair_list(path: Path, n: int, *, label: str) -> list[tuple[int, int]]:
    payload = json.loads(path.read_text())
    raw_pairs = payload.get("pairs", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_pairs, list):
        raise ValueError(f"{label} pair JSON must be a list or an object with 'pairs'")
    pairs: list[tuple[int, int]] = []
    for item in raw_pairs:
        if isinstance(item, str):
            pairs.append(parse_pair_token(item, n, label=label))
        elif isinstance(item, list) and len(item) == 2:
            pairs.append(normalize_pair((int(item[0]), int(item[1])), n, label=label))
        elif isinstance(item, dict) and {"u", "v"} <= set(item):
            pairs.append(normalize_pair((int(item["u"]), int(item["v"])), n, label=label))
        else:
            raise ValueError(f"cannot parse {label} pair entry: {item!r}")
    return sorted(set(pairs))


def make_summary(result: dict[str, Any]) -> str:
    lines = [
        "FFF CNF generation summary",
        "",
        f"n: {result['n']}",
        f"views: {','.join(result['views'])}",
        f"encoding_version: {result['encoding_version']}",
        f"reduced: {result['reduced']}",
        f"color_gauge: {result.get('color_gauge')}",
        f"color_balance: {result.get('color_balance')}",
        f"active_row_pairs: {len(result.get('active_row_pairs') or [])}",
        f"active_col_pairs: {len(result.get('active_col_pairs') or [])}",
        f"active_sym_pairs: {len(result.get('active_sym_pairs') or [])}",
        f"fixed_row1_case_id: {result.get('fixed_row1_case_id')}",
        f"fixed_row1_col1_case_id: {result.get('fixed_row1_col1_case_id')}",
        f"fixed_row1_permutation: {result.get('fixed_row1_permutation')}",
        f"fixed_col1_permutation: {result.get('fixed_col1_permutation')}",
        f"fixed_table_input: {result.get('fixed_table_input')}",
        f"variables: {result['var_count']}",
        f"clauses: {result['clause_count']}",
        f"cnf_sha256: {result['cnf']['sha256']}",
        f"var_map_sha256: {result['var_map']['sha256']}",
        "",
        "Clause stats:",
    ]
    for key, value in result["clause_stats"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--views", required=True)
    parser.add_argument("--cnf-output", type=Path, required=True)
    parser.add_argument("--var-map-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--fixed-row1-permutation")
    parser.add_argument("--fixed-row1-cases-json", type=Path)
    parser.add_argument("--fixed-row1-case-id")
    parser.add_argument("--fixed-col1-permutation")
    parser.add_argument("--fixed-row1-col1-cases-json", type=Path)
    parser.add_argument("--fixed-row1-col1-case-id")
    parser.add_argument("--color-gauge", action="store_true")
    parser.add_argument("--color-balance", "--balanced-colors", dest="color_balance", action="store_true")
    parser.add_argument("--sym-pairs", nargs="*")
    parser.add_argument("--sym-pairs-json", type=Path)
    parser.add_argument("--fixed-table-json", type=Path)
    parser.add_argument("--fixed-table-counterexample-index", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    views = parse_views(args.views)
    fixed_row1 = None
    fixed_col1 = None
    fixed_table_info: dict[str, Any] | None = None
    fixed_row1_case: dict[str, Any] | None = None
    fixed_row1_col1_case: dict[str, Any] | None = None
    active_row_pairs = [(a, b) for a in range(args.n) for b in range(a + 1, args.n)] if "row" in views else []
    active_col_pairs = [(c, d) for c in range(args.n) for d in range(c + 1, args.n)] if "col" in views else []
    if args.sym_pairs and args.sym_pairs_json:
        raise ValueError("use either --sym-pairs or --sym-pairs-json, not both")
    if args.sym_pairs_json:
        active_sym_pairs = load_pair_list(args.sym_pairs_json, args.n, label="symbol")
    elif args.sym_pairs:
        active_sym_pairs = sorted({parse_pair_token(token, args.n, label="symbol") for token in args.sym_pairs})
    else:
        active_sym_pairs = [(u, v) for u in range(args.n) for v in range(u + 1, args.n)] if "sym" in views else []
    if args.fixed_row1_col1_cases_json:
        if not args.fixed_row1_col1_case_id:
            raise ValueError("--fixed-row1-col1-cases-json requires --fixed-row1-col1-case-id")
        if args.fixed_row1_permutation or args.fixed_row1_cases_json or args.fixed_col1_permutation:
            raise ValueError("row1+col1 case JSON cannot be combined with other fixed row/column options")
        fixed_row1_col1_case = load_row1_col1_case(args.fixed_row1_col1_cases_json, args.fixed_row1_col1_case_id, args.n)
        fixed_row1 = fixed_row1_col1_case["row1_permutation"]
        fixed_col1 = fixed_row1_col1_case["col1_permutation"]
    if args.fixed_row1_permutation and args.fixed_row1_cases_json:
        raise ValueError("use either --fixed-row1-permutation or --fixed-row1-cases-json, not both")
    if args.fixed_row1_col1_cases_json:
        pass
    elif args.fixed_row1_cases_json:
        if not args.fixed_row1_case_id:
            raise ValueError("--fixed-row1-cases-json requires --fixed-row1-case-id")
        fixed_row1_case = load_row1_case(args.fixed_row1_cases_json, args.fixed_row1_case_id, args.n)
        fixed_row1 = fixed_row1_case["row1_permutation"]
    elif args.fixed_row1_permutation:
        fixed_row1 = parse_row1_permutation(args.fixed_row1_permutation, args.n)
    if args.fixed_col1_permutation:
        fixed_col1 = parse_col1_permutation(args.fixed_col1_permutation, args.n, fixed_row1=fixed_row1)
    if args.fixed_table_json:
        fixed_table_info = load_fixed_table(args.fixed_table_json, args.n, args.fixed_table_counterexample_index)

    cnf = build_cnf(
        args.n,
        views,
        active_row_pairs=active_row_pairs,
        active_col_pairs=active_col_pairs,
        active_sym_pairs=active_sym_pairs,
        fixed_row1=fixed_row1,
        fixed_col1=fixed_col1,
        color_gauge=args.color_gauge,
        color_balance=args.color_balance,
        fixed_table=fixed_table_info["table"] if fixed_table_info else None,
    )
    dimacs = dimacs_text(cnf["var_count"], cnf["clauses"]).encode("ascii")
    var_map = {
        "n": cnf["n"],
        "views": cnf["views"],
        "reduced": True,
        "encoding_version": ENCODING_VERSION,
        "color_gauge": args.color_gauge,
        "color_balance": args.color_balance,
        "active_row_pairs": active_row_pairs,
        "active_col_pairs": active_col_pairs,
        "active_sym_pairs": active_sym_pairs,
        "var_count": cnf["var_count"],
        "var_prefix_counts": cnf["var_prefix_counts"],
        "var_names": cnf["var_names"],
    }
    if fixed_row1 is not None:
        var_map["fixed_row1_permutation"] = fixed_row1
        var_map["fixed_row1_case_id"] = args.fixed_row1_case_id
        var_map["fixed_row1_case"] = fixed_row1_case
    if fixed_col1 is not None:
        var_map["fixed_col1_permutation"] = fixed_col1
    if fixed_row1_col1_case is not None:
        var_map["fixed_row1_col1_case_id"] = args.fixed_row1_col1_case_id
        var_map["fixed_row1_col1_case"] = fixed_row1_col1_case
    if fixed_table_info is not None:
        var_map["fixed_table_input"] = {
            key: value for key, value in fixed_table_info.items() if key != "table"
        }
        var_map["fixed_table"] = fixed_table_info["table"]
    var_map_bytes = (json.dumps(var_map, indent=2, sort_keys=True) + "\n").encode("utf-8")

    args.cnf_output.parent.mkdir(parents=True, exist_ok=True)
    args.var_map_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.cnf_output.write_bytes(dimacs)
    args.var_map_output.write_bytes(var_map_bytes)

    result = {
        "n": cnf["n"],
        "views": cnf["views"],
        "reduced": True,
        "encoding_version": ENCODING_VERSION,
        "color_gauge": args.color_gauge,
        "color_balance": args.color_balance,
        "active_row_pairs": active_row_pairs,
        "active_col_pairs": active_col_pairs,
        "active_sym_pairs": active_sym_pairs,
        "fixed_row1_permutation": fixed_row1,
        "fixed_col1_permutation": fixed_col1,
        "fixed_table_input": {key: value for key, value in fixed_table_info.items() if key != "table"} if fixed_table_info else None,
        "fixed_row1_case_id": args.fixed_row1_case_id,
        "fixed_row1_case": fixed_row1_case,
        "fixed_row1_col1_case_id": args.fixed_row1_col1_case_id,
        "fixed_row1_col1_case": fixed_row1_col1_case,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "elapsed_seconds": time.time() - start,
        "var_count": cnf["var_count"],
        "var_prefix_counts": cnf["var_prefix_counts"],
        "clause_count": cnf["clause_count"],
        "clause_stats": cnf["clause_stats"],
        "cnf": {
            "path": str(args.cnf_output),
            "size_bytes": args.cnf_output.stat().st_size,
            "sha256": sha256_bytes(dimacs),
        },
        "var_map": {
            "path": str(args.var_map_output),
            "size_bytes": args.var_map_output.stat().st_size,
            "sha256": sha256_bytes(var_map_bytes),
        },
    }
    args.metadata_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(make_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
