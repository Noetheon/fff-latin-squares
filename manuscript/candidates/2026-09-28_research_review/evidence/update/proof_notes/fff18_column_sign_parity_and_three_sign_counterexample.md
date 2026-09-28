# Column-sign parity after the dual-sign normal form

**Scope.** C266 proves a reduced isotope with positive row 1 and column 1
for every even-order row-F and column-F square of order at least six. This
note gives an exact SAT encoding of the column-1 sign. It does not decide
order 18 or add a condition to C243's shorter 14-case split.

## Exact parity encoding

Let `L` be reduced and write `q(r)=L(r,1)`. Latinness makes `q` a
permutation. For every `r<t`, introduce a Boolean `I[r,t]` and, for all
distinct values `v,w`, add

```text
not X[r,1,v] or not X[t,1,w] or I[r,t]      if v>w;
not X[r,1,v] or not X[t,1,w] or not I[r,t]  if v<w.
```

Here `X[r,c,v]` is the C39 cell literal. Exactly-one cell clauses force
`I[r,t]` to equal the inversion indicator `[q(r)>q(t)]`; Latin column
clauses exclude the omitted equality case. A Tseitin XOR chain enforces
the parity of all `I[r,t]` to be zero. Hence the overlay is satisfiable
exactly when `sign(q)=+1`. For a reduced square, column 0 is the
identity, so this is exactly the positive relative sign of columns
0 and 1. The four standard clauses for `z=x XOR y` make every chain
extension unique. This is an equisatisfiable, not merely necessary,
encoding of column-1 positivity for a fixed Latin table.

Applied separately to all **33** cases of C266, the overlay is a sound
necessary condition for FFF18. It is **not** sound to impose it on
C243's **14** longest-zero-cycle cases without a separate coverage proof.
The [companion preflight](../repro_runs/2026-09-28_fff18_column_parity_preflight/README.md)
checks the encoding on finite controls and records one bounded solver pilot.

## A three-sign strengthening is false

One might seek a reduced isotope in which row 1, column 1, and the
relative symbol-line pair `(0,1)` all have positive sign. In any such
isotope, let old rows `a,b` become rows `0,1`, old columns `x,y` become
columns `0,1`, and old symbols `s,t` become symbols `0,1`. Reduction
forces `s=L(a,x)`, `t=L(b,x)=L(a,y)`, and `y=(r_a^{-1}r_b)(x)`.
Equality of signs within a line pair is preserved under isotopy.
Consequently all three positive relative signs require

```text
row_sign(a) = row_sign(b),
col_sign(x) = col_sign(y),
sym_sign(s) = sym_sign(t).
```

This implication has an explicit FFF order-8 counterexample, the frozen
core representative on line `108473`:

```text
01234567
14326705
25607431
37065124
42573610
56410273
60751342
73142056
```

Direct inversion parity gives row signs `+ - + + + + - +`, column signs
`+ + + + - - - -`, and symbol-line signs `+ + - - - + - +`.
Of the 16 same-sign row pairs, 14 have at least one co-sign column
edge, but **none** of these edges joins same-sign symbol lines. The
remaining two row pairs have no co-sign column edge. The dated audit
records all 16 pair counts and independently scans all three views as
`FFF`. Therefore no isotopy of this table has the proposed three
simultaneously positive distinguished relative line pairs. This
finite counterexample does not rule out other cross-view constraints
or say anything negative about FFF18 existence.
