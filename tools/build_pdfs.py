#!/usr/bin/env python3
"""Delegate PDF rebuilding to the current frozen candidate."""
from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1]
                      / "manuscript/candidates/2026-09-30_research_review/scripts/build_pdfs.py"),
                   run_name="__main__")
