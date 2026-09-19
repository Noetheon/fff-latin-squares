#!/usr/bin/env python3
"""Build the smaller exact clique encoding for pair-block row-F families."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

from pysat.card import CardEnc, EncType

from build_pairblock_wreath_cnf import cycle_lengths, relative_is_even, wreath_perm


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", type=int, choices=(3, 5), required=True)
    parser.add_argument("--cnf-output", type=Path, required=True)
    parser.add_argument("--mapping-output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    p = args.p
    n = 2 * p
    identity = tuple(range(n))
    elements = []
    for phi in itertools.permutations(range(p)):
        for flips in itertools.product((0, 1), repeat=p):
            perm = wreath_perm(phi, flips)
            if perm != identity and relative_is_even(perm, identity):
                elements.append({"phi": phi, "flips": flips, "perm": perm})
    elements.sort(key=lambda item: item["perm"])
    variables = list(range(1, len(elements) + 1))
    cardinality = CardEnc.equals(
        lits=variables,
        bound=n - 1,
        top_id=len(elements),
        encoding=EncType.totalizer,
    )
    clauses = [list(clause) for clause in cardinality.clauses]
    cardinality_clause_count = len(clauses)
    incompatible_count = 0
    compatible_count = 0
    for left_index in range(len(elements)):
        left = elements[left_index]["perm"]
        for right_index in range(left_index + 1, len(elements)):
            right = elements[right_index]["perm"]
            if relative_is_even(left, right):
                compatible_count += 1
            else:
                clauses.append([-variables[left_index], -variables[right_index]])
                incompatible_count += 1
    args.cnf_output.parent.mkdir(parents=True, exist_ok=True)
    with args.cnf_output.open("w", encoding="ascii") as handle:
        handle.write(f"p cnf {cardinality.nv} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")
    mapping = {
        "encoding_version": "pairblock_wreath_row_f_clique_totalizer_v1",
        "p": p,
        "n": n,
        "identity_permutation": list(identity),
        "target_nonidentity_clique_size": n - 1,
        "elements": [
            {
                "variable": variables[index],
                "phi": list(item["phi"]),
                "flips": list(item["flips"]),
                "permutation": list(item["perm"]),
                "cycle_lengths_vs_identity": cycle_lengths(item["perm"]),
            }
            for index, item in enumerate(elements)
        ],
    }
    args.mapping_output.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
    metadata = {
        "encoding_version": mapping["encoding_version"],
        "p": p,
        "n": n,
        "full_wreath_order": len(list(itertools.permutations(range(p)))) * (2**p),
        "candidate_count_excluding_identity": len(elements),
        "target_clique_size": n - 1,
        "variables": cardinality.nv,
        "clauses": len(clauses),
        "cardinality_clause_count": cardinality_clause_count,
        "compatible_pair_count": compatible_count,
        "incompatible_pair_clause_count": incompatible_count,
        "cnf_sha256": sha256(args.cnf_output),
        "mapping_sha256": sha256(args.mapping_output),
        "elapsed_seconds": time.time() - started,
        "equivalence_note": "Pairwise derangement plus 2p selected permutations (including identity) implies sharp transitivity.",
        "scope": "Common p-blocks-of-size-2 row-F sharply transitive families only.",
    }
    args.metadata_output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    args.summary_output.write_text(
        "Pair-block wreath row-F clique CNF\n\n"
        f"p: {p}\nn: {n}\nfull_wreath_order: {metadata['full_wreath_order']}\n"
        f"candidates_excluding_identity: {len(elements)}\ntarget_clique_size: {n - 1}\n"
        f"variables: {cardinality.nv}\nclauses: {len(clauses)}\n"
        f"compatible_pairs: {compatible_count}\nincompatible_pairs: {incompatible_count}\n"
        f"cnf_sha256: {metadata['cnf_sha256']}\nelapsed_seconds: {metadata['elapsed_seconds']:.6f}\n"
        "scope: common pair-block imprimitive row-F model; not a global FFF model.\n"
    )


if __name__ == "__main__":
    main()
