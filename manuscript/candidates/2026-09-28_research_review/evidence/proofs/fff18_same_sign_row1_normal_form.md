# A same-sign row-1 normal form for unrestricted order-18 FFF searches

**Status.** The reduction below is rigorous. It applies to every Latin square
whose row view is F, not to a selected construction family. It is a lossless
symmetry break for an eventual exact order-18 existence model. It does not
settle existence, exclude any of the retained cases, or supply a solver
certificate. The finite companion checks the case enumeration and the
isotopy on independently validated small positive controls.

## Same-sign row anchor

Let `L:R x C -> S` be Latin of even order `n>=4`. For a row `r`, let
`rho_r:C -> S` be its line permutation under arbitrary fixed labelings.
There are only two signs, so two distinct rows `a,b` have the same sign.
Equivalently, the relative permutation

```text
phi = rho_a^(-1) rho_b : C -> C
```

has sign `+1`. Its sign is independent of the chosen column and symbol
labels: an isotopy conjugates `phi`, while an inverse changes neither sign
nor cycle lengths. If the row view is F, `phi` has only even cycles; it
has no fixed point because distinct Latin rows cannot agree in a column.

Choose `c0` in a **longest cycle** of `phi`. This is allowed because
the first column has not yet been fixed in an unrestricted existence
question. Write `c0,phi(c0),...,phi^(d-1)(c0)` for its cycle. Choose a
column bijection `kappa:C -> {0,...,n-1}` that sends those
points, in that order, to `0,1,...,d-1`, and sends each other cycle in
its cyclic order to a consecutive canonical interval. Sort the remaining
cycles by decreasing length. Put

```text
sigma = kappa rho_a^(-1) : S -> {0,...,n-1},
alpha(r) = sigma(L(r,c0)) : R -> {0,...,n-1},
L'(alpha(r), kappa(c)) = sigma(L(r,c)).
```

The maps are bijections, since row `a` and column `c0` are Latin lines.
Also `alpha(a)=0` and

```text
alpha(b) = kappa(phi(c0)) = 1.
```

The square `L'` is reduced: its first row is the identity because
`sigma rho_a=kappa`, and its first column is the identity by the
definition of `alpha`. Its row 1 is exactly `kappa phi kappa^(-1)`.
Thus row 1 has the same cycle partition as `phi`, with the cycle
containing zero oriented `0 -> 1 -> ...`. This is an ordinary isotopy,
so the complete row/column/symbol witness pattern is unchanged by C03.
No automorphism, transitivity, intercalate, group isotopy, or special
prolongation is assumed.

Conversely, any reduced FFF square satisfying one of the resulting
row-1 cases is an unrestricted FFF square. The finite split is therefore
an equivalence of existence questions, not merely a necessary screen.

## Order-18 case count

For `n=18`, all cycles of row 1 have even length. Such partitions are
twice the ordinary partitions of nine, giving 30 partitions. If there
are `t` cycles, then

```text
sgn(phi)=(-1)^(18-t)=(-1)^t.
```

Our same-sign choice requires `t` even. Exactly 14 of the 30 even-part
partitions satisfy this condition:

```text
16+2                 14+4                 12+6
12+2+2+2             10+8                 10+4+2+2
8+6+2+2              8+4+4+2              8+2+2+2+2+2
6+6+4+2              6+4+4+4              6+4+2+2+2+2
4+4+4+2+2+2          4+2+2+2+2+2+2+2
```

If a first column `c0` is already fixed, one must retain every distinct
possible zero-cycle length. That gives 67 canonical cases for all
even-cycle partitions, or 33 after the same-sign choice. For **unrestricted
existence**, however, `c0` may be chosen *before* reduction in a longest
cycle. The zero-cycle length is then determined by the partition and
there are only **14 cases**, one for each displayed sign-positive
partition. This removes 53 of the 67 cases of the usual fixed-first-
column split. It does not assert that any retained case is realized.
The free-column step is invalid if a separate model has already pinned
source cells, a transversal, or a distinguished first column and has not
proved that its anchors can be transported with the isotopy.

The [dated generator and controls](../repro_runs/2026-09-26_fff18_same_sign_row1_split/README.md)
produce all 14 permutations and verify the normalization on frozen
FFF tables of orders 14 and 98. A complete reduced order-6 generator
provides a smaller row-F, non-FFF boundary control. The fixed
order-98 and order-14 inputs are not evidence for order-18 existence.

## Use and limitation

An exact full-view order-18 CNF may be split into these 14 cases only if
its table variables, row-1 units, Latin/reduced constraints and all three
view constraints are themselves proved equivalent to FFF. A SAT model
still requires an independent physical three-view scan. To establish
nonexistence by this split, *every* case needs a sound terminal UNSAT
result and a checkable certificate or an alternative rigorous exclusion.
Timeouts and a sample of cases have no global force. The existing C39
encoding is a possible base, but no full 14-case solver portfolio is
started here.
