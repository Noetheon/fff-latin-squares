#!/usr/bin/env python3
"""Build the three current reading-edition candidates; never publish them."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      "manuscript/candidates/2026-10-02_e9_symmetry_review/scripts/build_editions.py"),
                  run_name="__main__")
