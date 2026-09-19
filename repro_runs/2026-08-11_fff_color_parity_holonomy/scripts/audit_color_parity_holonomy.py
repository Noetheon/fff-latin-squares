#!/usr/bin/env python3
"""Audit C85 colour-parity cocycles on frozen Latin-square corpora."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import runpy
from collections import Counter, defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SURFACE = runpy.run_path(
    str(ROOT / "repro_runs/2026-08-09_fff_flag_surface_audit/scripts/audit_flag_surface.py")
)
PAIR = runpy.run_path(
    str(
        ROOT
        / "repro_runs/2026-08-09_fff_labelled_flag_incidence/scripts/audit_labelled_flag_incidence.py"
    )
)
SMALL = PAIR["SMALL"]
VIEWS = ("row", "col", "sym")
VIEW_INDEX = {view: index for index, view in enumerate(VIEWS)}


def mask_potential_on_component(
    flag_ids: list[int], alphas: list[list[int]], mask: int
) -> dict[int, int] | None:
    """Return a binary potential when the selected colour cochain is exact."""
    allowed = set(flag_ids)
    potentials: dict[int, int] = {}
    for start in flag_ids:
        if start in potentials:
            continue
        potentials[start] = 0
        queue = deque([start])
        while queue:
            flag = queue.popleft()
            for color, alpha in enumerate(alphas):
                neighbor = alpha[flag]
                if neighbor not in allowed:
                    return None
                expected = potentials[flag] ^ ((mask >> color) & 1)
                if neighbor not in potentials:
                    potentials[neighbor] = expected
                    queue.append(neighbor)
                elif potentials[neighbor] != expected:
                    return None
    return potentials


def exact_mask_on_component(
    flag_ids: list[int], alphas: list[list[int]], mask: int
) -> bool:
    return mask_potential_on_component(flag_ids, alphas, mask) is not None


def binary_basis(values: list[int]) -> list[int]:
    """Return a deterministic GF(2) basis of three-bit masks."""
    pivots: dict[int, int] = {}
    basis = []
    for original in sorted(values):
        value = original
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                basis.append(original)
                break
    return basis


def permute_mask(mask: int, colour_permutation: tuple[int, int, int]) -> int:
    """Apply one global permutation of the three view colours to a bit mask."""
    return sum(
        ((mask >> old_colour) & 1) << colour_permutation[old_colour]
        for old_colour in range(3)
    )


def canonical_holonomy_signature(components: list[dict]) -> str:
    """Hash the component profile after quotienting by global colour permutation."""
    candidates = []
    for colour_permutation in itertools.permutations(range(3)):
        profile = sorted(
            (
                component["flags"],
                component["chi"],
                component["orientable"],
                tuple(
                    sorted(
                        permute_mask(mask, colour_permutation)
                        for mask in component["exact_masks"]
                    )
                ),
            )
            for component in components
        )
        candidates.append(profile)
    canonical = min(candidates)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def analyze_table(table: list[list[int]], source_index: int) -> dict:
    n = len(table)
    atoms, point_to_atom, _atoms_by_view = SURFACE["build_atoms"](table)
    flags = SURFACE["build_flags"](table, point_to_atom)
    alphas, bad_edge_groups = SURFACE["build_dual_involutions"](flags)
    pattern = PAIR["pattern"](table)
    errors: list[list] = []
    errors.extend(["dual_edge_group", *entry] for entry in bad_edge_groups[:20])

    incident_flags: dict[int, list[int]] = defaultdict(list)
    for flag_id, flag in enumerate(flags):
        for atom_id in flag["atoms"]:
            incident_flags[atom_id].append(flag_id)

    atom_delta_masks: list[int] = [0] * len(atoms)
    boundary_colour_edge_checks = 0
    for atom in atoms:
        atom_id = atom["id"]
        view = VIEW_INDEX[atom["view"]]
        members = set(incident_flags[atom_id])
        delta_mask = 0
        for color in range(3):
            if color == view:
                continue
            edges = set()
            for flag_id in members:
                neighbor = alphas[color][flag_id]
                if neighbor not in members:
                    errors.append(["atom_boundary_escape", atom_id, color, flag_id])
                    continue
                edges.add(tuple(sorted((flag_id, neighbor))))
            if len(edges) != atom["length"]:
                errors.append(
                    ["atom_boundary_colour_count", atom_id, color, len(edges), atom["length"]]
                )
            if len(edges) % 2:
                delta_mask ^= 1 << color
            boundary_colour_edge_checks += 1
        expected_delta = 0
        if atom["length"] % 2:
            expected_delta = 0b111 ^ (1 << view)
        if delta_mask != expected_delta:
            errors.append(["atom_coboundary", atom_id, delta_mask, expected_delta])
        atom_delta_masks[atom_id] = delta_mask

    coordinate_closed = [
        all(not (delta_mask & (1 << color)) for delta_mask in atom_delta_masks)
        for color in range(3)
    ]
    view_f = [letter == "F" for letter in pattern]
    expected_coordinate_closed = [
        all(view_f[other] for other in range(3) if other != color)
        for color in range(3)
    ]
    if coordinate_closed != expected_coordinate_closed:
        errors.append(
            ["coordinate_cocycle_pattern", coordinate_closed, expected_coordinate_closed, pattern]
        )
    vector_closed = all(delta_mask == 0 for delta_mask in atom_delta_masks)
    if vector_closed != (pattern == "FFF"):
        errors.append(["vector_cocycle_fff", vector_closed, pattern])

    adjacency = [set() for _flag in flags]
    for alpha in alphas:
        for flag_id, neighbor in enumerate(alpha):
            adjacency[flag_id].add(neighbor)
    flag_components = SURFACE["connected_components"](adjacency)

    components = []
    for component_id, flag_ids in enumerate(flag_components):
        atom_ids = sorted(
            {atom_id for flag_id in flag_ids for atom_id in flags[flag_id]["atoms"]}
        )
        edge_count = len(
            {
                (color, *sorted((flag_id, alphas[color][flag_id])))
                for color in range(3)
                for flag_id in flag_ids
            }
        )
        chi = len(flag_ids) - edge_count + len(atom_ids)
        orientable = SURFACE["is_bipartite"](flag_ids, adjacency)
        component_fff = all(atoms[atom_id]["length"] % 2 == 0 for atom_id in atom_ids)
        exact_masks = [
            mask for mask in range(8) if exact_mask_on_component(flag_ids, alphas, mask)
        ]
        if 0 not in exact_masks or len(exact_masks) & (len(exact_masks) - 1):
            errors.append(["exact_mask_not_subspace_size", component_id, exact_masks])
        relation_dimension = len(exact_masks).bit_length() - 1
        class_span_rank = 3 - relation_dimension
        if (7 in exact_masks) != orientable:
            errors.append(["orientation_class", component_id, orientable, exact_masks])
        if component_fff:
            b1 = 2 - chi
            if class_span_rank > b1:
                errors.append(
                    ["cohomology_dimension_bound", component_id, class_span_rank, b1]
                )
            relation_basis = binary_basis(exact_masks)
            if len(relation_basis) != relation_dimension:
                errors.append(
                    ["exact_mask_basis_dimension", component_id, relation_basis, exact_masks]
                )
            potentials = [
                mask_potential_on_component(flag_ids, alphas, mask)
                for mask in relation_basis
            ]
            if any(potential is None for potential in potentials):
                errors.append(["exact_mask_basis_potential", component_id, relation_basis])
                quotient_label_counts = {}
            else:
                quotient_label_counts = Counter(
                    tuple(potential[flag_id] for potential in potentials)
                    for flag_id in flag_ids
                )
                expected_fibres = 1 << relation_dimension
                expected_size = len(flag_ids) // expected_fibres
                if (
                    len(flag_ids) % expected_fibres
                    or len(quotient_label_counts) != expected_fibres
                    or set(quotient_label_counts.values()) != {expected_size}
                ):
                    errors.append(
                        [
                            "holonomy_quotient_fibres",
                            component_id,
                            relation_basis,
                            dict(quotient_label_counts),
                            expected_fibres,
                            expected_size,
                        ]
                    )
        else:
            b1 = None
            relation_basis = None
            quotient_label_counts = None

        intercalate_component = (
            len(flag_ids) == 4
            and len(atom_ids) == 3
            and all(atoms[atom_id]["length"] == 2 for atom_id in atom_ids)
        )
        if intercalate_component:
            if exact_masks != [0, 3, 5, 6] or class_span_rank != 1 or orientable:
                errors.append(
                    [
                        "intercalate_holonomy",
                        component_id,
                        exact_masks,
                        class_span_rank,
                        orientable,
                    ]
                )
        components.append(
            {
                "component_id": component_id,
                "flags": len(flag_ids),
                "atoms": len(atom_ids),
                "chi": chi,
                "b1_mod2": b1,
                "fff_component": component_fff,
                "orientable": orientable,
                "exact_masks": exact_masks,
                "exact_mask_basis": relation_basis,
                "colour_class_span_rank": class_span_rank if component_fff else None,
                "quotient_colour_fibre_count": (
                    len(quotient_label_counts) if quotient_label_counts is not None else None
                ),
                "quotient_colour_fibre_size": (
                    next(iter(quotient_label_counts.values()))
                    if quotient_label_counts
                    else None
                ),
                "intercalate_component": intercalate_component,
            }
        )

    if pattern == "FFF" and n % 2 == 0:
        total_chi = sum(component["chi"] for component in components)
        if total_chi % 2 != (n // 2) % 2:
            errors.append(["fff_euler_parity", total_chi, n // 2])
        if n % 4 == 2 and all(component["orientable"] for component in components):
            errors.append(["order_2mod4_holonomy", n])

    holonomy_signature = (
        canonical_holonomy_signature(components) if pattern == "FFF" else None
    )
    return {
        "source_index": source_index,
        "order": n,
        "pattern": pattern,
        "atom_count": len(atoms),
        "flag_count": len(flags),
        "boundary_colour_edge_checks": boundary_colour_edge_checks,
        "coordinate_closed": coordinate_closed,
        "vector_closed": vector_closed,
        "component_count": len(components),
        "canonical_holonomy_signature_sha256": holonomy_signature,
        "components": components,
        "errors": errors,
    }


def dataset_summary(name: str, records: list[dict]) -> dict:
    errors = [
        [record["source_index"], error]
        for record in records
        for error in record["errors"]
    ]
    components = [component for record in records for component in record["components"]]
    fff_components = [component for component in components if component["fff_component"]]
    fff_records = [record for record in records if record["pattern"] == "FFF"]
    rank_counts = Counter(
        component["colour_class_span_rank"] for component in fff_components
    )
    exact_mask_counts = Counter(
        ",".join(map(str, component["exact_masks"])) for component in fff_components
    )
    table_max_ranks = [
        max(component["colour_class_span_rank"] for component in record["components"])
        for record in fff_records
    ]
    signature_groups: dict[str, list[int]] = defaultdict(list)
    for record in fff_records:
        signature_groups[record["canonical_holonomy_signature_sha256"]].append(
            record["source_index"]
        )
    signature_collision_counts = Counter(
        len(source_indices) for source_indices in signature_groups.values()
    )
    return {
        "name": name,
        "table_count": len(records),
        "pattern_counts": dict(sorted(Counter(record["pattern"] for record in records).items())),
        "coordinate_closed_signatures": dict(
            sorted(
                Counter(
                    "".join("1" if value else "0" for value in record["coordinate_closed"])
                    for record in records
                ).items()
            )
        ),
        "atom_count": sum(record["atom_count"] for record in records),
        "flag_count": sum(record["flag_count"] for record in records),
        "boundary_colour_edge_checks": sum(
            record["boundary_colour_edge_checks"] for record in records
        ),
        "component_count": len(components),
        "fff_component_count": len(fff_components),
        "orientable_fff_component_count": sum(
            component["orientable"] for component in fff_components
        ),
        "nonorientable_fff_component_count": sum(
            not component["orientable"] for component in fff_components
        ),
        "intercalate_component_count": sum(
            component["intercalate_component"] for component in components
        ),
        "holonomy_quotient_component_checks": len(fff_components),
        "colour_class_span_rank_counts": {
            str(rank): count for rank, count in sorted(rank_counts.items())
        },
        "exact_mask_relation_counts": dict(sorted(exact_mask_counts.items())),
        "fff_table_max_component_rank_range": (
            [min(table_max_ranks), max(table_max_ranks)] if table_max_ranks else None
        ),
        "fff_holonomy_signature_count": len(signature_groups),
        "fff_holonomy_singleton_signature_count": signature_collision_counts.get(1, 0),
        "fff_holonomy_max_signature_collision": (
            max(signature_collision_counts) if signature_collision_counts else None
        ),
        "fff_holonomy_signature_collision_histogram": {
            str(size): count for size, count in sorted(signature_collision_counts.items())
        },
        "fff_holonomy_signature_groups": dict(sorted(signature_groups.items())),
        "error_count": len(errors),
        "errors": errors[:100],
    }


def load_n8(path: Path):
    with path.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            yield int(row["line_number"]), SURFACE["parse_compact"](row["square"], 8)


def write_summary(payload: dict, path: Path) -> None:
    totals = payload["totals"]
    lines = [
        "Colour-parity holonomy audit",
        "",
        f"audit version: {payload['audit_version']}",
        f"tables: {totals['tables']}",
        f"atoms: {totals['atoms']}",
        f"flags: {totals['flags']}",
        f"boundary colour-count checks: {totals['boundary_colour_edge_checks']}",
        f"components: {totals['components']}",
        f"holonomy quotient fibre checks: {totals['holonomy_quotient_component_checks']}",
        f"errors: {totals['errors']}",
        "",
        "Exact theorem audited:",
        "- the F2^3 colour-edge cochain is closed exactly for FFF;",
        "- each coordinate is closed exactly when the other two views are F;",
        "- the sum of the three colour classes is the orientation class w1;",
        "- exact colour masks determine the span rank of the three classes;",
        "- rank h gives 2^(3-h) equal flag fibres and flag divisibility;",
        "- every intercalate RP2 component has exact masks 000,011,101,110.",
        "",
    ]
    for name, data in payload["datasets"].items():
        lines.extend(
            [
                name,
                f"- tables: {data['table_count']}",
                f"- patterns: {data['pattern_counts']}",
                f"- coordinate-closed signatures: {data['coordinate_closed_signatures']}",
                f"- atoms / flags: {data['atom_count']} / {data['flag_count']}",
                f"- components: {data['component_count']}",
                f"- FFF components: {data['fff_component_count']}",
                f"- orientable / nonorientable FFF components: {data['orientable_fff_component_count']} / {data['nonorientable_fff_component_count']}",
                f"- intercalate components: {data['intercalate_component_count']}",
                f"- colour-class span ranks: {data['colour_class_span_rank_counts']}",
                f"- FFF table max-rank range: {data['fff_table_max_component_rank_range']}",
                f"- canonical FFF holonomy signatures: {data['fff_holonomy_signature_count']}",
                f"- singleton / max-collision signatures: {data['fff_holonomy_singleton_signature_count']} / {data['fff_holonomy_max_signature_collision']}",
                f"- signature collision histogram: {data['fff_holonomy_signature_collision_histogram']}",
                f"- errors: {data['error_count']}",
                "",
            ]
        )
    lines.extend(
        [
            "Evidence boundary:",
            "- C85 is rigorous; this run is exact sanity evidence.",
            "- Nontrivial holonomy at order 2 mod 4 is necessary, not contradictory.",
            "- The order-10 corpus is tracked partial data, not an exhaustive census.",
            "- C38 remains open and C40 remains absent.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fff-metadata", type=Path, required=True)
    parser.add_argument("--n10-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    datasets = {}
    datasets["order4_complete"] = dataset_summary(
        "order4_complete",
        [
            analyze_table(table, source)
            for source, table in enumerate(SMALL["reduced_latin_squares"](4), start=1)
        ],
    )
    datasets["order6_complete"] = dataset_summary(
        "order6_complete",
        [
            analyze_table(table, source)
            for source, table in enumerate(SMALL["reduced_latin_squares"](6), start=1)
        ],
    )
    datasets["order8_fff_complete"] = dataset_summary(
        "order8_fff_complete",
        [analyze_table(table, source) for source, table in load_n8(args.fff_metadata)],
    )
    datasets["order10_tracked_partial"] = dataset_summary(
        "order10_tracked_partial",
        [
            analyze_table(table, source)
            for source, table, _metadata in PAIR["FLAG"]["n10_tables"](args.n10_corpus)
        ],
    )

    payload = {
        "audit_version": "color_parity_holonomy_v2",
        "datasets": datasets,
        "totals": {
            "tables": sum(data["table_count"] for data in datasets.values()),
            "atoms": sum(data["atom_count"] for data in datasets.values()),
            "flags": sum(data["flag_count"] for data in datasets.values()),
            "boundary_colour_edge_checks": sum(
                data["boundary_colour_edge_checks"] for data in datasets.values()
            ),
            "components": sum(data["component_count"] for data in datasets.values()),
            "holonomy_quotient_component_checks": sum(
                data["holonomy_quotient_component_checks"] for data in datasets.values()
            ),
            "errors": sum(data["error_count"] for data in datasets.values()),
        },
        "claim_boundary": [
            "C85 globally glues the local C83 even-cycle bipartitions.",
            "The colour holonomy theorem is equivalent to FFF, not an order-10 decision.",
            "No order-10 existence or nonexistence result is claimed.",
            "C38 remains open and C40 remains absent.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_summary(payload, args.summary)
    return int(payload["totals"]["errors"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
