#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_GRAPH_SHA256 = (
    "c4f46131f9a60708b6410502a2765ce85db3f9bbf38efdf5217316fa7d010510"
)
EXPECTED_PATTERNS = {"FFF", "FFT", "FTF", "FTT", "TFF", "TFT", "TTF", "TTT"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_odd_cycle(permutation: list[int]) -> bool:
    seen = set()
    for start in range(len(permutation)):
        if start in seen:
            continue
        point = start
        length = 0
        while point not in seen:
            seen.add(point)
            point = permutation[point]
            length += 1
        if length % 2:
            return True
    return False


def direct_view_f(table: list[list[int]], view: str) -> bool:
    order = len(table)
    for left in range(order):
        for right in range(left + 1, order):
            permutation = [None] * order
            for row in table:
                if view == "col":
                    permutation[row[left]] = row[right]
                else:
                    inverse_row = [0] * order
                    for column, symbol in enumerate(row):
                        inverse_row[symbol] = column
                    permutation[inverse_row[left]] = inverse_row[right]
            if has_odd_cycle(permutation):
                return False
    return True


def incremental_channel_status(table: list[list[int]]) -> tuple[bool, bool]:
    order = len(table)
    channel_count = order * (order - 1) // 2
    maps = [[[None] * order for _ in range(channel_count)] for _ in range(2)]
    valid = [True, True]
    for row in table:
        inverse_row = [0] * order
        for column, symbol in enumerate(row):
            inverse_row[symbol] = column
        channel = 0
        for left in range(order):
            for right in range(left + 1, order):
                edges = (
                    (row[left], row[right]),
                    (inverse_row[left], inverse_row[right]),
                )
                for side, (source, target) in enumerate(edges):
                    mapping = maps[side][channel]
                    if mapping[source] is not None:
                        raise SystemExit("pattern control is not a partial permutation")
                    mapping[source] = target
                    length = 1
                    point = target
                    while point != source and mapping[point] is not None:
                        point = mapping[point]
                        length += 1
                        if length > order:
                            raise SystemExit("malformed incremental channel")
                    if point == source and length % 2:
                        valid[side] = False
                channel += 1
    return valid[0], valid[1]


def parse_square(compact: str, order: int) -> list[list[int]]:
    if len(compact) != order * order or order > 10:
        raise SystemExit("unsupported compact square")
    return [
        [int(value) for value in compact[start:start + order]]
        for start in range(0, len(compact), order)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-result", type=Path, required=True)
    parser.add_argument("--reference-merge", type=Path, required=True)
    parser.add_argument("--pattern-reference", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.raw_result.read_text())
    reference = json.loads(args.reference_merge.read_text())
    pattern_reference = json.loads(args.pattern_reference.read_text())
    pattern_rows = []
    for example in pattern_reference["selected_pattern_examples"]:
        summary = example["summary"]
        name = summary["pattern_name"]
        table = parse_square(example["compact_square"], summary["order"])
        incremental = incremental_channel_status(table)
        direct = (direct_view_f(table, "col"), direct_view_f(table, "sym"))
        expected = (
            not summary["pattern_has_odd_cycle"]["col"],
            not summary["pattern_has_odd_cycle"]["sym"],
        )
        pattern_rows.append({
            "pattern": name,
            "source_index": example["source_index"],
            "incremental_col_sym_f": list(incremental),
            "direct_col_sym_f": list(direct),
            "expected_col_sym_f": list(expected),
            "match": incremental == direct == expected,
        })

    graph_hash = sha256(args.graph)
    count_fields = {
        "completed_tasks": 2520,
        "search_nodes": 2658008,
        "crossview_odd_cycle_prunes": 796328,
        "fff_found": False,
    }
    checks = {
        "graph_hash_frozen": graph_hash == EXPECTED_GRAPH_SHA256
        == reference.get("graph_sha256"),
        "reference_complete_negative": reference.get("negative_search_complete") is True
        and reference.get("complete_disjoint_cover") is True,
        "raw_interval_full": raw.get("full_initial_tasks") == 2520
        and raw.get("total_initial_tasks") == 2520
        and raw.get("task_start") == 0
        and raw.get("task_end_exclusive") == 2520,
        "raw_complete_negative": raw.get("slice_complete") is True
        and raw.get("fff_found") is False,
        "raw_counts_frozen": all(raw.get(key) == value for key, value in count_fields.items()),
        "raw_matches_historical_search": all(
            raw.get(key) == reference.get(key) for key in count_fields
        ),
        "all_eight_patterns_present": {row["pattern"] for row in pattern_rows}
        == EXPECTED_PATTERNS,
        "all_pattern_channel_controls_match": all(row["match"] for row in pattern_rows),
        "fff_positive_channel_control": next(
            row for row in pattern_rows if row["pattern"] == "FFF"
        )["incremental_col_sym_f"] == [True, True],
    }
    result = {
        "schema_version": "incremental-partial-channel-search-control-v1",
        "files": {
            "raw_result": {"path": str(args.raw_result.resolve()), "sha256": sha256(args.raw_result)},
            "reference_merge": {"path": str(args.reference_merge.resolve()), "sha256": sha256(args.reference_merge)},
            "pattern_reference": {"path": str(args.pattern_reference.resolve()), "sha256": sha256(args.pattern_reference)},
            "graph": {"path": str(args.graph.resolve()), "sha256": graph_hash},
            "source": {"path": str(args.source.resolve()), "sha256": sha256(args.source)},
            "binary": {"path": str(args.binary.resolve()), "sha256": sha256(args.binary)},
        },
        "f18_counts": count_fields,
        "pattern_controls": pattern_rows,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "evidence_boundary": (
            "Search-implementation equivalence and channel-semantics control only; "
            "no six-/seven-type graph or search result."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.summary.write_text("\n".join([
        "Incremental partite-search control",
        "",
        f"f18 tasks/nodes/prunes: {raw.get('completed_tasks')}/{raw.get('search_nodes')}/{raw.get('crossview_odd_cycle_prunes')}",
        f"f18 result matches historical search: {str(checks['raw_matches_historical_search']).lower()}",
        f"pattern channel controls: {sum(row['match'] for row in pattern_rows)}/{len(pattern_rows)}",
        f"checks passed: {sum(checks.values())}/{len(checks)}",
        f"all checks passed: {str(result['all_checks_passed']).lower()}",
    ]) + "\n")
    if not result["all_checks_passed"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"incremental search control failed: {failed}")


if __name__ == "__main__":
    main()
