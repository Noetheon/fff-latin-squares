#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$ROOT"
OUT=$(mktemp -d "$ROOT/.audit/review-20260930.XXXXXX")
PACKAGE=manuscript/candidates/2026-09-30_research_review
python3 -B "$PACKAGE/scripts/audit_new_results.py" --with-cpp \
  --compare "$PACKAGE/results/portable_audit.json" --output "$OUT/new-results.json"
python3 -B "$PACKAGE/scripts/build_pdfs.py" --candidate-only --output "$OUT/pdfs"
