# Fixed-remainder two-point contraction of represented FFF20 classes

## Evidence and scope

The transport and hole-graph arguments below are rigorous. The exclusion of
the named 514 represented order-20 main classes is an exact finite result
based on hash-frozen inputs and a fresh independent three-view scan. It is
**not** a census of all FFF20 classes, an exclusion of other contraction or
repair operations, or a decision about unrestricted FFF18 existence.

## Main-class invariance of the operation

Regard an order-`n` Latin square as a set of triples in three disjoint sorts
`R,C,S`. Choose two-element sets `A subset R`, `B subset C`, and `D subset S`
such that the four triples on `A x B` form an order-two Latin subsquare with
symbol set `D`. Retain every triple whose three coordinates lie outside
`A,B,D`. A **fixed-remainder contraction** is any Latin square on
`R\A,C\B,S\D` containing all of those retained triples. Only holes left by
deleted symbols may be filled; no other retained cell may be changed.

Independent bijections of the three sorts map deleted sets, retained triples,
and completions bijectively. A permutation of the three sorts does the same:
the definition selects triples by membership in the three complementary
coordinate sets, so it is symmetric under parastrophy. Thus existence of an
FFF fixed-remainder contraction is a main-class invariant, using the proved
three-view isotopy/parastrophy invariance of FFF (C03). It is enough to test
one table from each represented main class. This does not extend to a repair
that changes retained triples.

For a fixed choice of `A,B,D`, the retained row-column hole graph is
2-regular. Each connected component has at most two completions, determined
by a value at one edge. This is the exact general hole-graph lemma proved in
[the original contraction note](fff_two_point_subsquare_contraction.md). The
new [audit](../repro_runs/2026-09-27_fff20_trade_contraction_screen/README.md)
implements its component propagation independently of the frozen enumerator.

## The 512-class trade family

The frozen Steiner FFF20 source has ten disjoint two-cycles between rows
`0,1`. Swapping those row entries independently on any subset gives `2^10`
Latin FFF tables. C246 proves and exactly checks that the 1024 masks comprise
512 different main classes within this family; complementary masks differ by
a global row swap. Two separately frozen quadratic FFF20 tables represent
two further classes, yielding 514 represented classes in all.

The fresh finite audit enumerates every intercalate and every hole component
for all 1024 masks. Masks `0` and `1023` have 19 feasible deleted subsquares
and 9728 labelled completion paths each. Each of the other 1022 masks has
exactly one feasible deleted subsquare: rows `{0,1}`, columns `{0,1}`, and
symbols `{0,1}`, with 512 completion paths. These are exact finite counts,
not an extrapolation from sampled masks.

For a proper mask, the trade changes only rows `0,1`, precisely the deleted
rows in its unique feasible case. Every retained triple, missing-symbol set
at a retained row or column, hole, and hole-component option therefore agrees
with the base mask's `{0,1}` case. The audit checks equality of the complete
component-option tuples for each of the 1022 masks. Its 512 possible output
tables are a subset of the base source's already enumerated 9728 output
paths. Mask `1023` is a global swap of the source rows and hence has the
same contraction outcomes up to isotopy.

The new direct scanner rechecks all 9728 base completions, obtaining only
pattern `TTT`, with exactly `72/72/72` odd-witness line pairs in the three
views. Its row-major completion-byte stream has the same SHA-256 as the
frozen dual-scanner [full contraction run](../repro_runs/2026-09-25_fff20_to18_contraction/README.md).
The two additional quadratic source tables, with coefficients `(2,2)` and
`(8,8)`, have respectively 190 and 19 intercalates, but neither admits even
one Latin fixed-remainder completion. A `C2 x C2` positive control has two
Latin and FFF order-two completions, so the algorithm is not hardwired to a
negative result.

## Exact conclusion and remaining frontier

**A+B scoped result:** No table in the 514 FFF20 main classes represented by
C246 yields an FFF18 table by this fixed-remainder two-point contraction.
This closes that constructive route for those classes, not for every FFF20
main class. It also leaves unrestricted cell repairs, other source orders,
and the unrestricted order-18 existence problem open. No new FFF18 witness,
global exclusion, literature-priority claim, external review, or Goal
completion follows.
