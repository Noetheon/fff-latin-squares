#!/usr/bin/env python3
"""Independent finite controls for the cubefree CRT common-fibre lift."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from math import gcd, prod
from pathlib import Path


RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
FROZEN_P3 = (ROOT / "repro_runs/2026-09-23_fff_quadratic_norm_lift_audit/"
             "results/p3_greedy_twists.json")
SPECS = (
    ((3, 2, 2),),
    ((3, 1, 0), (5, 1, 0)),
    ((3, 2, 2), (5, 1, 0)),
    ((3, 1, 0), (5, 2, 2)),
)
FIELD_PARAMS = {3: (6, 0x43), 15: (8, 0x11B)}
VIEWS = ("row", "col", "sym")


class BinaryField:
    def __init__(self, degree: int, modulus: int):
        self.order = 1 << degree
        self.modulus = modulus
        if modulus.bit_length() != degree + 1 or not (modulus & 1):
            raise ValueError("invalid binary-field modulus")
        if any(self.power(value, self.order - 1) != 1
               for value in range(1, self.order)):
            raise ValueError("reducible binary-field modulus")

    def mul(self, left: int, right: int) -> int:
        value = 0
        while right:
            if right & 1:
                value ^= left
            right >>= 1
            left <<= 1
            if left & self.order:
                left ^= self.modulus
        return value

    def power(self, value: int, exponent: int) -> int:
        result = 1
        while exponent:
            if exponent & 1:
                result = self.mul(result, value)
            value = self.mul(value, value)
            exponent >>= 1
        return result


class Context:
    def __init__(self, spec: tuple[tuple[int, int, int], ...]):
        self.spec = spec
        self.radical = prod(p for p, _, _ in spec)
        self.dimension = sum(rank for _, rank, _ in spec)
        self.n = prod(p**rank for p, rank, _ in spec)
        degree, modulus = FIELD_PARAMS[self.radical]
        self.field = BinaryField(degree, modulus)
        self.q = self.field.order
        if self.q <= 3 * (self.n - 1) or (self.q - 1) % self.radical:
            raise ValueError("field is too small or lacks the required roots")
        positions = []
        weights = []
        index = 0
        for p, rank, nonsquare in spec:
            if rank not in (1, 2) or p % 2 == 0:
                raise ValueError("only odd cubefree groups are supported")
            if rank == 2 and (nonsquare % p == 0 or
                              nonsquare % p in {x * x % p for x in range(p)}):
                raise ValueError("rank-two norm requires a nonsquare")
            positions.append((p, rank, nonsquare, index))
            index += rank
            m = self.radical // p
            weights.append(m * pow(m, -1, p) % self.radical)
        self.positions = tuple(positions)
        self.weights = tuple(weights)
        if any(weight % p != int(index == target)
               for index, weight in enumerate(self.weights)
               for target, (p, _, _, _) in enumerate(self.positions)):
            raise AssertionError("CRT idempotent weights differ")
        self.coordinate_primes = tuple(p for p, rank, _, _ in positions
                                       for _ in range(rank))
        self.elements = tuple(product(*(range(p) for p in self.coordinate_primes)))
        if len(self.elements) != self.n:
            raise AssertionError("wrong quotient group size")
        lookup = {element: index for index, element in enumerate(self.elements)}
        self.add = tuple(tuple(lookup[tuple((a + b) % p for a, b, p in
                                           zip(x, y, self.coordinate_primes, strict=True))]
                               for y in self.elements) for x in self.elements)
        self.sub = tuple(tuple(lookup[tuple((a - b) % p for a, b, p in
                                           zip(x, y, self.coordinate_primes, strict=True))]
                               for y in self.elements) for x in self.elements)
        self.inner = tuple(tuple(self.bilinear(x, y) for y in self.elements)
                           for x in self.elements)
        self.norm = tuple(self.inner[x][x] for x in range(self.n))
        if any(self.norm[d] % p == 0
               for d in range(1, self.n)
               for p, rank, _, start in self.positions
               if any(self.elements[d][start + j] for j in range(rank))):
            raise AssertionError("norm vanishes on an active component")
        self.orders = tuple(self.element_order(d) for d in range(self.n))
        if any(self.orders[d] != self.radical // gcd(self.radical, self.norm[d])
               for d in range(self.n)):
            raise AssertionError("norm-character order does not match quotient order")
        factors = tuple(p for p, _, _ in spec)
        omega = next((value for value in range(2, self.q)
                      if self.field.power(value, self.radical) == 1
                      and all(self.field.power(value, self.radical // p) != 1
                              for p in factors)), None)
        if omega is None:
            raise AssertionError("missing primitive radical-th root")
        self.omega = omega
        self.roots = tuple(self.field.power(omega, exponent)
                           for exponent in range(self.radical))
        if len(set(self.roots)) != self.radical:
            raise AssertionError("root order differs")

    def bilinear(self, x: tuple[int, ...], y: tuple[int, ...]) -> int:
        result = 0
        for (p, rank, nonsquare, start), weight in zip(
                self.positions, self.weights, strict=True):
            value = x[start] * y[start]
            if rank == 2:
                value -= nonsquare * x[start + 1] * y[start + 1]
            result += weight * (value % p)
        return result % self.radical

    def element_order(self, d: int) -> int:
        factors = [p for p, rank, _, start in self.positions
                   if any(self.elements[d][start + j] for j in range(rank))]
        return prod(factors)

    def scaled(self, exponent: int, value: int) -> int:
        return self.field.mul(self.roots[exponent % self.radical], value)

    def operation(self, row: int, column: int, twists: list[int]) -> int:
        x, a = divmod(row, self.q)
        y, b = divmod(column, self.q)
        symbol = self.add[x][y]
        fibre = (self.scaled(2 * self.inner[x][y], a)
                 ^ self.scaled(self.norm[x], b) ^ twists[x * self.n + y])
        return symbol * self.q + fibre


def return_forms(ctx: Context) -> list[dict]:
    n, modulus = ctx.n, ctx.radical
    forms = []
    for view in VIEWS:
        for high in range(n):
            for low in range(high):
                d = ctx.sub[low][high] if view == "sym" else ctx.sub[high][low]
                orbit_length = ctx.orders[d]
                seen = [False] * n
                for start in range(n):
                    if seen[start]:
                        continue
                    positions = []
                    point = start
                    while not seen[point]:
                        seen[point] = True
                        positions.append(point)
                        point = ctx.add[point][d]
                    if point != start or len(positions) != orbit_length:
                        raise AssertionError("quotient orbit has wrong length")
                    steps = []
                    for point in positions:
                        other = ctx.add[point][d]
                        if view == "row":
                            slope = ctx.norm[high] - ctx.norm[low]
                            label1 = 2 * ctx.inner[high][point] - ctx.norm[low]
                            label2 = 2 * ctx.inner[low][other] - ctx.norm[low]
                            weight1 = weight2 = -ctx.norm[low]
                            cell1, cell2 = high * n + point, low * n + other
                        elif view == "col":
                            slope = 2 * (ctx.inner[point][high] -
                                         ctx.inner[other][low])
                            label1 = ctx.norm[point] - 2 * ctx.inner[other][low]
                            label2 = ctx.norm[other] - 2 * ctx.inner[other][low]
                            weight1 = weight2 = -2 * ctx.inner[other][low]
                            cell1, cell2 = point * n + high, other * n + low
                        else:
                            row = ctx.sub[high][point]
                            slope = 2 * ctx.inner[row][d]
                            label1 = -ctx.norm[row] + slope
                            label2 = -ctx.norm[row]
                            weight1, weight2 = label1, label2
                            cell1, cell2 = row * n + point, row * n + other
                        steps.append((slope % modulus, label1 % modulus,
                                      label2 % modulus, cell1, weight1 % modulus,
                                      cell2, weight2 % modulus))
                    later = 0
                    label_sums = [0, 0]
                    support = []
                    for reverse_index, step in enumerate(reversed(steps)):
                        slope, label1, label2, cell1, weight1, cell2, weight2 = step
                        t = orbit_length - 1 - reverse_index
                        qd = ctx.norm[d]
                        if view == "row":
                            expected1 = (2 * ctx.inner[high][start] -
                                         ctx.norm[high] + t * qd)
                            start_plus_d = ctx.add[start][d]
                            expected2 = (2 * ctx.inner[low][start_plus_d] -
                                         ctx.norm[high] - t * qd)
                        elif view == "col":
                            expected1 = (ctx.norm[start] -
                                         2 * ctx.inner[start][high] - t * qd)
                            expected2 = (ctx.norm[start] -
                                         2 * ctx.inner[start][low] + (t + 1) * qd)
                        else:
                            row_start = ctx.sub[high][start]
                            expected1 = -ctx.norm[row_start] - t * qd
                            expected2 = (-ctx.norm[row_start] -
                                         2 * ctx.inner[row_start][d] + t * qd)
                        if ((label1 + later - expected1) % modulus or
                                (label2 + later - expected2) % modulus):
                            raise AssertionError(
                                f"accumulated exponent formula differs: {view} {high} {low} {start} {t}")
                        label_sums[0] ^= ctx.roots[(label1 + later) % modulus]
                        label_sums[1] ^= ctx.roots[(label2 + later) % modulus]
                        support.extend(((cell1, (weight1 + later) % modulus),
                                        (cell2, (weight2 + later) % modulus)))
                        later = (later + slope) % modulus
                    if later or any(label_sums):
                        raise AssertionError(f"affine return did not cancel: {view} {high} {low}")
                    if len({cell for cell, _ in support}) != 2 * orbit_length:
                        raise AssertionError("return cell support is not disjoint")
                    forms.append({"view": view, "high": high, "low": low,
                                  "start": start, "orbit_length": orbit_length,
                                  "support": tuple(support)})
    return forms


def greedy_twists(ctx: Context, forms: list[dict]) -> tuple[list[int], int]:
    closing = [[] for _ in range(ctx.n * ctx.n)]
    incidence = [0] * (ctx.n * ctx.n)
    for form in forms:
        support = form["support"]
        closing[max(cell for cell, _ in support)].append(support)
        for cell, _ in support:
            incidence[cell] += 1
    expected = 3 * (ctx.n - 1)
    if any(value != expected for value in incidence):
        raise AssertionError("cell/form incidence is not uniform")
    twists = [0] * len(closing)
    max_closing = 0
    for cell, conditions in enumerate(closing):
        max_closing = max(max_closing, len(conditions))
        forbidden = set()
        for support in conditions:
            partial = 0
            last_exponent = None
            for index, exponent in support:
                if index == cell:
                    last_exponent = exponent
                else:
                    if index > cell:
                        raise AssertionError("condition closed too early")
                    partial ^= ctx.scaled(exponent, twists[index])
            if last_exponent is None:
                raise AssertionError("condition lacks its last cell")
            forbidden.add(ctx.scaled(-last_exponent, partial))
        twists[cell] = next((value for value in range(ctx.q)
                             if value not in forbidden), -1)
        if twists[cell] < 0:
            raise AssertionError("greedy choice exhausted the field")
    for form in forms:
        value = 0
        for cell, exponent in form["support"]:
            value ^= ctx.scaled(exponent, twists[cell])
        if value == 0:
            raise AssertionError("zero return after greedy construction")
    return twists, max_closing


def physical_scan(ctx: Context, twists: list[int]) -> dict:
    order = ctx.n * ctx.q
    pairs = []
    for view in VIEWS:
        pairs.append((view, 0, 1, 2))
        for orbit_length in sorted(set(ctx.orders[1:])):
            high, low = next((high, low) for high in range(ctx.n)
                             for low in range(high) if ctx.orders[ctx.sub[high][low]] == orbit_length)
            pairs.extend(((view, high * ctx.q, low * ctx.q, 2 * orbit_length),
                          (view, high * ctx.q + 1, low * ctx.q + 2,
                           2 * orbit_length)))

    def line(view: str, label: int) -> list[int]:
        if view == "row":
            return [ctx.operation(label, col, twists) for col in range(order)]
        if view == "col":
            return [ctx.operation(row, label, twists) for row in range(order)]
        symbol_outer, symbol_inner = divmod(label, ctx.q)
        values = []
        for column in range(order):
            y, b = divmod(column, ctx.q)
            x = ctx.sub[symbol_outer][y]
            raw = (symbol_inner ^ ctx.scaled(ctx.norm[x], b)
                   ^ twists[x * ctx.n + y])
            a = ctx.scaled(-2 * ctx.inner[x][y], raw)
            row = x * ctx.q + a
            if ctx.operation(row, column, twists) != label:
                raise AssertionError("direct symbol line disagrees with operation")
            values.append(row)
        return values

    histogram = Counter()
    for view, first, second, expected_length in pairs:
        first_map, second_map = line(view, first), line(view, second)
        if len(set(first_map)) != order or len(set(second_map)) != order:
            raise AssertionError("physical line is not bijective")
        inverse = [0] * order
        for point, value in enumerate(second_map):
            inverse[value] = point
        permutation = [inverse[value] for value in first_map]
        seen = [False] * order
        for start in range(order):
            if seen[start]:
                continue
            point, length = start, 0
            while not seen[point]:
                seen[point] = True
                length += 1
                point = permutation[point]
            if point != start or length != expected_length:
                raise AssertionError("physical view cycle has unexpected length")
            histogram[(view, length)] += 1
    return {"line_pairs": len(pairs),
            "cycle_histogram": {f"{view}:{length}": count
                                for (view, length), count in sorted(histogram.items())}}


def audit_case(spec: tuple[tuple[int, int, int], ...]) -> dict:
    ctx = Context(spec)
    forms = return_forms(ctx)
    twists, max_closing = greedy_twists(ctx, forms)
    frozen_p3 = None
    if ctx.n == 9:
        reference = json.loads(FROZEN_P3.read_text())
        if twists != reference:
            raise AssertionError("prime-square specialization differs from frozen C164 twist")
        frozen_p3 = {"exact_twist_match": True,
                     "source_sha256": sha256(FROZEN_P3.read_bytes()).hexdigest()}
    counts = Counter((form["view"], form["orbit_length"]) for form in forms)
    if not forms or any(view not in {form["view"] for form in forms} for view in VIEWS):
        raise AssertionError("a physical view has no return controls")
    direct = physical_scan(ctx, twists)
    return {"N": ctx.n, "radical": ctx.radical,
            "components": [{"prime": p, "rank": rank, "nonsquare": nu}
                           for p, rank, nu in spec],
            "field_order": ctx.q, "field_modulus_hex": hex(ctx.field.modulus),
            "root": ctx.omega, "root_order": ctx.radical,
            "greedy_bound": 3 * (ctx.n - 1),
            "max_forms_closing_at_cell": max_closing,
            "return_forms": len(forms),
            "forms_by_view_and_order": {f"{view}:{length}": count
                                        for (view, length), count in sorted(counts.items())},
            "all_affine_returns_cancel": True, "all_twist_returns_nonzero": True,
            "twists_sha256": sha256(bytes(twists)).hexdigest(),
            "twists": twists,
            "frozen_p3_control": frozen_p3,
            "nonzero_twist_cells": sum(value != 0 for value in twists),
            "physical_validation": direct,
            "full_table_materialized": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RUN / "results/cubefree_lift_status.json")
    parser.add_argument("--summary", type=Path, default=RUN / "results/cubefree_lift_summary.txt")
    args = parser.parse_args()
    cases = [audit_case(spec) for spec in SPECS]
    result = {"scope": "exact compact return controls for cubefree CRT lifts",
              "cases": cases, "unrestricted_fff18_decided": False,
              "claim_classification": "universal theorem requires the separate written proof"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = ["Cubefree CRT common-fibre lift: compact exact controls"]
    for item in cases:
        lines.append(f"N={item['N']} radical={item['radical']} q={item['field_order']}: "
                     f"{item['return_forms']} returns, all nonzero; "
                     f"{item['physical_validation']['line_pairs']} physical pairs checked")
    lines.append("No full table is materialized; order 18 remains open.")
    args.summary.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
