
from collections import Counter
import itertools

def reduced_latin_squares(n):
    """
    Generate all reduced Latin squares of order n.
    Reduced means first row and first column are 0,1,...,n-1.
    """
    if n == 1:
        yield ((0,),)
        return
    # Exact-cover columns
    col_id = {}
    cols = []
    def add_col(key):
        col_id[key] = len(cols)
        cols.append(key)

    for r in range(1, n):
        for c in range(1, n):
            add_col(("cell", r, c))
    for r in range(1, n):
        for s in range(n):
            if s != r:
                add_col(("row", r, s))
    for c in range(1, n):
        for s in range(n):
            if s != c:
                add_col(("col", c, s))

    rows = []
    row_info = []
    col_to_rows = [set() for _ in range(len(cols))]
    for r in range(1, n):
        for c in range(1, n):
            for s in range(n):
                if s == r or s == c:
                    continue
                cover = (
                    col_id[("cell", r, c)],
                    col_id[("row", r, s)],
                    col_id[("col", c, s)],
                )
                idx = len(rows)
                rows.append(cover)
                row_info.append((r, c, s))
                for col in cover:
                    col_to_rows[col].add(idx)

    active_cols = set(range(len(cols)))
    row_active = [True] * len(rows)
    col_rows = [set(s) for s in col_to_rows]
    solution = []

    def select_row(ridx, removed_cols, removed_rows):
        for col in rows[ridx]:
            if col not in active_cols:
                continue
            active_cols.remove(col)
            removed_cols.append(col)
            affected_rows = list(col_rows[col])
            for rr in affected_rows:
                if not row_active[rr]:
                    continue
                row_active[rr] = False
                removed_rows.append(rr)
                for cc in rows[rr]:
                    col_rows[cc].discard(rr)

    def deselect_row(removed_cols, removed_rows):
        for rr in reversed(removed_rows):
            row_active[rr] = True
            for cc in rows[rr]:
                col_rows[cc].add(rr)
        for col in reversed(removed_cols):
            active_cols.add(col)

    def search():
        if not active_cols:
            sq = [[None] * n for _ in range(n)]
            for i in range(n):
                sq[0][i] = i
                sq[i][0] = i
            for ridx in solution:
                r, c, s = row_info[ridx]
                sq[r][c] = s
            yield tuple(tuple(row) for row in sq)
            return
        col = min(active_cols, key=lambda c: len(col_rows[c]))
        cand_rows = list(col_rows[col])
        if not cand_rows:
            return
        for ridx in cand_rows:
            removed_cols = []
            removed_rows = []
            select_row(ridx, removed_cols, removed_rows)
            solution.append(ridx)
            yield from search()
            solution.pop()
            deselect_row(removed_cols, removed_rows)

    yield from search()

def perm_sign(p):
    n = len(p)
    seen = [False] * n
    sign = 1
    for i in range(n):
        if not seen[i]:
            cur = i
            cyc_len = 0
            while not seen[cur]:
                seen[cur] = True
                cur = p[cur]
                cyc_len += 1
            if (cyc_len - 1) % 2 == 1:
                sign = -sign
    return sign

def row_col_sym_parity(L):
    n = len(L)
    row_sign = 1
    col_sign = 1
    sym_sign = 1
    for r in range(n):
        row_sign *= perm_sign(list(L[r]))
    for c in range(n):
        col_sign *= perm_sign([L[r][c] for r in range(n)])
    # For each symbol s, map row -> column position of s
    pos = [[None] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            pos[L[r][c]][r] = c
    for s in range(n):
        sym_sign *= perm_sign(pos[s])
    return (row_sign, col_sign, sym_sign)

def induced_perm_row(L, r1, r2):
    n = len(L)
    inv = [None] * n
    for c, s in enumerate(L[r2]):
        inv[s] = c
    return [inv[s] for s in L[r1]]

def induced_perm_col(L, c1, c2):
    n = len(L)
    inv = [None] * n
    for r in range(n):
        inv[L[r][c2]] = r
    return [inv[L[r][c1]] for r in range(n)]

def induced_perm_sym(L, s1, s2):
    n = len(L)
    pos1 = [None] * n
    pos2 = [None] * n
    for c in range(n):
        for r in range(n):
            x = L[r][c]
            if x == s1:
                pos1[c] = r
            elif x == s2:
                pos2[c] = r
    inv = [None] * n
    for c, r in enumerate(pos2):
        inv[r] = c
    return [inv[r] for r in pos1]

def cycle_lengths(perm):
    n = len(perm)
    seen = [False] * n
    out = []
    for i in range(n):
        if not seen[i]:
            cur = i
            cyc_len = 0
            while not seen[cur]:
                seen[cur] = True
                cur = perm[cur]
                cyc_len += 1
            out.append(cyc_len)
    return out

def has_odd_cycle_perm(perm):
    return any(l > 1 and l % 2 == 1 for l in cycle_lengths(perm))

def has_odd_cycle_view(L, view, pairs=None):
    n = len(L)
    if pairs is None:
        pairs = list(itertools.combinations(range(n), 2))
    if view == "row":
        func = induced_perm_row
    elif view == "col":
        func = induced_perm_col
    elif view == "sym":
        func = induced_perm_sym
    else:
        raise ValueError(view)
    return any(has_odd_cycle_perm(func(L, a, b)) for a, b in pairs)

def get_1_factors(size):
    factors = []
    m = size - 1
    inf_vertex = size - 1
    for turn in range(m):
        pairs = []
        pairs.append(tuple(sorted((turn, inf_vertex))))
        for k in range(1, size // 2):
            a = (turn - k + m) % m
            b = (turn + k) % m
            pairs.append(tuple(sorted((a, b))))
        factors.append(tuple(pairs))
    return tuple(factors)

def cayley_z(n):
    return tuple(tuple((i + j) % n for j in range(n)) for i in range(n))

def summarize_order(n):
    total = 0
    patterns = Counter()
    parity_by_pattern = {}
    first_examples = {}
    first_factor = get_1_factors(n)[0] if n % 2 == 0 and n >= 2 else None
    first_factor_patterns = Counter()
    for L in reduced_latin_squares(n):
        total += 1
        patt = tuple(has_odd_cycle_view(L, v) for v in ("row", "col", "sym"))
        patterns[patt] += 1
        if patt not in first_examples:
            first_examples[patt] = L
        parity_by_pattern.setdefault(patt, Counter())[row_col_sym_parity(L)] += 1
        if first_factor is not None:
            patt_ff = tuple(has_odd_cycle_view(L, v, first_factor) for v in ("row", "col", "sym"))
            first_factor_patterns[patt_ff] += 1
    return {
        "n": n,
        "reduced_count": total,
        "patterns_any_pairs": {str(k): v for k, v in patterns.items()},
        "patterns_first_factor_only": {str(k): v for k, v in first_factor_patterns.items()},
        "parity_by_pattern": {str(k): {str(pk): pv for pk, pv in pc.items()} for k, pc in parity_by_pattern.items()},
        "examples": {str(k): ex for k, ex in first_examples.items()},
    }

if __name__ == "__main__":
    out = {
        "orders": [summarize_order(n) for n in (2, 4, 6)],
        "group_counterexamples": {
            "Z2": {
                "row": has_odd_cycle_view(cayley_z(2), "row"),
                "col": has_odd_cycle_view(cayley_z(2), "col"),
                "sym": has_odd_cycle_view(cayley_z(2), "sym"),
            },
            "Z4": {
                "row": has_odd_cycle_view(cayley_z(4), "row"),
                "col": has_odd_cycle_view(cayley_z(4), "col"),
                "sym": has_odd_cycle_view(cayley_z(4), "sym"),
            },
            "Z8": {
                "row": has_odd_cycle_view(cayley_z(8), "row"),
                "col": has_odd_cycle_view(cayley_z(8), "col"),
                "sym": has_odd_cycle_view(cayley_z(8), "sym"),
            },
            "Z6": {
                "row": has_odd_cycle_view(cayley_z(6), "row"),
                "col": has_odd_cycle_view(cayley_z(6), "col"),
                "sym": has_odd_cycle_view(cayley_z(6), "sym"),
            },
        },
    }
    import json
    print(json.dumps(out, indent=2))
