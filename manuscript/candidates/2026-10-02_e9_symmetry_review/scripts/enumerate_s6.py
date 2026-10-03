#!/usr/bin/env python3
"""Independent bounded S6 control; standard library, one process, no repo imports."""

from collections import Counter
from itertools import combinations, permutations
from pathlib import Path
import hashlib
import json
import platform
import signal
import sys
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def budget_expired(*_):
    raise TimeoutError("4.5s wall-clock budget exceeded")


def compose(p, q):
    """Right-to-left composition: (p q)(x) = p(q(x))."""
    return tuple(p[q[x]] for x in range(len(q)))


def inverse(p):
    result = [0] * len(p)
    for x, y in enumerate(p):
        result[y] = x
    return tuple(result)


def product_by_edges(gamma, beta):
    # Solve delta(beta(x)) = gamma(x), without computing beta's inverse.
    result = [None] * len(beta)
    for x in range(len(beta)):
        result[beta[x]] = gamma[x]
    return tuple(result)


def cycles(p):
    unseen = set(range(len(p)))
    result = []
    while unseen:
        x = min(unseen)
        cycle = []
        while x in unseen:
            unseen.remove(x)
            cycle.append(x)
            x = p[x]
        require(x == cycle[0], "cycle did not close at its start")
        result.append(tuple(cycle))
    return tuple(result)


def signature(p):
    return tuple(sorted((len(c) for c in cycles(p)), reverse=True))


def signature_by_powers(p):
    # Fixed points of p^k determine the number of cycles of each length k.
    power = tuple(range(len(p)))
    counts = {}
    for k in range(1, len(p) + 1):
        power = compose(p, power)
        fixed = sum(x == y for x, y in enumerate(power))
        accounted = sum(d * counts[d] for d in counts if k % d == 0)
        require((fixed - accounted) % k == 0, "nonintegral cycle count")
        counts[k] = (fixed - accounted) // k
        require(counts[k] >= 0, "negative cycle count")
    result = tuple(k for k in sorted(counts, reverse=True) for _ in range(counts[k]))
    require(sum(result) == len(p), "power method missed a cycle")
    return result


def checked_product(gamma, beta):
    delta = compose(gamma, inverse(beta))
    require(delta == product_by_edges(gamma, beta), "product conventions disagree")
    require(signature(delta) == signature_by_powers(delta), "cycle scanners disagree")
    return delta


def from_cycles(n, *blocks):
    p = list(range(n))
    used = set()
    for block in blocks:
        require(len(set(block)) == len(block), "repeated point in cycle")
        require(not used.intersection(block), "overlapping cycles")
        require(all(0 <= x < n for x in block), "point outside domain")
        used.update(block)
        for x, y in zip(block, block[1:] + block[:1]):
            p[x] = y
    return tuple(p)


def label(sig):
    return "+".join(map(str, sig))


def histogram(counter):
    return {label(k): counter[k] for k in sorted(counter)}


def even_cycled(p):
    return all(length % 2 == 0 for length in signature(p))


def record(gamma, beta):
    delta = checked_product(gamma, beta)
    return {
        "gamma_images": gamma,
        "gamma_cycles_including_fixed_points": cycles(gamma),
        "delta_images": delta,
        "delta_cycles_including_fixed_points": cycles(delta),
        "delta_type": label(signature(delta)),
        "fixed_point_free_even_cycled": even_cycled(delta),
    }


def support_generated_classes():
    class33 = set()
    class3111 = set()
    points = set(range(6))
    for triple in combinations(range(6), 3):
        a, b, c = triple
        orientations = ((a, b, c), (a, c, b))
        for orientation in orientations:
            class3111.add(from_cycles(6, orientation))
        if 0 not in triple:
            continue
        d, e, f = sorted(points.difference(triple))
        for first in orientations:
            for second in ((d, e, f), (d, f, e)):
                class33.add(from_cycles(6, first, second))
    return class33, class3111


def odd_fiber_controls():
    records = []
    for length in range(1, 7):
        for voltage in range(3):
            p = tuple(
                3 * ((i + 1) % length) + (a + (voltage if i == length - 1 else 0)) % 3
                for i in range(length) for a in range(3)
            )
            expected = (length,) * 3 if voltage == 0 else (3 * length,)
            require(signature(p) == expected, "odd-fiber spectrum mismatch")
            require(signature_by_powers(p) == expected, "odd-fiber power mismatch")
            require(even_cycled(p) == (length % 2 == 0), "odd lift changed parity")
            records.append({"quotient_length": length, "voltage": voltage,
                            "physical_cycle_type": label(expected)})
    return records


def literal_e9_quotient(specs):
    # None = regular E9 orbit; (u,v) = E9/kernel(u*a+v*b), a three-point orbit.
    points = []
    for orbit, form in enumerate(specs):
        points.extend((orbit, a, b) for a in range(3)
                      for b in (range(3) if form is None else (0,)))
    index = {point: i for i, point in enumerate(points)}
    elements = tuple((a, b) for a in range(3) for b in range(3))
    action = {}
    for ga, gb in elements:
        images = []
        for orbit, a, b in points:
            form = specs[orbit]
            if form is None:
                target = (orbit, (a + ga) % 3, (b + gb) % 3)
            else:
                target = (orbit, (a + form[0] * ga + form[1] * gb) % 3, 0)
            images.append(index[target])
        action[ga, gb] = tuple(images)
    require(len(points) == 18, "literal coordinate is not size 18")
    for a, b in elements:
        for c, d in elements:
            require(compose(action[a, b], action[c, d]) == action[(a+c) % 3, (b+d) % 3],
                    "literal action failed the group law")
    fibers = cycles(action[1, 0])
    require(len(fibers) == 6 and all(len(f) == 3 for f in fibers), "H is not free")
    fiber_index = {point: i for i, fiber in enumerate(fibers) for point in fiber}
    residual = tuple(fiber_index[action[0, 1][fiber[0]]] for fiber in fibers)
    for i, fiber in enumerate(fibers):
        require({fiber_index[action[0, 1][x]] for x in fiber} == {residual[i]},
                "residual action is not well-defined")
    return {"physical_points": len(points), "group_elements": len(elements),
            "group_law_checks": len(elements) ** 2, "H_orbits": len(fibers),
            "H_orbit_lengths": [len(f) for f in fibers],
            "residual_images": residual, "residual_type": label(signature(residual))}


def mixed_rectangle_control(beta, alpha):
    # Here columns have alpha of type 3+1+1+1 and symbols have beta of type 3+3.
    identity = tuple(range(6))
    rows = [identity]
    for _ in range(2):
        rows.append(compose(beta, compose(rows[-1], inverse(alpha))))
    require(compose(beta, compose(rows[-1], inverse(alpha))) == identity,
            "three-row orbit did not close")
    require(all(len({r[c] for r in rows}) == 3 for c in range(6)),
            "mixed rectangle has a repeated column entry")
    pairs = []
    for i, j in combinations(range(3), 2):
        relative = compose(inverse(rows[i]), rows[j])
        require(signature(relative) == (4, 2), "mixed rectangle is not row-F")
        require(signature_by_powers(relative) == (4, 2), "rectangle scanner mismatch")
        pairs.append({"rows": [i, j], "relative_type": label(signature(relative)),
                      "relative_images": relative})
    for i in range(3):
        for c in range(6):
            require(rows[(i+1) % 3][alpha[c]] == beta[rows[i][c]],
                    "mixed rectangle failed residual autotopy")
    return {"rows": rows, "column_action_images": alpha, "symbol_action_images": beta,
            "pair_controls": pairs, "residual_autotopy_cell_checks": 18,
            "scope": "row-F 3x6 rectangle only; not a Latin18 square or FFF witness"}


def main():
    started = time.perf_counter()
    require(sys.version_info >= (3, 11), "Python 3.11+ required")
    signal.signal(signal.SIGALRM, budget_expired)
    signal.setitimer(signal.ITIMER_REAL, 4.5)
    output = Path(__file__).resolve().parent / "enumeration_results.json"
    require(not output.exists(), "refusing to overwrite an existing result")

    beta = from_cycles(6, (0, 1, 2), (3, 4, 5))
    alpha = from_cycles(6, (0, 3, 1))
    all_s6 = tuple(permutations(range(6)))
    class33 = {p for p in all_s6 if signature(p) == (3, 3)}
    class3111 = {p for p in all_s6 if signature(p) == (3, 1, 1, 1)}
    require(len(all_s6) == 720 and len(set(all_s6)) == 720, "S6 coverage failure")
    require((class33, class3111) == support_generated_classes(), "class generators disagree")
    require(len(class33) == len(class3111) == 40, "class size mismatch")
    all_hist = Counter(signature(checked_product(p, beta)) for p in all_s6)
    expected_s6 = {(1,1,1,1,1,1): 1, (2,1,1,1,1): 15, (2,2,1,1): 45,
                   (2,2,2): 15, (3,1,1,1): 40, (3,2,1): 120, (3,3): 40,
                   (4,1,1): 90, (4,2): 90, (5,1): 144, (6,): 120}
    require(all_hist == expected_s6, "full S6 product inventory mismatch")
    expected33 = {(1,1,1,1,1,1): 1, (3,1,1,1): 2, (3,3): 10,
                  (2,2,1,1): 9, (5,1): 18}
    expected_mixed = {(3,1,1,1): 2, (3,3): 2, (4,2): 18, (5,1): 18}
    records33 = [record(p, beta) for p in sorted(class33)]
    records_mixed = [record(p, beta) for p in sorted(class3111)]
    hist33 = Counter(signature(checked_product(p, beta)) for p in class33)
    hist_mixed = Counter(signature(checked_product(p, beta)) for p in class3111)
    require(hist33 == expected33, "analytic two-3+3 histogram mismatch")
    require(hist_mixed == expected_mixed, "mixed histogram mismatch")
    ordered33 = Counter(signature(checked_product(g, b)) for g in class33 for b in class33)
    ordered_mixed = Counter(signature(checked_product(g, b)) for g in class3111 for b in class33)
    require(ordered33 == Counter({k: 40*v for k,v in expected33.items()}), "ordered 3+3 mismatch")
    require(ordered_mixed == Counter({k: 40*v for k,v in expected_mixed.items()}), "ordered mixed mismatch")
    require(not any(all(k % 2 == 0 for k in sig) for sig in ordered33), "candidate counterexample")

    shared = Counter()
    mixed = Counter()
    beta_partition = {frozenset(c) for c in cycles(beta)}
    for gamma in class33:
        is_shared = {frozenset(c) for c in cycles(gamma)} == beta_partition
        (shared if is_shared else mixed)[signature(checked_product(gamma, beta))] += 1
    require(sum(shared.values()) == 4 and sum(mixed.values()) == 36, "partition case coverage")
    witness = record(alpha, beta)
    require(witness["delta_images"] == (2,3,0,5,1,4), "explicit mixed witness changed")
    require(witness["delta_type"] == "4+2", "adversarial witness is not 4+2")
    require(signature(compose(beta, inverse(alpha))) == (4,2), "reversed factor control failed")
    free_action = literal_e9_quotient([None, None])
    mixed_action = literal_e9_quotient([None, (1,0), (1,0), (1,2)])
    require(free_action["residual_type"] == "3+3", "free residual action mismatch")
    require(mixed_action["residual_type"] == "3+1+1+1", "mixed residual action mismatch")
    elements = tuple((a,b) for a in range(3) for b in range(3))
    row_action = {(a,b): tuple((r+b) % 3 for r in range(3)) for a,b in elements}
    row_stabilizer = [g for g in elements if row_action[g][0] == 0]
    require(row_stabilizer == [(0,0), (1,0), (2,0)], "selected row stabilizer mismatch")
    require({row_action[g][0] for g in elements} == {0,1,2}, "row action not transitive")
    require(all(row_action[h] == (0,1,2) for h in row_stabilizer), "H did not fix all rows")
    for a,b in elements:
        for c,d in elements:
            require(compose(row_action[a,b], row_action[c,d]) == row_action[(a+c) % 3, (b+d) % 3],
                    "selected row action failed the group law")

    result = {
        "status": "PASS",
        "scope": "independent internal finite permutation and quotient controls; no full Latin18 enumeration",
        "composition": "gamma * beta^{-1}; rightmost acts first; images indexed from zero",
        "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                    "processes": 1, "wall_timer_seconds": 4.5, "native_solver": False,
                    "repository_imports": False, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "coverage": {"S6": 720, "class_3+3": 40, "class_3+1+1+1": 40,
                     "all_fixed_beta_products": 720, "ordered_3+3_pairs": 1600,
                     "ordered_mixed_pairs": 1600,
                     "independent_class_generation": "cycle supports versus all S6",
                     "independent_product_check": "inverse composition versus edge equation",
                     "independent_cycle_check": "orbit tracing versus fixed points of powers"},
        "beta_images": beta,
        "all_S6_fixed_beta_histogram": histogram(all_hist),
        "two_3+3_fixed_beta_histogram": histogram(hist33),
        "two_3+3_shared_partition_histogram": histogram(shared),
        "two_3+3_mixed_partition_histogram": histogram(mixed),
        "two_3+3_ordered_pair_histogram": histogram(ordered33),
        "two_3+3_fixed_point_free_even_cycled_count": 0,
        "mixed_fixed_beta_histogram": histogram(hist_mixed),
        "mixed_ordered_pair_histogram": histogram(ordered_mixed),
        "mixed_ordered_even_cycled_count": ordered_mixed[(4,2)],
        "two_3+3_fixed_beta_records": records33,
        "mixed_fixed_beta_records": records_mixed,
        "adversarial_witness": witness,
        "mixed_row_F_rectangle": mixed_rectangle_control(beta, alpha),
        "odd_fiber_cycle_controls": odd_fiber_controls(),
        "literal_E9_free_coordinate": free_action,
        "literal_E9_mixed_A21_coordinate": mixed_action,
        "literal_selected_E9_H_row_orbit": {"rows": 3, "stabilizer_H": row_stabilizer,
                                           "group_law_checks": 81,
                                           "residual_action": row_action[0,1]},
    }
    result["runtime"]["elapsed_seconds_before_serialization"] = time.perf_counter() - started
    require(result["runtime"]["elapsed_seconds_before_serialization"] < 4.5, "elapsed budget exceeded")
    with output.open("x", encoding="ascii") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    elapsed = time.perf_counter() - started
    require(elapsed < 5, "five-second run limit exceeded")
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({"status": "PASS", "elapsed_seconds_including_output": elapsed,
                      "output": output.name, "two_3+3_even_cycled": 0,
                      "mixed_ordered_even_cycled": ordered_mixed[(4,2)]}, sort_keys=True))


if __name__ == "__main__":
    main()
