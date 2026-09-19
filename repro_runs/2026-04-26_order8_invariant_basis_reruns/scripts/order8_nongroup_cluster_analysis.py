#!/usr/bin/env python3
from __future__ import annotations
import json, importlib.util, sys
from pathlib import Path
from collections import defaultdict, Counter

RUN_ROOT = Path(__file__).resolve().parents[1]
DATA = RUN_ROOT / 'data'
SCRIPTS = RUN_ROOT / 'scripts'
RESULTS = RUN_ROOT / 'results'
spec = importlib.util.spec_from_file_location('loopinv_cluster', str(SCRIPTS/'order8_loop_invariants_analysis.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['loopinv_cluster'] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

scan = json.loads((DATA/'order8_mc8_scan.json').read_text(encoding='utf-8'))
records = [rec for rec in scan['counterexamples'] if not rec['group_isotopic']]

coarse_clusters = defaultdict(list)
fine_clusters = defaultdict(list)
all_records = []

for idx, rec in enumerate(records, start=1):
    inv = mod.loop_invariants(mod.parse_square(rec['square']))
    coarse = (
        len(inv['left_nucleus']),
        len(inv['middle_nucleus']),
        len(inv['right_nucleus']),
        len(inv['center']),
        inv['inverse_property'],
        inv['antiautomorphic_inverse_property'],
        inv['flexible'],
        inv['left_translation_group_size'],
        inv['right_translation_group_size'],
        inv['multiplication_group_size'],
        inv['inner_mapping_group_size'],
        inv['automorphism_group_size'],
    )
    fine = (
        tuple(inv['left_nucleus']),
        tuple(inv['middle_nucleus']),
        tuple(inv['right_nucleus']),
        tuple(inv['center']),
        inv['inverse_property'],
        inv['antiautomorphic_inverse_property'],
        inv['flexible'],
        inv['left_translation_group_size'],
        inv['right_translation_group_size'],
        inv['multiplication_group_size'],
        inv['inner_mapping_group_size'],
        inv['automorphism_group_size'],
    )
    coarse_clusters[coarse].append(int(rec['line_number']))
    fine_clusters[fine].append(int(rec['line_number']))
    all_records.append({
        'line_number': int(rec['line_number']),
        'index': int(rec['index']),
        'coarse_profile': list(coarse),
        'fine_profile': {
            'left_nucleus': inv['left_nucleus'],
            'middle_nucleus': inv['middle_nucleus'],
            'right_nucleus': inv['right_nucleus'],
            'center': inv['center'],
            'inverse_property': inv['inverse_property'],
            'antiautomorphic_inverse_property': inv['antiautomorphic_inverse_property'],
            'flexible': inv['flexible'],
            'left_translation_group_size': inv['left_translation_group_size'],
            'right_translation_group_size': inv['right_translation_group_size'],
            'multiplication_group_size': inv['multiplication_group_size'],
            'inner_mapping_group_size': inv['inner_mapping_group_size'],
            'automorphism_group_size': inv['automorphism_group_size'],
        },
        'associative': inv['associative'],
        'commutative': inv['commutative'],
    })
    if idx % 25 == 0:
        print(f'processed {idx}/{len(records)}', flush=True)

coarse_size_dist = Counter(len(v) for v in coarse_clusters.values())
fine_size_dist = Counter(len(v) for v in fine_clusters.values())

by_line = {rec['line_number']: rec for rec in all_records}
cycle_pure = [19, 114, 1955, 10776, 85446]

def fine_key_from_record(rec):
    fp = rec['fine_profile']
    return (
        tuple(fp['left_nucleus']),
        tuple(fp['middle_nucleus']),
        tuple(fp['right_nucleus']),
        tuple(fp['center']),
        fp['inverse_property'],
        fp['antiautomorphic_inverse_property'],
        fp['flexible'],
        fp['left_translation_group_size'],
        fp['right_translation_group_size'],
        fp['multiplication_group_size'],
        fp['inner_mapping_group_size'],
        fp['automorphism_group_size'],
    )

coarse_list = sorted(
    ({'profile': list(k), 'size': len(v), 'lines': sorted(v)} for k, v in coarse_clusters.items()),
    key=lambda d: (-d['size'], d['lines'][0])
)
fine_list = sorted(
    ({
        'profile': {
            'left_nucleus': list(k[0]),
            'middle_nucleus': list(k[1]),
            'right_nucleus': list(k[2]),
            'center': list(k[3]),
            'inverse_property': k[4],
            'antiautomorphic_inverse_property': k[5],
            'flexible': k[6],
            'left_translation_group_size': k[7],
            'right_translation_group_size': k[8],
            'multiplication_group_size': k[9],
            'inner_mapping_group_size': k[10],
            'automorphism_group_size': k[11],
        },
        'size': len(v),
        'lines': sorted(v)
    } for k, v in fine_clusters.items()),
    key=lambda d: (-d['size'], d['lines'][0])
)

stats = {
    'associative': Counter(rec['associative'] for rec in all_records),
    'commutative': Counter(rec['commutative'] for rec in all_records),
    'inverse_property': Counter(rec['fine_profile']['inverse_property'] for rec in all_records),
    'left_nucleus_size': Counter(len(rec['fine_profile']['left_nucleus']) for rec in all_records),
    'middle_nucleus_size': Counter(len(rec['fine_profile']['middle_nucleus']) for rec in all_records),
    'right_nucleus_size': Counter(len(rec['fine_profile']['right_nucleus']) for rec in all_records),
    'center_size': Counter(len(rec['fine_profile']['center']) for rec in all_records),
    'left_translation_group_size': Counter(rec['fine_profile']['left_translation_group_size'] for rec in all_records),
    'right_translation_group_size': Counter(rec['fine_profile']['right_translation_group_size'] for rec in all_records),
    'multiplication_group_size': Counter(rec['fine_profile']['multiplication_group_size'] for rec in all_records),
    'inner_mapping_group_size': Counter(rec['fine_profile']['inner_mapping_group_size'] for rec in all_records),
    'automorphism_group_size': Counter(rec['fine_profile']['automorphism_group_size'] for rec in all_records),
}

result = {
    'nongroup_case_count': len(all_records),
    'coarse_cluster_count': len(coarse_list),
    'fine_cluster_count': len(fine_list),
    'coarse_cluster_size_distribution': {str(k): v for k, v in sorted(coarse_size_dist.items())},
    'fine_cluster_size_distribution': {str(k): v for k, v in sorted(fine_size_dist.items())},
    'global_invariant_distributions': {k: {str(a): b for a, b in sorted(v.items(), key=lambda kv: str(kv[0]))} for k, v in stats.items()},
    'coarse_clusters': coarse_list,
    'fine_clusters': fine_list,
    'cycle_pure_lines': cycle_pure,
    'cycle_pure_positions': {
        str(line): {
            'coarse_cluster_size': len(coarse_clusters[tuple(by_line[line]['coarse_profile'])]),
            'coarse_cluster_lines': sorted(coarse_clusters[tuple(by_line[line]['coarse_profile'])]),
            'fine_cluster_size': len(fine_clusters[fine_key_from_record(by_line[line])]),
            'fine_cluster_lines': sorted(fine_clusters[fine_key_from_record(by_line[line])]),
            'record': by_line[line],
        }
        for line in cycle_pure
    }
}

(RESULTS/'order8_nongroup_cluster_analysis_results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')

lines = []
lines.append('Order-8 nongroup FFF cluster analysis')
lines.append('')
lines.append(f'nongroup cases: {len(all_records)}')
lines.append(f'coarse invariant clusters: {len(coarse_list)}')
lines.append(f'fine invariant clusters: {len(fine_list)}')
lines.append(f'coarse cluster size distribution: {dict(sorted(coarse_size_dist.items()))}')
lines.append(f'fine cluster size distribution: {dict(sorted(fine_size_dist.items()))}')
lines.append('')
lines.append('Top 10 coarse clusters:')
for entry in coarse_list[:10]:
    lines.append(f"  size {entry['size']}: {entry['lines']}")
lines.append('')
lines.append('Cycle-pure exception positions:')
for line in cycle_pure:
    pos = result['cycle_pure_positions'][str(line)]
    lines.append(f"  line {line}: coarse size {pos['coarse_cluster_size']} -> {pos['coarse_cluster_lines']}; fine size {pos['fine_cluster_size']} -> {pos['fine_cluster_lines']}")
lines.append('')
lines.append('Selected global counts:')
for k in ['center_size','left_nucleus_size','middle_nucleus_size','right_nucleus_size','left_translation_group_size','right_translation_group_size','multiplication_group_size','inner_mapping_group_size','automorphism_group_size']:
    lines.append(f"  {k}: {dict(stats[k])}")
(RESULTS/'order8_nongroup_cluster_analysis_summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('wrote nongroup cluster artifacts')
