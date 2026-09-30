#!/usr/bin/env python3
"""Independent mixed three-row certificate; no SAT builder or completion search."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations, permutations, product
import json
from math import comb, factorial
from pathlib import Path
import subprocess
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[3]
PREFIX = (2, 4, 0, 5, 3, 1, 8, 9, 6, 7, 12, 13, 10, 11, 16, 17, 14, 15)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(p: tuple[int, ...]) -> None:
    require(isinstance(p, tuple), "permutation must be a tuple")
    require(all(type(x) is int for x in p), "permutation entries must be integers")
    require(sorted(p) == list(range(len(p))), "not a permutation")


def root(n: int) -> tuple[int, ...]:
    require(type(n) is int and n >= 4 and n % 2 == 0, "even degree >=4 required")
    return tuple(x ^ 1 for x in range(n))


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[x] for x in q)


def inverse(p: tuple[int, ...]) -> tuple[int, ...]:
    validate(p)
    q = [0] * len(p)
    for x, y in enumerate(p):
        q[y] = x
    return tuple(q)


def cycles(p: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    validate(p)
    seen: set[int] = set()
    result = []
    for start in range(len(p)):
        if start in seen:
            continue
        orbit = []
        x = start
        while x not in seen:
            seen.add(x)
            orbit.append(x)
            x = p[x]
        require(x == start, "cycle did not close at its start")
        result.append(tuple(orbit))
    return tuple(result)


def cycle_type(p: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(len(c) for c in cycles(p)))


def sign(p: tuple[int, ...]) -> int:
    return (-1) ** (len(p) - len(cycles(p)))


def target_type(n: int, exceptional: int) -> tuple[int, ...]:
    require(n >= exceptional and (n - exceptional) % 2 == 0, "invalid cycle type")
    return (2,) * ((n - exceptional) // 2) + (exceptional,)


def components(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    validate(a)
    validate(b)
    require(len(a) == len(b), "component degrees differ")
    remaining = set(range(len(a)))
    result = []
    while remaining:
        start = min(remaining)
        orbit = {start}
        pending = [start]
        while pending:
            x = pending.pop()
            for y in (a[x], b[x]):
                if y not in orbit:
                    orbit.add(y)
                    pending.append(y)
        remaining.difference_update(orbit)
        result.append(tuple(sorted(orbit)))
    return tuple(result)


def pairings(points: tuple[int, ...]):
    if not points:
        yield ()
        return
    x = points[0]
    for i in range(1, len(points)):
        y = points[i]
        for rest in pairings(points[1:i] + points[i + 1:]):
            yield ((x, y),) + rest


class Budget:
    def __init__(self, seconds: float):
        require(0 < seconds <= 30, "budget must be >0 and <=30 seconds")
        self.deadline = time.monotonic() + seconds

    def check(self) -> None:
        if time.monotonic() >= self.deadline:
            raise TimeoutError("certificate budget exhausted; no output written")


def one_exception(n: int, length: int, budget: Budget):
    """Choose support, oriented cycle (minimum first), and remaining matching."""
    count = 0
    for support in combinations(range(n), length):
        outside = tuple(x for x in range(n) if x not in support)
        matchings = tuple(pairings(outside))
        for tail in permutations(support[1:]):
            cycle = (support[0],) + tail
            for matching in matchings:
                if count % 512 == 0:
                    budget.check()
                count += 1
                p = [-1] * n
                for x, y in zip(cycle, cycle[1:] + cycle[:1]):
                    p[x] = y
                for x, y in matching:
                    p[x], p[y] = y, x
                yield tuple(p)


def validate_rows(rows: tuple[tuple[int, ...], ...]) -> None:
    require(len(rows) == 3, "exactly three rows required")
    n = len(rows[0])
    for row in rows:
        validate(row)
        require(len(row) == n, "row degrees differ")
    require(all(len({row[c] for row in rows}) == 3 for c in range(n)),
            "rows are not pointwise disjoint")


def partial_odd_cycles(arrows: dict[int, int]) -> tuple[tuple[int, ...], ...]:
    require(len(set(arrows.values())) == len(arrows), "partial map is not injective")
    found = set()
    for start in sorted(arrows):
        path = []
        positions = {}
        x = start
        while x in arrows and x not in positions:
            positions[x] = len(path)
            path.append(x)
            x = arrows[x]
        if x in positions:
            cycle = tuple(path[positions[x]:])
            if len(cycle) > 1 and len(cycle) % 2:
                i = cycle.index(min(cycle))
                found.add(cycle[i:] + cycle[:i])
    return tuple(sorted(found))


def closed_witnesses(rows: tuple[tuple[int, ...], ...], *, direct: bool = False):
    """Compare partial-map walks with independent cyclic orders of the three rows."""
    validate_rows(rows)
    positions = tuple(inverse(row) for row in rows)
    found = set()
    for view, lines in (("column", rows), ("symbol", positions)):
        for u, v in combinations(range(len(rows[0])), 2):
            edges = tuple((line[u], line[v]) for line in lines)
            if direct:
                for order in permutations(range(3)):
                    e = tuple(edges[i] for i in order)
                    if all(e[i][1] == e[(i + 1) % 3][0] for i in range(3)):
                        cycle = tuple(edge[0] for edge in e)
                        i = cycle.index(min(cycle))
                        found.add((view, u, v, cycle[i:] + cycle[:i]))
            else:
                for cycle in partial_odd_cycles(dict(edges)):
                    found.add((view, u, v, cycle))
    return tuple(sorted(found))


def centralizer(n: int, budget: Budget):
    require(n in (6, 10), "only bounded centralizers are enumerated")
    m = n // 2
    for order in permutations(range(m)):
        budget.check()
        for flips in product((0, 1), repeat=m):
            yield tuple(2 * order[x // 2] + ((x % 2) ^ flips[x // 2])
                        for x in range(n))


def conjugate(p: tuple[int, ...], g: tuple[int, ...]) -> tuple[int, ...]:
    return compose(g, compose(p, inverse(g)))


def stream_hash(candidates: set[tuple[int, ...]]) -> str:
    h = hashlib.sha256()
    for p in sorted(candidates):
        h.update((json.dumps(p, separators=(",", ":")) + "\n").encode("ascii"))
    return h.hexdigest()


def finite_check(n: int, budget: Budget) -> dict:
    a = root(n)
    mixed: set[tuple[int, ...]] = set()
    near: set[tuple[int, ...]] = set()
    scanned_b = 0
    for b in one_exception(n, 4, budget):
        scanned_b += 1
        c = compose(a, b)
        ct = cycle_type(c)
        if ct == target_type(n, 6):
            mixed.add(b)
        if n == 10 and ct == (2, 4, 4):
            near.add(b)
    # Reverse search is generated from C, not from B's candidate set.
    reverse: set[tuple[int, ...]] = set()
    scanned_c = 0
    for c in one_exception(n, 6, budget):
        scanned_c += 1
        b = compose(a, c)
        if cycle_type(b) == target_type(n, 4):
            reverse.add(b)
    require(mixed == reverse, "forward/reverse enumerations disagree")
    expected = {6: (90, 120, 24), 10: (18900, 75600, 480)}[n]
    require((scanned_b, scanned_c, len(mixed)) == expected, "finite count mismatch")
    require(not near, "unexpected degree-ten two-four-cycle case")
    profiles = Counter()
    witness_counts = Counter()
    for b in sorted(mixed):
        budget.check()
        rows = (tuple(range(n)), a, b)
        w1 = closed_witnesses(rows)
        w2 = closed_witnesses(rows, direct=True)
        require(w1 == w2, "physical partial scanners disagree")
        witness_counts.update(w[0] for w in w1)
        require(not w1, "unexpected closed odd companion cycle")
        profile = tuple(sorted(map(len, components(a, b))))
        profiles[profile] += 1
    require(dict(profiles) == {(6,) if n == 6 else (4, 6): len(mixed)},
            "exceptional connected ten-point component exists")
    representative = min(mixed)
    orbit = set()
    stabilizer = 0
    centralizer_size = 0
    for g in centralizer(n, budget):
        centralizer_size += 1
        require(compose(g, a) == compose(a, g), "invalid centralizer element")
        image = conjugate(representative, g)
        orbit.add(image)
        stabilizer += image == representative
    require(orbit == mixed, "bounded root-centralizer orbit is incomplete")
    require(centralizer_size == 2 ** (n // 2) * factorial(n // 2),
            "centralizer order mismatch")
    require(centralizer_size == len(orbit) * stabilizer, "orbit/stabilizer mismatch")
    return {
        "degree": n,
        "root": a,
        "forward_B_scanned": scanned_b,
        "reverse_C_scanned": scanned_c,
        "mixed_count": len(mixed),
        "exact_sets_agree": True,
        "candidate_stream_sha256": stream_hash(mixed),
        "candidates": sorted(mixed),
        "component_size_histogram": {"+".join(map(str, p)): count
                                      for p, count in sorted(profiles.items())},
        "partial_closed_odd_cycles": {"column": witness_counts["column"],
                                      "symbol": witness_counts["symbol"]},
        "physical_scanners_agree": True,
        "centralizer_order": centralizer_size,
        "centralizer_orbit_count": 1,
        "stabilizer_order": stabilizer,
        "two_four_cycle_count": len(near) if n == 10 else None,
    }


def formula_check(degree6: dict, budget: Budget) -> dict:
    n = 18
    a = root(n)
    validate_rows((tuple(range(n)), a, PREFIX))
    require(cycle_type(PREFIX) == target_type(n, 4), "prefix B type mismatch")
    require(cycle_type(compose(a, PREFIX)) == target_type(n, 6), "prefix C mismatch")
    require(tuple(sorted(map(len, components(a, PREFIX)))) == (4, 4, 4, 6),
            "prefix component mismatch")
    require(not closed_witnesses((tuple(range(n)), a, PREFIX)), "prefix has witness")
    require(not closed_witnesses((tuple(range(n)), a, PREFIX), direct=True),
            "prefix direct scanner has witness")
    signs = tuple(sign(p) for p in (tuple(range(n)), a, PREFIX))
    require(signs == (1, -1, 1), "prefix row signs mismatch")
    require(sign(compose(a, PREFIX)) == -1, "prefix relative sign mismatch")
    require(PREFIX[:6] in degree6["candidates"], "prefix core missing from certificate")
    # Exhaust all local four-point components and every local six-point core.
    four = tuple(p for p in permutations(range(4))
                 if cycle_type(p) == (2, 2)
                 and cycle_type(compose(root(4), p)) == (2, 2))
    require(len(four) == 2, "four-point complement count mismatch")
    for b in four:
        rows = (tuple(range(4)), root(4), b)
        require(not closed_witnesses(rows), "four-point component has witness")
        require(not closed_witnesses(rows, direct=True), "four-point scanner disagrees")
    # Seven consecutive core placements on n18, each with all 24 local cores.
    # This is a transport control, NOT enumeration of the full n18 class.
    transported = 0
    for offset in range(7):
        budget.check()
        core_points = tuple(range(2 * offset, 2 * offset + 6))
        outside = tuple(x for x in range(n) if x not in core_points)
        for local in degree6["candidates"]:
            b = [-1] * n
            for x, y in enumerate(local):
                b[core_points[x]] = core_points[y]
            for i in range(0, len(outside), 4):
                u, v, w, z = outside[i:i + 4]
                b[u], b[w], b[v], b[z] = w, u, z, v
            bt = tuple(b)
            rows = (tuple(range(n)), a, bt)
            require(cycle_type(bt) == target_type(n, 4), "transport B mismatch")
            require(cycle_type(compose(a, bt)) == target_type(n, 6), "transport C mismatch")
            require(not closed_witnesses(rows), "transported core has witness")
            require(not closed_witnesses(rows, direct=True), "transport scanner mismatch")
            transported += 1
    m, q = 9, 3
    pair_partition_count = 1
    for k in range(1, 2 * q, 2):
        pair_partition_count *= k
    count = comb(m, 3) * 24 * pair_partition_count * 2 ** q
    stabilizer = 2 * 4 ** q * factorial(q)
    group_order = 2 ** m * factorial(m)
    require(count == 241920 and group_order == count * stabilizer,
            "derived degree-eighteen orbit count mismatch")
    return {
        "degree": n,
        "prefix_B": PREFIX,
        "prefix_A_inverse_B": compose(a, PREFIX),
        "prefix_component_sizes": (4, 4, 4, 6),
        "four_point_complement_candidates": four,
        "transported_n18_controls": transported,
        "full_n18_enumeration_performed": False,
        "classification_basis": "written component proof + exact degree6/10 certificate",
        "derived_labelled_count": count,
        "derived_centralizer_orbit_count": 1,
        "centralizer_order": group_order,
        "derived_stabilizer_order": stabilizer,
        "partial_closed_odd_cycles": {"column": 0, "symbol": 0},
        "row_signs": signs,
        "FFF_extendibility": "not decided",
        "unrestricted_FFF18": "not decided",
        "novelty": "not assessed",
    }


def output_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    scratch = ROOT / ".audit"
    require(path.is_relative_to(scratch), "output must be inside this repo's .audit/")
    require(path.suffix == ".json", "output must have .json suffix")
    require(not path.exists(), "refusing to overwrite existing output")
    relative = path.relative_to(ROOT)
    check = subprocess.run(["git", "check-ignore", "-q", "--", str(relative)],
                           cwd=ROOT, capture_output=True, timeout=2, check=False)
    require(check.returncode == 0, "output path must be Git-ignored and untracked")
    return path


class MixedCoreTests(unittest.TestCase):
    def test_strict_permutations(self):
        for bad in ((0, 0), (False, 1), (0, 2), [0, 1]):
            with self.assertRaises(ValueError):
                validate(bad)

    def test_open_chain_is_not_a_cycle(self):
        self.assertEqual(partial_odd_cycles({0: 1, 1: 2, 2: 3}), ())
        self.assertEqual(partial_odd_cycles({0: 1, 1: 2, 2: 0}), ((0, 1, 2),))
        with self.assertRaises(ValueError):
            partial_odd_cycles({0: 2, 1: 2})

    def test_physical_positive_witness(self):
        for view, b in (("column", (2, 0, 4, 5, 1, 3)),
                        ("symbol", (2, 4, 1, 5, 0, 3))):
            with self.subTest(view=view):
                rows = (tuple(range(6)), (1, 2, 3, 0, 5, 4), b)
                actual = closed_witnesses(rows)
                self.assertTrue(any(w[0] == view for w in actual))
                self.assertEqual(actual, closed_witnesses(rows, direct=True))

    def test_degree_six_certificate(self):
        result = finite_check(6, Budget(5))
        self.assertEqual(result["mixed_count"], 24)
        self.assertEqual(result["stabilizer_order"], 2)

    def test_prefix_and_pairings(self):
        rows = (tuple(range(18)), root(18), PREFIX)
        self.assertEqual(cycle_type(compose(root(18), PREFIX)), target_type(18, 6))
        self.assertEqual(closed_witnesses(rows), ())
        self.assertEqual(closed_witnesses(rows, direct=True), ())
        self.assertEqual(len(tuple(pairings(tuple(range(6))))), 15)

    def test_reject_outside_output(self):
        with self.assertRaises(ValueError):
            output_path(str(ROOT / "results.json"))
        with self.assertRaises(ValueError):
            Budget(31)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new ignored .audit/ JSON path")
    parser.add_argument("--seconds", type=float, default=25, help="budget, maximum 30 seconds")
    args = parser.parse_args()
    try:
        destination = output_path(args.output)
        budget = Budget(args.seconds)
        degree6 = finite_check(6, budget)
        degree10 = finite_check(10, budget)
        report = {
            "schema": "fff18-independent-mixed-core-v1",
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "python_version": sys.version.split()[0],
            "composition": "(A^-1 B)(x)=A^-1(B(x)); A^-1=A",
            "finite_checks": (degree6, degree10),
            "degree18_deduction_and_controls": formula_check(degree6, budget),
            "limits": "No SAT, Latin completion, unrestricted search, or novelty claim.",
        }
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        budget.check()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="ascii") as handle:
            handle.write(payload)
        print(json.dumps({"output": str(destination), "degree6": 24, "degree10": 480,
                          "degree18_derived_not_enumerated": 241920}, sort_keys=True))
        return 0
    except (ValueError, TimeoutError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
