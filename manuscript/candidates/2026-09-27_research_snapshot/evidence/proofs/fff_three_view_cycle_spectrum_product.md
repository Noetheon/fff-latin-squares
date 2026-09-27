# Three-view cycle spectra under direct products with `C2`

**Evidence boundary.** The invariant and product formulas below have direct
proofs for every Latin square in the stated domains. The `512` and `514`
figures depend on an exact, finite audit of specified frozen order-20 tables.
They are lower bounds on represented main classes, not an order-20 census.
Nothing here decides FFF existence at order 18, establishes literature
priority, or substitutes for independent expert review.

## Canonical three-view spectrum

For a Latin square `L` of order `n`, let `P_v(L;lambda)` count unordered pairs
of distinct lines in view `v` whose induced permutation has cycle partition
`lambda`, **sorted as an unordered partition**. Define

```text
Sigma_L(lambda) = P_row(L;lambda) + P_col(L;lambda) + P_sym(L;lambda).
```

This is a main-class invariant. An isotopy independently relabels the three
coordinate sets; each two-line permutation is conjugated or inverted, so its
cycle partition is unchanged. A parastrophy permutes the three views and may
also invert their pair permutations. Aggregating the three views removes their
names, while inversion again preserves cycle partitions. In particular, a
raw cycle listing ordered by the least labelled point is **not** invariant;
each partition must first be sorted.

Let `I(L)` be the number of intercalates, counted as unordered pairs of rows
and columns whose four entries have the form `a,b;b,a`. A 2-cycle in a row
pair corresponds to exactly one intercalate. The same four triples give one
2-cycle in each of the other two views. Hence

```text
3 I(L) = sum_lambda Sigma_L(lambda) * (# of 2-parts of lambda).
```

This also proves directly that `I(L)` is a main-class invariant.

## Product formulas

For Latin squares `L` of order `n` and `K` of order `m`, count the row-pair
2-cycles of `L x K` by whether the two product rows differ in the first,
second, or both coordinates. If only the first coordinate differs, there
are `m` choices of the common second coordinate and each 2-cycle of the
`L` relative permutation is copied `m` times, for `m^2 I(L)` in total.
Likewise, pairs differing only in the second coordinate contribute
`n^2 I(K)`. For each pair of distinct first coordinates and each pair of
distinct second coordinates there are two alignments of product rows. A
2-cycle from each factor produces two 2-cycles in the product. Thus the
both-different contribution is `4 I(L) I(K)`, and

```text
I(L x K) = m^2 I(L) + n^2 I(K) + 4 I(L) I(K).       (1)
```

No FFF assumption is needed for (1): distinct Latin lines have no fixed
points, so product 2-cycles in the both-different case can only arise from
factor 2-cycles. By parastrophy, the same count applies in all views.

Now suppose `L` is FFF and let `C2` denote the order-2 group table. For a
cycle partition `lambda` of `n`, let `D(lambda)` repeat every part twice,
so it is a partition of `2n`. In one product view, the `n` pairs with the
same `L` line and different `C2` lines have type `2^n`. For each unordered
pair of different `L` lines there are four product-line pairs. Their
permutation is the product of the `L` pair permutation with either the
identity or the transposition on two points. Every part of `lambda` is even;
in both cases the product has **two cycles of the same length** for each
factor cycle (the product-cycle `gcd`/`lcm` rule). Consequently

```text
Sigma_(L x C2) = 4 D_*(Sigma_L) + 3n [2^n].          (2)
```

Here `D_*` replaces each partition `lambda` by `D(lambda)` and `[2^n]`
is the unit mass at the all-transposition partition. The map `D` is
injective. Therefore different canonical spectra of FFF squares remain
different after product with `C2`. Formula (1) specializes to

```text
I(L x C2) = 8 I(L) + n^2.                           (3)
```

Iteration of (2) preserves this distinction under `C2^k` for every `k>=0`;
FFF preservation itself is C34. This is a statement about an invariant
which separates some main classes, not a claim that direct product is
injective on *all* main classes.

## Exact frozen order-20 input and corollary

The [dated audit](../repro_runs/2026-09-26_fff20_steiner_trade_mainclasses/README.md)
starts from the frozen FFF Steiner-loop table of order 20. Rows 0 and 1
induce ten disjoint transpositions on the columns. For each of the `2^10`
subsets, exchanging those two row entries in both columns of every selected
component is a Latin cycle-union trade. Two independently implemented
physical scanners verify that **all 1,024 resulting labelled tables are
FFF**. Direct four-cell intercalate counts agree with the counts obtained
from the three-view spectra for every table.

The exact tuple comparison of **sorted** three-view cycle partitions gives
`512` different spectra. Every spectrum occurs for exactly the two
complementary masks. Complementing the mask swaps rows 0 and 1 globally,
so those two tables are isotopic. Distinct spectra cannot share a main
class. Therefore this one finite trade family represents **exactly 512
main classes within the family**. It does not classify other order-20
Latin squares.

Two separately frozen quadratic FFF20 tables, with coefficients `(2,2)`
and `(8,8)`, have spectra not present in the trade family and different
from each other. Their intercalate totals are `190` and `19`, whereas
the trade-family totals range from `542` to `676`. Thus at least **514**
FFF main classes of order 20 are explicitly represented. By (2), at
least **514** FFF main classes are represented at every order
`20 * 2^k`, `k>=0`, by taking their direct products with `C2^k`.

The finite count is computational evidence backed by frozen input hashes,
complete enumeration, independent three-view scans, direct four-cell
intercalate counts, and direct order-40 product controls. The general
invariance and product implications are rigorous deductions from those
finite facts; the `514` base count is not itself a purely theoretical
classification. No main-class count beyond this lower bound is claimed.
