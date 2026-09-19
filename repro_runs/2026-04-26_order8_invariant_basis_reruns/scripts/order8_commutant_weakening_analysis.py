#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import itertools
import json
from collections import defaultdict
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
DATA = RUN_ROOT / 'data'
SCRIPTS = RUN_ROOT / 'scripts'
RESULTS = RUN_ROOT / 'results'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

basis = load('basis_mod_weak', SCRIPTS / 'order8_invariant_basis_minimization.py')

# Load all 230 FFF reps.
records = []
with open(DATA / 'order8_fff_counterexamples.tsv', newline='') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        records.append({
            'line': int(row['line_number']),
            'group_isotopic': row['group_isotopic'].lower() == 'true',
            'square': row['square'],
        })

lines = [r['line'] for r in records]

# Base invariants from previous analysis.
inv_by_line = {}
for rec in records:
    inv = basis.extended_invariants(basis.parse_square(rec['square']))
    inv_by_line[rec['line']] = inv

# Extend feature family by weaker replacements.
feature_values = {}
for feat in basis.FEATURES:
    feature_values[feat] = [inv_by_line[line][feat] for line in lines]

for feat in ['left_nucleus', 'middle_nucleus', 'right_nucleus', 'commutant', 'center']:
    feature_values[f'{feat}_size'] = [len(inv_by_line[line][feat]) for line in lines]

feature_values['nucleus_size_triple'] = [
    (
        len(inv_by_line[line]['left_nucleus']),
        len(inv_by_line[line]['middle_nucleus']),
        len(inv_by_line[line]['right_nucleus']),
    )
    for line in lines
]
feature_values['translation_type_pair'] = [
    (
        inv_by_line[line]['left_translation_cycle_types'],
        inv_by_line[line]['right_translation_cycle_types'],
    )
    for line in lines
]
feature_values['inverse_pair'] = [
    (
        inv_by_line[line]['left_inverse_map'],
        inv_by_line[line]['right_inverse_map'],
    )
    for line in lines
]

encoded = {}
for feat, vals in feature_values.items():
    uniq = {v: i for i, v in enumerate(sorted(set(vals), key=repr))}
    encoded[feat] = [uniq[v] for v in vals]


def cluster_count(subset: tuple[str, ...] | list[str]) -> int:
    seen = set()
    for i in range(len(lines)):
        seen.add(tuple(encoded[f][i] for f in subset))
    return len(seen)


def separates(subset: tuple[str, ...] | list[str]) -> bool:
    return cluster_count(subset) == len(lines)


def first_collision(subset: tuple[str, ...] | list[str]):
    sig_to_lines = defaultdict(list)
    for i, line in enumerate(lines):
        sig = tuple(encoded[f][i] for f in subset)
        sig_to_lines[sig].append(line)
    for sig, L in sig_to_lines.items():
        if len(L) > 1:
            return {
                'subset': list(subset),
                'lines': L,
                'signature': list(sig),
            }
    return None

# 1) Full original family but commutant forbidden.
orig_wo_comm = [f for f in basis.FEATURES if f != 'commutant']
min_size_without_comm = None
min_subsets_without_comm = []
for r in range(1, len(orig_wo_comm) + 1):
    found = []
    for subset in itertools.combinations(orig_wo_comm, r):
        if separates(subset):
            found.append(subset)
    if found:
        min_size_without_comm = r
        min_subsets_without_comm = found
        break

# 2) Restricted weaker family.
weak_family = [
    'commutative',
    'left_inverse_property',
    'right_inverse_property',
    'inverse_property',
    'inverse_coincide',
    'antiautomorphic_inverse_property',
    'left_alternative',
    'right_alternative',
    'flexible',
    'left_nucleus',
    'middle_nucleus',
    'right_nucleus',
    'left_nucleus_size',
    'middle_nucleus_size',
    'right_nucleus_size',
    'nucleus_size_triple',
    'center',
    'center_size',
    'commutant_size',
    'left_translation_cycle_types',
    'right_translation_cycle_types',
    'translation_type_pair',
    'left_inverse_map',
    'right_inverse_map',
    'inverse_pair',
]

weak_min_size = None
weak_min_subsets = []
for r in range(1, len(weak_family) + 1):
    found = []
    for subset in itertools.combinations(weak_family, r):
        if separates(subset):
            found.append(subset)
    if found:
        weak_min_size = r
        weak_min_subsets = found
        break

# 3) Direct weakening tests around the known minimal basis.
base_triples = {
    'commutant,left_translation_cycle_types,left_inverse_map': ('commutant', 'left_translation_cycle_types', 'left_inverse_map'),
    'commutant,left_translation_cycle_types,right_inverse_map': ('commutant', 'left_translation_cycle_types', 'right_inverse_map'),
    'commutant_size,left_translation_cycle_types,left_inverse_map': ('commutant_size', 'left_translation_cycle_types', 'left_inverse_map'),
    'commutant_size,left_translation_cycle_types,right_inverse_map': ('commutant_size', 'left_translation_cycle_types', 'right_inverse_map'),
    'center,left_translation_cycle_types,left_inverse_map': ('center', 'left_translation_cycle_types', 'left_inverse_map'),
    'center,left_translation_cycle_types,right_inverse_map': ('center', 'left_translation_cycle_types', 'right_inverse_map'),
    'center_size,left_translation_cycle_types,left_inverse_map': ('center_size', 'left_translation_cycle_types', 'left_inverse_map'),
    'center_size,left_translation_cycle_types,right_inverse_map': ('center_size', 'left_translation_cycle_types', 'right_inverse_map'),
    'left_nucleus,left_translation_cycle_types,left_inverse_map': ('left_nucleus', 'left_translation_cycle_types', 'left_inverse_map'),
    'left_nucleus,left_translation_cycle_types,right_inverse_map': ('left_nucleus', 'left_translation_cycle_types', 'right_inverse_map'),
    'middle_nucleus,left_translation_cycle_types,left_inverse_map': ('middle_nucleus', 'left_translation_cycle_types', 'left_inverse_map'),
    'middle_nucleus,left_translation_cycle_types,right_inverse_map': ('middle_nucleus', 'left_translation_cycle_types', 'right_inverse_map'),
    'right_nucleus,left_translation_cycle_types,left_inverse_map': ('right_nucleus', 'left_translation_cycle_types', 'left_inverse_map'),
    'right_nucleus,left_translation_cycle_types,right_inverse_map': ('right_nucleus', 'left_translation_cycle_types', 'right_inverse_map'),
    'nucleus_size_triple,left_translation_cycle_types,left_inverse_map': ('nucleus_size_triple', 'left_translation_cycle_types', 'left_inverse_map'),
    'nucleus_size_triple,left_translation_cycle_types,right_inverse_map': ('nucleus_size_triple', 'left_translation_cycle_types', 'right_inverse_map'),
    'right_translation_cycle_types,left_translation_cycle_types,left_inverse_map': ('right_translation_cycle_types', 'left_translation_cycle_types', 'left_inverse_map'),
    'right_translation_cycle_types,left_translation_cycle_types,right_inverse_map': ('right_translation_cycle_types', 'left_translation_cycle_types', 'right_inverse_map'),
    'translation_type_pair,left_inverse_map': ('translation_type_pair', 'left_inverse_map'),
    'translation_type_pair,right_inverse_map': ('translation_type_pair', 'right_inverse_map'),
}

base_replacement_stats = {}
for name, subset in base_tripples.items() if False else []:
    pass
# normal loop after the disabled typo line
base_replacement_stats = {}
for name, subset in base_triples.items():
    base_replacement_stats[name] = {
        'cluster_count': cluster_count(subset),
        'separates': separates(subset),
        'first_collision': first_collision(subset),
    }

# 4) Best triples without full commutant.
triples_wo_comm = []
for subset in itertools.combinations(orig_wo_comm, 3):
    triples_wo_comm.append((cluster_count(subset), subset))
triples_wo_comm.sort(reverse=True)
best_triples_wo_comm = [
    {'cluster_count': c, 'subset': list(s)} for c, s in triples_wo_comm[:20]
]

# 5) Best weak-family subsets at minimal size.
weak_min_subset_details = []
for subset in weak_min_subsets:
    weak_min_subset_details.append({
        'subset': list(subset),
        'first_collision': first_collision(subset),
    })

result = {
    'case_count': len(lines),
    'original_minimal_basis_size': 3,
    'original_minimal_bases': [
        ['commutant', 'left_translation_cycle_types', 'left_inverse_map'],
        ['commutant', 'left_translation_cycle_types', 'right_inverse_map'],
    ],
    'full_family_without_commutant': {
        'feature_count': len(orig_wo_comm),
        'minimal_separating_subset_size': min_size_without_comm,
        'num_minimal_subsets': len(min_subsets_without_comm),
        'minimal_subsets': [list(s) for s in min_subsets_without_comm],
    },
    'weaker_replacement_family': {
        'feature_count': len(weak_family),
        'minimal_separating_subset_size': weak_min_size,
        'num_minimal_subsets': len(weak_min_subsets),
        'minimal_subsets': [list(s) for s in weak_min_subsets],
        'minimal_subset_details': weak_min_subset_details,
    },
    'base_replacement_stats': base_replacement_stats,
    'best_triples_without_commutant': best_triples_wo_comm,
}

(RESULTS / 'order8_commutant_weakening_analysis_results.json').write_text(
    json.dumps(result, indent=2, sort_keys=True) + '\n',
    encoding='utf-8',
)

lines_out = []
lines_out.append('Order-8 FFF commutant-weakening analysis')
lines_out.append('')
lines_out.append('Original minimal separating bases on all 230 FFF cases:')
lines_out.append('  - commutant, left_translation_cycle_types, left_inverse_map')
lines_out.append('  - commutant, left_translation_cycle_types, right_inverse_map')
lines_out.append('')
lines_out.append(f"Minimal separating size with the original 18-feature family but WITHOUT full commutant: {min_size_without_comm}")
lines_out.append(f"Number of such minimal subsets: {len(min_subsets_without_comm)}")
lines_out.append('')
lines_out.append(f"Minimal separating size in the weaker replacement family: {weak_min_size}")
lines_out.append(f"Number of minimal subsets there: {len(weak_min_subsets)}")
lines_out.append('')
lines_out.append('Selected weakening tests around the original minimal triple:')
for name in [
    'commutant_size,left_translation_cycle_types,left_inverse_map',
    'commutant_size,left_translation_cycle_types,right_inverse_map',
    'center,left_translation_cycle_types,left_inverse_map',
    'center,left_translation_cycle_types,right_inverse_map',
    'right_nucleus,left_translation_cycle_types,left_inverse_map',
    'right_nucleus,left_translation_cycle_types,right_inverse_map',
    'right_translation_cycle_types,left_translation_cycle_types,left_inverse_map',
    'right_translation_cycle_types,left_translation_cycle_types,right_inverse_map',
]:
    stat = base_replacement_stats[name]
    lines_out.append(f"  - {name}: {stat['cluster_count']} clusters; separates={stat['separates']}")
lines_out.append('')
lines_out.append('Top triples without full commutant:')
for item in best_triples_wo_comm[:10]:
    lines_out.append(f"  - {', '.join(item['subset'])}: {item['cluster_count']} clusters")
lines_out.append('')
lines_out.append('Key collision for commutant_size + left_translation_cycle_types + left_inverse_map:')
collision = base_replacement_stats['commutant_size,left_translation_cycle_types,left_inverse_map']['first_collision']
lines_out.append(f"  - lines {collision['lines']}")

(RESULTS / 'order8_commutant_weakening_analysis_summary.txt').write_text(
    '\n'.join(lines_out) + '\n',
    encoding='utf-8',
)
print(f'wrote {RESULTS / "order8_commutant_weakening_analysis_results.json"}')
