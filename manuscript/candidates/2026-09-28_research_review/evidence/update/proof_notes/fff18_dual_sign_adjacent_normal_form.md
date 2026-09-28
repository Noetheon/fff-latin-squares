# A simultaneous row/column sign normal form

**Evidence boundary.** The statements below are elementary, source-independent
isotopy results. They do not construct or exclude an FFF Latin square of order
18. The finite checks in the [companion run](../repro_runs/2026-09-28_fff18_dual_sign_normal_form/README.md)
test the implementation, not the proof.

Let `L:R x C -> S` be a Latin square of order `n>=5`. Write `r_a:C->S`
for its row maps and `c_x:R->S` for its column maps. Set
`rho(a)=sign(r_a)` and `chi(x)=sign(c_x)`, using any fixed labellings of
the three sorts. Equality of two row signs, or of two column signs, is
independent of those labellings.

## Co-sign edge lemma

**Lemma (rigorously proved).** Among any three rows of the same sign there
are two distinct rows `a,b` and a column `x` such that, with
`phi=r_a^{-1} r_b`, the columns `x` and `phi(x)` have the same sign.

**Proof.** Call a row pair `a,b` *flipping* if
`chi(phi(x))=-chi(x)` for every `x in C`. If both `a,b` and `b,c` are
flipping, then `r_a^{-1}r_c=(r_a^{-1}r_b)(r_b^{-1}r_c)` preserves `chi`.
It cannot also be flipping. Thus the flipping graph on any set of
same-sign rows has no triangle. Among three such rows, some pair is
nonflipping. For that pair, some column `x` satisfies
`chi(phi(x))=chi(x)`. The rows differ, so Latinness makes `phi`
fixed-point-free and `x != phi(x)`. `QED`

The same argument gives a quantitative bound. If a row-sign class has
`k` elements, its flipping graph has at most `floor(k^2/4)` edges.
Indeed, for every edge `uv` of a triangle-free graph,
`deg(u)+deg(v)<=k`. Summing and applying Cauchy--Schwarz yields
`4E^2/k <= sum_v deg(v)^2 <= kE`. Hence at least
`binom(k,2)-floor(k^2/4)` same-sign row pairs admit a co-sign
adjacent column pair. For `n=18`, a row-sign class has at least nine
members, so at least **16** such pairs exist. This is a selection
count, not an FFF existence count.

## Reduced isotope with two positive lines

**Theorem (rigorously proved).** Every row-F and column-F Latin square
of even order `n>=6` is isotopic to a reduced square for which both
row 1 and column 1 are even-cycle derangements of positive sign.
This applies in particular to every hypothetical FFF square of order 18.

**Proof.** One row-sign class has at least `ceil(n/2)>=3` members.
Choose `a,b,x` by the lemma and put `y=phi(x)`. Relabel the columns
by a bijection `kappa` with `kappa(x)=0`, `kappa(y)=1`. We may order
the cycles of `phi` so that `kappa phi kappa^{-1}` is a canonical
even-cycle permutation beginning `0 -> 1`; the cycle containing `x`
need not be a longest cycle. Define the symbol relabelling
`sigma=kappa r_a^{-1}` and the row relabelling
`alpha(r)=sigma(L(r,x))`. Both are bijections. Then

```text
L'(alpha(r), kappa(c)) = sigma(L(r,c))
```

is Latin, has `L'(0,j)=j` and `L'(i,0)=i`, and satisfies
`alpha(a)=0`, `alpha(b)=1`. Its row 1 is
`kappa phi kappa^{-1}`. Because `rho(a)=rho(b)`, this permutation
has positive sign. Since the original row view is F, all its cycles
are even, and Latinness rules out fixed points.

Columns 0 and 1 of `L'` come from old columns `x,y`.
The same left symbol relabelling and right row relabelling multiply
every column sign by one common factor. Their signs therefore remain
equal. Column 0 is the identity, so column 1 has positive sign.
Column-F makes its fixed-point-free relative permutation to column 0
even-cycled. Finally, isotopy preserves the full three-view pattern
(C03), so FFF remains FFF. `QED`

## Exact order-18 search implication and limit

An even-cycle permutation of degree 18 has positive sign exactly when
it has an even number of cycles. There are 14 such even-cycle
partitions. If `0` is allowed to lie in **any distinct cycle length**,
these give **33** canonical row-1 cases. The theorem shows that a
complete unrestricted order-18 FFF search may use those 33 cases and
add the positive-sign condition on column 1 in every case. No case is
excluded by this note. A SAT encoding of column-1 parity still needs
an independent clause-level check and positive controls.

C243 has a different, smaller **14-case** split: it chooses `0` in a
longest row-1 cycle. The proof here does **not** show that the selected
co-sign adjacent edge lies in a longest cycle. Therefore one must not
add `column 1 positive` to C243's 14 cases without a separate theorem.
Finite controls where such an edge happens to exist in a longest cycle
do not establish that theorem for arbitrary order 18. The 33-case
alternative trades a larger case list for a second sign constraint;
whether this helps solving is unmeasured.

As a guard against silently conflating the two normal forms, the
companion run replays C243's existing deterministic normalizer on all
936 reduced order-6 row+column-F controls. It produces a negative
column-1 sign in 420 cases. This does **not** show that another
longest-cycle choice cannot work; it shows that appending a positive
column-1 constraint to those already emitted representatives is
invalid without a separate coverage proof.
