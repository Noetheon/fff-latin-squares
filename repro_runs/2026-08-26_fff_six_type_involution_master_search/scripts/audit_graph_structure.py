#!/usr/bin/env python3
import argparse
import hashlib
import json
import mmap
import struct
from pathlib import Path


MAGIC = b"O8HTv1\0\0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_perm10(value: bytes) -> bool:
    return len(value) == 10 and sorted(value) == list(range(10))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    errors = []
    with args.graph.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
            if len(data) < 26:
                raise SystemExit("graph is shorter than its fixed header")
            magic = data[:8]
            n, words = struct.unpack_from("<II", data, 8)
            expected_words = (n + 63) // 64
            expected_size = 26 + 10 * n + 8 * n * words
            if magic != MAGIC:
                errors.append("magic_mismatch")
            if words != expected_words:
                errors.append("word_count_mismatch")
            if len(data) != expected_size:
                errors.append("exact_size_mismatch")
            root = bytes(data[16:26])
            if not is_perm10(root):
                errors.append("invalid_root_permutation")

            vertices = []
            if len(data) >= 26 + 10 * n:
                vertices = [bytes(data[26 + 10 * i:36 + 10 * i]) for i in range(n)]
                if any(not is_perm10(vertex) for vertex in vertices):
                    errors.append("invalid_vertex_permutation")
                if any(not 2 <= vertex[0] <= 9 for vertex in vertices):
                    errors.append("invalid_first_image")
                if any(vertices[i - 1] >= vertices[i] for i in range(1, n)):
                    errors.append("vertices_not_strictly_lexicographic")

            diagonal_nonzero = 0
            padding_nonzero = 0
            adjacency_offset = 26 + 10 * n
            if len(data) == expected_size and words == expected_words:
                final_mask = (1 << (n % 64)) - 1 if n % 64 else (1 << 64) - 1
                for row in range(n):
                    row_offset = adjacency_offset + row * words * 8
                    diagonal_word = struct.unpack_from(
                        "<Q", data, row_offset + (row // 64) * 8
                    )[0]
                    diagonal_nonzero += (diagonal_word >> (row % 64)) & 1
                    if n % 64:
                        final_word = struct.unpack_from(
                            "<Q", data, row_offset + (words - 1) * 8
                        )[0]
                        padding_nonzero += (final_word & ~final_mask) != 0
                if diagonal_nonzero:
                    errors.append("nonzero_diagonal_bits")
                if padding_nonzero:
                    errors.append("nonzero_padding_rows")

    result = {
        "schema_version": "master-graph-structural-audit-v1",
        "graph_path": str(args.graph.resolve()),
        "graph_sha256": sha256(args.graph),
        "actual_size_bytes": args.graph.stat().st_size,
        "expected_size_bytes": expected_size,
        "magic_hex": magic.hex(),
        "vertices": n,
        "words": words,
        "expected_words": expected_words,
        "root_permutation": list(root),
        "diagonal_nonzero": diagonal_nonzero,
        "padding_nonzero_rows": padding_nonzero,
        "errors": errors,
        "valid": not errors,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text(
        "\n".join([
            "Four-type graph structural audit",
            "",
            f"graph SHA-256: {result['graph_sha256']}",
            f"size actual/expected: {result['actual_size_bytes']}/{expected_size}",
            f"vertices/words: {n}/{words}",
            f"diagonal/padding errors: {diagonal_nonzero}/{padding_nonzero}",
            f"errors: {len(errors)}",
            f"valid: {str(result['valid']).lower()}",
        ]) + "\n"
    )
    if errors:
        raise SystemExit("structural graph audit failed: " + ", ".join(errors))


if __name__ == "__main__":
    main()
