#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


PATTERNS = {"FFF", "FFT", "FTF", "FTT", "TFF", "TFT", "TTF", "TTT"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inverse(permutation: list[int]) -> list[int]:
    result = [0] * len(permutation)
    for point, image in enumerate(permutation):
        result[image] = point
    return result


def relative(left: list[int], right: list[int]) -> list[int]:
    left_inverse = inverse(left)
    return [right[left_inverse[point]] for point in range(len(left))]


def cycle_lengths(permutation: list[int]) -> list[int]:
    seen = [False] * len(permutation)
    lengths = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        current = start
        length = 0
        while not seen[current]:
            seen[current] = True
            current = permutation[current]
            length += 1
        lengths.append(length)
    return sorted(lengths, reverse=True)


def view_has_odd_witness(lines: list[list[int]]) -> bool:
    for left in range(len(lines)):
        for right in range(left + 1, len(lines)):
            if any(length > 1 and length % 2 for length in cycle_lengths(
                relative(lines[left], lines[right])
            )):
                return True
    return False


def classify(table: list[list[int]]) -> dict:
    n = len(table)
    latin = (
        all(sorted(row) == list(range(n)) for row in table)
        and all(sorted(table[row][column] for row in range(n)) == list(range(n))
                for column in range(n))
    )
    columns = [[table[row][column] for row in range(n)] for column in range(n)]
    symbols = []
    for symbol in range(n):
        line = []
        for row in range(n):
            line.append(table[row].index(symbol))
        symbols.append(line)
    bits = [
        view_has_odd_witness(table),
        view_has_odd_witness(columns),
        view_has_odd_witness(symbols),
    ]
    pattern = "".join("T" if bit else "F" for bit in bits)
    return {"latin": latin, "pattern": pattern, "fff": pattern == "FFF"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text())
    examples = reference.get("selected_pattern_examples", [])
    records = []
    for example in examples:
        compact = example["compact_square"]
        n = int(len(compact) ** 0.5)
        if n * n != len(compact):
            raise SystemExit("non-square compact fixture")
        table = [[int(compact[n * row + column]) for column in range(n)]
                 for row in range(n)]
        actual = classify(table)
        expected = example["summary"]["pattern_name"]
        records.append({
            "label": example["label"],
            "source_line_number": example["source_line_number"],
            "expected_pattern": expected,
            "actual": actual,
            "passed": actual["latin"] and actual["pattern"] == expected,
        })
    expected_patterns = {record["expected_pattern"] for record in records}
    result = {
        "schema_version": "all-pattern-truth-table-audit-v1",
        "reference_path": str(args.reference.resolve()),
        "reference_sha256": sha256(args.reference),
        "expected_patterns": sorted(expected_patterns),
        "records": records,
        "checks": {
            "all_eight_patterns_present": expected_patterns == PATTERNS,
            "all_examples_latin": all(record["actual"]["latin"] for record in records),
            "all_patterns_reproduced": all(record["passed"] for record in records),
            "fff_truth_value_reproduced": all(
                record["actual"]["fff"] == (record["expected_pattern"] == "FFF")
                for record in records
            ),
        },
    }
    result["all_checks_passed"] = all(result["checks"].values())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Independent all-pattern truth-table audit",
        "",
        f"patterns: {','.join(sorted(expected_patterns))}",
        f"examples: {len(records)}",
        f"checks passed: {sum(result['checks'].values())}/{len(result['checks'])}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        raise SystemExit("pattern truth-table audit failed")


if __name__ == "__main__":
    main()
