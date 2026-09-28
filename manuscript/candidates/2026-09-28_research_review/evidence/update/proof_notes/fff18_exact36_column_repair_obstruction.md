# Exact minimum-support repair obstruction for one FTF18 table

**Scope.** This is a source-relative computer-assisted statement. It does not
exclude an FFF Latin square of order 18, another labelled source, or any
repair at distance at least 37. The finite UNSAT step is backed by a frozen
DIMACS formula and an independently checked DRAT trace in the
[companion run](../repro_runs/2026-09-28_fff18_exact36_repair/README.md).

## Statement

Let `S` be the frozen order-18 Latin table in
`repro_runs/2026-09-27_fff18_order9_column_cardinality/results/union_trade_best_normalized_table.json`
(SHA-256 `2a1a5fb2192f833a288f011f3850aac9f6145db7df68026a2e82f5483495fdef`).
Every Latin table `T` whose **column view is F** and which uses the same
labelled rows, columns and symbols as `S` satisfies

```text
                         d_H(T,S) >= 37.
```

In particular, this necessary source-relative bound holds for every FFF
target. It improves the earlier 36-cell support bound for this source by one.

## Physical support reduction

The source has 36 odd three-cycles in its column view, with pairwise disjoint
six-cell supports `U_1,...,U_36`. Their physical reconstruction and the
independent scanner are documented in
[the parent run](../repro_runs/2026-09-28_fff18_ftf_disjoint_supports/README.md).
If a column-F target agreed with `S` on all cells of one `U_i`, the
corresponding induced column permutation would retain that odd cycle.
Therefore every column-F target changes at least one cell of every `U_i`.
If its Hamming distance is exactly 36, it changes **exactly one** cell in
each `U_i` and no other cell. Distances below 36 are already excluded.

## Exact Latin CNF at distance 36

For a cell `x` in one of the disjoint supports, let `X_x` say that its source
symbol changes. The formula requires exactly one `X_x` per support. Cells
outside the supports retain their source value.

For each eligible replacement symbol `v != S(x)`, let `Y_(x,v)` say that the
target puts `v` at `x`. If source cell `y` is the occurrence of `v` in the
same row as `x`, and `z` is its occurrence in the same column, then a Latin
target with `Y_(x,v)` must also change `y` and `z`; otherwise `v` would be
duplicated. A replacement is ineligible if either old occurrence lies
outside the 216-cell union, or if two of `x,y,z` belong to the same support.
These restrictions are valid because exactly one cell changes per support.

The base formula imposes `Y_(x,v) => X_x,X_y,X_z`, exactly one replacement
for each changed cell, at most one new occurrence of a symbol in each row
and column, and replacement of every removed old row/column symbol. A Latin
target at distance 36 gives a satisfying assignment by setting precisely its
changed cells and new values. Conversely, any satisfying assignment defines
a Latin target: unchanged source cells retain their symbols; each removed
old symbol is replaced exactly once in its row and column; no replacement
duplicates another occurrence. Thus the base CNF represents exactly the
Latin tables in this fixed support-saturated search.

## Sound odd-cycle cuts and certificate

For any candidate Latin table `A`, consider an odd cycle of a physical
column-pair permutation and its two-column cell support `U`. Every column-F
target must differ from `A` in at least one cell of `U`, by the same
unchanged-cycle argument. For a cell `x` of `U` that is mutable:

* if `A(x)=S(x)`, the difference literal is `X_x`;
* if `A(x)=v != S(x)`, the difference literal is `not Y_(x,v)`.

Cells outside the mutable union are fixed and contribute no literal. The OR
of these literals is a necessary clause for **every** column-F target,
not just for the candidate used to discover it.

The retained certificate contains nine explicit Latin candidates at
distance 36. Each is independently checked in all three views as `TTT`;
inverse-orientation column scanning confirms its physical odd-cycle
supports. Their cycles yield 1,016 distinct, nonempty sound clauses.
Together with 12,384 base clauses, the final 1,476-variable,
13,400-clause CNF is CaDiCaL 3.0.0 UNSAT. Its 752,109-byte ASCII DRAT trace
is independently `VERIFIED` by `drat-trim` against that exact CNF.
Consequently no column-F Latin target exists at distance 36. Combined with
the disjoint-support argument for smaller distances, the stated bound follows.

The computational step is a finite exact exclusion for **this** source and
distance. It neither establishes a general Latin-trade parity law nor
decides unrestricted order-18 FFF existence. No literature priority or
independent human proof review is claimed.
