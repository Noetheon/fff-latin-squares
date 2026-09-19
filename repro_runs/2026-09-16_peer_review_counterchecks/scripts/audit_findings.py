#!/usr/bin/env python3
"""Independent small exact checks of the September review's local examples.

No historical flag scanner or external audit program is imported.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict, deque
from fractions import Fraction
from itertools import combinations
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def rref(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    pivots = []
    if not a:
        return a, pivots
    for col in range(len(a[0])):
        pivot = next((i for i in range(len(pivots), len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        row = len(pivots)
        a[row], a[pivot] = a[pivot], a[row]
        value = a[row][col]
        a[row] = [x / value for x in a[row]]
        for i in range(len(a)):
            if i != row and a[i][col]:
                value = a[i][col]
                a[i] = [x - value * y for x, y in zip(a[i], a[row])]
        pivots.append(col)
        if len(pivots) == len(a):
            break
    return a, pivots


def rank(matrix):
    return len(rref(matrix)[1])


def nullspace(matrix):
    reduced, pivots = rref(matrix)
    free = [c for c in range(len(matrix[0])) if c not in pivots]
    basis = []
    for col in free:
        v = [Fraction(0)] * len(matrix[0])
        v[col] = 1
        for row, pivot in enumerate(pivots):
            v[pivot] = -reduced[row][col]
        basis.append(v)
    return basis


def latin_flags(table):
    n = len(table)
    assert all(sorted(row) == list(range(n)) for row in table)
    assert all(sorted(table[r][c] for r in range(n)) == list(range(n)) for c in range(n))
    flags, labels = [], []
    edges = [defaultdict(list) for _ in range(3)]
    for r in range(n):
        for other in range(n):
            if r == other:
                continue
            for c in range(n):
                s = table[r][c]
                d = table[other].index(s)
                a, b, t = r*n+c, other*n+d, r*n+d
                index = len(flags)
                flags.append((a, b, t))
                labels.append((tuple(sorted((r, other))), tuple(sorted((c, d))),
                               tuple(sorted((s, table[r][d])))))
                for view, pair in enumerate(((a, t), (b, t), (a, b))):
                    edges[view][tuple(sorted(pair))].append(index)
    alpha = [[None]*len(flags) for _ in range(3)]
    for view in range(3):
        for adjacent in edges[view].values():
            assert len(adjacent) == 2
            f, g = adjacent
            alpha[view][f], alpha[view][g] = g, f
    return flags, labels, alpha


def components(alpha):
    unseen = set(range(len(alpha[0])))
    result = []
    while unseen:
        found, queue = {min(unseen)}, deque([min(unseen)])
        while queue:
            f = queue.popleft()
            for adj in alpha:
                if adj[f] not in found:
                    found.add(adj[f])
                    queue.append(adj[f])
        unseen -= found
        result.append(sorted(found))
    return result


def potential(alpha, component, bits):
    values, queue = {component[0]: 0}, deque([component[0]])
    while queue:
        f = queue.popleft()
        for view, bit in enumerate(bits):
            g, value = alpha[view][f], values[f] ^ bit
            if g in values:
                if values[g] != value:
                    return None
            else:
                values[g] = value
                queue.append(g)
    assert set(values) == set(component)
    return values


def pushforward(flags, values, n):
    out = [0]*(n*n)
    for f, value in values.items():
        for cell in flags[f]:
            out[cell] += (-1)**value
    return out


def rank_check(table):
    n = len(table)
    flags, labels, _ = latin_flags(table)
    pairs = list(combinations(range(n), 2))
    m = len(pairs)
    z = [[int(pair == lab[v]) for v in range(3) for pair in pairs] for lab in labels]
    k = [[Fraction(sum(row[i]*row[j] for row in z), 2) for j in range(3*m)] for i in range(3*m)]
    e = [[int(v in pair) for pair in pairs] for v in range(n)]
    basis = nullspace(e)
    block_basis = [[0]*(view*m) + list(b) + [0]*((2-view)*m) for view in range(3) for b in basis]
    kb = [[sum(a*b for a, b in zip(row, vector)) for row in k] for vector in block_basis]
    restricted = [[sum(a*b for a,b in zip(left, right)) for right in kb] for left in block_basis]
    b = [[int(cell in flag) for cell in range(n*n)] for flag in flags]
    result = dict(n=n, flags=len(flags), rank_K=rank(k), rank_C=rank(restricted),
                  rank_B=rank(b), projected_Schur_rank=rank([x+y for x,y in zip(b,z)])-rank(b))
    result['rank_formula_rhs'] = 3*n-2+result['rank_C']
    if n == 2:
        assert k == [[2]*3 for _ in range(3)]
        assert result['rank_K'] == 1 and result['rank_formula_rhs'] == 4
    else:
        assert result['rank_K'] == result['rank_formula_rhs']
        assert result['projected_Schur_rank'] == result['rank_K']-1
    return result


def local_checks():
    cyclic = lambda n: [[(r+c) % n for c in range(n)] for r in range(n)]
    ranks = [rank_check(cyclic(n)) for n in (2,3,4)]
    ranks.append(rank_check([[r ^ c for c in range(4)] for r in range(4)]))
    assert ranks[1]['rank_B'] == 7  # ordinary cell Gram inverse does not exist at n=3
    flags, labels, _ = latin_flags(cyclic(3))
    tensor = Counter(labels)
    fiber = {str(key[2]): value for key,value in tensor.items() if key[:2] == ((0,1),(0,2))}
    assert sorted(fiber.values()) == [1,1]
    assert sum(fiber.values()) == 2
    all_fibers = 0
    for n in (2,3,4):
        _, labs, _ = latin_flags(cyclic(n))
        count = Counter(labs)
        for a,b in combinations(range(3),2):
            groups = defaultdict(list)
            for key,value in count.items():
                groups[(key[a],key[b])].append(value)
            assert all(sorted(v) in ([1,1],[4]) for v in groups.values())
            all_fibers += len(groups)
    table = cyclic(2)
    flags, _, alpha = latin_flags(table)
    expected = {'011':[1,1,-1,-1], '101':[-1,1,-1,1], '110':[1,-1,-1,1]}
    masks = []
    for label, vector in expected.items():
        bits = tuple(map(int,label))
        values = potential(alpha, list(range(4)), bits)
        assert values is not None
        actual = pushforward(flags, values, 2)
        assert actual in (vector, [-v for v in vector])
        marginals = [[sum(actual[r*2+c] for c in range(2)) for r in range(2)],
                     [sum(actual[r*2+c] for r in range(2)) for c in range(2)],
                     [sum(actual[r*2+c] for r in range(2) for c in range(2) if table[r][c] == s) for s in range(2)]]
        assert [all(x == 0 for x in v) for v in marginals] == list(map(bool,bits))
        masks.append(dict(tuple_RCS=label, integer_code=sum(b << i for i,b in enumerate(bits)),
                          pushforward=actual, marginals=marginals))
    flags, _, alpha = latin_flags(cyclic(4))
    zero_examples = []
    for component in components(alpha):
        values = potential(alpha, component, (1,1,1))
        if len(component) == 32 and values is not None:
            u = pushforward(flags, values, 4)
            assert u == [0]*16
            zero_examples.append(dict(flags=32, mask_RCS='111', pushforward=u,
                                      charge_nonzero=True, evaluated_value_gauge_invariant=True))
    assert len(zero_examples) == 1
    return dict(ranks=ranks, tensor_C3_fiber=fiber, tensor_fibers_checked=all_fibers,
                intercalate_masks=masks, zero_monomial_examples=zero_examples)


def graph_check(kind, graph):
    run = ROOT / f'repro_runs/2026-08-26_fff_six_type_{kind}_master_search'
    manifest = json.loads((ROOT/'archive/github_releases/2026-08-28/bundle_manifest.json').read_text())
    expected = next(e for e in manifest['files'] if e['path'].endswith('/'+graph.name))
    assert graph.stat().st_size == expected['bytes']
    checksum = sha256(graph)
    assert checksum == expected['sha256']
    with graph.open('rb') as stream:
        assert stream.read(8) == b'O8HTv1\0\0'
        n, words = struct.unpack('<II', stream.read(8))
        assert words == (n+63)//64
        q1 = list(stream.read(10))
        vertices = [stream.read(10) for _ in range(n)]
    buckets = [[i for i,v in enumerate(vertices) if v[0] == b+2] for b in range(8)]
    initial = min(range(8), key=lambda b: len(buckets[b]))
    tasks = buckets[initial]
    ordinals_path = run/f'data/{kind}_task_ordinals.txt'
    ordinals = list(map(int,ordinals_path.read_text().split()))
    selected = []
    for ordinal in ordinals:
        assert 0 <= ordinal < len(tasks)
        assert not selected or ordinal > selected[-1]  # exact historical predicate
        selected.append(tasks[ordinal])
    assert ordinals == sorted(set(ordinals))
    assert tasks == list(range(len(tasks)))
    assert selected == ordinals
    return dict(kind=kind, graph_sha256=checksum, graph_bytes=graph.stat().st_size,
                vertices=n, q1=q1, bucket_sizes=list(map(len,buckets)), initial_bucket=initial,
                root_tasks=len(tasks), selected_orbits=len(ordinals), all_task_ordinals_equal_vertex_ids=True,
                historical_predicate_accepts_actual_file=True,
                task_file_sha256=sha256(ordinals_path),
                scope='Task selection only; no edge enumeration or DFS rerun.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphs-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = dict(passed=True, independent_local_checks=local_checks(),
                  external_audit_reruns_verified=False, master_task_selection=[])
    if args.graphs_root:
        for kind,name in [('involution','involution_master_all_7_types.bin'),
                          ('noninvolution','noninvolution_master_6_types.bin')]:
            report['master_task_selection'].append(graph_check(kind,args.graphs_root/kind/name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
