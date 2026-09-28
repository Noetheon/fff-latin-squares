# A three-view bad-pair graph bound for FFF repair distance

**Evidence boundary.** The graph-distance theorem and the triangle
argument below are rigorous. The identification of the graphs of three
named frozen source tables is an exact finite computation with two
independent physical line-pair methods and a third frozen aggregate
validator. The [dated run](../repro_runs/2026-09-27_fff_bad_pair_graph_distance/README.md)
pins every input and output. No unrestricted order-18 existence or
nonexistence statement, literature priority, or external human review
follows.

## General theorem

Let `T` and `L` be Latin squares of order `n` on the same labelled row,
column and symbol sets. For `V` in `{row,col,sym}`, define the **bad-pair
graph** `Gamma_V(T)` on the `n` lines of view `V`: two line labels are
adjacent exactly when their induced two-line permutation in `T` has a
nontrivial odd cycle. Let `alpha_V(T)` be its independence number.

**Theorem.** If `L` is FFF, then

```text
d_H(L,T) >= max_V 2*(n-alpha_V(T)),
```

where `d_H` counts cells `(r,c)` on which `L(r,c)!=T(r,c)`.

**Proof.** Fix a view `V` and let `U` be the set of its lines that are
identical in `L` and `T`. An edge of `Gamma_V(T)` cannot have both
endpoints in `U`: the two unchanged lines would induce exactly the same
odd cycle in `L`, contradicting FFF. Thus `U` is independent and at
least `n-alpha_V(T)` lines have changed.

Each line in every view is a bijection between `n` positions and `n`
values. Two distinct bijections differ at **at least two** positions:
if one value moved away from its old position, bijectivity forces at
least one more change. For row and column views, each changed line
therefore contributes at least two distinct changed cells, and
different lines of that view have disjoint cell supports. For the
symbol view, a line gives the location of one symbol in each column;
two distinct such matchings lose at least two of the old cells bearing
that symbol. The lost old cells for different symbols are also
disjoint. Hence `d_H(L,T)>=2(n-alpha_V(T))` in each view; take the
maximum. QED.

The statement is source-relative. Applying the same isotopy or
parastrophy to **both** `L` and `T` preserves Hamming distance: it
permutes their three-sorted triple sets, whose symmetric difference
has size `2*d_H(L,T)`. The FFF property and the three graph bounds
permute accordingly. This does not constrain an unrelated distant
table. The theorem subsumes the unchanged-symbol-line argument of
[C236](fff_symmetric_source_hamming_bound.md).

## A reusable triangular graph corollary

For odd `p>=3`, put `h=(p-1)/2`. Suppose a bad-pair graph contains, on
`p` selected labels identified with `Z_p`, every edge of the circulant
`C_p(1,h)` with cyclic differences `+-1` and `+-h`. For each
`t in Z_p`, the three vertices `{t,t+1,t+h+1}` form a triangle:
their cyclic differences are `1`, `h`, and `h+1=-h`. The `p` translated
triangles are counted with multiplicity and each vertex occurs three
times. An independent set meets each triangle at most once, so
`3|I|<=p` and `|I|<=floor(p/3)` on these labels. Regardless of any
other vertices or edges, at least `p-floor(p/3)` of those lines must
change. The theorem yields

```text
d_H(L,T) >= 2*(p-floor(p/3)).
```

This is a general **conditional source-graph** bound, not a theorem
that all order-`p+1` sources have that graph.

## The frozen FFT18 source

The frozen order-18 `FFT` source has zero row and column bad-pair
edges. Its symbol bad-pair graph has isolated symbol `0` and exactly
the 34 edges of `C_17(1,8)` on labels `1,...,17`, taking `17` as zero
modulo 17. The [finite audit](../repro_runs/2026-09-27_fff_bad_pair_graph_distance/README.md)
compares a relative-permutation cycle scanner with an independent
alternating bipartite matching-component scanner on all 459 line pairs;
both agree with the frozen three-view aggregate validator. The source
SHA-256 is `1ed0abb7bae546375fe9595f408b7ede9c95fb02bae582e99d80ebbe4a9764d8`.

The 17 translated triangles above give `alpha(C_17(1,8))<=5`, and
`{1,4,6,8,11}` is an explicit independent five-set. Therefore the
full symbol graph has `alpha=6`, including the isolated `0`, and the
general theorem proves

```text
every FFF order-18 table L has d_H(L,T) >= 2*(18-6) = 24.
```

This is an independent graph-theoretic deduction beyond C254's
checked-DRAT radius 16, but it is **not the strongest known bound for
this source**. The earlier [disjoint odd-cycle support certificate](fff18_p17_symbol_cell_packing_bound.md)
uses the **same source SHA-256** and gives **32** changed cells for any
symbol-F target. Its retained certificate was rechecked for this audit.
Thus the 24-cell graph consequence is numerically dominated here; it
must not be presented as a new best radius or used to justify a weaker
search cut. C254's historical `k=20` solver timeout remains a true
record of that run, not an UNSAT result.

For this same source, each of the 32 pairwise disjoint odd-cycle
supports in the earlier certificate supplies a necessary changed-cell
clause. Their conjunction already implies Hamming distance at least
32. Adding only the C255 distance-at-least-24 inequality to a solver
that retains those clauses cannot remove any candidate. It could
change propagation but has **no additional semantic exclusion**; no
runtime gain is asserted or measured here.

## Controls and remaining question

The frozen symmetric midpoint18 source has symbol graph `K_17` plus
one isolated vertex. Hence `alpha=2` and the graph theorem gives 32,
matching C236's separate proof. A frozen FFF8 square has empty
bad-pair graphs in all three views and the bound zero, as it must.

The calculation of the named source graphs is tiny and exactly
rerunnable. The general theorem does **not** say the bound is sharp,
does not produce an FFF18 square, and does not exclude one at distance
24 or more by itself. The already certified 32-cell support bound
excludes distances 24 through 31 for this same source. The order-18
breakthrough Goal remains active; no paper upgrade, commit, push or
release follows.
