#!/usr/bin/env python3
from __future__ import annotations

import csv
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


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


def main():
    nongroup = []
    with open(DATA / 'order8_fff_counterexamples.tsv', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['group_isotopic'].lower() == 'false':
                nongroup.append({'line': int(row['line_number']), 'square': row['square']})

    groups = defaultdict(list)
    line_to_inv = {}
    for rec in nongroup:
        inv = extended_invariants(parse_square(rec['square']))
        line_to_inv[rec['line']] = inv
        profile = (
            inv['commutative'],
            inv['left_inverse_property'],
            inv['right_inverse_property'],
            inv['inverse_property'],
            inv['inverse_coincide'],
            inv['antiautomorphic_inverse_property'],
            inv['left_alternative'],
            inv['right_alternative'],
            inv['flexible'],
            inv['left_nucleus'],
            inv['middle_nucleus'],
            inv['right_nucleus'],
            inv['commutant'],
            inv['center'],
            inv['left_translation_cycle_types'],
            inv['right_translation_cycle_types'],
            inv['left_inverse_map'],
            inv['right_inverse_map'],
        )
        groups[profile].append(rec['line'])

    size_dist = {str(k): v for k, v in sorted(Counter(len(v) for v in groups.values()).items())}
    largest = sorted((len(v), sorted(v)) for v in groups.values())[::-1][:10]

    result = {
        'nongroup_case_count': len(nongroup),
        'extended_cluster_count': len(groups),
        'extended_cluster_size_distribution': size_dist,
        'largest_extended_clusters': [{'size': size, 'lines': lines} for size, lines in largest],
        'singleton_count': sum(1 for v in groups.values() if len(v) == 1),
        'nonsingleton_clusters': [sorted(v) for v in sorted(groups.values(), key=lambda xs: (len(xs), xs)) if len(v) > 1],
        'line_10776_cluster': next(sorted(v) for v in groups.values() if 10776 in v),
        'commutative_lines': sorted(line for line, inv in line_to_inv.items() if inv['commutative']),
        'main_findings': {
            'extended_profile_splits_10776_cluster_completely': len(next(v for v in groups.values() if 10776 in v)) == 1,
            'extended_profile_splits_all_12_commutative_cases_completely': len([v for v in groups.values() if any(line_to_inv[x]['commutative'] for x in v)]) == 12,
        },
    }

    (RESULTS / 'order8_extended_nongroup_cluster_analysis_results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    lines = []
    lines.append('Order-8 extended nongroup-FFF clustering')
    lines.append('')
    lines.append(f'nongroup cases: {len(nongroup)}')
    lines.append(f'extended cluster count: {len(groups)}')
    lines.append(f'extended cluster size distribution: {size_dist}')
    lines.append(f'singletons: {result["singleton_count"]}')
    lines.append(f'10776-cluster under extended profile: {result["line_10776_cluster"]}')
    lines.append(f'commutative lines: {result["commutative_lines"]}')
    (RESULTS / 'order8_extended_nongroup_cluster_analysis_summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
