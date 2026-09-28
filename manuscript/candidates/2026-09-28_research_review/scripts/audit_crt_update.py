#!/usr/bin/env python3
"""Read-only, bounded CRT companion audit (Python 3.11+ standard library).

Load the package's byte-pinned builder, physical verifier, and frozen twists,
not their command-line entry points. No twists are regenerated, no full Latin
table is built, and no solver is used. The four probes independently isolate
the constant, each line-label coefficient, and the slope of each K-affine
return. Field arithmetic, quotient/form enumeration, and physical inversions
are shared frozen dependencies: this is not a wholly independent implementation
or a proof of the universal theorem.

Only --output is written, exclusively as a new file outside frozen evidence;
its parent must already exist. Imports create no bytecode. --max-seconds is a
cooperative limit checked between bounded operations, not a process sandbox.
"""

from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import sys
from time import perf_counter


HERE = Path(__file__).resolve().parents[1]
RUN_RELATIVE = Path("evidence/update/repro_runs/2026-09-28_fff_cubefree_crt_lift")
RUN = HERE / RUN_RELATIVE
INPUT_HASHES = {
    "scripts/check_cubefree_lift.py":
        "5b3005a3560ff4ecc79c11c4f4a1b2da574a7ea3319aa68c37134c328cd1dcb6",
    "scripts/verify_compact_certificate.py":
        "f8f30d638df78ee98ba073eda2d141cc32d435494e17fd8c814fb05389e393b3",
    "results/cubefree_lift_status.json":
        "8e06ed5ff9645cf41e758303f6aa7d2cd1fe4520a50a3d79fa5c326f51bed91f",
}
CASES = {
    9: (((3, 2, 2),), 64, 324),
    15: (((3, 1, 0), (5, 1, 0)), 256, 675),
    45: (((3, 2, 2), (5, 1, 0)), 256, 17010),
    75: (((3, 1, 0), (5, 2, 2)), 256, 73125),
}
VIEWS = ("row", "col", "sym")
PROBES = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_deadline(deadline):
    if perf_counter() >= deadline:
        raise TimeoutError("CRT audit exceeded --max-seconds; no report written")


def load_inputs(run=RUN):
    sources = {name: (run / name).read_bytes() for name in INPUT_HASHES}
    for name, expected in INPUT_HASHES.items():
        require(sha256(sources[name]).hexdigest() == expected,
                f"frozen input hash mismatch: {name}")

    def load_source(name):
        path = run / name
        spec = importlib.util.spec_from_file_location("_crt_" + path.stem, path)
        require(spec is not None and spec.loader is not None, f"cannot import {name}")
        module = importlib.util.module_from_spec(spec)
        # Execute exactly the checked source, bypassing both reading and writing pyc.
        exec(compile(sources[name], str(path), "exec"), module.__dict__)
        return module

    builder = load_source("scripts/check_cubefree_lift.py")
    missing = object()
    previous = sys.modules.get("check_cubefree_lift", missing)
    try:
        sys.modules["check_cubefree_lift"] = builder
        physical = load_source("scripts/verify_compact_certificate.py")
    finally:
        if previous is missing:
            sys.modules.pop("check_cubefree_lift", None)
        else:
            sys.modules["check_cubefree_lift"] = previous
    payload = json.loads(sources["results/cubefree_lift_status.json"])
    require([item["N"] for item in payload["cases"]] == list(CASES),
            "frozen case coverage differs")
    return builder, physical, payload


def verify_return(ctx, twists, form, direct_return):
    value = 0
    for cell, exponent in form["support"]:
        value ^= ctx.scaled(exponent, twists[cell])
    require(value != 0, "zero compact twist return")
    for a, b, start in PROBES:
        actual = direct_return(ctx, twists, form, a, b, start)
        require(actual == (value ^ start),
                f"physical probe {(a, b, start)} differs: "
                f"N={ctx.n} {form['view']} pair={form['high']},{form['low']} "
                f"orbit={form['start']}")


def check_case(builder, physical, item, deadline):
    check_deadline(deadline)
    n = item["N"]
    require(type(n) is int and n in CASES, "unsupported quotient size")
    expected_spec, expected_q, expected_count = CASES[n]
    spec = tuple((part["prime"], part["rank"], part["nonsquare"])
                 for part in item["components"])
    require(spec == expected_spec and item["field_order"] == expected_q,
            "frozen quotient/field specification differs")
    twists = item["twists"]
    require(len(twists) == n * n and all(type(x) is int and 0 <= x < expected_q
                                        for x in twists), "invalid frozen twists")
    require(sha256(bytes(twists)).hexdigest() == item["twists_sha256"],
            "frozen twist hash mismatch")
    ctx = builder.Context(spec)
    require(ctx.n == n and ctx.q == expected_q, "context differs from certificate")
    # Only repeated scalar products are cached, never a physical Latin table.
    ctx.scaled = lru_cache(maxsize=32768)(ctx.scaled)
    forms = builder.return_forms(ctx)
    check_deadline(deadline)
    require(len(forms) == expected_count == item["return_forms"],
            "compact return coverage differs")
    require(len({(f["view"], f["high"], f["low"], f["start"]) for f in forms})
            == expected_count, "duplicate compact return")
    counts = Counter(f["view"] for f in forms)
    require(counts == {view: expected_count // 3 for view in VIEWS},
            "three-view return coverage differs")
    zero_twists = [0] * (n * n)
    for view in VIEWS:
        form = next(f for f in forms if f["view"] == view)
        require(physical.direct_return(ctx, zero_twists, form, 0, 0, 0) == 0,
                f"zero-twist negative control differs: {view}")
    for form in forms:
        check_deadline(deadline)
        verify_return(ctx, twists, form, physical.direct_return)
    return {
        "N": n, "field_order": ctx.q, "returns_checked": len(forms),
        "returns_by_view": dict(sorted(counts.items())),
        "physical_probe_evaluations": len(PROBES) * len(forms),
        "zero_twist_controls": list(VIEWS),
        "frozen_twists_sha256": item["twists_sha256"],
        "separate_label_coefficients_and_unit_slope": True,
        "all_compact_returns_nonzero": True,
    }


def audit(max_seconds=120.0, run=RUN):
    require(math.isfinite(max_seconds) and max_seconds > 0,
            "--max-seconds must be finite and positive")
    started = perf_counter()
    deadline = started + max_seconds
    builder, physical, payload = load_inputs(run)
    cases = [check_case(builder, physical, item, deadline) for item in payload["cases"]]
    for name, expected in INPUT_HASHES.items():
        require(sha256((run / name).read_bytes()).hexdigest() == expected,
                f"frozen input changed during audit: {name}")
    check_deadline(deadline)
    return {
        "schema_version": 1, "passed": True,
        "scope": "all frozen CRT compact returns for N=9,15,45,75; three physical views",
        "sources_sha256": {(RUN_RELATIVE / name).as_posix(): digest
                           for name, digest in INPUT_HASHES.items()},
        "probes_a_b_start_fibre": [list(probe) for probe in PROBES],
        "cases": cases,
        "total_returns_checked": sum(case["returns_checked"] for case in cases),
        "total_physical_probe_evaluations": sum(case["physical_probe_evaluations"]
                                                for case in cases),
        "independence_limits": [
            "Shares frozen field arithmetic, quotient model and compact-form enumeration.",
            "Shares frozen direct physical inversion code; label probes are separated here.",
            "Four probes determine coefficients only using the verified K-affine model.",
            "Does not scan all physical line pairs or establish the universal theorem.",
        ],
        "frozen_inputs_unchanged": True, "twists_regenerated": False,
        "full_table_materialized": False, "solver_used": False,
        "external_peer_review": False, "unrestricted_fff18_decided": False,
        "max_seconds": max_seconds, "runtime_seconds": round(perf_counter() - started, 6),
    }


def validate_output(path):
    require(not path.exists() and not path.is_symlink(),
            "--output must be a new file; existing files are never overwritten")
    resolved = path.resolve()
    require(not resolved.is_relative_to(HERE / "evidence")
            and not {"evidence", "repro_runs"}.intersection(resolved.parts),
            "--output must be outside frozen evidence/repro_runs")
    require(resolved.parent.is_dir(), "--output parent directory must already exist")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, default=120.0)
    args = parser.parse_args()
    output = validate_output(args.output)
    result = audit(args.max_seconds)
    with output.open("x", encoding="utf-8") as target:
        target.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {result['total_returns_checked']} CRT returns; "
          f"{result['total_physical_probe_evaluations']} separate physical probes; "
          f"{result['runtime_seconds']:.3f}s")


if __name__ == "__main__":
    main()
