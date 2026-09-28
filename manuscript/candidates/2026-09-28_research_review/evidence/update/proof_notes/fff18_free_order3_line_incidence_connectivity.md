# Line-incidence connectivity under a free order-three autotopism

**Scope.** This is a theorem for a Latin square with a specified free
diagonal order-three autotopism. It is not a theorem that every order-18
FFF square has such an autotopism. The argument needs only one F view at
a time. Any autotopism whose three coordinate components are all free
of order three can be put in this diagonal form by independent
coordinate conjugations; isotopy preserves the view pattern. The
finite controls are secondary to the proof.

## The incidence graph of a line

Write `g` for the common permutation of rows, columns, and symbols,
with all cycles of length three, and suppose
`L(g r,g c)=g L(r,c)`. In any of the row, column, or symbol views,
let `f:P->V` be one line permutation. Its next line is

```text
f_next = g_V f g_P^(-1).
```

The formula holds also in the symbol view: there `P` is the column
set and `V` is the row set. Identify the three-element orbits of
`g_P` and `g_V`. Form a bipartite multigraph `B_f` with one vertex
per orbit on each side and one edge for each `p in P`, from the orbit
of `p` to the orbit of `f(p)`. It is 3-regular on both sides.

Put `h=f^(-1) g_V f`, a fixed-point-free permutation of type `3^m`
on `P`, where `|P|=3m`. The relative two-line permutation is
`P_f=f^(-1)f_next=h g_P^(-1)`. The connected components of `B_f`
are exactly the orbits of `<g_P,h>` on `P`: `g_P` moves among the
three positions at one left vertex, while `h` moves among the three
preimages of one right vertex. In particular, a component containing
`k` vertices on each side contains `3k` positions and is invariant
under `P_f`.

If this view is F, `P_f` has only even cycles. Its restriction to
every component also has only even cycles, so `3k` is even and `k`
must be even.

## The six-position obstruction

The possibility `k=2` is also impossible. On a six-position component,
both `g_P` and `h` have type `3+3`. Up to relabeling take
`g_P=(0 1 2)(3 4 5)`. Its two orbit sets are `A={0,1,2}` and
`B={3,4,5}`. If `h` preserves `A` and `B`, its two orientations on
each triple show that `h g_P^(-1)` has type `1^6`, `3+1^3`, or
`3+3`; none consists only of even cycles.

Otherwise, the two cycles of `h` each meet both `A` and `B`. Rotating
the two `g_P` cycles, swapping them if necessary, and exchanging the
two unnamed cycles of `h` puts their supports at
`{0,1,3}` and `{2,4,5}`. The four possible orientations give:

| Orientation on `(0,1,3)` | Orientation on `(2,4,5)` | Type of `h g_P^(-1)` |
| --- | --- | --- |
| forward | forward | `2+2+1+1` |
| forward | reverse | `5+1` |
| reverse | forward | `5+1` |
| reverse | reverse | `3+3` |

Thus no product of two fixed-point-free `3+3` permutations is a
fixed-point-free even-cycle permutation. The companion run checks all
40 distinct choices of `h` independently of the table controls.

**Theorem.** In an F view under the specified free diagonal order-three
autotopism, every component of every line-incidence graph `B_f` has
`k` orbit vertices per side with **even `k>=4`**. In particular, at
order 18 (`m=6`), every `B_f` is connected: if it were disconnected,
one component would have `k<=3`, contrary to the theorem. The
conclusion applies separately to row, column, and symbol views of an
FFF table.

This rules out a closed `3 x 6` line-rectangle as well as the
`3 x 3` case. It is not merely the absence of an aligned square
subtable: a single three-row orbit can map six columns into six
symbols without there being a six-row subsquare. It also does not
exclude the connected graphs of non-FFF Latin squares.

## Exact finite clause consequence

For order 18, let `I` and `J` be equally sized nonempty proper sets
of position and value orbit indices, respectively. A line has a
disconnected incidence graph exactly when some such `I,J` are closed:
all positions in the orbits `I` map into the value orbits `J`.
For a table-variable encoding with exactly one value per position,
forbid this by the disjunction

```text
OR_{p in orbit(I), v outside orbit(J)} X[line,p,v].
```

Use `X[r,p,v]` in the row view, `X[p,c,v]` in the column view, and
`X[v,p,s]` in the symbol view, whose line map sends columns to rows.
Because the line is a bijection, the cut for `(I,J)` is equivalent to
the one for its complements. Keeping sizes 1 and 2 and one of each
complementary size-3 pair gives `36+225+200=461` cuts per line-orbit
representative, or `18*461=8298` for all three views. There are six
line orbits in each view, and equivariance carries a cut on one line
to the corresponding cut on its other two orbit members. They are valid
redundant clauses only for the specified free-symmetry model, not for
an unrestricted order-18 CNF. A SAT model of these clauses alone is
not evidence of FFF; a full CNF still needs a decoded, independently
scanned table, and UNSAT needs complete coverage and certification.

The cuts are not implied by the earlier **Latin-plus-aligned-subsquare**
relaxation. The dated run stores an explicit equivariant Latin table
(SHA-256 `dc7b3ab6608072ed9f68c99227582f4904dcb5e7786b9e2448561de1d33da768`)
with no forbidden aligned subsquare of orders 3, 6, or 9, but whose
row-0 incidence graph has components of sizes `4+2`. The table satisfies
every clause of the old relaxation plus units closing row 0's first
two position orbits into its first two value orbits; the SAT assignment
was checked clause by clause. A separate physical validator finds
`TTT`, not FFF. That relaxation did **not** include C227 anchors or
full-view FFF constraints. This proves additional logical filtering
over the weak relaxation only. Compiling all symbolic cuts into the
anchored full three-view model yields 8,082 distinct CNF clauses after
orbit-variable deduplication. The base and overlay both time out in a
single controlled 20-second CaDiCaL pilot, so there is no measured
full-model speedup or decision.

The [dated audit](../repro_runs/2026-09-27_fff18_order3_line_incidence/README.md)
rechecks the 40-case lemma, the `3m`-orbit graph equivalence, a frozen
FFF12 positive, a frozen FTF18 near miss, a generated group-table
negative, and the explicit old-relaxation countercontrol. No general
order-18 existence decision or literature-priority
claim follows.
