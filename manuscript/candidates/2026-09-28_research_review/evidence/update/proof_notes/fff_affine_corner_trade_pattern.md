# Affine one-point corner trade preserves the three-view FFF pattern

## Statement and scope

Let `p` be an odd prime, `a in F_p \ {0,-1}`, and write `infinity` for a
new element. Define the affine one-point prolongation `Q_a` of addition on
`F_p` by

```text
Q_a(r,c) = infinity                 if r,c are finite and c = a*r,
         = r+c                      if r,c are finite and c != a*r,
Q_a(r,infinity) = (a+1)*r,
Q_a(infinity,c) = ((a+1)/a)*c,
Q_a(infinity,infinity) = infinity.
```

Its cells on rows `0,infinity` and columns `0,infinity` are an
intercalate. Let `Q'_a` exchange the two entries in each of those two rows
at columns `0,infinity`. Then

1. `Q'_a` is Latin and `pat(Q'_a) = pat(Q_a)` in the row, column, and
   symbol views, for every admissible `p,a`.
2. If `p >= 5` and `a` is outside `{1,-2,-1/2}` in `F_p`, then `Q_a`
   has exactly `p` intercalates and `Q'_a` has exactly **one**.
3. Consequently, whenever such a generic `Q_a` is FFF, the traded table
   is another FFF table in a different main class. The intercalate count
   is invariant under row/column/symbol relabeling and parastrophy.

The theorem concerns this affine construction and this one corner trade,
not arbitrary intercalate trades or arbitrary order-18 Latin squares.

## Row-view cycle proof

Put `b=(a+1)/a` and `d=ord_p(b)`. For two rows use the relative column
permutation `P_(u,v)=R_v^{-1} R_u`. Every `P_(u,v)` is fixed-point-free.
The affine translations

```text
(r,c,s) -> (r+t, c+a*t, s+(a+1)*t)
```

fix `infinity` and preserve `Q_a`, so all distinct finite-finite row
pairs have the same cycle type. For `(0,t)`, `t != 0`, divide finite
column coordinates by `t`. The relative permutation is

```text
0 -> a, infinity -> -1,
x -> x-1 for x != 0,a+1, and a+1 -> infinity.
```

Thus its two cycles have lengths `a_0+1` and `p-a_0`, where `a_0` is
the integer representative of `a` in `{1,...,p-2}`. The first contains
`0`; the second contains `infinity`.

For `(infinity,t)`, `t != 0`, the finite part away from the exceptional
coordinate `a*t` is `x -> b*x-t`. This affine map has fixed point
`a*t`; the prolongation replaces that fixed point by the 2-cycle
`(a*t,infinity)`. Translation by `-a*t` conjugates the rest to
multiplication by `b` on `F_p^*`. Its other cycles therefore have
length `d`. The point `0` belongs to one of these `d`-cycles, since
`a*t != 0`. The pair `(infinity,0)` has the same cycle type by the
displayed affine translations.

Let `tau=(0,infinity)` act on the column positions. In `Q'_a`, only
rows `0` and `infinity` are changed, each by precomposing its row map
with `tau`. For the pair `(0,infinity)` the relative permutation is
conjugate to the old one, so its cycle type is unchanged. For
`(0,t)`, `t != 0`, the relative permutation is `P_(0,t) tau`.
The transposition joins the two even-or-odd cycles containing `0` and
`infinity` into one `(p+1)`-cycle. For `(infinity,t)`, `t != 0`, it joins
the 2-cycle containing `infinity` to the separate `d`-cycle containing
`0`, giving lengths `d+2` and `d` repeated `(p-1)/d-1` times. Pairs
of nonzero finite rows are unchanged.

Therefore the row view of the traded table is F exactly when both
`a_0+1` and `p-a_0` are even and `d` is even. Necessity is witnessed
by any unchanged pair of distinct nonzero finite rows and by
`(infinity,0)`. Sufficiency follows from the complete pair partition
above. These are also exactly the row-F conditions for `Q_a`. In
particular the joined `(p+1)`-cycle cannot by itself repair a failed
row view.

## Column and symbol views

Transposition gives **exactly** `Q_a^T = Q_(a^{-1})`: the selected
finite cell condition becomes `r=a^{-1}c`, and the new-row/new-column
formulas agree. The corner intercalate is fixed by this coordinate
swap, hence `(Q'_a)^T = Q'_(a^{-1})`. The row proof applies to the
column view.

For the symbol view, take symbols as lines, columns as positions, and
rows as values. Relabel the finite column coordinate by `c'=-c`,
fixing `infinity`. The resulting Latin operation is exactly

```text
Q_(a_sym),  where a_sym = -a/(a+1).
```

Indeed the finite selected cell for symbol `s` is at
`c'=-a*s/(a+1)`; its new-column value is `s/(a+1)`, and the
new-row value at finite `c'` is `-c'/a`. These are the three defining
formulas with coefficient `a_sym`. The corner intercalate again maps
to the corner intercalate. Thus the symbol view of `Q'_a` is the
corresponding `Q'_(a_sym)`, and the row proof applies a third time.
This establishes the componentwise pattern equality, not merely FFF
preservation.

## Exact intercalate count

A 2-cycle in a relative row permutation corresponds to one
intercalate, counted once by its row pair. In `Q_a`, every one of the
`p` finite/infinity row pairs has its distinguished 2-cycle.
An additional 2-cycle in such a pair occurs exactly if `d=2`, that
is, if `b=-1` or `a=-1/2`. A finite-finite row pair has a 2-cycle
exactly if `a_0+1=2` or `p-a_0=2`, equivalently `a=1` or `a=-2`.
For a generic coefficient none of these occurs, so `I(Q_a)=p`.

After the trade, nonzero finite-finite row pairs have the old type;
`(0,t)` has the single `(p+1)`-cycle; `(infinity,t)` has the cycle
lengths `d+2,d,...,d`; and `(0,infinity)` retains exactly its one
distinguished 2-cycle. For generic `a`, neither an old finite-finite
pair nor a `d`-cycle contributes a 2-cycle. Hence `I(Q'_a)=1`.
The remaining intercalate is physically the same four corner cells.

## Consequences and evidence boundary

The C225 affine criterion shows that `p=13,a=3` is FFF; the same
arithmetic or a full direct scan gives `p=19,a=7` FFF. Both coefficients
are generic, so each traded square is FFF with one intercalate. The
dated [finite control](../repro_runs/2026-09-28_affine_corner_trade/README.md)
independently scans the two traded tables in all three views and
checks the cycle formulas over small primes. This finite validation
is secondary to the proof above.

There is also an **infinite existence corollary**, conditional on the
already proved C165 large-prime parameter bound. C165 uses the loop
notation `x*y=alpha*x+(1-alpha)*y` away from the diagonal, with
`alpha not in {0,1}`. The isotopy from our `Q_a` to that loop is

```text
x=(a+1)*r,  y=((a+1)/a)*c,  symbol labels unchanged,
alpha=1/(a+1),  1-alpha=a/(a+1).
```

It fixes `infinity` and sends the selected cell `c=a*r` to the
diagonal `x=y`. Thus the parameter correspondence
`a=(1-alpha)/alpha` is a bijection. C165 proves that for **every
prime `p>=10^12`**, more than `p/1000` such parameters give FFF.
Only the three coefficients `{1,-2,-1/2}` are excluded from the
one-intercalate conclusion. Since `p/1000>3`, at least one FFF
parameter is generic. Hence every prime `p>=10^12` admits an FFF
Latin square of order `p+1` with exactly one intercalate. There are
infinitely many such orders by Euclid's theorem. This is a deduction
from C165 and the present trade theorem, **not** a physical scan of
tables of those sizes.

Every one-intercalate even-order example here is also
non-group-isotopic. A group table of even order `n` with `t` nonidentity
involutions has exactly `t*n^2/4` intercalates: each involution gives
`n/2` unordered row pairs, and each such pair gives `n/2` 2-cycles.
Here `t>=1` in even order: all non-self-inverse elements pair with
their inverses, so the identity cannot be the sole self-inverse
element. Since `n>=4`, this count cannot equal one. Intercalate number is
isotopy invariant. We do not infer simplicity, a main-class census, or
a least possible order from this observation.

At `p=17` the C225 affine criterion excludes every `a`; pattern
preservation also excludes every **traded affine corner table**.
This says nothing about other order-18 constructions or the
unrestricted existence question. No literature priority or external
human review is asserted. The older C252 lower bound can be raised
only after the new order-20 spectrum is compared to all 1,702
previously certified representatives; that comparison belongs to
the dated run, not to an assumption in this proof.
