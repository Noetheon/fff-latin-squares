#!/usr/bin/env python3
"""Audit online census inputs against the frozen paper inputs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import platform
import sys
import urllib.request
from pathlib import Path


URLS = {
    "latin_mc8": "https://users.cecs.anu.edu.au/~bdm/data/latin_mc8.txt.gz",
    "reduced6": "https://users.cecs.anu.edu.au/~bdm/data/reduced6.txt",
    "transitive8": (
        "https://users.monash.edu.au/~iwanless/data/autotopisms/"
        "transitive/transitive8"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "order8-paper-audit/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        target.write_bytes(response.read())


def load_generator(script_path: Path):
    spec = importlib.util.spec_from_file_location("latin_trade_search", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.reduced_latin_squares


def square_string(square) -> str:
    return " ".join("".join(str(value) for value in row) for row in square)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    root = args.project_root.resolve()
    download_dir = args.download_dir.resolve()
    download_dir.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)

    downloaded = {
        "latin_mc8": download_dir / "latin_mc8.txt.gz",
        "reduced6": download_dir / "reduced6.txt",
        "transitive8": download_dir / "transitive8",
    }
    for key, url in URLS.items():
        download(url, downloaded[key])

    local = {
        "latin_mc8": root / "repro_runs/2026-04-26_order8_core/data/latin_mc8.txt.gz",
        "transitive8": root / "repro_runs/2026-04-26_order8_core/data/transitive8.txt",
    }

    file_audits = {}
    for key in ("latin_mc8", "transitive8"):
        file_audits[key] = {
            "url": URLS[key],
            "downloaded_size_bytes": downloaded[key].stat().st_size,
            "downloaded_sha256": sha256(downloaded[key]),
            "local_path": str(local[key].relative_to(root)),
            "local_size_bytes": local[key].stat().st_size,
            "local_sha256": sha256(local[key]),
            "exact_byte_match": downloaded[key].read_bytes() == local[key].read_bytes(),
        }

    with gzip.open(downloaded["latin_mc8"], "rt", encoding="ascii") as handle:
        latin_mc8_nonempty_lines = sum(1 for line in handle if line.strip())

    official_reduced6 = {
        line.strip()
        for line in downloaded["reduced6"].read_text(encoding="ascii").splitlines()
        if line.strip()
    }
    generator_path = (
        root
        / "repro_runs/2026-04-26_small_order_witness_reruns/scripts/latin_trade_search.py"
    )
    reduced_latin_squares = load_generator(generator_path)
    generated_reduced6 = {square_string(square) for square in reduced_latin_squares(6)}

    reduced6_audit = {
        "url": URLS["reduced6"],
        "downloaded_size_bytes": downloaded["reduced6"].stat().st_size,
        "downloaded_sha256": sha256(downloaded["reduced6"]),
        "generator_path": str(generator_path.relative_to(root)),
        "generator_sha256": sha256(generator_path),
        "official_unique_count": len(official_reduced6),
        "generated_unique_count": len(generated_reduced6),
        "set_exact_match": generated_reduced6 == official_reduced6,
        "missing_from_generated": len(official_reduced6 - generated_reduced6),
        "extra_in_generated": len(generated_reduced6 - official_reduced6),
    }

    transitive_header = downloaded["transitive8"].read_text(encoding="ascii").splitlines()[0]
    report = {
        "schema_version": 1,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "file_audits": file_audits,
        "content_checks": {
            "latin_mc8_nonempty_lines": latin_mc8_nonempty_lines,
            "latin_mc8_expected_lines": 283657,
            "latin_mc8_count_matches": latin_mc8_nonempty_lines == 283657,
            "transitive8_header": transitive_header,
            "transitive8_header_declares_11": transitive_header.startswith("8 8 11 "),
        },
        "reduced6_audit": reduced6_audit,
    }
    report["overall_ok"] = all(
        [
            file_audits["latin_mc8"]["exact_byte_match"],
            file_audits["transitive8"]["exact_byte_match"],
            report["content_checks"]["latin_mc8_count_matches"],
            report["content_checks"]["transitive8_header_declares_11"],
            reduced6_audit["set_exact_match"],
        ]
    )

    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_lines = [
        "Order-8 paper external-input audit",
        f"Overall OK: {report['overall_ok']}",
        "",
        "ANU order-8 main-class file:",
        f"  SHA-256: {file_audits['latin_mc8']['downloaded_sha256']}",
        f"  Exact online/local byte match: {file_audits['latin_mc8']['exact_byte_match']}",
        f"  Nonempty records: {latin_mc8_nonempty_lines}",
        "",
        "Wanless transitive order-8 file:",
        f"  SHA-256: {file_audits['transitive8']['downloaded_sha256']}",
        f"  Exact online/local byte match: {file_audits['transitive8']['exact_byte_match']}",
        f"  Header: {transitive_header}",
        "",
        "ANU reduced order-6 cross-check:",
        f"  Official unique tables: {len(official_reduced6)}",
        f"  Freshly generated unique tables: {len(generated_reduced6)}",
        f"  Exact set match: {reduced6_audit['set_exact_match']}",
        f"  Missing/extra: {reduced6_audit['missing_from_generated']}/"
        f"{reduced6_audit['extra_in_generated']}",
    ]
    args.summary.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
