# Prime-cyclic one-point prolongations: direction rigidity and three-view criterion

**Scope and dependency.** This theorem concerns *every transversal* of the
addition table of `F_p`, for an odd **prime** `p`, and its standard
one-point prolongation. It does not concern arbitrary order-`p+1`
Latin squares, noncyclic bases, or all one-point prolongations. The
rigidity step uses the established Rédei-Megyesi direction theorem:
`p` noncollinear points of `F_p^2` determine at least `(p+3)/2`
directions. We cite Gabor Somlai, *A new proof of Redei's theorem on
the number of directions* (2022),
[Theorem 1.1](https://arxiv.org/pdf/2212.12823v1), for this
established external result.
The cycle-splicing and affine-view calculations below are direct.

## Construction and Latin condition

Write the base addition table as `L(r,c)=r+c` on `F_p`, and let
`f:F_p -> F_p` select the cell `(r,f(r))` in each row. Put
`h(r)=r+f(r)`. The selected cells form a transversal if and only if
both `f` and `h` are permutations. Replace the symbol at each
selected cell by a new symbol `infinity`, move the removed symbol
`h(r)` into cell `(r,infinity)` and cell `(infinity,f(r))`, and set
`M(infinity,infinity)=infinity`. This is a Latin square of order
`p+1`: every old line loses one old symbol and gains `infinity`,
while the new row and column each contain every old symbol once.

## Exact old-row cycle formula

Take distinct old rows `r,s` and set `d=r-s`, `a=f(r)`, `b=f(s)`.
The original two-row permutation on old columns is the single
`p`-cycle `x -> x+d`. Since `f` and `h` are permutations,

```text
t = (b-a)/d in F_p has least representative 2,...,p-1.
```

Indeed `t=0` would give `f(r)=f(s)` and `t=1` would give
`h(r)=h(s)`. In the prolonged row-pair permutation, exactly the
following three arrows change:

```text
a       -> b                (instead of a+d)
b-d     -> infinity         (instead of b)
infinity -> a+d.
```

Index the original cycle by `a+i*d`, `i=0,...,p-1`. Then
`b=a+t*d` and `b-d=a+(t-1)*d`. The displayed rewiring splits
the old cycle and inserts `infinity` to give **exactly two** cycles
of lengths `t` and `p+1-t`. Both are even if and only if the
integer representative of `t` is even. This is an exact statement
about the pair of **old rows**; it says nothing yet about pairs
containing the new row.

## Rigidity

Suppose the entire row view of `M` is F. Then every old-row pair
satisfies the preceding even-`t` condition. The graph
`{(r,f(r)):r in F_p}` determines only secant slopes

```text
(f(s)-f(r))/(s-r) = -t in -{2,4,...,p-1}.
```

There are at most `(p-1)/2` such directions, and the graph has no
vertical direction. The cited Rédei-Megyesi theorem says a
noncollinear `p`-point set determines at least `(p+3)/2`
directions. Therefore the graph is a line:

```text
f(r)=a*r+b, with a not in {0,-1}.
```

The restrictions on `a` are exactly the permutation conditions on
`f` and `h`. This is a necessary conclusion from **row-F alone**,
not an assumption of translation equivariance. Translating old
columns and symbols by `-b` gives a pattern-preserving isotopy
to the case `b=0`.

## Exact affine three-view criterion

For `f(r)=a*r`, put `inv=1/a`, `k=a/(a+1)` in `F_p`. Write
`even(x)` for the least positive residue of `x` being even, and
`ord(x)` for its multiplicative order in `F_p^*`. The complete
view pattern is determined by:

| View is F iff | Old-old line pairs | New-old line pairs |
| --- | --- | --- |
| row | `even(-a)` | `ord((a+1)/a)` is even |
| column | `even(-inv)` | `ord(a+1)` is even |
| symbol | `even(k)` | `ord(-inv)` is even |

For the row view, the old-old test is the cycle formula above.
For the pair of rows `infinity,0`, the induced permutation is
`(0 infinity)` on those two columns and multiplication by
`(a+1)/a` on `F_p^*`; hence the order test. Simultaneous
translation of finite rows, columns and symbols sends any old
row to zero, so this one pair covers all new-old row pairs.

The column view is the same construction after swapping the old
row and column coordinates, which replaces `a` by `1/a`.
For the symbol view, use coordinates `(symbol s, column c, row r)`.
The unprolonged operation is `r=s-c`; replacing the column coordinate
by `c'=-c` makes it addition. Its selected transversal is
`c'= -a/(a+1) * s`, so the row-view formulas apply with
`a_sym=-a/(a+1)`. The resulting old-old and new-old expressions
are exactly `even(k)` and `ord(-1/a)` above. These coordinate
permutations preserve the relevant cycle lengths; they do not
assume the three views have identical patterns.

## Order 18 corollary

Let `p=17`. Every nonidentity element of `F_17^*`, a group of
order 16, has even order. The three order conditions in the table
are automatic for `a not in {0,-1}`. The row old-old parity requires
`a` odd; the column old-old parity then holds only for
`a=1,5,7`. For these values the symbol old-old residues are,
respectively,

```text
a=1: a/(a+1)=9;
a=5: a/(a+1)=15;
a=7: a/(a+1)=3 (mod 17).
```

All three are odd, so the symbol view is T. Consequently **no
standard one-point prolongation of the cyclic group table of order
17 along any transversal is FFF**. This is an analytic family
exclusion using an established finite-geometric theorem. It covers
cyclic-base prolongations without assuming C221's translation
equivariance. This corollary does not claim to subsume the `Q_f`
family. It remains a construction-family result, not a proof
that FFF18 does not exist. Neither originality nor an independent expert
review of this corollary is claimed.

## Separate finite certificate at p=17

The [dated companion](../repro_runs/2026-09-24_fff_prime_cyclic_one_point_direction/README.md)
independently scans every complete mapping for `p=3,5,7` and all
affine cases through `p=31`. It also builds a second, finite proof
route to the `p=17` rigidity step. A Boolean variable `F[r,c]` means
`f(r)=c`. Exactly-one clauses on rows, selected columns, and removed
symbols `r+c` encode the transversal condition. A unit fixes
`f(0)=0`, which is without loss under simultaneous translation of
old column and symbol labels. For each old-row pair `r<s` and each
candidate `a=f(r), b=f(s)` with odd or forbidden
`t=(b-a)/(r-s)`, the clause `not F[r,a] or not F[s,b]` removes that
assignment. Finally, for each eligible affine coefficient
`a=1,3,...,15`, one clause excludes the full assignment
`f(r)=a*r` for all `r`. Thus the formula is satisfiable exactly if
there is a **nonaffine** transversal whose **old-row** pairs are all
F; it does not encode the whole order-18 FFF condition.

The 289-variable/27,804-clause CNF has SHA-256
`263e28b45e9375b2fce243dc2534f6671321b5a2f7f6e0c1b69e64c6489f5c8a`.
CaDiCaL 3.0.0 reports UNSAT. Its 538,486-byte ASCII DRAT has SHA-256
`79e235fbe471dac0d48b60fd46c78a01ad4176db21828bf4630d9bf6e9fad3ec`;
`drat-trim` independently reports `s VERIFIED` for this exact pair.
Small exhaustive CNF truth tables and a physically scanned
`p=13,a=3` FFF-positive control guard the encoding. The cited
direction theorem gives the all-prime analytic rigidity; the CNF
only supplies a separate, proof-checked p=17 instance.
