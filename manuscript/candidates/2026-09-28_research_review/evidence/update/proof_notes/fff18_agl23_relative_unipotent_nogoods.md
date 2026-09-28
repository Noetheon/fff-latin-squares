# Relative unipotent exclusion in the AGL(2,3) pair-block model

**Scope.** This note concerns a complete normalized *one-view* row-F
family of 18 physical line permutations in the pair-block wreath product
`C2^9 : AGL(2,3)`. It is conditional on the independently checked C213
forced-selector UNSAT certificate. It neither excludes the whole AGL
family nor decides FFF existence at order 18.
The [projection-injectivity lemma](fff_pairblock_projection_injectivity.md)
ensures that the 18 selected quotient maps are distinct; thus the
selector-pair clauses below match the exact model rather than assuming
an unproved no-duplicate restriction.

## Rebasing lemma

Write the selected physical line permutations as `P_0,...,P_17` and
their induced block permutations as `phi_0,...,phi_17` in `AGL(2,3)`.
For any selected `P_a`, replace every physical line by

```text
                         Q_g = P_a^{-1} P_g.
```

This is a common relabelling of the *value* coordinate, followed if
necessary by a relabelling of the lines. The wreath product is a group,
so every `Q_g` remains in the same pair-block model. `Q_a` is the
identity, including its zero fibre voltage. For any two lines,

```text
                 Q_h^{-1} Q_g = P_h^{-1} P_g.
```

Thus sharp transitivity, Latinness and every physical relative-cycle
condition are unchanged. In particular, the rebased family is a
solution of the same normalized exact one-view row-F model whenever
the original family is. Its selected quotient maps are
`phi_a^{-1} phi_g`.

## Certified consequence

Let `U` be the 24-element affine conjugacy class with three fixed
points and nontrivial unipotent linear part. C213 rules out a solution
of the exact normalized row-F model selecting **any** member of `U`:
conjugate it to selector 6, whose base-plus-unit CNF has an
independently verified DRAT refutation. Applying the rebasing lemma
at any selected line `a` gives the necessary condition

```text
                phi_a^{-1} phi_b not in U       for all a != b.
```

This yields a valid pair-selector no-good `(-x_i or -x_j)` whenever
`MAPS[i]^{-1} MAPS[j]` belongs to `U`. Because `U` is inverse-closed,
the order of `i,j` does not matter. The [finite companion audit](../repro_runs/2026-09-28_fff18_agl23_relative_nogoods/README.md)
checks that precisely 5,184 of the `choose(432,2)` unordered pairs
have this property, that each map has 24 forbidden neighbours, and
that the 24 pairs incident to the identity recover C213's individual
selector exclusions. These no-goods apply to *full-family
completion*. They do not say that an isolated pair of physical lines
with such a quotient difference is itself impossible.

## Inverse-class reduction

The two irreducible fixed-point-one affine classes represented by
selectors 2 and 3 are exchanged by inversion. Their linear parts are

```text
             A_2 = [0 1; 1 1],       A_3 = [0 1; 1 2]
```

over `F_3`. Both have determinant 2 and irreducible characteristic
polynomial; their traces are 1 and 2. For an invertible two-by-two
matrix, `tr(A^{-1})=tr(A)/det(A)` and
`det(A^{-1})=det(A)^{-1}`. Thus `A_2^{-1}` has trace 2 and determinant
2, the same irreducible characteristic polynomial as `A_3`.
Two matrices of degree two with the same irreducible characteristic
polynomial are conjugate over `GL(2,3)`. Every affine map in either
class has a unique fixed point, so translation of that point to zero
reduces its affine conjugacy to the linear conjugacy. Inversion
therefore exchanges the two affine classes; the independent finite
enumeration checks this for all 54 maps in each class. If a
complete family selects class 2, rebasing at that selected map yields
the inverse map in class 3; conversely class 3 rebases to class 2.
Hence the two *existence cases* are equisatisfiable. Together with
the C213 exclusion of case 6, the seven-case cover has five
unresolved logical cases represented by selectors `1,2,4,5,32`.
This reduction does not solve any of those cases.

## Evidence boundary

The rebasing and inverse-class implications are mathematical. The
counts 24 and 5,184 are exact finite enumeration. Their contradiction
source is the specific C213 certificate for one complete one-view
model; no claim is made for arbitrary pair-block quotient groups,
primitive degree-18 view groups, or arbitrary FFF squares.
