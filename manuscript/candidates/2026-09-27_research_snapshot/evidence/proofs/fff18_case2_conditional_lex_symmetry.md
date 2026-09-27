# Conditional lex leaders in the one-point complete-mapping family

**Scope.** This is a lossless existence reduction for the *full three-view*
FFF CNF of the translation-equivariant one-point family `Q_f` from C170.
It does not normalize arbitrary order-18 Latin squares and cannot by
itself decide whether an order-18 FFF square exists.

For prime `p`, let `f(0)=0` with both `f` and `f-id` permutations of
`F_p`. Write `F[t,z]` for the proposition `f(t)=z`; at nonzero `t`,
the allowed `z` are precisely the nonzero elements other than `t`.
The graph of `f` on those allowed pairs is transformed by

```text
T: (t,z) -> (-t,z-t),
I: (t,z) -> (z,t),
S_lambda: (t,z) -> (lambda*t,lambda*z), lambda != 0.
```

The first two operations are the transposition and right-division
parastrophes proved in [C170](fff18_parastrophe_scaling_normal_form.md),
and the third is a simultaneous scaling isomorphism. Their closure
is a finite group of bijections of the allowed pair set. Every element
maps the graph of a complete mapping to the graph of another complete
mapping and preserves the **FFF** property, though it may permute the
individual row, column and symbol views. An affine `f(t)=at` remains
affine under all three operations, so C170's affine-blocking clauses
are invariant as an existence restriction.

Fix a coefficient-orbit case `c` by requiring `f(1)=c`; the remaining
order-18 case uses `p=17,c=2`. For a group element `g`, the transformed
mapping `g(f)` also satisfies the anchor exactly when

```text
F[g^{-1}(1,c)] = true.
```

This is a single existing complete-mapping variable. Let `V(f)` be the
lexicographic vector `(f(1),...,f(p-1))` using the ordinary integer
representatives. Add the implication

```text
F[g^{-1}(1,c)] -> V(f) <=_lex V(g(f))
```

for every nonidentity group element `g` whose trigger is not already
incompatible with `f(1)=c`. This remains **equisatisfiable for FFF
existence** with the anchored full-view parent formula. To see this,
take any satisfying mapping `f`. Its finite orbit has at least one
member satisfying the anchor, namely `f`; choose the lexicographically
least anchored member `f_min`. All orbit members remain complete,
nonaffine when required, and FFF. For every `g` whose trigger is true
on `f_min`, `g(f_min)` is another anchored orbit member and cannot be
lexicographically smaller. Thus `f_min` satisfies every implication.
Conversely the overlay only adds constraints, so any overlay model
is a parent model. No uniqueness or Main-Class count is asserted.

## CNF correctness

Each `g(f)(i)=w` is exactly the parent literal `F[g^{-1}(i,w)]`.
For each eligible `g`, introduce prefix variables `P_i` meaning
`f(j)=g(f)(j)` for all `j<i`, with `P_1=true`. For every allowed
`v,w` at index `i`, enforce

```text
P_(i+1) -> P_i,
P_(i+1) and F[i,v] and G[i,w] -> (v=w),
P_i and F[i,v] and G[i,v] -> P_(i+1),
trigger and P_i and F[i,v] and G[i,w] -> (v<=w).
```

The second and third families make `P_(i+1)` equivalent to the prior
prefix being equal and the current values agreeing. The final family
forbids the first differing position from having `v>w`; positions
after the first difference have false prefix and impose no comparison.
The implementation emits these implications as ordinary clauses and
checks their truth conditions independently on *all* complete mappings
at `p=5,7`, plus a frozen positive FFF control. These finite checks
test the implementation, not the group-action proof.

The group action concerns all three views together. Applying the same
overlay to a row-only or row+column model would be unsound unless the
active view set were invariant under the chosen parastrophes. Any
Order-18 SAT model must still be decoded and scanned in all three
physical views. A timeout says nothing about existence; an UNSAT
claim needs a checked certificate for this exact, lossless overlay.

## Certified scoped consequence (C221)

The regenerated `p=17,c=2` nonaffine parent formula matches its frozen
SHA-256, and its conditional-lex overlay has SHA-256
`e3e199bacafd195bf612b0306dcb7e3e0d8aa853d0221c264bd63adbf823d17a`.
CaDiCaL reports UNSAT; `drat-trim` independently verifies the binary DRAT
against exactly that overlay (proof SHA-256
`51a460d865040ec2891485349381a7cd4a592a3f565448975a6d20edf27e8e8b`).
The [dated run](../repro_runs/2026-09-24_fff18_case2_lex_symmetry/README.md)
records commands, hashes, controls, and local artifact retention.

The C170 normal-form theorem covers every nonaffine FFF `Q_f` over `F_17`
by cases 2, 3, or 4. Case 2 is excluded by the new lossless overlay and
checked DRAT; cases 3 and 4 have earlier independently checked DRAT.
The exact affine scan checks the remaining 15 parameters and finds no
FFF instance. Therefore **no table in this translation-equivariant
one-point complete-mapping family is FFF at order 18**. This does not
exclude any order-18 table outside that family. In particular the
one-pairblock and all-primitive normalized-view branches remain open.
