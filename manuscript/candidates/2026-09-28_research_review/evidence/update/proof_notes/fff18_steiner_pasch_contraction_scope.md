# One-Pasch Steiner parents and fixed-remainder contraction

**Scope.** This note combines a general theorem about principal contractions
of Steiner loops with finite construction-family screens. Neither decides
arbitrary FFF Latin squares of order 18. The known FFF order-20 Steiner loop
comes from a 57-block Steiner triple system on 19 nonidentity points. A
Pasch trade replaces four triples on six points by the other four triples
covering the same twelve pairs, preserving the Steiner property.

## General principal-contraction obstruction (C259)

Let `S` be any Steiner loop of order `n` with identity `e`, and fix
`x != e`. Here Steiner loop means the commutative loop with
`r*r=e` and `r*(r*s)=s` for all `r,s`. Its principal order-two
subsquare uses rows, columns, and
symbols `{e,x}`. Delete all three pairs and preserve every other cell.
On the remaining set `U=S\{e,x}`, multiplication by `x` is a
fixed-point-free involution: `x*(x*r)=r`, and `x*r=r` would contradict
Latin cancellation. Write `r'=x*r`.

In retained row `r`, deletion of columns `e,x` removes precisely the
symbols `r,r'`. The erased cells are `(r,r)` and `(r,r')`, since
`r*r=e` and `r*r'=x`. Similarly, the two holes in column `r` are
`(r,r)` and `(r',r)`. Thus every pair `{r,r'}` forms one isolated
`2 x 2` hole component. Both rows and both columns of that component
are missing exactly the symbols `{r,r'}`. Its only two Latin fillings
are

```text
    r  r'       r' r
    r' r   or  r  r'
```

and both are symmetric. Every unchanged cell is symmetric because `S`
is commutative. Consequently **every** fixed-remainder Latin
completion of a principal deletion is symmetric, without assuming
that the parent is FFF. If `n=0 (mod 4)` and `n>=8`, the output has
order `n-2=2 (mod 4)` and at least six points, so C177 gives a
symbol-view odd-cycle witness. No such completion is FFF.

The lower boundary is necessary: at parent order four, a principal
contraction has order two and may be FFF. The proof says nothing about
nonprincipal intercalates, non-Steiner parents or changes to retained
cells.

Nor can every nonprincipal case be dismissed by isotopy to a symmetric
square. There is an exact small recognition test. Fix a row `r0` of an
order-`m` Latin table `T`. A column relabelling `f` makes
`T(r,f(s))` symmetric only if, for `c0=f(r0)`,

```text
f(s) = inverse(T[r0,*])[T[s,c0]]  for every row s.
```

Conversely each `c0` gives a bijection `f` by Latinness, and checking
`T(r,f(s))=T(s,f(r))` for all `r,s` is sufficient. Arbitrary row and
symbol relabellings do not enlarge this class: absorb the row
relabelling into the row index and note that symbol relabelling
preserves equality. Thus at most `m` candidate maps decide whether `T`
has a symmetric isotope. The [physical countercontrol](../repro_runs/2026-09-27_fff18_steiner_pasch_contraction/results/symmetrization_boundary_summary.txt)
checks all 18 maps for one nonprincipal completion from a one-Pasch
neighbor of `C2 x Steiner10`; none works. An untraded-source completion
passes as a positive control. The nonsymmetrizable output nevertheless
has a direct odd row cycle, so it is **not** an FFF18 example. This
counterexample prevents extending C259 to all nonprincipal deletions
by an unproved isotopy argument.

Earlier fixed-remainder two-point contraction screens started from FFF
order-20 parents. That hypothesis is **not logically necessary** for a
successful FFF order-18 descendant: the deleted rows, columns, and symbols
may remove the parent's odd-cycle witnesses. The 24 single-Pasch neighbors,
which are not FFF at order 20, are therefore a separate finite control
family. However, their only Latin-completable deletions turn out to be
principal, with deleted row, column and symbol sets all `{0,x}`. Every
completion is symmetric, and the earlier rigorous C177 theorem already
excludes FFF at order 18. The 243,200 physical checks independently confirm
that boundary; they are **not** a new unrestricted exclusion.

For each source, the screen enumerates every intercalate, deletes its two
rows, columns, and symbols, and keeps all surviving cell values. The holes
form a 2-regular bipartite row-column incidence graph. Each component has at
most two alternating assignments, and the algorithm enumerates both whenever
they meet every row/column missing-symbol domain. This is the fixed-remainder
completion lemma of [C251](fff20_represented_class_contraction_screen.md),
applied without assuming the parent is FFF. Every generated completion is
tested for the row view's even-cycle condition; a row-F candidate is then
tested in column and symbol views and rechecked by the independent physical
validator. A row-view odd cycle is a complete FFF rejection certificate for
that **specific** completion.

To test whether a nonprincipal completion can avoid that simple C177
argument, take the different Steiner loop `C2 x Steiner10`, where the
ten-point factor is the affine-plane STS(9) loop. It has 81 nonprincipal
Latin-completable deletion contexts. Of its 84 one-Pasch neighbors, 432
explicit `AGL(2,3)` automorphisms of the source form three move orbits of
sizes `36,12,36`. An automorphism carries the source, the traded blocks,
every deleted intercalate, and every fixed-remainder completion bijectively
to those of the image move. It is a common relabelling of the three Latin
sorts, so the FFF pattern is preserved. Thus a full check of one
representative per orbit covers **all 84 immediate neighbors**. The run
scans each representative's complete completion space; all fail row F.

For clarity, the affine action is a genuine source automorphism: for
distinct affine-plane points, the Steiner product is `u*v=-u-v` over
`F_3^2`. An invertible affine map `phi(u)=M u+t` satisfies
`phi(-u-v)=-phi(u)-phi(v)` because `-2t=t` in characteristic three;
it also preserves the identity and the diagonal rule. Acting in the
ten-point factor and fixing the `C2` bit gives exactly
`|AGL(2,3)|=9*48=432` automorphisms. The finite orbit partition of the
84 Pasch moves is checked exhaustively in the run; the general
automorphism-invariance of contraction is elementary relabelling, while
the three orbit sizes and row-T results are exact finite computations.

A fixed-seed 1,000-transition Pasch walk from the original STS(19) is
exploratory only: its 1,001 distinct states happened to have only principal
feasible contexts. This is not an STS(19) census or a proof that
nonprincipal completions are impossible in that component.

The [dated run](../repro_runs/2026-09-27_fff18_steiner_pasch_contraction/README.md)
records exact coverage and hashes. It excludes only the stated immediate
one-Pasch fixed-remainder families. It does not exclude other Steiner
systems, two or more trades, changing retained cells, other order-20
parents, or arbitrary order-18 FFF squares.
