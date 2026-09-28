# All eligible two-cycle row-pair trades of the frozen FFF20 square

Status: exact finite computation (B) plus rigorous invariant/product and
row-fibred-extension deductions (A). This is not an order-20 census, an
order-18 decision, a literature-priority claim, or external peer review.

## Finite family and Latin preservation

Fix the hash-pinned FFF20 table in the [run](../repro_runs/2026-09-27_fff20_all_two_cycle_row_trades/README.md).
For any two rows `a<b`, let `p` map each column `c` to the column `d` for
which `L(a,c)=L(b,d)`. The Latin property makes `p` a fixed-point-free
permutation. Exactly 22 of the 190 row pairs have `p` of type `2^10`.
For each such pair, independently choose whether to exchange the two row
entries in both columns of each 2-cycle. There are `2^10=1024` masks per
pair, or 22,528 labelled mask instances in this finite family.

Every exchanged 2-cycle swaps the same two symbols in each of the two
rows. Thus both rows remain permutations, every affected column retains
its two values, and all other cells are unchanged. Every mask therefore
defines a Latin square. Complementary masks differ by globally swapping
the two selected rows; they are isotopic, and in particular have the same
FFF status and aggregate three-view cycle spectrum.

## Exact count and main-class consequence

The run evaluates every mask with two separately implemented physical
line-pair cycle scanners in row, column, and symbol views. They agree on
Latinness, odd-pair counts, and all cycle partitions. Exactly 19,480
labelled mask instances are FFF. The script groups their **exact sorted
aggregate spectra as tuples**, not by hash equality. There are 1,700
distinct spectra in the trade family; the old row-0/1 family contributes
512 of them. Two separately frozen quadratic FFF20 controls have spectra
outside the entire trade set and outside each other. Hence 1,702 different
aggregate spectra are represented by FFF20 squares.

By [C246's proof](fff_three_view_cycle_spectrum_product.md), the aggregate
spectrum is a main-class invariant. Different spectra imply different
main classes; equal spectra do **not** imply equivalent squares. Therefore
there are at least **1,702** FFF main classes of order 20. C246's proved
injective spectrum formula for product with `C2` gives at least 1,702
FFF main classes at every order `20*2^k`, `k>=0`.

The same 1,702 source classes are quotient-free by C41 and the exact C157
order-10 exclusion. Hence the independent [C250 affine-orbit theorem](fff_affine_orbit_fibre_classification.md)
applies with `m=1702`: at order `20*2^d`, `d>=1`, the lower bound is
`T_d(1702)=|AGL(d,2)|^{-1} sum_g 1702^{cycles(g)}`. In particular, at order
40 this gives `binom(1703,2)=1,449,253` distinct FFF main classes. These
are mathematical consequences of the proven injection theorem and the
finite 1,702-source certificate, **not** individual physical scans of
1,449,253 order-40 tables.

## Boundaries

This run exhausts only trades from the 22 eligible row pairs of one
particular frozen table. There may be further FFF20 main classes within
the same exact spectrum or outside the selected trade family. It does
not classify all order-20 FFF tables or decide whether an FFF18 square
exists. Literature priority and independent human review are open.
