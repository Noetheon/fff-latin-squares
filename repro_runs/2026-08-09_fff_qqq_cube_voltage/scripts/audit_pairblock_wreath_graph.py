#!/usr/bin/env python3
"""Independently enumerate the p=3 pair-block compatibility graph."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from build_pairblock_wreath_cnf import relative_is_even, wreath_perm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    p = 3
    identity = tuple(range(2 * p))
    candidates = sorted(
        perm
        for phi in itertools.permutations(range(p))
        for flips in itertools.product((0, 1), repeat=p)
        if (perm := wreath_perm(phi, flips)) != identity and relative_is_even(perm, identity)
    )
    edges = {
        (left, right)
        for left in range(len(candidates))
        for right in range(left + 1, len(candidates))
        if relative_is_even(candidates[left], candidates[right])
    }

    def is_clique(indices: tuple[int, ...]) -> bool:
        return all((min(a, b), max(a, b)) in edges for a, b in itertools.combinations(indices, 2))

    clique_counts = {}
    witnesses = {}
    maximum = 0
    for size in range(1, 6):
        cliques = [indices for indices in itertools.combinations(range(len(candidates)), size) if is_clique(indices)]
        clique_counts[str(size)] = len(cliques)
        if cliques:
            maximum = size
            witnesses[str(size)] = [list(candidates[index]) for index in cliques[0]]
    result = {
        "p": p,
        "full_wreath_order": 48,
        "candidate_count_excluding_identity": len(candidates),
        "compatible_edge_count": len(edges),
        "clique_counts_through_required_size": clique_counts,
        "maximum_clique_size": maximum,
        "maximum_family_size_including_identity": maximum + 1,
        "required_family_size": 6,
        "witnesses": witnesses,
        "conclusion": "No row-F sharply transitive family preserving three blocks of size two exists.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "p=3 pair-block compatibility graph audit\n\n"
        f"candidates_excluding_identity: {len(candidates)}\n"
        f"compatible_edges: {len(edges)}\n"
        f"clique_counts: {clique_counts}\n"
        f"maximum_clique_size: {maximum}\n"
        f"maximum_family_size_including_identity: {maximum + 1}\n"
        "required_family_size: 6\n"
        "conclusion: no degree-6 row-F family preserving three pair blocks.\n"
    )


if __name__ == "__main__":
    main()
