#!/usr/bin/env python3
import argparse
import itertools
import json
from pathlib import Path


TYPES = ("10", "2+2+2+2+2", "4+2+2+2", "4+4+2", "6+2+2", "6+4", "8+2")
ODD_TYPES = {"10", "2+2+2+2+2", "4+4+2", "6+2+2"}
TWO_CYCLES = {
    "10": 0,
    "2+2+2+2+2": 5,
    "4+2+2+2": 3,
    "4+4+2": 1,
    "6+2+2": 2,
    "6+4": 0,
    "8+2": 1,
}
INVOLUTION = "2+2+2+2+2"


def positive_compositions(total: int, parts: int):
    if parts == 1:
        if total >= 1:
            yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in positive_compositions(total - first, parts - 1):
            yield (first,) + rest


def states_for_palette(palette):
    odd = [kind for kind in palette if kind in ODD_TYPES]
    even = [kind for kind in palette if kind not in ODD_TYPES]
    states = set()
    witnesses = {}
    for minority_size in range(1, 6):
        odd_edges = minority_size * (10 - minority_size)
        even_edges = 45 - odd_edges
        for odd_counts in positive_compositions(odd_edges, len(odd)):
            counts = dict(zip(odd, odd_counts))
            if counts.get(INVOLUTION, 0) > minority_size:
                continue
            for even_counts in positive_compositions(even_edges, len(even)):
                counts.update(zip(even, even_counts))
                intercalates = sum(TWO_CYCLES[kind] * count for kind, count in counts.items())
                state = (intercalates, minority_size % 2)
                states.add(state)
                witnesses.setdefault(state, {
                    "minority_sign_class_size": minority_size,
                    "type_counts": {kind: counts[kind] for kind in palette},
                })
    return states, witnesses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    palettes = list(itertools.combinations(TYPES, 5))
    records = []
    state_sets = []
    for number, palette in enumerate(palettes, 1):
        states, witnesses = states_for_palette(palette)
        values = sorted({value for value, _ in states})
        state_sets.append(states)
        records.append({
            "case_id": f"f{number:02d}",
            "palette": list(palette),
            "possible_intercalate_values": values,
            "possible_state_count": len(states),
            "minimum_intercalates": min(values),
            "maximum_intercalates": max(values),
            "missing_values_inside_range": sorted(set(range(min(values), max(values) + 1)) - set(values)),
            "minimum_witnesses": [
                witnesses[state] for state in sorted(states)
                if state[0] == min(values)
            ],
            "maximum_witnesses": [
                witnesses[state] for state in sorted(states)
                if state[0] == max(values)
            ],
        })

    incompatible_pairs = []
    for left in range(len(palettes)):
        left_values = {value for value, _ in state_sets[left]}
        for right in range(left + 1, len(palettes)):
            right_values = {value for value, _ in state_sets[right]}
            if left_values.isdisjoint(right_values):
                incompatible_pairs.append([f"f{left + 1:02d}", f"f{right + 1:02d}"])

    incompatible_triples = []
    for left in range(len(palettes)):
        for middle in range(left, len(palettes)):
            for right in range(middle, len(palettes)):
                compatible = any(
                    i_left == i_middle == i_right
                    and (parity_left + parity_middle + parity_right) % 2 == 1
                    for i_left, parity_left in state_sets[left]
                    for i_middle, parity_middle in state_sets[middle]
                    for i_right, parity_right in state_sets[right]
                )
                if not compatible:
                    incompatible_triples.append([
                        f"f{left + 1:02d}",
                        f"f{middle + 1:02d}",
                        f"f{right + 1:02d}",
                    ])

    expected_pairs = [["f01", "f07"], ["f01", "f09"], ["f01", "f15"]]
    pair_explains_triples = all(
        any(pair[0] in triple and pair[1] in triple for pair in expected_pairs)
        for triple in incompatible_triples
    )
    checks = {
        "palette_count_21": len(records) == 21,
        "no_individually_empty_palette": all(state_sets),
        "incompatible_pairs_exact": incompatible_pairs == expected_pairs,
        "incompatible_triple_multisets_60": len(incompatible_triples) == 60,
        "pair_incompatibilities_explain_all_triples": pair_explains_triples,
    }
    output = {
        "schema_version": "five-type-intercalate-range-audit-v1",
        "model": {
            "odd_edge_count": "k*(10-k), 1<=k<=5",
            "exact_palette_usage": "every listed type count is positive",
            "involution_matching_bound": "count(2^5)<=k",
            "intercalate_count": "sum(type_count * number_of_2_cycles)",
            "cross_view_constraints": "common I and k_R+k_C+k_S odd",
        },
        "records": records,
        "incompatible_view_palette_pairs": incompatible_pairs,
        "incompatible_unordered_view_palette_triples": incompatible_triples,
        "counts": {
            "palettes": len(records),
            "incompatible_pairs": len(incompatible_pairs),
            "incompatible_unordered_triples": len(incompatible_triples),
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "claim_boundary": (
            "necessary aggregate conditions only; no individual five-type "
            "palette and no order-10 FFF square is excluded"
        ),
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    lines = [
        "Five-type exact-palette intercalate audit",
        "",
        "case  min  max  possible-I-count",
    ]
    lines.extend(
        f"{record['case_id']}  {record['minimum_intercalates']:3d}  "
        f"{record['maximum_intercalates']:3d}  "
        f"{len(record['possible_intercalate_values']):3d}"
        for record in records
    )
    lines += [
        "",
        "incompatible view-palette pairs: "
        + ", ".join("/".join(pair) for pair in incompatible_pairs),
        f"incompatible unordered view-palette triples: {len(incompatible_triples)}/1771",
        "all triple incompatibilities are explained by those pairs: "
        + str(pair_explains_triples).lower(),
        "no individual five-type palette is excluded",
        f"all checks passed: {str(output['all_checks_passed']).lower()}",
        "C38 open; C40 absent",
    ]
    args.summary.write_text("\n".join(lines) + "\n")
    if not output["all_checks_passed"]:
        raise SystemExit("five-type intercalate audit failed")


if __name__ == "__main__":
    main()
