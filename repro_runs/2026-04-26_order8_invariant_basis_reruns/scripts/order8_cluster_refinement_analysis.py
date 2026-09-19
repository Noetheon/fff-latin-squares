#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
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


def light_invariants(square):
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


def cluster_by(records, keys):
    groups = defaultdict(list)
    for line, inv in records.items():
        groups[tuple(inv[k] for k in keys)].append(line)
    return groups


def size_distribution(groups):
    return {str(k): v for k, v in sorted(Counter(len(v) for v in groups.values()).items())}


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


def main():
    cluster_data = json.loads((RESULTS / 'order8_nongroup_cluster_analysis_results.json').read_text(encoding='utf-8'))

    # 41-cluster containing 10776
    cluster_41 = next(cl['lines'] for cl in cluster_data['fine_clusters'] if 10776 in cl['lines'])

    # all nongroup FFF records
    nongroup = []
    with open(DATA / 'order8_fff_counterexamples.tsv', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['group_isotopic'].lower() == 'false':
                nongroup.append({'line': int(row['line_number']), 'square': row['square']})
    by_line = {r['line']: r['square'] for r in nongroup}

    # compute light invariants only where needed
    inv_41 = {line: light_invariants(parse_square(by_line[line])) for line in cluster_41}
    comm_lines = []
    inv_comm = {}
    for rec in nongroup:
        inv = light_invariants(parse_square(rec['square']))
        if inv['commutative']:
            comm_lines.append(rec['line'])
            inv_comm[rec['line']] = inv

    # staged refinement of the 41-cluster
    base_keys = [
        'antiautomorphic_inverse_property',
        'flexible',
        'left_nucleus',
        'middle_nucleus',
        'right_nucleus',
        'center',
    ]
    stage2_keys = base_keys + [
        'left_inverse_property',
        'right_inverse_property',
        'left_alternative',
        'right_alternative',
        'commutant',
    ]
    stage3_keys = stage2_keys + [
        'left_translation_cycle_types',
        'right_translation_cycle_types',
    ]
    stage4_keys = stage3_keys + [
        'left_inverse_map',
        'right_inverse_map',
    ]

    staged = {}
    for name, keys in [
        ('stage1_base_loop_shape', base_keys),
        ('stage2_add_lip_rip_alt_commutant', stage2_keys),
        ('stage3_add_translation_cycle_multisets', stage3_keys),
        ('stage4_add_inverse_maps', stage4_keys),
    ]:
        groups = cluster_by(inv_41, keys)
        staged[name] = {
            'cluster_count': len(groups),
            'size_distribution': size_distribution(groups),
            'clusters': [sorted(v) for v in sorted(groups.values(), key=lambda xs: (len(xs), xs))],
        }

    # commutative cases clustering by the full light profile
    comm_keys = stage4_keys
    comm_groups = cluster_by(inv_comm, comm_keys)

    # line-specific snapshots for 10776 and the 12 commutative cases
    spotlight_lines = sorted(set([10776] + comm_lines))
    spotlight = {}
    for line in spotlight_lines:
        inv = inv_41.get(line) or inv_comm[line]
        spotlight[str(line)] = jsonable(inv)

    result = {
        'cluster_41_lines': cluster_41,
        'cluster_41_refinement': staged,
        'commutative_nongroup_lines': comm_lines,
        'commutative_nongroup_count': len(comm_lines),
        'commutative_nongroup_fine_cluster_count_under_extended_profile': len(comm_groups),
        'commutative_nongroup_size_distribution_under_extended_profile': size_distribution(comm_groups),
        'commutative_nongroup_clusters_under_extended_profile': [sorted(v) for v in sorted(comm_groups.values(), key=lambda xs: xs)],
        'spotlight_invariants': spotlight,
        'main_findings': {
            'cluster_41_splits_into_singletons_under_extended_profile': len(staged['stage4_add_inverse_maps']['clusters']) == 41,
            'commutative_nongroup_cases_split_into_singletons_under_extended_profile': len(comm_groups) == len(comm_lines),
        },
    }

    (RESULTS / 'order8_cluster_refinement_analysis_results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    lines = []
    lines.append('Order-8 nongroup-FFF cluster refinement')
    lines.append('')
    lines.append(f'41-cluster containing 10776: {cluster_41}')
    lines.append('')
    for name in ['stage1_base_loop_shape', 'stage2_add_lip_rip_alt_commutant', 'stage3_add_translation_cycle_multisets', 'stage4_add_inverse_maps']:
        entry = staged[name]
        lines.append(f'{name}: {entry["cluster_count"]} clusters; size distribution {entry["size_distribution"]}')
    lines.append('')
    lines.append(f'Commutative nongroup-FFF lines ({len(comm_lines)} total): {comm_lines}')
    lines.append(f'Under the extended profile they split into {len(comm_groups)} clusters with size distribution {size_distribution(comm_groups)}.')
    (RESULTS / 'order8_cluster_refinement_analysis_summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
