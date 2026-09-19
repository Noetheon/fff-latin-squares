#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict:
    return {"path": str(path.resolve()), "sha256": sha256(path), "size_bytes": path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--dimacs", type=Path, required=True)
    parser.add_argument("--cliquer", type=Path, required=True)
    parser.add_argument("--source-tarball", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    text = args.stdout.read_text(errors="replace") + "\n" + args.stderr.read_text(errors="replace")
    maxima = [int(value) for value in re.findall(r"max\s+(\d+)", text)]
    no_clique = "No such clique found." in text and maxima and max(maxima) <= 7
    result = {
        "schema_version": "f16-independent-cliquer-check-v1",
        "command": [str(args.cliquer), "-u", "-m", "8", "-M", "8", "-r", "unweighted-coloring", str(args.dimacs)],
        "requested_clique_size": 8,
        "maximum_seen_below_request": max(maxima) if maxima else None,
        "result": "no_clique_of_size_8" if no_clique else "unrecognized",
        "files": {
            name: artifact(path) for name, path in (
                ("graph", args.graph), ("dimacs", args.dimacs),
                ("cliquer_binary", args.cliquer),
                ("cliquer_source_tarball", args.source_tarball),
                ("stdout", args.stdout), ("stderr", args.stderr),
            )
        },
        "independence_note": "Cliquer 1.21 reads DIMACS and shares neither the project DFS nor its orbit task reduction.",
        "valid": bool(no_clique),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Independent Cliquer 1.21 f16 check", "",
        "requested clique size: 8",
        f"maximum seen below request: {result['maximum_seen_below_request']}",
        f"result: {result['result']}",
        f"graph SHA-256: {result['files']['graph']['sha256']}",
        f"DIMACS SHA-256: {result['files']['dimacs']['sha256']}",
        f"Cliquer source SHA-256: {result['files']['cliquer_source_tarball']['sha256']}",
        f"valid: {str(result['valid']).lower()}",
    ]) + "\n")
    if not result["valid"]:
        raise SystemExit("Cliquer result not recognized as a negative clique-8 result")


if __name__ == "__main__":
    main()
