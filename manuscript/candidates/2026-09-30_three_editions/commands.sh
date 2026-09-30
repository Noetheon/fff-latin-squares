#!/bin/sh
set -eu
# Run from the repository root. Both output directories must be new.
PACKAGE=manuscript/candidates/2026-09-30_three_editions
OUT=${1:-.audit/three-editions-check}
REPEAT=${2:-.audit/three-editions-check-repeat}
PYTHON=${PYTHON:-python3}
"$PYTHON" -B "$PACKAGE/scripts/build_editions.py" --output "$OUT"
"$PYTHON" -B "$PACKAGE/scripts/build_editions.py" --output "$REPEAT"
"$PYTHON" -B "$PACKAGE/scripts/check_compact_examples.py" --source "$OUT/compact/source" --output "$OUT/compact_examples.json"
# Optional environment must provide pypdf, pypdfium2 and Pillow for PDF inspection.
"${PDF_PYTHON:-$PYTHON}" -B tools/check_paper_editions.py --build "$OUT" --render
"$PYTHON" -B -m unittest discover -s tests -p test_paper_three_editions.py -v
# Review rendered pages manually. This script never reseals a historical package.
