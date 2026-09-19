#!/usr/bin/env python3
"""Cross-check every computational theorem in the manuscript against frozen results."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
RESULTS = RUN / "results"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(relative: str) -> tuple[Path, dict]:
    path = ROOT / relative
    return path, json.loads(path.read_text(encoding="utf-8"))


def package_checks(path: Path) -> dict[str, bool]:
    run = path.parents[1]
    return {
        name: (run / name).is_file()
        for name in (
            "README.md",
            "commands.sh",
            "environment.txt",
            "inputs_manifest.tsv",
            "outputs_manifest.tsv",
            "MANIFEST.tsv",
        )
    }


def parse_order10_palette_list(path: Path) -> list[frozenset[str]]:
    text = path.read_text(encoding="utf-8")
    start = text.index("\\begin{computationaltheorem}[Order-$10$ cycle-type palette exclusions]")
    end = text.index("\\end{computationaltheorem}", start)
    block = text[start:end]
    palettes: list[frozenset[str]] = []
    for raw in re.findall(r"&\\\{(.*?)\\\}", block):
        normalized = raw.replace("2^5", "2+2+2+2+2").replace(" ", "")
        palettes.append(frozenset(normalized.split(",")))
    return palettes


def record(title: str, relative: str, checks: dict[str, bool], boundary: str) -> dict:
    path, _ = load(relative)
    return {
        "title": title,
        "evidence_path": relative,
        "evidence_sha256": sha256(path),
        "theorem_relevant_checks": checks,
        "all_theorem_relevant_checks_pass": all(checks.values()),
        "package_files_present": package_checks(path),
        "all_package_files_present": all(package_checks(path).values()),
        "evidence_boundary": boundary,
    }


def record_many(
    title: str,
    primary_relative: str,
    supporting_relatives: list[str],
    checks: dict[str, bool],
    boundary: str,
) -> dict:
    primary_path, _ = load(primary_relative)
    paths = [primary_path]
    for relative in supporting_relatives:
        path, _ = load(relative)
        paths.append(path)
    package_presence: dict[str, bool] = {}
    for path in paths:
        run_name = path.parents[1].name
        for name, present in package_checks(path).items():
            package_presence[f"{run_name}/{name}"] = present
    return {
        "title": title,
        "evidence_path": primary_relative,
        "evidence_sha256": sha256(primary_path),
        "supporting_evidence": {
            str(path.relative_to(ROOT)): sha256(path) for path in paths[1:]
        },
        "theorem_relevant_checks": checks,
        "all_theorem_relevant_checks_pass": all(checks.values()),
        "package_files_present": package_presence,
        "all_package_files_present": all(package_presence.values()),
        "evidence_boundary": boundary,
    }


def main() -> None:
    manuscript_files = [
        ROOT / "manuscript/sections/02_flag_surface.tex",
        ROOT / "manuscript/sections/04_primitive_degree10.tex",
        ROOT / "manuscript/sections/05_computational_results.tex",
        ROOT / "manuscript/sections/07_open_problems.tex",
    ]
    theorem_titles: list[str] = []
    pattern = re.compile(r"\\begin\{computationaltheorem\}\[([^]]+)\]")
    for path in manuscript_files:
        theorem_titles.extend(pattern.findall(path.read_text(encoding="utf-8")))

    small_path, small = load(
        "repro_runs/2026-04-26_small_order_witness_reruns/results/latin_trade_results.json"
    )
    small_validation_path, small_validation = load(
        "repro_runs/2026-04-26_small_order_witness_reruns/results/"
        "small_order_generation_validation.json"
    )
    order8_path, order8 = load(
        "repro_runs/2026-04-26_order8_core/results/order8_recheck_fullscan_results.json"
    )
    subsquare_path, subsquare = load(
        "repro_runs/2026-08-09_fff_subsquare_congruence_obstructions/results/"
        "subsquare_congruence_validation.json"
    )
    affine_path, affine = load(
        "repro_runs/2026-08-09_fff_cycle_profile_affine_span/results/"
        "cycle_profile_affine_span_audit.json"
    )
    rainbow_path, rainbow = load(
        "repro_runs/2026-08-09_fff_flag_surface_audit/results/"
        "rainbow_square_classifier.json"
    )
    rainbow_independent_path, rainbow_independent = load(
        "repro_runs/2026-08-09_fff_flag_surface_audit/results/"
        "rainbow_square_independent_validation.json"
    )
    labelled_path, labelled = load(
        "repro_runs/2026-08-09_fff_labelled_flag_incidence/results/"
        "labelled_flag_incidence_audit.json"
    )
    primitive_path, primitive = load(
        "repro_runs/2026-08-09_fff_primitive_group_reduction/results/"
        "primitive_group_reduction_status.json"
    )
    holonomy_path, holonomy = load(
        "repro_runs/2026-08-11_fff_color_parity_holonomy/results/"
        "color_parity_holonomy_audit.json"
    )
    trade_lattice_path, trade_lattice = load(
        "repro_runs/2026-08-11_fff_common_mode_trade_lattice/results/"
        "common_mode_trade_lattice_audit.json"
    )
    _, trade_lattice_saturation = load(
        "repro_runs/2026-08-11_fff_common_mode_trade_lattice/results/"
        "common_mode_saturation_audit.json"
    )
    _, trade_lattice_verification = load(
        "repro_runs/2026-08-11_fff_common_mode_trade_lattice/results/"
        "common_mode_trade_lattice_verification.json"
    )
    intrinsic_parity_path, intrinsic_parity = load(
        "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/results/"
        "all_rank19_exchange_parity_audit.json"
    )
    _, intrinsic_mainclasses = load(
        "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/results/"
        "order6_exchange_mainclass_classification.json"
    )
    _, intrinsic_exceptional = load(
        "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/results/"
        "intrinsic_exchange_parity_audit.json"
    )
    _, intrinsic_verification = load(
        "repro_runs/2026-08-11_fff_intrinsic_exchange_parity/results/"
        "intrinsic_exchange_parity_verification.json"
    )
    exchange_controls_path, exchange_controls = load(
        "repro_runs/2026-08-11_fff_exchange_parity_controls/results/"
        "exchange_parity_controls_merged.json"
    )
    exchange_controls_verification_path, exchange_controls_verification = load(
        "repro_runs/2026-08-11_fff_exchange_parity_controls/results/"
        "exchange_parity_controls_verification.json"
    )
    p20_path, p20 = load(
        "repro_runs/2026-08-14_fff_four_type_p20_search/results/"
        "p20_case_run_validation.json"
    )
    five_inventory_path, five_inventory = load(
        "repro_runs/2026-08-14_fff_five_type_palette_inventory/results/"
        "five_type_orbit_inventory_validation.json"
    )
    five_inventory_independent_path, five_inventory_independent = load(
        "repro_runs/2026-08-14_fff_five_type_palette_inventory/results/"
        "five_type_inventory_independent_audit.json"
    )
    five_ranges_path, five_ranges = load(
        "repro_runs/2026-08-14_fff_five_type_palette_inventory/results/"
        "five_type_intercalate_ranges.json"
    )
    five_case_records: dict[str, tuple[Path, dict]] = {}
    for case_id in ("f01", "f16", "f17", "f18", "f19"):
        five_case_records[case_id] = load(
            f"repro_runs/2026-08-14_fff_five_type_{case_id}_search/results/"
            f"{case_id}_run_validation.json"
        )
    five_case_records["f20"] = load(
        "repro_runs/2026-08-20_fff_five_type_f20_search/results/"
        "f20_run_validation.json"
    )
    five_case_records["f21"] = load(
        "repro_runs/2026-08-20_fff_five_type_f21_search/results/"
        "f21_run_validation.json"
    )
    five_case_records["f02"] = load(
        "repro_runs/2026-08-21_fff_five_type_f02_search/results/"
        "f02_run_validation.json"
    )
    five_case_records["f07"] = load(
        "repro_runs/2026-08-21_fff_five_type_f07_search/results/"
        "f07_run_validation.json"
    )
    five_case_records["f04"] = load(
        "repro_runs/2026-08-21_fff_five_type_f04_search/results/"
        "f04_run_validation.json"
    )
    five_case_records["f03"] = load(
        "repro_runs/2026-08-21_fff_five_type_f03_search/results/"
        "f03_run_validation.json"
    )
    five_case_records["f05"] = load(
        "repro_runs/2026-08-21_fff_five_type_f05_search/results/"
        "f05_run_validation.json"
    )
    five_case_records["f11"] = load(
        "repro_runs/2026-08-21_fff_five_type_f11_search/results/"
        "f11_run_validation.json"
    )
    five_case_records["f06"] = load(
        "repro_runs/2026-08-21_fff_five_type_f06_search/results/"
        "f06_run_validation.json"
    )
    five_case_records["f12"] = load(
        "repro_runs/2026-08-21_fff_five_type_f12_search/results/"
        "f12_run_validation.json"
    )
    five_case_records["f08"] = load(
        "repro_runs/2026-08-22_fff_five_type_f08_search/results/"
        "f08_run_validation.json"
    )
    five_case_records["f13"] = load(
        "repro_runs/2026-08-22_fff_five_type_f13_search/results/"
        "f13_run_validation.json"
    )
    five_case_records["f14"] = load(
        "repro_runs/2026-08-23_fff_five_type_f14_search/results/"
        "f14_run_validation.json"
    )
    five_case_records["f09"] = load(
        "repro_runs/2026-08-24_fff_five_type_f09_search/results/"
        "f09_run_validation.json"
    )
    five_case_records["f10"] = load(
        "repro_runs/2026-08-24_fff_five_type_f10_search/results/"
        "f10_run_validation.json"
    )
    five_case_records["f15"] = load(
        "repro_runs/2026-08-25_fff_five_type_f15_search/results/"
        "f15_run_validation.json"
    )
    noninvolution_master_path, noninvolution_master = load(
        "repro_runs/2026-08-26_fff_six_type_noninvolution_master_search/results/"
        "noninvolution_run_validation.json"
    )
    noninvolution_comparison_path, noninvolution_comparison = load(
        "repro_runs/2026-08-26_fff_six_type_noninvolution_master_search/results/"
        "noninvolution_reduced_control_comparison.json"
    )
    involution_master_path, involution_master = load(
        "repro_runs/2026-08-26_fff_six_type_involution_master_search/results/"
        "involution_run_validation.json"
    )
    involution_comparison_path, involution_comparison = load(
        "repro_runs/2026-08-26_fff_six_type_involution_master_search/results/"
        "involution_reduced_control_comparison.json"
    )
    f18_clique_path, f18_cliques = load(
        "repro_runs/2026-08-14_fff_five_type_f18_search/results/"
        "f18_all_clique_completion_audit.json"
    )
    f17_binary_path, f17_binary = load(
        "repro_runs/2026-08-14_fff_five_type_f17_search/results/"
        "f17_binary_clique_table_audit.json"
    )
    f19_binary_path, f19_binary = load(
        "repro_runs/2026-08-14_fff_five_type_f19_search/results/"
        "f19_binary_clique_table_audit.json"
    )
    f20_binary_path, f20_binary = load(
        "repro_runs/2026-08-20_fff_five_type_f20_search/results/"
        "f20_binary_clique_table_audit.json"
    )
    f21_binary_path, f21_binary = load(
        "repro_runs/2026-08-20_fff_five_type_f21_search/results/"
        "f21_binary_clique_table_audit.json"
    )
    f02_binary_path, f02_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f02_search/results/"
        "f02_binary_clique_table_audit.json"
    )
    f07_binary_path, f07_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f07_search/results/"
        "f07_binary_clique_table_audit.json"
    )
    f04_binary_path, f04_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f04_search/results/"
        "f04_binary_clique_table_audit.json"
    )
    f03_binary_path, f03_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f03_search/results/"
        "f03_binary_clique_table_audit.json"
    )
    f05_binary_path, f05_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f05_search/results/"
        "f05_binary_clique_table_audit.json"
    )
    f11_binary_path, f11_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f11_search/results/"
        "f11_binary_clique_table_audit.json"
    )
    f06_binary_path, f06_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f06_search/results/"
        "f06_binary_clique_table_audit.json"
    )
    f12_binary_path, f12_binary = load(
        "repro_runs/2026-08-21_fff_five_type_f12_search/results/"
        "f12_binary_clique_table_audit.json"
    )
    f08_binary_path, f08_binary = load(
        "repro_runs/2026-08-22_fff_five_type_f08_search/results/"
        "f08_binary_clique_table_audit.json"
    )
    f13_binary_path, f13_binary = load(
        "repro_runs/2026-08-22_fff_five_type_f13_search/results/"
        "f13_binary_clique_table_audit.json"
    )
    f14_binary_path, f14_binary = load(
        "repro_runs/2026-08-23_fff_five_type_f14_search/results/"
        "f14_binary_clique_table_audit.json"
    )
    f09_binary_path, f09_binary = load(
        "repro_runs/2026-08-24_fff_five_type_f09_search/results/"
        "f09_binary_clique_table_audit.json"
    )
    f10_binary_path, f10_binary = load(
        "repro_runs/2026-08-24_fff_five_type_f10_search/results/"
        "f10_binary_clique_table_audit.json"
    )
    f15_binary_path, f15_binary = load(
        "repro_runs/2026-08-25_fff_five_type_f15_search/results/"
        "f15_binary_clique_table_audit.json"
    )
    printed_five_palettes = parse_order10_palette_list(
        ROOT / "manuscript/sections/07_open_problems.tex"
    )
    evidence_five_palettes = [
        frozenset(result["result"]["palette"])
        for _, result in five_case_records.values()
    ]
    reproducibility_text = re.sub(
        r"\s+",
        " ",
        (ROOT / "manuscript/sections/06_reproducibility.tex").read_text(
            encoding="utf-8"
        ),
    )

    expected_patterns = {
        "FFF": 230,
        "FFT": 81,
        "FTF": 40,
        "FTT": 315,
        "TFF": 133,
        "TFT": 209,
        "TTF": 232,
        "TTT": 282417,
    }
    small_by_order = {item["n"]: item for item in small["orders"]}
    validation_by_order = {item["n"]: item for item in small_validation["orders"]}
    small_patterns = small_by_order[6]["patterns_any_pairs"]
    order8_scan = order8["scan"]
    order8_sub = subsquare["order8_fff_subsquare_census"]
    order8_labelled = labelled["datasets"]["order8_fff_complete"]
    order8_holonomy = holonomy["datasets"]["order8_fff_complete"]

    claims = [
        record(
            "Small orders",
            str(small_path.relative_to(ROOT)),
            {
                "n2_count_1": validation_by_order[2]["generated_total_count"] == 1,
                "n4_count_4": validation_by_order[4]["generated_total_count"] == 4,
                "n6_count_9408": validation_by_order[6]["generated_total_count"] == 9408,
                "n6_all_latin": validation_by_order[6]["all_latin"],
                "n6_all_reduced": validation_by_order[6]["all_reduced"],
                "n6_all_unique": validation_by_order[6]["all_unique"],
                "n6_pattern_counts": small_patterns
                == {
                    "(False, False, True)": 936,
                    "(False, True, False)": 936,
                    "(True, False, False)": 936,
                    "(True, True, True)": 6600,
                },
            },
            "Complete reduced enumeration; extension to all squares uses isotopy invariance.",
        ),
        record(
            "Order-8 pattern census",
            str(order8_path.relative_to(ROOT)),
            {
                "main_classes_283657": order8_scan["total_main_classes"] == 283657,
                "pattern_counts": order8_scan["pattern_counts"] == expected_patterns,
                "fff_count_230": order8_scan["counterexamples_count"] == 230,
                "group_isotopic_5": order8_scan["counterexample_group_isotopy"]["group_isotopic"]
                == 5,
                "non_group_isotopic_225": order8_scan["counterexample_group_isotopy"][
                    "non_group_isotopic"
                ]
                == 225,
            },
            "Complete frozen ANU main-class census; completeness of the external census is cited.",
        ),
        record(
            "Subsquare census of the FFF classes",
            str(subsquare_path.relative_to(ROOT)),
            {
                "fff_count_230": order8_sub["fff_square_count"] == 230,
                "intercalate_range_2_112": (
                    order8_sub["minimum_intercalates"], order8_sub["maximum_intercalates"]
                )
                == (2, 112),
                "order3_total_0": order8_sub["order3_subsquare_total"] == 0,
                "order4_distribution": order8_sub["order4_subsquare_count_distribution"]
                == {"0": 63, "4": 156, "12": 10, "28": 1},
                "extremal_lines": {
                    item["line_number"] for item in order8_sub["extremal_entries"]
                }
                == {1, 10776},
            },
            "Exact on the frozen 230 order-8 FFF representatives only.",
        ),
        record(
            "Affine cycle-profile saturation",
            str(affine_path.relative_to(ROOT)),
            {
                f"gf_{prime}_baseline_span": affine["orders"]["8"]["prime_results"][prime][
                    "observed_nullspace_equals_baseline_span"
                ]
                for prime in ("2", "3", "5", "7")
            },
            "Exact finite-field row reduction on the complete frozen order-8 census.",
        ),
        record(
            "Order-8 rainbow-square classifier",
            str(rainbow_path.relative_to(ROOT)),
            {
                "table_count_230": rainbow["table_count"] == 230,
                "c70_distinct_226": rainbow["c70_distinct_count"] == 226,
                "joint_distinct_230": rainbow["c70_rainbow_square_joint_distinct_count"] == 230,
                "four_collision_pairs": len(rainbow["c70_collision_groups"]) == 4,
                "no_remaining_collisions": rainbow["remaining_joint_collision_groups"] == [],
                "independent_zero_mismatches": rainbow_independent["beta2_mismatch_count"] == 0,
            },
            "Classifier only on the frozen 230 order-8 FFF representatives.",
        ),
        record(
            "Pair-label triangle classifier",
            str(labelled_path.relative_to(ROOT)),
            {
                "table_count_230": order8_labelled["table_count"] == 230,
                "c70_distinct_226": order8_labelled["c70_distinct_count"] == 226,
                "triangle_distinct_100": order8_labelled["triangle_trace_distinct_count"] == 100,
                "intercalate_triangle_distinct_188": order8_labelled[
                    "intercalate_triangle_trace_distinct_count"
                ]
                == 188,
                "joint_distinct_230": order8_labelled[
                    "c70_triangle_trace_joint_distinct_count"
                ]
                == 230,
                "zero_audit_errors": labelled["totals"]["errors"] == 0,
            },
            "Classifier only on the frozen 230 order-8 FFF representatives.",
        ),
        record(
            "Primitive one-view reduction",
            str(primitive_path.relative_to(ROOT)),
            {
                "group_constructions_valid": primitive["group_constructions_valid"],
                "seven_small_groups_excluded": primitive[
                    "all_seven_small_groups_exclude_required_ten_clique"
                ],
                "nontrivial_bounds_proof_checked": primitive[
                    "all_nontrivial_upper_bounds_proof_checked"
                ],
                "maximum_cliques": [
                    item["maximum_f_clique_including_identity"]
                    for item in primitive["small_primitive_groups"]
                ]
                == [1, 2, 1, 2, 2, 2, 4],
                "remaining_groups": primitive["remaining_generated_groups"] == ["A10", "S10"],
            },
            "Finite exclusions are proof-checked; completeness of the standard degree-10 primitive-group classification is external.",
        ),
        record(
            "Order-8 holonomy profiles",
            str(holonomy_path.relative_to(ROOT)),
            {
                "table_count_230": order8_holonomy["table_count"] == 230,
                "profile_count_152": order8_holonomy[
                    "fff_holonomy_signature_count"
                ]
                == 152,
                "singleton_count_109": order8_holonomy[
                    "fff_holonomy_singleton_signature_count"
                ]
                == 109,
                "maximum_collision_5": order8_holonomy[
                    "fff_holonomy_max_signature_collision"
                ]
                == 5,
                "collision_histogram": order8_holonomy[
                    "fff_holonomy_signature_collision_histogram"
                ]
                == {"1": 109, "2": 22, "3": 12, "4": 4, "5": 5},
                "zero_audit_errors": holonomy["totals"]["errors"] == 0,
            },
            "Canonical profile only on the frozen 230 order-8 FFF representatives; not a complete classifier.",
        ),
        record(
            "Order-6 common-mode exchange lattice",
            str(trade_lattice_path.relative_to(ROOT)),
            {
                "table_count_9408": trade_lattice["totals"]["table_count"] == 9408,
                "rank_distribution": trade_lattice["totals"][
                    "elementary_rank_distribution"
                ]
                == {"19": 3960, "20": 5448},
                "all_saturated": trade_lattice["totals"]["saturated_table_count"]
                == 9408,
                "all_3plus3_contained": trade_lattice["totals"][
                    "three_exchange_containment_count"
                ]
                == 9408,
                "rank19_r3_count_180": trade_lattice["totals"][
                    "rank19_r3_table_count"
                ]
                == 180,
                "six_exchange_completions_180": trade_lattice["totals"][
                    "six_exchange_completion_count"
                ]
                == 180,
                "saturated_common_mode_index_two_180": trade_lattice_saturation[
                    "totals"
                ]["rank19_r3_index_two_count"]
                == 180,
                "independent_flint_verification": trade_lattice_verification[
                    "overall_pass"
                ]
                and trade_lattice_verification["error_count"] == 0,
            },
            "Complete reduced order-6 census; no universal quotient or order-10 claim.",
        ),
        record(
            "Order-6 intrinsic exchange parity",
            str(intrinsic_parity_path.relative_to(ROOT)),
            {
                "mainclass_count_12": intrinsic_mainclasses["totals"][
                    "mainclass_count"
                ]
                == 12,
                "classified_tables_9408": intrinsic_mainclasses["totals"][
                    "table_count"
                ]
                == 9408,
                "rank19_tables_3960": intrinsic_parity["totals"]["table_count"]
                == 3960,
                "rank19_mainclasses_3": intrinsic_parity["totals"][
                    "mainclass_count"
                ]
                == 3,
                "three_parity_signatures": intrinsic_parity["totals"][
                    "parity_signature_count"
                ]
                == 3,
                "exceptional_class_180": intrinsic_exceptional["totals"][
                    "table_count"
                ]
                == 180,
                "all_exceptional_modes_even": intrinsic_exceptional["totals"][
                    "common_mode_even_count"
                ]
                == 180,
                "all_completions_odd": intrinsic_exceptional["totals"][
                    "completion_odd_count"
                ]
                == 180,
                "independent_verification": intrinsic_verification["overall_pass"]
                and intrinsic_verification["error_count"] == 0,
            },
            "Complete order-6 main-class classification; no FFF or order-10 obstruction.",
        ),
        record(
            "Order-8 FFF exchange-parity controls",
            str(exchange_controls_path.relative_to(ROOT)),
            {
                "order8_tables_230": exchange_controls["order8_fff_complete"][
                    "table_count"
                ]
                == 230,
                "order8_all_fff": exchange_controls["order8_fff_complete"][
                    "pattern_distribution"
                ]
                == {"FFF": 230},
                "q4_distribution": exchange_controls["order8_fff_complete"][
                    "exchange_quotient_dimension_mod2_distribution"
                ]
                == {"0": 39, "1": 147, "2": 35, "3": 9},
                "line_rank_distribution": exchange_controls[
                    "order8_fff_complete"
                ]["line_rank_mod2_distribution"]
                == {"19": 1, "20": 10, "21": 156, "22": 63},
                "exchange_rank_distribution": exchange_controls[
                    "order8_fff_complete"
                ]["exchange_rank_mod2_distribution"]
                == {"39": 1, "40": 8, "41": 46, "42": 175},
                "forced_q4_equals_1_false": not exchange_controls[
                    "codimension_one_forced_by_fff"
                ],
                "independent_order8_verification_230": exchange_controls_verification[
                    "order8_verified_table_count"
                ]
                == 230,
                "explicit_source_170_q4_zero": exchange_controls_verification[
                    "explicit_fff_counterexample_to_forced_q4_equals_1"
                ]["source_index"]
                == 170
                and exchange_controls_verification[
                    "explicit_fff_counterexample_to_forced_q4_equals_1"
                ]["exchange_quotient_dimension_mod2"]
                == 0
                and exchange_controls_verification[
                    "explicit_fff_counterexample_to_forced_q4_equals_1"
                ]["independently_computed_pattern"]
                == "FFF",
                "independent_zero_errors": exchange_controls_verification[
                    "error_count"
                ]
                == 0,
            },
            "Complete frozen order-8 FFF controls; the order-10 companion corpus is diagnostic only.",
        ),
        record_many(
            "Order-10 cycle-type palette exclusions",
            str(p20_path.relative_to(ROOT)),
            [
                str(five_inventory_path.relative_to(ROOT)),
                str(five_inventory_independent_path.relative_to(ROOT)),
                str(five_ranges_path.relative_to(ROOT)),
                *[
                    str(path.relative_to(ROOT))
                    for path, _ in five_case_records.values()
                ],
                str(f18_clique_path.relative_to(ROOT)),
                str(f17_binary_path.relative_to(ROOT)),
                str(f19_binary_path.relative_to(ROOT)),
                str(f20_binary_path.relative_to(ROOT)),
                str(f21_binary_path.relative_to(ROOT)),
                str(f02_binary_path.relative_to(ROOT)),
                str(f07_binary_path.relative_to(ROOT)),
                str(f04_binary_path.relative_to(ROOT)),
                str(f03_binary_path.relative_to(ROOT)),
                str(f05_binary_path.relative_to(ROOT)),
                str(f11_binary_path.relative_to(ROOT)),
                str(f06_binary_path.relative_to(ROOT)),
                str(f12_binary_path.relative_to(ROOT)),
                str(f08_binary_path.relative_to(ROOT)),
                str(f13_binary_path.relative_to(ROOT)),
                str(f14_binary_path.relative_to(ROOT)),
                str(f09_binary_path.relative_to(ROOT)),
                str(f10_binary_path.relative_to(ROOT)),
                str(f15_binary_path.relative_to(ROOT)),
            ],
            {
                "p20_complete_negative": p20["all_checks_passed"]
                and not p20["result"]["fff_found"]
                and p20["result"]["orbits"] == 1831,
                "five_type_inventory_21_palettes_105_roots": five_inventory[
                    "all_checks_passed"
                ]
                and five_inventory_independent["all_checks_passed"]
                and five_inventory_independent["counts"]
                == {"palettes": 21, "record_errors": 0, "root_records": 105},
                "intercalate_inventory_valid": five_ranges["all_checks_passed"]
                and five_ranges["counts"]["palettes"] == 21,
                "five_cases_complete_negative": all(
                    result["all_checks_passed"]
                    and not result["result"]["fff_found"]
                    for _, result in five_case_records.values()
                ),
                "five_case_ids_exact": set(five_case_records)
                == {
                    "f01",
                    "f02",
                    "f03",
                    "f04",
                    "f05",
                    "f06",
                    "f07",
                    "f08",
                    "f09",
                    "f10",
                    "f11",
                    "f12",
                    "f13",
                    "f14",
                    "f15",
                    "f16",
                    "f17",
                    "f18",
                    "f19",
                    "f20",
                    "f21",
                },
                "printed_palette_count_21": len(printed_five_palettes) == 21,
                "printed_palettes_unique": len(set(printed_five_palettes)) == 21,
                "printed_palettes_match_evidence_exactly": set(printed_five_palettes)
                == set(evidence_five_palettes),
                "open_palette_arithmetic_is_zero": 21
                - len(set(printed_five_palettes))
                == 0,
                "reproducibility_prose_hands_off_to_master_packages": (
                    "all exact six- and seven-type palettes are handled by the following master packages"
                    in reproducibility_text
                ),
                "reproducibility_prose_does_not_leave_five_type_open": (
                    "five-type palette and all six- and seven-type palettes remain open"
                    not in reproducibility_text
                ),
                "f17_independent_zero_cliques": f17_binary["valid"]
                and f17_binary["clique_count"] == 0,
                "f18_independent_1920_nonfff": f18_cliques["all_checks_passed"]
                and f18_cliques["pattern_counts"] == {"FFT": 960, "FTF": 960}
                and f18_cliques["fff_count"] == 0,
                "f19_independent_1920_nonfff": f19_binary["valid"]
                and f19_binary["clique_count"] == 1920
                and f19_binary["pattern_counts"] == {"FFT": 960, "FTF": 960}
                and f19_binary["fff_count"] == 0,
                "f20_independent_23040_nonfff": f20_binary["valid"]
                and f20_binary["clique_count"] == 23040
                and f20_binary["exact_palette_count"] == 19200
                and f20_binary["pattern_counts"]
                == {"FFT": 11520, "FTF": 11520}
                and f20_binary["fff_count"] == 0,
                "f21_independent_1920_nonfff": f21_binary["valid"]
                and f21_binary["clique_count"] == 1920
                and f21_binary["exact_palette_count"] == 0
                and f21_binary["pattern_counts"]
                == {"FFT": 768, "FTF": 768, "FTT": 384}
                and f21_binary["fff_count"] == 0,
                "f02_independent_101760_nonfff": f02_binary["valid"]
                and f02_binary["clique_count"] == 101760
                and f02_binary["exact_palette_count"] == 99840
                and f02_binary["pattern_counts"]
                == {"FFT": 31680, "FTF": 31680, "FTT": 38400}
                and f02_binary["fff_count"] == 0,
                "f07_independent_1920_nonfff": f07_binary["valid"]
                and f07_binary["clique_count"] == 1920
                and f07_binary["exact_palette_count"] == 0
                and f07_binary["pattern_counts"]
                == {"FFT": 960, "FTF": 960}
                and f07_binary["fff_count"] == 0,
                "f04_independent_zero_cliques": f04_binary["valid"]
                and f04_binary["clique_count"] == 0
                and f04_binary["exact_palette_count"] == 0
                and f04_binary["pattern_counts"] == {}
                and f04_binary["fff_count"] == 0,
                "f03_independent_768_nonfff": f03_binary["valid"]
                and f03_binary["clique_count"] == 768
                and f03_binary["exact_palette_count"] == 0
                and f03_binary["pattern_counts"]
                == {"FFT": 384, "FTF": 384}
                and f03_binary["fff_count"] == 0,
                "f05_independent_8832_nonfff": f05_binary["valid"]
                and f05_binary["clique_count"] == 8832
                and f05_binary["exact_palette_count"] == 8832
                and f05_binary["pattern_counts"]
                == {"FFT": 2496, "FTF": 2496, "FTT": 3840}
                and f05_binary["fff_count"] == 0,
                "f11_independent_384_nonfff": f11_binary["valid"]
                and f11_binary["clique_count"] == 384
                and f11_binary["exact_palette_count"] == 384
                and f11_binary["pattern_counts"] == {"FTT": 384}
                and f11_binary["fff_count"] == 0,
                "f06_independent_2880_nonfff": f06_binary["valid"]
                and f06_binary["clique_count"] == 2880
                and f06_binary["exact_palette_count"] == 0
                and f06_binary["pattern_counts"]
                == {"FFT": 864, "FTF": 864, "FTT": 1152}
                and f06_binary["fff_count"] == 0,
                "f12_independent_1920_nonfff": f12_binary["valid"]
                and f12_binary["clique_count"] == 1920
                and f12_binary["exact_palette_count"] == 1152
                and f12_binary["pattern_counts"]
                == {"FFT": 384, "FTF": 384, "FTT": 1152}
                and f12_binary["fff_count"] == 0,
                "f08_independent_21120_nonfff": f08_binary["valid"]
                and f08_binary["clique_count"] == 21120
                and f08_binary["exact_palette_count"] == 0
                and f08_binary["pattern_counts"]
                == {"FFT": 6720, "FTF": 6720, "FTT": 7680}
                and f08_binary["fff_count"] == 0,
                "f13_independent_17280_nonfff": f13_binary["valid"]
                and f13_binary["clique_count"] == 17280
                and f13_binary["exact_palette_count"] == 13632
                and f13_binary["pattern_counts"]
                == {"FFT": 3840, "FTF": 3840, "FTT": 9600}
                and f13_binary["fff_count"] == 0,
                "f14_independent_21312_nonfff": f14_binary["valid"]
                and f14_binary["clique_count"] == 21312
                and f14_binary["exact_palette_count"] == 18432
                and f14_binary["pattern_counts"]
                == {"FFT": 4128, "FTF": 4128, "FTT": 13056}
                and f14_binary["fff_count"] == 0,
                "f09_independent_23040_nonfff": f09_binary["valid"]
                and f09_binary["clique_count"] == 23040
                and f09_binary["exact_palette_count"] == 21120
                and f09_binary["pattern_counts"]
                == {"FFT": 7680, "FTF": 7680, "FTT": 7680}
                and f09_binary["fff_count"] == 0,
                "f10_independent_55680_nonfff": f10_binary["valid"]
                and f10_binary["clique_count"] == 55680
                and f10_binary["exact_palette_count"] == 34560
                and f10_binary["pattern_counts"]
                == {"FFT": 14400, "FTF": 14400, "FTT": 26880}
                and f10_binary["fff_count"] == 0,
                "f15_independent_32896_nonfff": f15_binary["valid"]
                and f15_binary["clique_count"] == 32896
                and f15_binary["exact_palette_count"] == 13504
                and f15_binary["pattern_counts"]
                == {"FFT": 13344, "FTF": 13344, "FTT": 6208}
                and f15_binary["fff_count"] == 0,
            },
            "Complete for palettes of size at most five; C155/C156 handle the remaining palettes.",
        ),
        record_many(
            "Order-10 nonexistence",
            str(noninvolution_master_path.relative_to(ROOT)),
            [
                str(noninvolution_comparison_path.relative_to(ROOT)),
                str(involution_master_path.relative_to(ROOT)),
                str(involution_comparison_path.relative_to(ROOT)),
            ],
            {
                "noninvolution_validator_15_of_15": noninvolution_master[
                    "all_checks_passed"
                ]
                and len(noninvolution_master["checks"]) == 15
                and all(noninvolution_master["checks"].values()),
                "noninvolution_exact_counts": noninvolution_master["result"]
                ["vertices"]
                == 172368
                and noninvolution_master["result"]["edges"] == 1650487056
                and noninvolution_master["result"]["orbits"] == 386
                and noninvolution_master["result"]["full_tasks"] == 18300
                and noninvolution_master["result"]["reduced_nodes"] == 2514104197
                and noninvolution_master["result"]["fff_found"] is False,
                "noninvolution_decompositions_match": noninvolution_comparison[
                    "all_checks_passed"
                ]
                and all(noninvolution_comparison["checks"].values())
                and noninvolution_comparison["values"]["crossview_odd_cycle_prunes"]
                == 1769153203,
                "involution_validator_15_of_15": involution_master[
                    "all_checks_passed"
                ]
                and len(involution_master["checks"]) == 15
                and all(involution_master["checks"].values()),
                "involution_exact_counts": involution_master["result"]["vertices"]
                == 190080
                and involution_master["result"]["edges"] == 2050329600
                and involution_master["result"]["orbits"] == 506
                and involution_master["result"]["full_tasks"] == 23760
                and involution_master["result"]["reduced_nodes"] == 5001728282
                and involution_master["result"]["fff_found"] is False,
                "involution_decompositions_match": involution_comparison[
                    "all_checks_passed"
                ]
                and all(involution_comparison["checks"].values())
                and involution_comparison["values"]["crossview_odd_cycle_prunes"]
                == 3586770865,
                "manuscript_has_nonexistence_theorem": (
                    "Nonexistence at order $10$" in theorem_titles
                ),
                "manuscript_has_no_stale_order10_open_status": all(
                    phrase not in " ".join(
                        path.read_text(encoding="utf-8")
                        for path in (ROOT / "manuscript/sections").glob("*.tex")
                    )
                    for phrase in (
                        "order $10$ remains undecided",
                        "counterexample, if one exists in the fixed reduced coordinates",
                        "all exact six- and seven-type palettes remain open",
                    )
                ),
                "manuscript_no_longer_calls_six_seven_open": (
                    "all exact six- and seven-type palettes remain open"
                    not in (ROOT / "manuscript/sections/07_open_problems.tex").read_text(
                        encoding="utf-8"
                    )
                ),
            },
            "Complete for order 10 only; C38 remains open beginning at order 12.",
        ),
    ]

    extra_inputs = {
        str(small_validation_path.relative_to(ROOT)): sha256(small_validation_path),
        str(rainbow_independent_path.relative_to(ROOT)): sha256(rainbow_independent_path),
        str(exchange_controls_verification_path.relative_to(ROOT)): sha256(
            exchange_controls_verification_path
        ),
    }
    report = {
        "audit_version": "manuscript_computational_claim_audit_v3",
        "manuscript_computational_theorem_count": len(theorem_titles),
        "manuscript_computational_theorem_titles": theorem_titles,
        "expected_theorem_count": 13,
        "claims": claims,
        "additional_validation_inputs": extra_inputs,
        "all_theorem_counts_match": len(theorem_titles) == 13,
        "all_theorem_relevant_checks_pass": all(
            claim["all_theorem_relevant_checks_pass"] for claim in claims
        ),
        "all_package_files_present": all(claim["all_package_files_present"] for claim in claims),
    }
    report["overall_pass"] = (
        report["all_theorem_counts_match"]
        and report["all_theorem_relevant_checks_pass"]
        and report["all_package_files_present"]
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / "manuscript_computational_claim_audit.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "Manuscript computational theorem audit",
        "=======================================",
        f"Computational theorem environments: {len(theorem_titles)}",
        f"Claims audited: {len(claims)}",
        f"All theorem-relevant checks pass: {report['all_theorem_relevant_checks_pass']}",
        f"All package files present: {report['all_package_files_present']}",
        f"Overall pass: {report['overall_pass']}",
        "",
    ]
    for claim in claims:
        lines.extend(
            [
                claim["title"],
                f"  evidence: {claim['evidence_path']}",
                f"  sha256: {claim['evidence_sha256']}",
                f"  checks pass: {claim['all_theorem_relevant_checks_pass']}",
                f"  package complete: {claim['all_package_files_present']}",
                f"  boundary: {claim['evidence_boundary']}",
            ]
        )
    summary_text = "\n".join(lines) + "\n"
    (RESULTS / "manuscript_computational_claim_audit_summary.txt").write_text(
        summary_text, encoding="utf-8"
    )
    print(summary_text, end="")
    if not report["overall_pass"]:
        raise SystemExit("manuscript computational theorem audit failed")


if __name__ == "__main__":
    main()
