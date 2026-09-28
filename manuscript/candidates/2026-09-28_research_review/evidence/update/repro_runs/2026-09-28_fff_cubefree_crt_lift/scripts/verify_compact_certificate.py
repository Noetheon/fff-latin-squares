#!/usr/bin/env python3
"""Check every compact return by direct physical line-map inversion."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from check_cubefree_lift import Context, RUN, return_forms


def relative_step(ctx: Context, twists: list[int], view: str,
                  high: int, low: int, point: int, fibre: int,
                  first_label: int, second_label: int) -> tuple[int, int]:
    n, q = ctx.n, ctx.q
    if view == "row":
        symbol = ctx.operation(high * q + first_label, point * q + fibre, twists)
        outer, value = divmod(symbol, q)
        target = ctx.sub[outer][low]
        raw = (value ^ ctx.scaled(2 * ctx.inner[low][target], second_label)
               ^ twists[low * n + target])
        second_fibre = ctx.scaled(-ctx.norm[low], raw)
        if ctx.operation(low * q + second_label, target * q + second_fibre,
                         twists) != symbol:
            raise AssertionError("row-view inverse is not physical")
    elif view == "col":
        symbol = ctx.operation(point * q + fibre, high * q + first_label, twists)
        outer, value = divmod(symbol, q)
        target = ctx.sub[outer][low]
        raw = (value ^ ctx.scaled(ctx.norm[target], second_label)
               ^ twists[target * n + low])
        second_fibre = ctx.scaled(-2 * ctx.inner[target][low], raw)
        if ctx.operation(target * q + second_fibre, low * q + second_label,
                         twists) != symbol:
            raise AssertionError("column-view inverse is not physical")
    elif view == "sym":
        row = ctx.sub[high][point]
        raw = (first_label ^ ctx.scaled(ctx.norm[row], fibre)
               ^ twists[row * n + point])
        row_fibre = ctx.scaled(-2 * ctx.inner[row][point], raw)
        if ctx.operation(row * q + row_fibre, point * q + fibre,
                         twists) != high * q + first_label:
            raise AssertionError("first symbol line is not physical")
        target = ctx.sub[low][row]
        raw = (second_label ^ ctx.scaled(2 * ctx.inner[row][target], row_fibre)
               ^ twists[row * n + target])
        second_fibre = ctx.scaled(-ctx.norm[row], raw)
        if ctx.operation(row * q + row_fibre, target * q + second_fibre,
                         twists) != low * q + second_label:
            raise AssertionError("second symbol line is not physical")
    else:
        raise ValueError(view)
    return target, second_fibre


def direct_return(ctx: Context, twists: list[int], form: dict,
                  first_label: int, second_label: int, start_fibre: int) -> int:
    point, fibre = form["start"], start_fibre
    for _ in range(form["orbit_length"]):
        point, fibre = relative_step(
            ctx, twists, form["view"], form["high"], form["low"],
            point, fibre, first_label, second_label)
    if point != form["start"]:
        raise AssertionError("physical quotient orbit did not close")
    return fibre


def check_case(item: dict) -> dict:
    spec = tuple((part["prime"], part["rank"], part["nonsquare"])
                 for part in item["components"])
    ctx = Context(spec)
    twists = item["twists"]
    if (len(twists) != ctx.n * ctx.n or
            any(not isinstance(value, int) or not 0 <= value < ctx.q
                for value in twists) or
            sha256(bytes(twists)).hexdigest() != item["twists_sha256"] or
            ctx.n != item["N"] or ctx.q != item["field_order"]):
        raise AssertionError("certificate shape or hash differs")
    forms = return_forms(ctx)
    if len(forms) != item["return_forms"]:
        raise AssertionError("return count differs")
    zero_twists = [0] * len(twists)
    for view in ("row", "col", "sym"):
        control = next(form for form in forms if form["view"] == view)
        if direct_return(ctx, zero_twists, control, 0, 0, 0) != 0:
            raise AssertionError("all-zero twist negative control did not vanish")
    by_view = Counter()
    for form in forms:
        analytic = 0
        for cell, exponent in form["support"]:
            analytic ^= ctx.scaled(exponent, twists[cell])
        if analytic == 0:
            raise AssertionError("analytical return is zero")
        physical00 = direct_return(ctx, twists, form, 0, 0, 0)
        physical12 = direct_return(ctx, twists, form, 1, 2, 0)
        physical_slope = direct_return(ctx, twists, form, 0, 0, 1)
        if (physical00 != analytic or physical12 != analytic or
                physical_slope != (analytic ^ 1)):
            raise AssertionError("direct physical return differs from compact form")
        by_view[form["view"]] += 1
    return {"N": ctx.n, "direct_returns_checked": len(forms),
            "returns_by_view": dict(sorted(by_view.items())),
            "two_label_choices_and_fibre_slope_checked": True,
            "zero_twist_negative_control": True,
            "all_nonzero": True,
            "twists_sha256": item["twists_sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=Path,
                        default=RUN / "results/cubefree_lift_status.json")
    parser.add_argument("--output", type=Path,
                        default=RUN / "results/physical_return_verification.json")
    parser.add_argument("--summary", type=Path,
                        default=RUN / "results/physical_return_verification_summary.txt")
    args = parser.parse_args()
    status = json.loads(args.status.read_text())
    cases = [check_case(item) for item in status["cases"]]
    result = {"input_status_sha256": sha256(args.status.read_bytes()).hexdigest(),
              "cases": cases,
              "scope": "all compact quotient returns checked against direct physical steps",
              "unrestricted_fff18_decided": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = ["Direct physical verification of every cubefree CRT return:"]
    for item in cases:
        lines.append(f"N={item['N']}: {item['direct_returns_checked']} returns in three views, "
                     "two line-label pairs and two start fibres, all agree")
    lines.append("Compact certificate control only; order 18 remains open.")
    args.summary.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
