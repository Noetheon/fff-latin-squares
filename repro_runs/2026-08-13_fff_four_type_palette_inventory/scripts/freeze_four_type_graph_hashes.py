#!/usr/bin/env python3
import json
from pathlib import Path


RUN = Path("repro_runs/2026-08-13_fff_four_type_palette_inventory")
RESULTS = RUN / "results"
EXPECTED_CASES = {
    "p01", "p02", "p03", "p04", "p06", "p07", "p08", "p11", "p12",
    "p14", "p17", "p21", "p22", "p23", "p24", "p25", "p27", "p28",
    "p29", "p30", "p31", "p32", "p33", "p34", "p35",
}

rows = []
for case_id in sorted(EXPECTED_CASES):
    path = RESULTS / f"{case_id}_graph_search_binding.json"
    if not path.exists():
        raise SystemExit(f"missing binding: {path}")
    binding = json.loads(path.read_text())
    if binding.get("case_id") != case_id or not binding.get("all_checks_passed"):
        raise SystemExit(f"invalid binding: {path}")
    rows.append((case_id, binding["graph_sha256"]))

output = RESULTS / "four_type_graph_hashes.tsv"
output.write_text(
    "case_id\tgraph_sha256\n"
    + "".join(f"{case_id}\t{digest}\n" for case_id, digest in rows)
)
