#!/usr/bin/env python3
"""Create an explicitly versioned successor; never alter frozen search code."""
import argparse
import difflib
import hashlib
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, required=True)
output = parser.parse_args().output_dir
output.mkdir(parents=True, exist_ok=True)
EXPECTED = '6a88a79fef8065169add1f0e9d7ec712a9446bd2dd4033e3d9223262f62f847b'
paths = [ROOT/f'repro_runs/2026-08-26_fff_six_type_{kind}_master_search/scripts/search_partite_fff_incremental_scratch.cpp'
         for kind in ('involution','noninvolution')]
for path in paths:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED
old = paths[0].read_text()
start = old.index('  if (argc == 11) {')
end = old.index('  uint32_t start =', start)
replacement = '''  if (argc == 11) {
    std::ifstream task_input(argv[10]);
    tasks = select_task_ordinals(tasks, task_input);
  }
'''
new = (old[:start]+replacement+old[end:]).replace('#include "partial_cycle.hpp"',
                                               '#include "partial_cycle.hpp"\n#include "task_ordinals.hpp"')
destination = output/'search_partite_fff_fixed_ordinals.cpp'
destination.write_text(new)
(output/'task_ordinal_fix.patch').write_text(''.join(difflib.unified_diff(
    old.splitlines(True), new.splitlines(True), fromfile='frozen/search_partite_fff_incremental_scratch.cpp',
    tofile='successor/search_partite_fff_fixed_ordinals.cpp', n=0)))
print('Frozen source SHA-256:', EXPECTED)
print('Successor SHA-256:', hashlib.sha256(destination.read_bytes()).hexdigest())
