#!/usr/bin/env python3
"""Reproduce this audit in a NEW work directory; retain the distributed outputs.
Requires Python 3.11+ and C++17 g++. No network, external solver, previous audit
ZIP or order-10 master graph. The helper scripts write only inside the new copy.
"""
from pathlib import Path
import argparse, json, shutil, subprocess, sys, time, os
from compare_outputs import compare, verify_source_manifest
ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    if sys.flags.optimize:
        raise RuntimeError('Audit checks require assertions: optimized Python is not supported.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True)
    args = parser.parse_args()
    target = args.work_dir.resolve()
    if target.exists() or target.is_relative_to(ROOT):
        parser.error('Choose a new directory outside the delivered audit package.')
    if shutil.which('g++') is None:
        parser.error('g++ with C++17 support is required.')
    count = verify_source_manifest(ROOT)
    print(f'Verified {count} frozen code/input/reference hashes.', flush=True)
    target.mkdir(parents=True)
    for name in ('scripts', 'inputs'):
        shutil.copytree(ROOT / name, target / name,
                        ignore=shutil.ignore_patterns('__pycache__', 'expanded_and_corner'))
    (target / 'results').mkdir()
    (target / 'rerun').mkdir()
    for name in ('code', 'inputs'):
        shutil.copytree(ROOT / 'rerun' / name, target / 'rerun' / name,
                        ignore=shutil.ignore_patterns('__pycache__'))
    for source in (ROOT / 'rerun').glob('*.cpp'):
        shutil.copy2(source, target / 'rerun' / source.name)
    shutil.copy2(ROOT / 'rerun/run_all.py', target / 'rerun/run_all.py')
    (target / 'rerun/results').mkdir()
    executable = target / 'expanded_and_corner'
    commands = [
        ['g++', '-O3', '-std=c++17', 'scripts/expanded_and_corner.cpp', '-o', str(executable)],
        [str(executable), 'results'],
        [sys.executable, '-B', 'scripts/verify_representatives.py'],
        *[[sys.executable, '-B', 'scripts/crt_independent.py', str(n)] for n in (9,15,45,75)],
        [sys.executable, '-B', 'scripts/burnside_new.py'],
        [sys.executable, '-B', 'scripts/additional_controls.py'],
        [sys.executable, '-B', 'rerun/run_all.py'],
        [sys.executable, '-B', 'scripts/rerun_cpp.py'],
    ]
    records = []
    for index, command in enumerate(commands):
        start = time.monotonic()
        with (target / 'results' / f'reproduce_{index:02d}.log').open('w') as out:
            result = subprocess.run(command, cwd=target, stdout=out,
                                    stderr=subprocess.STDOUT, timeout=600,
                                    env=dict(os.environ, PYTHONOPTIMIZE='0',
                                             PYTHONDONTWRITEBYTECODE='1'))
        record = {'command': command, 'returncode': result.returncode,
                  'seconds': round(time.monotonic() - start, 6)}
        records.append(record)
        (target / 'results/reproduction_receipt.json').write_text(
            json.dumps(records, indent=2), encoding='utf-8')
        print(f'{index+1}/{len(commands)}: returncode={result.returncode}', flush=True)
        if result.returncode:
            raise SystemExit(f'Reproduction stopped. Inspect {target}/results/reproduce_{index:02d}.log')
    previous = json.loads((target / 'rerun/results/execution_log.json').read_text())
    if len(previous) != 9 or any(x['returncode'] != 0 for x in previous):
        raise RuntimeError('Incomplete or failed inherited Python audit.')
    comparison = compare(ROOT, target)
    (target / 'results/comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')
    if not comparison['passed']:
        raise RuntimeError('Fresh/reference mismatch: see results/comparison.json')
    print('24/24 finite reference comparisons passed.', flush=True)
    print(f'All checks completed in the new work directory: {target}', flush=True)

if __name__ == '__main__':
    main()
