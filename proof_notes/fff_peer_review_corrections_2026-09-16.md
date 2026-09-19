# September 2026 peer-review corrections and scope

This dated companion supersedes only the statements identified below in the
historical notes. Frozen notes, computations and their hashes are not rewritten.
The current manuscript and claim register carry the corrected formulations.
The [countercheck package](../repro_runs/2026-09-16_peer_review_counterchecks/README.md)
contains independently written small exact checks, not a repeat of the census
or the order-10 master searches.

## Rank and Schur domains (C75/C76)

For the ordinary inverse-based Schur statements assume **n > 3**. The cell
Gram has eigenvalues `9(n-1)`, `5n-9`, and `3(n-3)` on the
constant, line and orthogonal cell subspaces, respectively; it is invertible
in that domain. The labelled-pair rank theorem is now uniformly stated for
n > 3. Its unsigned complete-graph incidence decomposition needs n >= 3.

At n=2 the pair Gram is `K=2 J_3`, of rank 1, while the cycle-space restriction
has rank zero. Thus the former unrestricted formula `rank(K)=3n-2+rank(C)`
is false. At n=3 the ordinary cell Gram is singular. The fresh C3 control
does satisfy the *orthogonal-projection* Schur rank identity; that control
is not a counterexample to this separate projection formulation.

## Tensor fibres and reconstruction (C78)

The pair-label tensor counts flags, so its two-coordinate marginals equal
`2W`, not W. The nonempty fibres are `[1,1]` and `[4]`, giving marginal sums
2 and 4. A marginal sum zero means an empty fibre. In C3, row pair {0,1}
and column pair {0,2} have two distinct unit completions and sum 2.
The reconstruction theorem explicitly requires n >= 3, where the action
on unordered pairs is faithful. At n=2 the two coordinate-labelled Latin
tables yield the same singleton tensor of value 4.

## Mask conventions and zero values (C87/C92)

Literal tuples are always `(R,C,S)`. Integer codes use `R+2C+4S`; consequently
tuple 011 has code 6, 101 has code 5, and 110 has code 3. For an intercalate
with cells ordered top-left, top-right, bottom-left, bottom-right, the
respective pushforwards, up to common sign, are

| Tuple | Integer | Vector | Zero line marginals |
| --- | --- | --- | --- |
| 011 | 6 | (1,1,-1,-1) | columns, symbols |
| 101 | 5 | (-1,1,-1,1) | rows, symbols |
| 110 | 3 | (1,-1,-1,1) | rows, columns |

The historical integer-coded computations and formulas using 3,5,6 do not
change. They must not be read as literal RCS tuples.

A formal monomial transforms with the character given by the sum of its
mask charges. That character is trivial iff the sum is zero: a nonzero
linear character has some gauge on which it equals -1. For an evaluated
monomial, invariance is equivalent to **zero charge or identically zero
value**. Indeed a nontrivial character negates it, so invariance forces the
whole value to vanish over the characteristic-zero coefficient field.
The C4 component of 32 flags has exact mask 111 with zero cell pushforward,
exhibiting the exception. The invariant cubic of charges 3,5,6 is unchanged.

## One F view implies order-2p congruence simplicity (C43, rigorous)

Let p be an odd prime and suppose at least one view is F. A proper nontrivial
quasigroup congruence has equal block sizes dividing 2p, so its
(block size, quotient order) is either (p,2) or (2,p). In the first case
C42's odd-block argument forces TTT. In the second the odd-order quotient
is TTT by C35, and C42's binary-block pattern equality again forces TTT.
Both contradict even one F view. C03 preserves the full pattern under
isotopy, so every isotope is congruence-simple. No enumeration is needed.

## Universal opposite-component bound (C96/C98, rigorous)

Take a nonempty connected flag component and its normalized cell-companion
triangles. Label every normalized vertex by its component in the graph
joining the two opposite vertices across each glued triangle edge.
Across that edge two corners are shared, while the opposite corners have
the same label. Thus the multiset of three labels on a triangle is unchanged
across every dual adjacency. Connectedness makes it constant on every
triangle. Every normalized vertex occurs in a triangle; hence the total
number of labels q is between 1 and 3.

Forgetting sheets maps every opposite edge to a coarse opposite edge and
surjects onto all used cells. It can merge, not split, connected components.
Thus **1 <= p <= q <= 3**. This argument does not assume FFF. It does not
assert p=q, or classify any finite-corpus multiplicities.

## Order-10 and engineering scope

The [master reduction](fff_six_type_master_reduction_degree10.md) remains
the source for the exhaustive mathematical bridge. The manuscript now
places its result, candidate/edge definitions, partial injective maps,
sound closed-cycle pruning, transversal DFS and orbit coverage together.
The primitive-group theorem is a separate reduction, not an additional
filter on the two master graphs.

The frozen task parser compared an ordinal against a stored vertex ID.
The successor fixes that generic defect. Fresh reads of the two fully
SHA-verified graph files establish that the selected first bucket has
`tasks[i]=i` throughout in both actual master runs; all 506 and 386
representatives are accepted and unchanged by the correction. This proves
non-impact of **this bug**, not independent correctness of every DFS step.

The historical master commands target the documented macOS/Apple Silicon
environment (`/usr/bin/clang++`, `-mcpu=apple-m4`, `/usr/bin/time -l`).
Path configurability is not cross-platform portability. The small successor
parser harness uses ordinary C++17; the full successor compiles as C++20
without Apple-specific architecture flags. No new exhaustive run was made.

The external review's separate computational ZIP was not supplied locally.
Its claimed large independent checks remain external assertions pending
receipt, inspection and reproduction. C157's recorded A+B evidence status
is unchanged; C38 is globally open, and C40 remains unused. This correction
is a review candidate, not public release authorization or certification.
