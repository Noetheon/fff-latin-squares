#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = RUN_ROOT / "scripts"
RESULTS = RUN_ROOT / "results"


def load_latin_trade_module():
    path = SCRIPTS / "latin_trade_search.py"
    spec = importlib.util.spec_from_file_location("latin_trade_search_runlocal", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tuple_key_dict_repr(mapping: dict[str, int]) -> str:
    converted = {ast.literal_eval(k): v for k, v in mapping.items()}
    return repr(converted)


def write_summary(result: dict) -> str:
    lines: list[str] = []
    lines.append("Exact computation summary for odd-cycle two-line trades")
    lines.append("======================================================")
    lines.append("")
    lines.append("Orders tested exhaustively via reduced Latin squares:")
    for order in result["orders"]:
        n = order["n"]
        patterns = order["patterns_any_pairs"]
        if n in (2, 4):
            lines.append(
                f"- n={n}: reduced count {order['reduced_count']}; "
                f"patterns over (row, col, sym): {tuple_key_dict_repr(patterns)}"
            )
        else:
            lines.append(
                f"- n={n}: reduced count {order['reduced_count']}; "
                "patterns over (row, col, sym):"
            )
            for key, value in patterns.items():
                lines.append(f"    {key}: {value}")
    lines.append("")
    lines.append("For n=6, using only the first perfect matching of the standard round-robin 1-factorization:")
    n6 = next(order for order in result["orders"] if order["n"] == 6)
    for key, value in n6["patterns_first_factor_only"].items():
        lines.append(f"    {key}: {value}")
    lines.append("")
    lines.append("Cayley tables of cyclic groups:")
    for group in ("Z2", "Z4", "Z6", "Z8"):
        values = result["group_counterexamples"][group]
        if values["row"] or values["col"] or values["sym"]:
            lines.append(f"- {group}: odd-cycle trade exists in rows, columns, and symbols")
        else:
            lines.append(f"- {group}: no odd-cycle trade in rows, columns, or symbols")
    return "\n".join(lines)


def main() -> int:
    module = load_latin_trade_module()
    result = {
        "orders": [module.summarize_order(n) for n in (2, 4, 6)],
        "group_counterexamples": {
            "Z2": {
                "row": module.has_odd_cycle_view(module.cayley_z(2), "row"),
                "col": module.has_odd_cycle_view(module.cayley_z(2), "col"),
                "sym": module.has_odd_cycle_view(module.cayley_z(2), "sym"),
            },
            "Z4": {
                "row": module.has_odd_cycle_view(module.cayley_z(4), "row"),
                "col": module.has_odd_cycle_view(module.cayley_z(4), "col"),
                "sym": module.has_odd_cycle_view(module.cayley_z(4), "sym"),
            },
            "Z8": {
                "row": module.has_odd_cycle_view(module.cayley_z(8), "row"),
                "col": module.has_odd_cycle_view(module.cayley_z(8), "col"),
                "sym": module.has_odd_cycle_view(module.cayley_z(8), "sym"),
            },
            "Z6": {
                "row": module.has_odd_cycle_view(module.cayley_z(6), "row"),
                "col": module.has_odd_cycle_view(module.cayley_z(6), "col"),
                "sym": module.has_odd_cycle_view(module.cayley_z(6), "sym"),
            },
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "latin_trade_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "latin_trade_summary.txt").write_text(write_summary(result) + "\n", encoding="utf-8")

    n2 = next(order for order in result["orders"] if order["n"] == 2)
    n4 = next(order for order in result["orders"] if order["n"] == 4)
    n6 = next(order for order in result["orders"] if order["n"] == 6)
    claims = {
        "C06_n2_fff": n2["patterns_any_pairs"] == {"(False, False, False)": 1},
        "C06_n4_all_4_reduced_fff": n4["reduced_count"] == 4 and n4["patterns_any_pairs"] == {"(False, False, False)": 4},
        "C06_n6_all_9408_have_positive_view": n6["reduced_count"] == 9408 and "(False, False, False)" not in n6["patterns_any_pairs"],
        "C07_n6_first_factor_negative_count": n6["patterns_first_factor_only"].get("(False, False, False)") == 2192,
    }
    (RESULTS / "small_order_claims.json").write_text(json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"orders": [2, 4, 6], "n6_reduced_count": n6["reduced_count"], "claims": claims}, sort_keys=True))
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
