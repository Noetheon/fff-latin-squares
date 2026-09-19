#!/usr/bin/env python3
from __future__ import annotations

import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
DATA = RUN_ROOT / 'data'
RESULTS = RUN_ROOT / 'results'
ORDER = 8


def parse_square(compact: str):
    vals = [ord(ch) - 48 for ch in compact.strip()]
    return [vals[i * ORDER:(i + 1) * ORDER] for i in range(ORDER)]


def cycle_type(perm):
    seen = [False] * ORDER
    parts = []
    for s in range(ORDER):
        if seen[s]:
            continue
        cur = s
        length = 0
        while not seen[cur]:
            seen[cur] = True
            cur = perm[cur]
            length += 1
        parts.append(length)
    parts.sort(reverse=True)
    return tuple(parts)


def extended_invariants(square):
    left_inv = [next(x for x in range(ORDER) if square[x][a] == 0) for a in range(ORDER)]
    right_inv = [next(x for x in range(ORDER) if square[a][x] == 0) for a in range(ORDER)]

    def assoc_left(a, x, y):
        return square[a][square[x][y]] == square[square[a][x]][y]

    def assoc_mid(a, x, y):
        return square[x][square[a][y]] == square[square[x][a]][y]

    def assoc_right(a, x, y):
        return square[x][square[y][a]] == square[square[x][y]][a]

    left_nucleus = [a for a in range(ORDER) if all(assoc_left(a, x, y) for x in range(ORDER) for y in range(ORDER))]
    middle_nucleus = [a for a in range(ORDER) if all(assoc_mid(a, x, y) for x in range(ORDER) for y in range(ORDER))]
    right_nucleus = [a for a in range(ORDER) if all(assoc_right(a, x, y) for x in range(ORDER) for y in range(ORDER))]
    commutant = [a for a in range(ORDER) if all(square[a][x] == square[x][a] for x in range(ORDER))]
    center = sorted(set(left_nucleus) & set(middle_nucleus) & set(right_nucleus) & set(commutant))

    left_ip = all(square[left_inv[a]][square[a][x]] == x for a in range(ORDER) for x in range(ORDER))
    right_ip = all(square[square[x][a]][right_inv[a]] == x for a in range(ORDER) for x in range(ORDER))
    inv_property = left_ip and right_ip
    inv_coincide = left_inv == right_inv
    aaip = inv_coincide and all(left_inv[square[a][b]] == square[left_inv[b]][left_inv[a]] for a in range(ORDER) for b in range(ORDER))

    left_alt = all(square[a][square[a][x]] == square[square[a][a]][x] for a in range(ORDER) for x in range(ORDER))
    right_alt = all(square[square[x][a]][a] == square[x][square[a][a]] for a in range(ORDER) for x in range(ORDER))
    flexible = all(square[a][square[x][a]] == square[square[a][x]][a] for a in range(ORDER) for x in range(ORDER))

    left_translation_cycle_types = Counter(cycle_type(tuple(square[a][x] for x in range(ORDER))) for a in range(1, ORDER))
    right_translation_cycle_types = Counter(cycle_type(tuple(square[x][a] for x in range(ORDER))) for a in range(1, ORDER))

    return {
        'group_isotopic': None,
        'commutative': len(commutant) == ORDER,
        'left_inverse_property': left_ip,
        'right_inverse_property': right_ip,
        'inverse_property': inv_property,
        'inverse_coincide': inv_coincide,
        'antiautomorphic_inverse_property': aaip,
        'left_alternative': left_alt,
        'right_alternative': right_alt,
        'flexible': flexible,
        'left_nucleus': tuple(left_nucleus),
        'middle_nucleus': tuple(middle_nucleus),
        'right_nucleus': tuple(right_nucleus),
        'commutant': tuple(commutant),
        'center': tuple(center),
        'left_translation_cycle_types': tuple(sorted((k, v) for k, v in left_translation_cycle_types.items())),
        'right_translation_cycle_types': tuple(sorted((k, v) for k, v in right_translation_cycle_types.items())),
        'left_inverse_map': tuple(left_inv),
        'right_inverse_map': tuple(right_inv),
    }


FEATURES = [
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
    'commutant',
    'center',
    'left_translation_cycle_types',
    'right_translation_cycle_types',
    'left_inverse_map',
    'right_inverse_map',
]

# add optional flags to test conceptual simplifications
FEATURES_PLUS = FEATURES + ['group_isotopic_flag']


def min_size_with_feature_constraint(subset_separates, features, required=set(), forbidden=set()):
    feats = [f for f in features if f not in forbidden]
    req = set(required)
    for r in range(len(req), len(feats) + 1):
        found = []
        others = [f for f in feats if f not in req]
        for extra in itertools.combinations(others, r - len(req)):
            subset = tuple(sorted(req.union(extra), key=features.index))
            if subset_separates(subset):
                found.append(subset)
        if found:
            return r, found
    return None, []


def analyze(records, features):
    lines = [r['line'] for r in records]
    by_line = {}
    for rec in records:
        inv = extended_invariants(parse_square(rec['square']))
        inv['group_isotopic_flag'] = bool(rec['group_isotopic'])
        by_line[rec['line']] = {f: inv[f] for f in features}

    encoded = {}
    value_maps = {}
    for f in features:
        vals = [by_line[line][f] for line in lines]
        uniq = {v: i for i, v in enumerate(sorted(set(vals), key=repr))}
        value_maps[f] = uniq
        encoded[f] = [uniq[by_line[line][f]] for line in lines]

    def subset_separates(subset):
        seen = set()
        for i in range(len(lines)):
            sig = tuple(encoded[f][i] for f in subset)
            if sig in seen:
                return False
            seen.add(sig)
        return True

    def cluster_count_only(subset):
        seen = set()
        for i in range(len(lines)):
            seen.add(tuple(encoded[f][i] for f in subset))
        return len(seen)

    minimal_size = None
    minimal_subsets = []
    all_counts = {}
    sep_masks_by_size = defaultdict(set)
    feature_index = {f: i for i, f in enumerate(features)}
    for r in range(1, len(features) + 1):
        count = 0
        mins = []
        for subset in itertools.combinations(features, r):
            if subset_separates(subset):
                count += 1
                if minimal_size is None:
                    mins.append(subset)
                mask = 0
                for f in subset:
                    mask |= 1 << feature_index[f]
                sep_masks_by_size[r].add(mask)
        all_counts[r] = count
        if minimal_size is None and count > 0:
            minimal_size = r
            minimal_subsets = mins
            break

    def mask_to_subset(mask):
        return tuple(features[i] for i in range(len(features)) if (mask >> i) & 1)

    incl_min_masks = []
    for size in sorted(sep_masks_by_size):
        for mask in sep_masks_by_size[size]:
            minimal = True
            for s2 in range(1, size):
                for m2 in sep_masks_by_size[s2]:
                    if m2 & mask == m2:
                        minimal = False
                        break
                if not minimal:
                    break
            if minimal:
                incl_min_masks.append(mask)
    incl_min_subsets = [mask_to_subset(m) for m in incl_min_masks]

    top_by_size = {}
    for r in [1, 2, 3]:
        lst = []
        for subset in itertools.combinations(features, r):
            lst.append((cluster_count_only(subset), subset))
        lst.sort(reverse=True)
        top_by_size[str(r)] = [{'cluster_count': c, 'subset': list(s)} for c, s in lst[:20]]

    return {
        'case_count': len(lines),
        'minimal_separating_subset_size': minimal_size,
        'minimal_separating_subsets': [list(s) for s in minimal_subsets],
        'inclusion_minimal_separating_subsets': [list(s) for s in sorted(incl_min_subsets, key=lambda s: (len(s), s))],
        'separating_subset_count_by_size': {str(k): v for k, v in all_counts.items()},
        'top_cluster_counts_by_size': top_by_size,
        'feature_names': features,
    }


def main():
    records = []
    with open(DATA / 'order8_fff_counterexamples.tsv', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            records.append({'line': int(row['line_number']), 'square': row['square'], 'group_isotopic': row['group_isotopic'].lower() == 'true'})

    full_analysis = analyze(records, FEATURES)
    plus_analysis = analyze(records, FEATURES_PLUS)

    # Check whether the previously found nongroup minimal triples already separate all 230.
    candidate_triples = [
        ('commutant', 'left_translation_cycle_types', 'left_inverse_map'),
        ('commutant', 'left_translation_cycle_types', 'right_inverse_map'),
    ]

    # build encoded for all 230 using FEATURES_PLUS maybe not needed
    full_records = records
    inv_by_line = {}
    for rec in full_records:
        inv = extended_invariants(parse_square(rec['square']))
        inv['group_isotopic_flag'] = bool(rec['group_isotopic'])
        inv_by_line[rec['line']] = inv
    triple_cluster_counts = {}
    triple_separates_all_230 = {}
    for subset in candidate_triples:
        sigs = defaultdict(list)
        for rec in full_records:
            sig = tuple(inv_by_line[rec['line']][f] for f in subset)
            sigs[sig].append(rec['line'])
        triple_cluster_counts[','.join(subset)] = len(sigs)
        triple_separates_all_230[','.join(subset)] = (len(sigs) == len(full_records))

    result = {
        'full_230_analysis': full_analysis,
        'full_230_plus_group_flag_analysis': plus_analysis,
        'candidate_triples_cluster_counts_on_230': triple_cluster_counts,
        'candidate_triples_separate_all_230': triple_separates_all_230,
        'group_lines': [r['line'] for r in records if r['group_isotopic']],
        'nongroup_lines_count': sum(1 for r in records if not r['group_isotopic']),
    }

    (RESULTS / 'order8_full_fff_basis_analysis_results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    lines_out = []
    lines_out.append('Order-8 full FFF invariant-basis analysis (all 230 cases)')
    lines_out.append('')
    lines_out.append(f"Minimal separating subset size on all 230 using the 18-loop-feature profile: {full_analysis['minimal_separating_subset_size']}")
    lines_out.append('Minimal separating subsets on all 230:')
    for s in full_analysis['minimal_separating_subsets']:
        lines_out.append('  - ' + ', '.join(s))
    lines_out.append('')
    lines_out.append(f"Minimal separating subset size on all 230 after adding the explicit group_isotopic flag: {plus_analysis['minimal_separating_subset_size']}")
    lines_out.append('')
    lines_out.append('Do the two nongroup-minimal triples already separate all 230?')
    for k, v in triple_separates_all_230.items():
        lines_out.append(f"  - {k}: {v} (clusters={triple_cluster_counts[k]})")
    lines_out.append('')
    lines_out.append('Top single features on all 230:')
    for item in full_analysis['top_cluster_counts_by_size']['1'][:8]:
        lines_out.append(f"  - {', '.join(item['subset'])}: {item['cluster_count']} clusters")
    lines_out.append('Top pairs on all 230:')
    for item in full_analysis['top_cluster_counts_by_size']['2'][:8]:
        lines_out.append(f"  - {', '.join(item['subset'])}: {item['cluster_count']} clusters")
    lines_out.append('Top triples on all 230:')
    for item in full_analysis['top_cluster_counts_by_size']['3'][:10]:
        lines_out.append(f"  - {', '.join(item['subset'])}: {item['cluster_count']} clusters")
    (RESULTS / 'order8_full_fff_basis_analysis_summary.txt').write_text('\n'.join(lines_out) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
