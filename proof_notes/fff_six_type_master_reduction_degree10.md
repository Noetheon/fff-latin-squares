# Six-type master reduction in degree 10

## Evidence status

The two-root reduction, the search-completeness argument, and the
intercalate-hypergraph lemma below are rigorous (A). C153 supplies the formerly
conditional f15 exclusion, so C154 makes the reduction applicable to every view
of a hypothetical order-10 FFF square. The two frozen master computations now
exclude both disjoint cases (B). Consequently order 10 is excluded by A+B
evidence. C38 nevertheless remains open for even non-powers of two beyond the
already decided orders 6 and 10.

## Conditional six-type lower bound

There are seven fixed-point-free even-cycle types in degree 10:

```text
T = {10, 2+2+2+2+2, 4+2+2+2, 4+4+2, 6+2+2, 6+4, 8+2}.
```

C131 proves that every view of a hypothetical order-10 FFF Latin square uses
at least five types. C133--C153 exclude all 21 exact five-type palettes.
Therefore C154 rigorously gives at least six members of `T` in every view.

## Two-root master reduction

Let `P` be the exact palette of one F-view and assume `|P|>=6`.

1. If `2+2+2+2+2` belongs to `P`, exact use supplies a line pair of this type.
   Left normalization and simultaneous conjugation reduce it to

   ```text
   rho_I = (0 1)(2 3)(4 5)(6 7)(8 9).
   ```

2. If `2+2+2+2+2` does not belong to `P`, then `P` is a subset of the six
   remaining members of `T`. Since `|P|>=6`, equality is forced. In particular
   `4+2+2+2` occurs, so one such line pair may be normalized to

   ```text
   rho_E = (0 1 2 3)(4 5)(6 7)(8 9).
   ```

These cases are disjoint and exhaustive. The first contains six of the seven
exact six-type palettes and the exact seven-type palette; the second is the
unique exact six-type palette omitting the involution type. The same
parastrophe argument used in the f15 proof note transfers a row-family search
to column and symbol views. Thus two complete master searches are sufficient;
seven separate exact-palette searches are unnecessary.

This reduction is only a decomposition of the remaining search space. It is
not an exclusion.

## Exact master inventory

`repro_runs/2026-08-26_fff_six_type_master_inventory/` independently
enumerates both normalized families in C++ and Python. The implementations
agree exactly on the following dimensions after the three-line cross-view
partial-cycle filter:

| family | candidates | root tasks | residual group | orbit distribution | orbits | dense graph bytes |
|---|---:|---:|---:|---|---:|---:|
| `rho_I`, all seven F-types allowed | 190,080 | 23,760 | 48 | `12*12 + 4*24 + 490*48` | 506 | 4,518,201,626 |
| `rho_E`, six noninvolution F-types | 172,368 | 18,300 | 48 | `5*12 + 2*24 + 379*48` | 386 | 3,716,598,842 |

The first residual group fixes the two distinguished transposition blocks
pointwise and freely permutes and flips the remaining three blocks. The
second fixes the distinguished 4-cycle pointwise and likewise permutes and
flips the three remaining transposition blocks. Both groups therefore have
order `3!*2^3=48`, in agreement with the direct enumeration.

These are exact inventory computations (B), not search results. The inventory
package alone excludes nothing; the graph and completion evidence is frozen in
the two dedicated master-search packages below.

## Why the master searches are exhaustive

After normalizing the identity line and the selected root `rho_I` or `rho_E`,
every remaining line is a permutation `q` of the ten points. Sharp
transitivity forces the eight remaining lines to have pairwise distinct values
`q(0)` in `{2,...,9}`. The graph vertices are exactly the permutations that
pass the allowed relative-cycle conditions against the two normalized lines
and the already determined three-line column- and symbol-channel conditions.
Two vertices are adjacent exactly when their relative row permutation has an
allowed even-cycle type and adjoining the corresponding line pair creates no
closed odd cycle in either partial cross-view channel. The complete semantic
auditors independently reconstruct every candidate and test every unordered
candidate pair against this definition.

Thus every normalized FFF line family gives one vertex in each image bucket
and all eight vertices are pairwise adjacent. Conversely, a selected
bucket-transversal clique gives ten row permutations, including the identity
and root. The DFS maintains all 45 column-pair and all 45 symbol-pair partial
permutations while adding these rows. By the cycle-closing lemma in
`proof_notes/fff_incremental_crossview_cycle_pruning.md`, a partial closed odd
cycle cannot be repaired by adding further rows, so every incremental prune is
sound. At depth eight, all maps are total; survival is therefore exactly the
row-, column-, and symbol-FFF condition. The minimum-bucket branching rule only
changes search order and visits every bucket-transversal clique unless a sound
cross-view prune has already excluded it.

Conjugation by the appropriate 48-element residual group preserves the root,
the graph, image-bucket structure, relative cycle types, and all partial
cross-view conditions. The graph-bound orbit audits reconstruct this action,
produce deterministic representative task files, and verify the exact cover
identities

```text
5*12 + 2*24 + 379*48 = 18300,
12*12 + 4*24 + 490*48 = 23760.
```

Therefore searching the 386 and 506 representatives is logically equivalent
to searching all 18,300 and 23,760 normalized root tasks. Repeating all
conjugate tasks would be a redundant engineering control, not an additional
mathematical premise.

## Root-involution matching consequence

C109 proves that the relative `2+2+2+2+2` edges in any F-view form a matching.
In the `rho_I` master family, the root is one such edge. Hence no other
involution edge meets a root endpoint, and all further involution edges lie
among the remaining eight lines and form a matching there. If `h` is the total
number of involution edges, then `1<=h<=5`. This is a valid search invariant,
not a contradiction.

## Intercalate-hypergraph lemma

For a Latin square `L`, let the three vertex classes be the unordered pairs of
rows, columns, and symbols. Associate to every intercalate the triple formed by
its row pair, column pair, and symbol pair.

This gives a simple three-partite 3-uniform hypergraph:

- an intercalate has exactly one pair of each coordinate kind;
- a row pair and column pair determine the four cells and hence at most one
  symbol pair;
- a row pair and symbol pair determine at most one column pair, since each
  selected symbol occurs in a unique column of each selected row;
- a column pair and symbol pair determine at most one row pair by the same
  Latin uniqueness, or equivalently by cyclic parastrophy;
- consequently two hyperedges cannot share two vertices;
- the degree of a line-pair vertex is exactly the number of 2-cycles in its
  induced relative permutation.

Thus the three viewwise distributions weighted by
`w(lambda)=number of 2-cycles of lambda` must be degree sequences of one common
simple linear three-partite hypergraph. This records the 2-cycle weight, not
the rest of each cycle type. Equality of the total intercalate count (C66) is
only the scalar shadow of this stronger cell-coupled condition.

## Why scalar aggregation cannot finish the problem

The sign equations, common intercalate total, and involution-matching bound
constrain only type counts. Existing order-10 partial tables already realize
F-views using six or seven types, so no one-view theorem of the form "an
F-view uses at most five types" can hold. The scalar aggregations examined so
far are insufficient. The currently strongest route preserves cross-view cell
labels, for example through the C78/C79 pair-label tensor or a proof-producing
SAT encoding of the C113 pair channels; this does not rule out a different,
stronger unlabeled invariant.

## Complete master computations

The noninvolution graph contains 172,368 vertices and 1,650,487,056 edges. Its
complete semantic audit checks all 14,855,277,528 unordered candidate pairs
and reports zero candidate, edge, reverse-edge, format, diagonal, padding, or
root errors. Two complete decompositions of the same 386-representative task
file, with slice widths 64 and 97, agree exactly at 2,514,104,197 search nodes
and 1,769,153,203 cross-view odd-cycle prunes. Both are complete negative. The
central package validator passes 15/15 checks and its fail-closed audit passes
13/13 mutations.

The involution/all-seven graph contains 190,080 vertices and 2,050,329,600
edges. Its complete semantic audit checks all 18,065,108,160 unordered pairs
with the same seven error counts equal to zero. Two complete decompositions of
the same 506-representative task file, with slice widths 64 and 127, agree
exactly at 5,001,728,282 search nodes and 3,586,770,865 prunes. Both are
complete negative. Its central validator likewise passes 15/15 checks and the
fail-closed audit 13/13 mutations. Both control runs record zero swaps.

The same frozen search binary is used in all four master searches. This exact
second decomposition controls task slicing, checkpoint merging, and
deterministic aggregate counts; it is not presented as an independent search
implementation. Independence at the model layer comes from the separate
Python/C++ inventory agreement, complete semantic graph auditors, graph-bound
orbit reconstruction, fail-closed validators, the frozen f18 positive
control, and all-eight-pattern order-8 controls.

## Conclusion

**C155 (A+B).** The exact six-type palette omitting `2+2+2+2+2` cannot occur
in any view of an order-10 FFF Latin square.

**C156 (A+B).** No order-10 FFF Latin square has a view containing the
involution type `2+2+2+2+2` once C154 is imposed; equivalently, all six exact
six-type palettes containing that type and the exact seven-type palette are
excluded by the involution-root master.

**C157 (A+B).** No FFF Latin square of order 10 exists. Indeed, C154 gives at
least six types in every view. In any selected view, presence of the
involution type falls under C156, while absence forces the unique palette of
C155. These cases are disjoint and exhaustive.

This decides order 10 but not the global power-of-two conjecture C38. Orders
`12,14,18,...` remain outside this computation. No count of higher-order
isotopy or main classes follows from the exclusion.

## Retained fallback route

The earlier SAT-oriented global experiment remains a fallback:

1. preserve complete row and column F constraints and require at least six
   types in both views;
2. use the 12 proved row-1 symmetry cases;
3. activate at least 38 of the 45 symbol-pair F constraints;
4. validate known partial tables with symbol defect eight as SAT controls at
   the weaker threshold 37;
5. solve the threshold-38 family with complete cube coverage and checked
   DRAT/LRAT evidence.

The global reduction is as follows. Isotopy permits reduced representatives
and preserves relative cycle types, hence also the number of types in each
view. The existing row-1 proof partitions all reduced row-F tables into twelve
complete canonical cases. For fixed Latin variables, activation gating is
monotone: a set of at least 38 true activation variables exists exactly when
at least 38 symbol-pair permutations are F, because true variables enforce the
corresponding F constraints and any actually F pair can be activated without
changing the table. Therefore complete, proof-checked UNSAT over all twelve
cases would prove the stated defect bound. The accepted evidence must bind the
cube cover, every CNF, every solver result, and every checked proof log.

A certified negative result would be a new cross-view defect theorem. Together
with C153/C154 it would also rule out order 10, but the direct master searches
are currently more tightly aligned with the remaining exact space. Without
independent direct validation, a threshold-38 SAT model is only partial.
Activating all 45 pairs is sufficient for FFF, but not necessary for
recognizing a lucky SAT table: any decoded table that independently validates
as Latin and FFF is a genuine example regardless of which activation
variables happened to be true.
