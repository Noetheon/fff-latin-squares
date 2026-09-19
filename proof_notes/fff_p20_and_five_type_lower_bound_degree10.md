# p20 exclusion and five-type lower bound in degree 10

## Evidence status

The normalization, residual-orbit reduction, and the intercalate corollary are
rigorous. The negative p20 result additionally uses the exact audited
computation in `repro_runs/2026-08-14_fff_four_type_p20_search/`. Together
with C124-C130, this supports C131 with status A+B. It does not decide C38.

The last open exact four-type palette was

```text
p20 = {10, 6+2+2, 6+4, 8+2}.
```

## Root normalization and residual action

By C123, every hypothetical exact four-type FFF realization uses all four
types. It therefore contains an edge of type `6+2+2`. C124's normalization
sends the edge endpoints to the identity and

```text
q = (0 1 2 3 4 5)(6 7)(8 9).
```

This preserves Latinity, all relative cycle types, and all three FFF views.
Sharp transitivity supplies a unique further normalized line `Q` with
`Q(0)=2`; the selected graph bucket is therefore complete.

The residual simultaneous-conjugation group is

```text
H = {g in S_10 : gq=qg, g(0)=0, g(2)=2}.
```

Fixing 0 and commuting with q fixes the six-cycle pointwise. On the two
two-cycles, g may flip each cycle independently and may exchange the cycles.
Hence

```text
H is isomorphic to C2 wr S2 and |H|=8.
```

This is the nonabelian dihedral group of order eight, not `C4 x C2`. The
action preserves root, palette, bucket, graph compatibility, sharp
transitivity, and all three FFF bits.

The graph-based orbit verifier reconstructs the action and partitions all
14,648 anchored root tasks into 1,831 disjoint full-size orbits:

```text
1,831 * 8 = 14,648.
```

It checks no orbit escape, disjointness, complete coverage, and exactly one
task-file representative per orbit.

## A p20 intercalate bound

Let `k` and `10-k` be the sign-cut class sizes in one normalized view and put
`q_s=k(10-k)`. The odd p20 types are `10` and `6+2+2`; the even types are
`6+4` and `8+2`. Let b and d be the numbers of `6+2+2` and `8+2` edges.
Using C66's transposition count,

```text
I(L) = 2b + d.
```

Exact four-type usage leaves at least one odd edge of type 10 and at least one
even edge of type `6+4`, so

```text
b <= q_s - 1,       d <= 44 - q_s.
```

Consequently

```text
I(L) <= 2(q_s-1) + (44-q_s) = q_s+42 <= 67.
```

The same common intercalate number is obtained in every view. This is a
rigorous p20-specific necessary condition, but it is not itself a
contradiction. The completed search below did not rely on this new prune.

## Why local type conditions do not exclude p20

There is no `2^5` type, so C109's matching argument does not apply. The sign
cut is consistent. An independently checked abstract `K10` colouring uses all
four p20 types and satisfies every C109 triangle and C111 four-line catalog
condition. An explicit admissible third permutation also generates `S10`
with q. Therefore the current sign, local type, and view-group conditions do
not replace the full global permutation and cross-view search.

## Exact graph and search evidence

The candidate graph contains 136,128 vertices and has SHA-256
`165df10b50bf85bb33d25654ec1cd9e489f3f8f64538eafef7e946cb564808cf`.
The independent semantic auditor re-enumerates all vertices, checks all
9,265,348,128 unordered candidate pairs and both adjacency directions, and
finds 929,166,384 edges. Every candidate, edge, reverse-edge, format,
diagonal, and padding error counter is zero.

A 58-slice ten-worker search and an independent one-slice eight-worker search
both exhaust all 1,831 orbit representatives. They agree exactly on
2,739,812,181 search nodes, 1,843,691,097 persistent cross-view odd-cycle
prunes, and no FFF completion. The hardened case validator checks all graph,
audit, task, plan, source, and double-search bindings; all 15 gates pass.

## Five-type lower bound and boundary

C124-C131 exclude every one of the 35 exact four-type palettes. C123 already
excluded all smaller palettes. Therefore, in each row, column, and symbol view
of a hypothetical order-10 FFF Latin square, at least five distinct relative
cycle types occur among its 45 two-line permutations.

This is a global necessary order-10 structure theorem, not an order-10
nonexistence theorem. Exact palettes of size five, six, and seven remain open.
There is no monotonicity from the four-type exclusions to their supersets.
C38 remains open and C40 is absent.
