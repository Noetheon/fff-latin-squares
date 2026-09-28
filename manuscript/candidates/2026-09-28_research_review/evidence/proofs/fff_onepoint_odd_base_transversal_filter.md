# Odd-cycle filter for one-point transversal prolongations

## Status and scope

The lemma and the old/old line-pair encoding below are direct proofs for
every odd-order Latin base. They are necessary conditions for an FFF
one-point prolongation, not a characterization of FFF and not an order-18
existence or nonexistence result. The companion computation tests a specified
translation-equivariant order-17 base family and arbitrary transversals of
each selected base. It does not cover arbitrary order-17 bases or arbitrary
order-18 squares.

## Standard prolongation

Let `B` be a Latin square of odd order `m`, and let `T` be a transversal.
For each selected cell `(r,c)` with old symbol `s=B(r,c)`, replace `s` by
a new symbol `infinity`, put `s` in `(r,infinity)` and `(infinity,c)`,
and set the new corner to `infinity`. The resulting square `P` has order
`m+1` and is Latin. Row, column and symbol parastrophes of this operation
are again one-point prolongations along the corresponding transversal.

## Two-cut lemma

Fix any one of the three views and two distinct old lines `a,b`. Regard
their maps from old positions to old values as `l_a,l_b`, and put
`pi=l_b^{-1} l_a`. Let `A` and `Bpos` be the selected old positions in
the two lines, and put `D=pi^{-1}(Bpos)`. Distinct transversal values
imply `A != D`. The relative permutation `pi_prime` after prolongation
has precisely these changed arrows:

```
A        -> Bpos       instead of A -> pi(A)
D        -> infinity   instead of D -> Bpos
infinity -> pi(A)
```

All other old arrows are unchanged. Therefore only the at most two
cycles containing `A` and `D` can change. In particular, every odd
cycle of `pi` disjoint from these two vertices survives as an odd cycle
of `pi_prime`.

Because `pi` acts without fixed points on an odd set, it has an odd
number of odd cycles and at least one. If it had three or more odd
cycles, two changed old arrows could not meet all of them. Hence:

> **Necessary three-view condition.** If the one-point prolongation is
> FFF, then *every* old two-line permutation of the odd base has
> **exactly one odd cycle**, separately in its row, column and symbol
> views.

The condition is not sufficient. Even when there is exactly one odd
base cycle, the selected positions may reconnect it into an odd cycle;
new/old line pairs in the prolonged square must also be checked.

## Exact old/old SAT projection

For each old cell, `X[r,c]` means that the transversal selects it.
Exactly-one constraints for every old row, column and symbol encode
precisely the transversals of `B`. For each view and each pair of old
lines, test every pair of selected cells on those lines by the three
arrows above. If its prolonged relative permutation has an odd cycle,
add the binary clause `not X[cell_a] or not X[cell_b]`.

For a fixed complete transversal, these clauses hold **if and only if**
all old/old line pairs in all three views are F. This is an exact
projection, not a relaxation of those particular pairs. It omits
the new/old line pairs; a SAT transversal must be prolonged and scanned
independently in all three physical views before any FFF claim. An
UNSAT result excludes an FFF one-point prolongation of that *fixed*
base, but must have a checkable solver certificate before promotion.

## Finite experiment boundary

The frozen odd-complete-mapping enumerator at
`repro_runs/2026-09-23_fff18_orthomorphism_probe/` generates
translation-equivariant order-17 bases

```
B_f(x,y) = x + f(y-x) mod 17,
```

where `f(0)=0`, `f` and `f-id` are permutations, and
`f(-t)=-f(t)`. A filter of this finite family can identify bases for
which the necessary three-view condition is not immediately false.
Any SAT/UNSAT experiment that follows concerns only this family and
arbitrary transversals of its selected members. It cannot decide FFF
existence at order 18 outside the stated construction.

## Certified finite-family corollary at order 18

Within the stated **odd translation-equivariant** family, no choice of
one-point transversal gives an FFF square of order 18.

Here is the exhaustive, evidence-labelled argument. The frozen enumerator
produces exactly `12,513` odd complete mappings; the new run reproduces
its complete-mapping count and coefficient-stream SHA-256. The direct
three-view UOC filter rejects `12,450` of them by the two-cut lemma.
For the `63` survivors, a second full-pair check confirms that the eight
translation representatives per view covered every old line pair.
There are `15` affine and `48` nonaffine survivors.

For an affine survivor `f(t)=a*t`, the base operation is

```
B_f(x,y) = (1-a)*x + a*y.
```

Both coefficients are nonzero. Independent relabellings
`x -> (1-a)*x`, `y -> a*y` turn this base into addition on `F_17`.
Extending those relabellings by fixing `infinity` carries every
transversal prolongation to a standard one-point prolongation of the
cyclic group table along an arbitrary transversal. C225 rigorously
excludes FFF for every such table at order 18.

For each of the `48` nonaffine survivors, the exact old/old three-view
CNF is UNSAT. CaDiCaL 3.0.0 generated an individual ASCII DRAT trace
for each SHA-pinned CNF, and `drat-trim` independently reported
`VERIFIED` on all `48`. The formulas have `289` variables and three
distinct clause counts: `51,187` (`24` cases), `46,563` (`12`), and
`36,771` (`12`). This is a finite certified result, not a purely
symbolic proof of a universal property of all order-17 bases. An
independent implementation of the two-cut permutation compared
`312,120` compatible selected-cell pairs across representatives of
all three CNF-size profiles with zero mismatch. Exhaustive order-3
and order-5 transversal truth tables, a frozen FFF14 positive
prolongation, and a `C3 x C3` negative base check the encoding boundary.

The seven C170 parastrophe/scaling orbits among the `63` survivors
provide a redundant coverage audit: their nonaffine sizes are
`6,24,6,12` and their affine sizes `3,6,6`. The individual `48`
checked proofs do **not** depend on orbit reduction.

This corollary excludes arbitrary transversals only for the listed
`12,513` **odd** `Q_f` bases. It says nothing about nonodd complete
mappings, nontranslation-equivariant order-17 bases, other order-18
constructions, or arbitrary FFF order-18 existence. The large proof
traces remain outside Git under `.audit/local/`; the companion report
records their bytes, paths, SHA-256 hashes and regeneration/checking
commands. Small traces are retained in the run package.
