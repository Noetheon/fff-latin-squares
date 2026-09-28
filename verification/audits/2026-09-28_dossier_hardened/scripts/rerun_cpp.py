"""Rerun three prior C++ checkers, not three newly authored implementations.
All sources and inputs are bundled. Use a disposable work copy.
"""
from pathlib import Path
import sys, subprocess, json, time
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'rerun/code'))
from flag_and_smallorder_checks import reduced_squares
out = R / 'inputs/reduced_2_4_6_fresh.txt'
counts = {}
with out.open('w') as f:
    for n in (2, 4, 6):
        counts[n] = 0
        for L in reduced_squares(n):
            f.write(str(n) + ' ' + ' '.join(str(v) for row in L for v in row) + '\n')
            counts[n] += 1
if not (R / 'inputs/order8_230.txt').is_file():
    raise FileNotFoundError('The bundled 230-table input is required.')
commands = []
for name, args, output in (
    ('exhaustive_trade_parity', [str(out)], 'trade_parity.json'),
    ('exchange_parity', [str(R / 'inputs/order8_230.txt')], 'exchange_parity.csv'),
    ('independent_master_inventory_audit', [], 'master_inventory.txt'),
):
    source = R / 'rerun' / f'{name}.cpp'
    binary = R / 'rerun' / name
    subprocess.run(['g++', '-O3', '-std=c++17', str(source), '-o', str(binary)], check=True, timeout=120)
    started = time.monotonic()
    with (R / 'results' / output).open('w') as f:
        p = subprocess.run([str(binary)] + args, stdout=f, stderr=subprocess.PIPE, text=True, timeout=300)
    commands.append({'checker': name, 'exit_code': p.returncode,
                     'seconds': time.monotonic() - started, 'stderr': p.stderr})
    if p.returncode:
        raise RuntimeError(p.stderr)
    print(commands[-1], flush=True)
(R / 'results/cpp_reruns.json').write_text(json.dumps(
    {'fresh_small_order_counts': counts, 'checks': commands}, indent=2))
