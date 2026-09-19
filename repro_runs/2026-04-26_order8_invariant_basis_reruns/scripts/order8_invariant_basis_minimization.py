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

LAYER_BLOCKS = {
    'logic': ['commutative','left_inverse_property','right_inverse_property','inverse_property','inverse_coincide','antiautomorphic_inverse_property','left_alternative','right_alternative','flexible'],
    'nuclei_center': ['left_nucleus','middle_nucleus','right_nucleus','commutant','center'],
    'translation_types': ['left_translation_cycle_types','right_translation_cycle_types'],
    'inverse_maps': ['left_inverse_map','right_inverse_map'],
}

def min_size_with_feature_constraint(subset_separates, features, required=set(), forbidden=set()):
    feats=[f for f in features if f not in forbidden]
    req=set(required)
    for r in range(len(req), len(feats)+1):
        found=[]
        others=[f for f in feats if f not in req]
        for extra in itertools.combinations(others, r-len(req)):
            subset=tuple(sorted(req.union(extra), key=features.index))
            if subset_separates(subset):
                found.append(subset)
        if found:
            return r, found
    return None, []

def main():
    records=[]
    with open(DATA/'order8_fff_counterexamples.tsv', newline='') as f:
        reader=csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['group_isotopic'].lower()=='false':
                records.append({'line': int(row['line_number']), 'square': row['square']})
    lines=[r['line'] for r in records]

    by_line={}
    for rec in records:
        inv=extended_invariants(parse_square(rec['square']))
        by_line[rec['line']]={f: inv[f] for f in FEATURES}

    encoded={}
    value_maps={}
    for f in FEATURES:
        vals=[by_line[line][f] for line in lines]
        uniq={v:i for i,v in enumerate(sorted(set(vals), key=repr))}
        value_maps[f]=uniq
        encoded[f]=[uniq[by_line[line][f]] for line in lines]

    def subset_separates(subset):
        seen=set()
        for i in range(len(lines)):
            sig=tuple(encoded[f][i] for f in subset)
            if sig in seen:
                return False
            seen.add(sig)
        return True

    def cluster_count_only(subset):
        seen=set()
        for i in range(len(lines)):
            seen.add(tuple(encoded[f][i] for f in subset))
        return len(seen)

    separating_counts_by_size={}
    minimal_size=None
    minimal_subsets=[]
    for r in range(1, len(FEATURES)+1):
        count=0
        mins=[]
        for subset in itertools.combinations(FEATURES, r):
            if subset_separates(subset):
                count += 1
                if minimal_size is None:
                    mins.append(subset)
        separating_counts_by_size[r]=count
        if minimal_size is None and count>0:
            minimal_size=r
            minimal_subsets=mins
            break

    all_counts={}
    sep_masks_by_size=defaultdict(set)
    feature_index={f:i for i,f in enumerate(FEATURES)}
    for r in range(1, len(FEATURES)+1):
        count=0
        for subset in itertools.combinations(FEATURES, r):
            if subset_separates(subset):
                count += 1
                mask=0
                for f in subset:
                    mask |= 1<<feature_index[f]
                sep_masks_by_size[r].add(mask)
        all_counts[r]=count

    def mask_to_subset(mask):
        return tuple(FEATURES[i] for i in range(len(FEATURES)) if (mask>>i)&1)

    incl_min_masks=[]
    for size in sorted(sep_masks_by_size):
        for mask in sep_masks_by_size[size]:
            minimal=True
            for s2 in range(1,size):
                for m2 in sep_masks_by_size[s2]:
                    if m2 & mask == m2:
                        minimal=False
                        break
                if not minimal:
                    break
            if minimal:
                incl_min_masks.append(mask)
    incl_min_subsets=[mask_to_subset(m) for m in incl_min_masks]

    minimal_core=set(minimal_subsets[0]).intersection(*map(set, minimal_subsets))
    minimal_union=set().union(*map(set, minimal_subsets))

    forbid_feature_min_size={}
    for feat in FEATURES:
        r, subs = min_size_with_feature_constraint(subset_separates, FEATURES, forbidden={feat})
        forbid_feature_min_size[feat]={
            'min_size_without_feature': r,
            'sample_subsets': [list(s) for s in subs[:10]],
        }

    block_combo_results={}
    def features_for_blocks(names):
        feats=[]
        for n in names:
            feats.extend(LAYER_BLOCKS[n])
        return feats

    for r in range(1, len(LAYER_BLOCKS)+1):
        for combo in itertools.combinations(LAYER_BLOCKS, r):
            feats=features_for_blocks(combo)
            size_dist=Counter()
            sig_to_lines=defaultdict(list)
            for i,line in enumerate(lines):
                sig=tuple(encoded[f][i] for f in feats)
                sig_to_lines[sig].append(line)
            for v in sig_to_lines.values():
                size_dist[len(v)] += 1
            minr, subs=min_size_with_feature_constraint(subset_separates, feats)
            block_combo_results[' + '.join(combo)] = {
                'feature_count': len(feats),
                'cluster_count': len(sig_to_lines),
                'size_distribution': {str(k): v for k,v in sorted(size_dist.items())},
                'min_separating_size': minr,
                'num_min_subsets': len(subs),
                'sample_subsets': [list(s) for s in subs[:10]],
            }

    top_by_size={}
    for r in [1,2,3]:
        lst=[]
        for subset in itertools.combinations(FEATURES, r):
            lst.append((cluster_count_only(subset), subset))
        lst.sort(reverse=True)
        top_by_size[str(r)] = [{'cluster_count':c,'subset':list(s)} for c,s in lst[:10]]

    result = {
        'feature_names': FEATURES,
        'nongroup_case_count': len(lines),
        'minimal_separating_subset_size': minimal_size,
        'minimal_separating_subsets': [list(s) for s in minimal_subsets],
        'minimal_subset_core': sorted(minimal_core, key=FEATURES.index),
        'minimal_subset_union': sorted(minimal_union, key=FEATURES.index),
        'separating_subset_count_by_size': {str(k): v for k,v in all_counts.items()},
        'inclusion_minimal_separating_subsets': [list(s) for s in sorted(incl_min_subsets, key=lambda s:(len(s), s))],
        'no_subset_without_inverse_maps_separates': min_size_with_feature_constraint(subset_separates, FEATURES, forbidden={'left_inverse_map','right_inverse_map'})[0] is None,
        'forbid_feature_min_size': forbid_feature_min_size,
        'block_combo_results': block_combo_results,
        'top_cluster_counts_by_size': top_by_size,
    }

    (RESULTS/'order8_invariant_basis_minimization_results.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')

    lines_out=[]
    lines_out.append('Order-8 nongroup-FFF invariant-basis minimization')
    lines_out.append('')
    lines_out.append(f'nongroup cases: {len(lines)}')
    lines_out.append(f'minimal separating subset size: {minimal_size}')
    lines_out.append('minimal separating subsets:')
    for s in minimal_subsets:
        lines_out.append('  - ' + ', '.join(s))
    lines_out.append('')
    lines_out.append('core of all minimal subsets: ' + ', '.join(sorted(minimal_core, key=FEATURES.index)))
    lines_out.append('union of all minimal subsets: ' + ', '.join(sorted(minimal_union, key=FEATURES.index)))
    lines_out.append('')
    lines_out.append('no subset without inverse maps separates: ' + str(result['no_subset_without_inverse_maps_separates']))
    lines_out.append('')
    lines_out.append('best single features by cluster count:')
    for item in top_by_size['1'][:5]:
        lines_out.append(f"  - {', '.join(item['subset'])} : {item['cluster_count']} clusters")
    lines_out.append('best pairs by cluster count:')
    for item in top_by_size['2'][:5]:
        lines_out.append(f"  - {', '.join(item['subset'])} : {item['cluster_count']} clusters")
    lines_out.append('best triples by cluster count:')
    for item in top_by_size['3'][:6]:
        lines_out.append(f"  - {', '.join(item['subset'])} : {item['cluster_count']} clusters")
    lines_out.append('')
    lines_out.append('block combinations:')
    for combo in sorted(block_combo_results):
        info=block_combo_results[combo]
        lines_out.append(f"  - {combo}: clusters={info['cluster_count']}, min separating size={info['min_separating_size']}")
    (RESULTS/'order8_invariant_basis_minimization_summary.txt').write_text('\n'.join(lines_out)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
