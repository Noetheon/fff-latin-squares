#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


RUN = Path("repro_runs/2026-04-26_order8_closure_reconstruction")
NEW_DIR = RUN / "results"
OLD_DIR = Path("order8_all_created_artifacts_bundle")
OUT = NEW_DIR / "semantic_comparison_to_created_artifacts.json"


def load(name: str) -> tuple[dict, dict]:
    return (
        json.loads((NEW_DIR / name).read_text(encoding="utf-8")),
        json.loads((OLD_DIR / name).read_text(encoding="utf-8")),
    )


def compare() -> dict:
    group_new, group_old = load("order8_group_isotope_subgroup_criterion_results.json")
    near_new, near_old = load("order8_near_closure_analysis_results.json")

    group_parts = {
        "theorem": group_new["theorem"] == group_old["theorem"],
        "transitive_species_profiles": group_new["transitive_species_profiles"]
        == group_old["transitive_species_profiles"],
        "order8_fff_summary": group_new["order8_fff_summary"] == group_old["order8_fff_summary"],
    }
    near_parts = {
        "theorems": near_new["theorems"] == near_old["theorems"],
        "transitive_species_profiles": near_new["transitive_species_profiles"]
        == near_old["transitive_species_profiles"],
        "order8_fff_summary": near_new["order8_fff_summary"] == near_old["order8_fff_summary"],
    }

    return {
        "scope": "Fresh reconstruction of the closure/group-isotope and near-closure outputs from the durable order-8 core JSON inputs.",
        "comparisons": {
            "order8_group_isotope_subgroup_criterion_results.json": {
                "exact_json_object_match": group_new == group_old,
                "matched_parts": group_parts,
            },
            "order8_near_closure_analysis_results.json": {
                "exact_json_object_match": near_new == near_old,
                "matched_parts": near_parts,
            },
        },
        "overall_semantic_match": all(group_parts.values()) and all(near_parts.values()),
        "supports_claims": ["C14", "C15"],
        "remaining_structure_generator_gaps": [
            "order8_orbit_data_refinement_results.json",
            "order8_coupled_full_ternary_classification_results.json",
            "order8_full_fff_reference_catalog.json",
            "order8_full_fff_reference_table.tsv",
            "order8_full_fff_bridge_schema.json",
            "order8_full_fff_bridge_schema.tsv",
            "order8_nongroup_fff_classification_catalog.json",
            "order8_nongroup_fff_classification_table.tsv",
        ],
    }


def main() -> None:
    OUT.write_text(json.dumps(compare(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
