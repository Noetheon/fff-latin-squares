#!/bin/sh
set -eu
# Run from the repository root; use a new output directory.
PYTHON=${PYTHON:-python3}
OUT=${1:-.audit/counteraudit-rebuild}
PACKAGE=manuscript/candidates/2026-09-30_counteraudit_revision
PREDECESSOR=manuscript/candidates/2026-09-30_three_editions
"$PYTHON" -B tools/build_paper_editions.py --output "$OUT"
"$PYTHON" -B "$PREDECESSOR/scripts/check_compact_examples.py" \
  --source "$OUT/compact/source" --output "$OUT/compact_examples.json"
"$PYTHON" -B "$PACKAGE/scripts/build_evidence_index.py" \
  --build "$OUT" --output "$OUT/THEOREM_EVIDENCE.md"
cmp "$PACKAGE/THEOREM_EVIDENCE.md" "$OUT/THEOREM_EVIDENCE.md"
cmp "$PACKAGE/THEOREM_EVIDENCE.json" "$OUT/THEOREM_EVIDENCE.json"
# Optional with pypdf and pypdfium2 installed in this Python environment:
# "$PYTHON" -B tools/check_paper_editions.py --build "$OUT" --render
# Compare pdfs/ hashes against OUTPUTS.sha256; visual review is still required.
