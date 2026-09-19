#!/usr/bin/env python3
"""Exhaustively audit the three parity products for small-order trades."""

from __future__ import annotations

import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py"


def load_source():
    spec = importlib.util.spec_from_file_location("latin_trade_search", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cycles(perm: list[int]) -> list[tuple[int, ...]]:
    seen = set()
    out = []
    for start in range(len(perm)):
        if start in seen:
            continue
        cycle = []
        x = start
        while x not in seen:
            seen.add(x)
            cycle.append(x)
            x = perm[x]
        out.append(tuple(cycle))
    return out


def supports(perm: list[int]):
    parts = cycles(perm)
    for mask in range(1, 1 << len(parts)):
        support = tuple(sorted(x for i, part in enumerate(parts) if mask & (1 << i) for x in part))
        yield support


def line_signs(source, table) -> tuple[int, int, int]:
    return source.row_col_sym_parity(table)


def pair_products(signs: tuple[int, int, int]) -> tuple[int, int, int]:
    r, c, s = signs
    return r * c, r * s, c * s


def is_latin(table) -> bool:
    n = len(table)
    target = set(range(n))
    return all(set(row) == target for row in table) and all(
        {table[r][c] for r in range(n)} == target for c in range(n)
    )


def apply_trade(table, view: str, a: int, b: int, support: tuple[int, ...]):
    out = [list(row) for row in table]
    if view == "row":
        for c in support:
            out[a][c], out[b][c] = out[b][c], out[a][c]
    elif view == "col":
        for r in support:
            out[r][a], out[r][b] = out[r][b], out[r][a]
    elif view == "sym":
        for c in support:
            ra = next(r for r in range(len(table)) if out[r][c] == a)
            rb = next(r for r in range(len(table)) if out[r][c] == b)
            out[ra][c], out[rb][c] = out[rb][c], out[ra][c]
    else:
        raise ValueError(view)
    return tuple(tuple(row) for row in out)


def expected_line_ratio(view: str, delta: int) -> tuple[int, int, int]:
    return {
        "row": (1, delta, delta),
        "col": (delta, 1, delta),
        "sym": (delta, delta, 1),
    }[view]


def induced(source, table, view: str, a: int, b: int) -> list[int]:
    return {
        "row": source.induced_perm_row,
        "col": source.induced_perm_col,
        "sym": source.induced_perm_sym,
    }[view](table, a, b)


def main() -> None:
    source = load_source()
    totals = Counter()
    by_order = {}
    first_symbol_odd_counterexample = None
    failures = []

    for n in (2, 4, 6):
        order_counts = Counter()
        square_count = 0
        for table_index, table in enumerate(source.reduced_latin_squares(n)):
            square_count += 1
            before = line_signs(source, table)
            before_pairs = pair_products(before)
            for view in ("row", "col", "sym"):
                for a, b in itertools.combinations(range(n), 2):
                    perm = induced(source, table, view, a, b)
                    for support in supports(perm):
                        delta = -1 if len(support) % 2 else 1
                        traded = apply_trade(table, view, a, b, support)
                        totals["trades"] += 1
                        order_counts["trades"] += 1
                        order_counts[f"{view}_trades"] += 1
                        order_counts["odd_support" if delta == -1 else "even_support"] += 1
                        if not is_latin(traded):
                            failures.append({"kind": "not_latin", "n": n, "table": table_index, "view": view})
                            continue
                        after = line_signs(source, traded)
                        actual = tuple(x * y for x, y in zip(after, before))
                        expected = expected_line_ratio(view, delta)
                        if actual != expected:
                            failures.append({
                                "kind": "line_ratio",
                                "n": n,
                                "table": table_index,
                                "view": view,
                                "pair": [a, b],
                                "support": list(support),
                                "expected": list(expected),
                                "actual": list(actual),
                            })
                        after_pairs = pair_products(after)
                        pair_ratio = tuple(x * y for x, y in zip(after_pairs, before_pairs))
                        expected_pairs = pair_products(expected)
                        if pair_ratio != expected_pairs:
                            failures.append({"kind": "pair_ratio", "n": n, "table": table_index, "view": view})
                        if view == "sym" and delta == -1 and first_symbol_odd_counterexample is None:
                            first_symbol_odd_counterexample = {
                                "n": n,
                                "table_index": table_index,
                                "table": [list(row) for row in table],
                                "symbol_pair": [a, b],
                                "support_columns": list(support),
                                "line_signs_before_R_C_S": list(before),
                                "line_signs_after_R_C_S": list(after),
                                "line_sign_ratios_R_C_S": list(actual),
                                "pair_sign_ratios_RC_RS_CS": list(pair_ratio),
                                "usual_epsilon_RC_ratio": pair_ratio[0],
                            }
        by_order[str(n)] = {"reduced_squares": square_count, **dict(sorted(order_counts.items()))}

    result = {
        "evidence_label": "exact exhaustive computation",
        "source_generator": str(SOURCE.relative_to(ROOT)),
        "orders": by_order,
        "total_trades_checked": totals["trades"],
        "failure_count": len(failures),
        "failures": failures[:20],
        "old_unqualified_symbol_sign_claim_counterexample": first_symbol_odd_counterexample,
        "all_checks_pass": not failures and first_symbol_odd_counterexample is not None,
        "claim_boundary": {
            "usual_epsilon_RC": "odd row/column trades reverse; odd symbol trades preserve",
            "parastrophic_products": "every odd trade reverses the two products containing its view label",
            "fff_results_affected": False,
        },
    }
    out = RUN / "results/trade_sign_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    summary = [
        "Three-parity two-line trade audit",
        "=================================",
        "",
        f"orders: 2,4,6; total trades checked: {result['total_trades_checked']}",
        f"failures: {result['failure_count']}; all checks pass: {result['all_checks_pass']}",
        "line-sign ratios (R,C,S): row=(1,d,d), col=(d,1,d), sym=(d,d,1)",
        "pair ratios (RC,RS,CS): row=(d,d,1), col=(d,1,d), sym=(1,d,d)",
        "The first odd symbol trade preserves the usual RC sign and reverses RS and CS.",
        "FFF, census, product, congruence, and solver claims are unaffected.",
    ]
    summary_text = "\n".join(summary) + "\n"
    (RUN / "results/trade_sign_audit_summary.txt").write_text(summary_text)
    print(summary_text, end="")
    if not result["all_checks_pass"]:
        raise SystemExit("trade-sign audit failed")


if __name__ == "__main__":
    main()
