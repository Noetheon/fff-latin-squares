#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transformed(text: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        if old not in text:
            raise ValueError(f"missing expected source fragment: {old!r}")
        text = text.replace(old, new)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    scripts = args.run / "scripts"
    reference = args.reference

    builder_replacements = [
        ("std::array<Type, 4>", "std::array<Type, 5>"),
        ("std::array<uint64_t, 4>", "std::array<uint64_t, 5>"),
        ("argc != 10 && argc != 11", "argc != 11 && argc != 12"),
        ("TYPE1 TYPE2 TYPE3 TYPE4 ROOT", "TYPE1 TYPE2 TYPE3 TYPE4 TYPE5 ROOT"),
        ("parse_type(argv[3]), parse_type(argv[4])};",
         "parse_type(argv[3]), parse_type(argv[4]), parse_type(argv[5])};"),
        ("type_code(palette[1]), type_code(palette[2]), type_code(palette[3])};",
         "type_code(palette[1]), type_code(palette[2]), type_code(palette[3]),\n      type_code(palette[4])};"),
        ("Type root_type = parse_type(argv[5]);", "Type root_type = parse_type(argv[6]);"),
        ("int filter_level = std::stoi(argv[6]);", "int filter_level = std::stoi(argv[7]);"),
        ("argc == 11 ? std::max(1, std::stoi(argv[10]))", "argc == 12 ? std::max(1, std::stoi(argv[11]))"),
        ("std::ofstream output(argv[7], std::ios::binary);", "std::ofstream output(argv[8], std::ios::binary);"),
        ("std::ofstream summary(argv[8]);", "std::ofstream summary(argv[9]);"),
        ("Filtered three-type candidate graph", "Filtered five-type candidate graph"),
        ("argv[9] << '\\n'", "argv[10] << '\\n'"),
        ("<< \" + \" << argv[4] << '\\n'", "<< \" + \" << argv[4] << \" + \" << argv[5] << '\\n'"),
        ("<< \"root: \" << argv[5]", "<< \"root: \" << argv[6]"),
    ]
    auditor_replacements = [
        ("std::array<Type, 4>", "std::array<Type, 5>"),
        ("std::array<uint64_t, 4>", "std::array<uint64_t, 5>"),
        ("argc != 10 && argc != 11", "argc != 11 && argc != 12"),
        ("parse_type(argv[3]), parse_type(argv[4])};",
         "parse_type(argv[3]), parse_type(argv[4]), parse_type(argv[5])};"),
        ("type_code(palette[1]), type_code(palette[2]), type_code(palette[3])};",
         "type_code(palette[1]), type_code(palette[2]), type_code(palette[3]),\n      type_code(palette[4])};"),
        ("Type root_type = parse_type(argv[5]);", "Type root_type = parse_type(argv[6]);"),
        ("int filter_level = std::stoi(argv[6]);", "int filter_level = std::stoi(argv[7]);"),
        ("argc == 11 ? std::max(1, std::stoi(argv[10]))", "argc == 12 ? std::max(1, std::stoi(argv[11]))"),
        ("std::ifstream input(argv[7], std::ios::binary);", "std::ifstream input(argv[8], std::ios::binary);"),
        ("std::ofstream result(argv[8]);", "std::ofstream result(argv[9]);"),
        ("std::ofstream summary(argv[9]);", "std::ofstream summary(argv[10]);"),
        ("Complete independent four-type graph audit", "Complete independent five-type graph audit"),
        ("static Perm inverse(const Perm &permutation) {",
         "static Perm representative(const Type &type) {\n"
         "  Perm result{};\n"
         "  int start = 0;\n"
         "  for (int length : type) {\n"
         "    for (int offset = 0; offset < length; ++offset) {\n"
         "      result[start + offset] = start + (offset + 1) % length;\n"
         "    }\n"
         "    start += length;\n"
         "  }\n"
         "  return result;\n"
         "}\n\n"
         "static Perm inverse(const Perm &permutation) {"),
        ("  bool valid = format_errors == 0 && diagonal_errors == 0 &&\n               padding_errors == 0 && cycle_type(root) == root_type &&\n",
         "  Perm canonical_root = representative(root_type);\n  uint64_t canonical_root_errors = root != canonical_root;\n  bool valid = format_errors == 0 && diagonal_errors == 0 &&\n               padding_errors == 0 && cycle_type(root) == root_type &&\n               canonical_root_errors == 0 &&\n"),
        ('         << "  \\\"padding_errors\\\": " << padding_errors << ",\\n"\n',
         '         << "  \\\"padding_errors\\\": " << padding_errors << ",\\n"\n         << "  \\\"canonical_root_errors\\\": " << canonical_root_errors << ",\\n"\n'),
        ("          << diagonal_errors << '/' << padding_errors << '\\n'\n",
         "          << diagonal_errors << '/' << padding_errors << '\\n'\n          << \"canonical-root errors: \" << canonical_root_errors << '\\n'\n"),
    ]
    checks = {}
    pairs = [
        ("builder_exact_mechanical_generalization",
         reference / "build_filtered_four_type_candidate_graph.cpp",
         scripts / "build_filtered_five_type_candidate_graph.cpp", builder_replacements),
        ("auditor_exact_mechanical_generalization",
         reference / "audit_complete_four_type_candidate_graph.cpp",
         scripts / "audit_complete_five_type_candidate_graph.cpp", auditor_replacements),
        ("task_plan_exact_mechanical_generalization",
         reference / "create_task_plan.py", scripts / "create_task_plan.py",
         [("nargs=4", "nargs=5"),
          ('"four-type-task-plan-v2"', '"five-type-task-plan-v1"')]),
        ("runner_schema_only_generalization",
         reference / "run_task_plan.py", scripts / "run_task_plan.py",
         [('"four-type-task-plan-v2"', '"five-type-task-plan-v1"'),
          ('"four-type-task-slice-v2"', '"five-type-task-slice-v1"')]),
        ("merger_schema_only_generalization",
         reference / "merge_task_slices.py", scripts / "merge_task_slices.py",
         [('"four-type-slice-merge-v2"', '"five-type-slice-merge-v1"')]),
        ("comparison_schema_only_generalization",
         reference / "compare_search_merges.py", scripts / "compare_search_merges.py",
         [('"four-type-search-merge-equivalence-v1"',
           '"five-type-search-merge-equivalence-v1"')]),
        ("structural_audit_title_only_generalization",
         reference / "audit_graph_structure.py", scripts / "audit_graph_structure.py",
         [("Four-type graph structural audit",
           "Candidate graph structural audit")]),
    ]
    details = {}
    for name, source, target, replacements in pairs:
        expected = transformed(source.read_text(), replacements)
        actual = target.read_text()
        checks[name] = actual == expected
        details[name] = {
            "reference_path": str(source.resolve()),
            "reference_sha256": sha256(source),
            "target_path": str(target.resolve()),
            "target_sha256": sha256(target),
        }
    for filename in (
        "bind_graph_audits.py", "partial_cycle.hpp", "search_partite_fff.cpp",
    ):
        name = f"unchanged_{filename}"
        source = reference / filename
        target = scripts / filename
        checks[name] = source.read_bytes() == target.read_bytes()
        details[name] = {
            "reference_sha256": sha256(source),
            "target_sha256": sha256(target),
        }
    result = {
        "schema_version": "five-type-source-generalization-audit-v1",
        "checks": checks,
        "details": details,
        "all_checks_passed": all(checks.values()),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Five-type source generalization audit", "",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"source generalization audit failed: {failed}")


if __name__ == "__main__":
    main()
