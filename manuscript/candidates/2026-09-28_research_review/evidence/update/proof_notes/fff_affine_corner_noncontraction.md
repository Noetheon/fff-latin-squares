# The one-intercalate affine family has no two-point fixed-remainder contraction

## Statement

Let `p>=5` be prime, and let `a` be a nonzero element of `F_p` outside
`{-1,1,-2,-1/2}`. Let `Q'_a` be the order-`p+1` affine one-point
corner-traded Latin square of [C269](fff_affine_corner_trade_pattern.md).
Then its unique intercalate does **not** admit a fixed-remainder
contraction to a Latin square of order `p-1`. Consequently `Q'_a` is not
isotopic or parastrophic to a standard two-transversal prolongation of
any order-`p-1` Latin square.

This is a construction-family theorem. It does not rule out an FFF
square of order 18 or an extension method that changes retained cells.

## Proof

Write `infinity` for the added label and `b=(a+1)/a`. C269 proves that
the only intercalate of `Q'_a` is the corner with rows, columns and
symbols `{0,infinity}`. Delete these two rows, columns and symbols.
The retained rows and columns are indexed by `F_p^*`. Apart from the
four traded corner cells, the table agrees with `Q_a`.

For each `r in F_p^*`, the retained cell `(r,-r)` contains symbol `0`:
`-r != a*r` because `a != -1`. It is therefore a hole in the
contraction. The two values absent from retained row `r` after the
column deletion are

```text
R_r = {Q'_a(r,0), Q'_a(r,infinity)} = {r,(a+1)r}.
```

The two values absent from retained column `-r` after the row
deletion are

```text
C_-r = {Q'_a(0,-r), Q'_a(infinity,-r)} = {-r,-b*r}.
```

Any fixed-remainder Latin completion would have to fill `(r,-r)`
from `R_r intersect C_-r`. This intersection is empty. Indeed,
`r=-r` would require characteristic two; `(a+1)r=-r` requires
`a=-2`; `r=-b*r` requires `a=-1/2`; and
`(a+1)r=-b*r` would require `a=-1` because `a+1 != 0`.
All alternatives are excluded. There are `p-1` distinct such holes,
and one empty hole domain already makes a Latin contraction
impossible. The general hole-graph lemma in
[the contraction proof](fff_two_point_subsquare_contraction.md) gives
the same necessary row/column intersection condition.

Every standard two-transversal prolongation has an order-two Latin
corner on its two new rows, columns and symbols. Deleting that corner
and reversing the two transversals recovers the original square while
preserving every other old/old cell. If `Q'_a` were such a prolongation,
its unique intercalate would be that corner and the just-refuted
fixed-remainder contraction would exist. Isotopy and parastrophy
merely relabel or permute the three coordinates, preserving the
intercalate and existence of this contraction. This proves the claim.

## Infinite FFF consequence and evidence boundary

[C270](fff_affine_corner_trade_pattern.md) combines C165 with C269
to give an FFF `Q'_a` with generic `a` for every prime `p>=10^12`.
Hence every such order `p+1` has a **non-group-isotopic FFF** table
with one intercalate that cannot be obtained by a standard
two-transversal prolongation from order `p-1`. This conclusion is a
deduction from the internally audited C165 analytic estimate, not a
physical scan of enormous tables or an external literature-priority
claim. The [dated finite control](../repro_runs/2026-09-28_affine_corner_noncontraction/README.md)
checks the exact hole domains of the frozen order-14 and order-20
examples and smaller generated generic cases. The proof, not those
finite tests, establishes the general statement.
