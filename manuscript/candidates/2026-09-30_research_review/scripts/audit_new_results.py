#!/usr/bin/env python3
"""Bounded portable proof-premise checks, not an unrestricted FFF18 search."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
EXPECTED_PAYLOADS = {
    "checkers/near_independent.py", "checkers/mixed_independent.py",
    "checkers/two_plex_independent.py", "checkers/independent_count.cpp",
    "data/near_core_certificate.json", "data/near_triangle_certificate.json",
    "data/mixed_certificate.json", "data/two_plex_certificate.json",
    "data/source21_base.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate JSON key")
            out[key] = value
        return out
    def bad(value):
        raise ValueError("non-finite JSON constant: " + value)
    def finite(value):
        result = float(value)
        require(math.isfinite(result), "non-finite JSON number: " + value)
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=bad, parse_float=finite)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def module(name):
    path = PACKAGE / "evidence/checkers" / (name + ".py")
    spec = importlib.util.spec_from_file_location("review_20260930_" + name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_inputs():
    manifest = read(PACKAGE / "evidence/source_manifest.json")
    seen = set()
    for record in manifest["files"]:
        relative = Path(record["payload"])
        require(not relative.is_absolute() and ".." not in relative.parts,
                "unsafe payload path")
        path = PACKAGE / "evidence" / relative
        require(relative.as_posix() not in seen, "duplicate evidence payload")
        seen.add(relative.as_posix())
        require(path.is_file() and not path.is_symlink(), "missing/linked evidence")
        require(path.stat().st_size == record["bytes"] and digest(path) == record["sha256"],
                "evidence hash/size differs: " + relative.as_posix())
        require(record["byte_identical"] is True, "unexpected evidence projection")
    require(seen == EXPECTED_PAYLOADS, "unexpected input coverage")
    return len(seen)


def even_partitions(n, minimum=2):
    if n == 0:
        yield ()
    for x in range(minimum, n + 1, 2):
        for rest in even_partitions(n - x, x):
            yield (x,) + rest


def anchor_counts():
    positive = [p for p in even_partitions(18) if len(p) % 2 == 0]
    nonnear = [p for p in positive if p != (2,) * 7 + (4,)]
    counts = {"positive_partitions": len(positive),
              "positive_zero_cycle_cases": sum(len(set(p)) for p in positive),
              "nonnear_longest_cases": len(nonnear),
              "nonnear_dual_positive_cases": sum(len(set(p)) for p in nonnear)}
    require(tuple(counts.values()) == (14, 33, 13, 31), "anchor count mismatch")
    bounds = [a * (a - 1) // 2 + (18-a) * (17-a) // 2
              - a*a//4 - (18-a)**2//4 for a in range(19)]
    require(min(bounds) == 32, "nonnear pair bound mismatch")
    return dict(counts, minimum_positive_nonnear_pairs=32,
                remaining_partitions=nonnear, mathematical_scope="two alternative normalizations; no case solved")


def degree_ten_prerequisite(mixed):
    a = (1, 2, 3, 0, 5, 4, 7, 6, 9, 8)
    ia = mixed.inverse(a)
    examined, retained, hist = 0, 0, Counter()
    for b in mixed.one_exception(10, 4, mixed.Budget(30)):
        examined += 1
        if mixed.cycle_type(mixed.compose(ia, b)) == (2, 2, 2, 4):
            retained += 1
            hist[tuple(sorted(map(len, mixed.components(a, b))))] += 1
    require(examined == 18900 and retained == 96 and hist == {(4, 6): 96},
            "near degree-ten prerequisite failed")
    return {"examined": examined, "retained": retained, "components_4_plus_6": hist[(4, 6)],
            "connected_size10": 0, "scope": "complete finite prerequisite, not an order10 Latin-square census"}


def cpp_count(scratch):
    compiler = shutil.which("c++")
    require(compiler is not None, "--with-cpp requires a C++17 compiler")
    source = PACKAGE / "evidence/checkers/independent_count.cpp"
    with tempfile.TemporaryDirectory(dir=scratch, prefix="counter-") as tmp:
        binary = Path(tmp) / "count"
        build = subprocess.run([compiler, "-std=c++17", "-O2", str(source), "-o", str(binary)],
                               capture_output=True, text=True, timeout=60)
        require(build.returncode == 0, "counter compilation failed: " + build.stderr[-2000:])
        table = read(PACKAGE / "evidence/data/source21_base.json")["table"]
        text = str(len(table)) + "\n" + "\n".join(" ".join(map(str, row)) for row in table) + "\n"
        run = subprocess.run([str(binary), "60"], input=text, capture_output=True, text=True, timeout=65)
        require(run.returncode == 0, "counter failed: " + run.stderr[-1000:])
        result = json.loads(run.stdout)
        require(result["complete"] is True, "count budget incomplete")
        for key, expected in {"totalP": 181768, "liftable": 138486,
                              "transvcount": 72474624, "canonical_first_count": 18118656}.items():
            require(type(result[key]) is int and result[key] == expected, "count mismatch: " + key)
        version = subprocess.run([compiler, "--version"], capture_output=True, text=True,
                                 timeout=10, check=True).stdout.splitlines()[0]
        return {"passed": True, "compiler_version": version,
                "source_sha256": digest(source), "result": result,
                "commands": ["c++ -std=c++17 -O2 evidence/checkers/independent_count.cpp -o <scratch>/count",
                             "<scratch>/count 60 < literal source21 table"],
                "scope": "complete first count, not complete mate coverage; binary discarded"}


def run_checks():
    checked = verify_inputs()
    near, mixed, plex = [module(name) for name in
                          ("near_independent", "mixed_independent", "two_plex_independent")]
    near_result = near.compute_audit()
    near.compare_certificate(read(PACKAGE / "evidence/data/near_core_certificate.json"), near_result)
    near.compare_triangle_certificate(read(PACKAGE / "evidence/data/near_triangle_certificate.json"), near_result)
    near.run_malformed_controls(near_result)
    near.triangle_comparison_controls(near_result)
    budget = mixed.Budget(30)
    finite = [mixed.finite_check(n, budget) for n in (6, 10)]
    deduction = mixed.formula_check(finite[0], budget)
    target = read(PACKAGE / "evidence/data/mixed_certificate.json")
    require(canonical(finite) == canonical(target["finite_checks"]), "mixed finite records differ")
    require(canonical(deduction) == canonical(target["degree18_deduction_and_controls"]), "mixed deduction differs")
    plex.self_test()
    plex_result = plex.check_document(read(PACKAGE / "evidence/data/two_plex_certificate.json"), census_seconds=120)
    for record in plex_result["full_twist_census_checked"]:
        record.pop("seconds")
    require(plex_result["verified"] is True and plex_result["counterexample_count"] == 0,
            "two-plex physical controls failed")
    require(sum(r["masks_checked"] for r in plex_result["full_twist_census_checked"]) == 131088,
            "twist census coverage changed")
    return {"inputs_verified": checked, "near_degree10": degree_ten_prerequisite(mixed),
            "near_palette": near_result, "normal_forms": anchor_counts(),
            "mixed_core": {"finite_checks": finite, "degree18": deduction},
            "two_plex": plex_result, "unrestricted_order18_decided": False,
            "new_FFF18": False, "external_human_review": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--with-cpp", action="store_true")
    ap.add_argument("--compare", type=Path)
    args = ap.parse_args()
    out = args.output.resolve()
    require(out.is_relative_to(ROOT / ".audit") and not out.exists(), "use a fresh .audit output")
    out.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    scientific = run_checks()
    if args.compare:
        expected = read(args.compare)
        require(canonical(scientific) == canonical(expected["scientific"]), "scientific replay differs")
    count = cpp_count(out.parent) if args.with_cpp else {"status": "not rerun; use --with-cpp"}
    result = {"passed": True, "scientific": scientific, "first_census_replay": count,
              "python": sys.version.split()[0], "elapsed_seconds": round(time.monotonic()-start, 3),
              "comparison": {"scientific_fields_ignored": [],
                             "precomparison_ignored_paths": ["two_plex.full_twist_census_checked[*].seconds"],
                             "normalizations": ["tuple arrays serialized as JSON arrays; object key order"],
                             "metadata_outside_scientific_comparison": ["python", "elapsed_seconds", "first_census_replay"],
                             "first_census_policy": "when requested, complete=true and all four exact counts are checked separately"},
              "historical_solver_proofs_rechecked": False, "full_order18_search": False}
    with out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "input_files": scientific["inputs_verified"],
                      "twists": 131088, "with_cpp": args.with_cpp, "seconds": result["elapsed_seconds"],
                      "unrestricted_order18": "open"}))


if __name__ == "__main__":
    main()
