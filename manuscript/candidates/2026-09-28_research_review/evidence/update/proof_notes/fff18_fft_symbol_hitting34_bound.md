# A 34-cell odd-cycle hitting bound for one FFT18 source

**Evidence boundary.** The implication from odd-cycle supports to changed
cells is rigorous and general. The numerical 34-cell bound is an exact,
independently proof-checked finite result for one SHA-pinned source. It is
not an order-18 existence or nonexistence theorem, a constructed Latin
square at distance 34, or a claim of literature priority or external review.

## General support implication

For a Latin source `S`, a pair of symbols `u,v`, and an odd cycle `C`
of their induced symbol-view permutation, let `W(C)` be the physical
cells containing the two symbols along the arrows of `C`. If a Latin
target `T` agrees with `S` on all cells of `W(C)`, the same closed odd
cycle survives in `T`. Thus every symbol-F target changes at least one
cell of every `W(C)`. The physical proof is given in the earlier
[support lemma](fff18_p17_symbol_cell_packing_bound.md). No trade model or
reduced-label assumption is needed.

## Exact 33-cell exclusion

The frozen `FFT` source is SHA-256
`1ed0abb7bae546375fe9595f408b7ede9c95fb02bae582e99d80ebbe4a9764d8`.
An independent physical reconstruction finds exactly 102 odd symbol-pair
cycles. The earlier checked certificate selects 32 pairwise disjoint
supports `W_1,...,W_32`, covering 288 distinct cells. Let `x_c` mean
that a target differs from the source in cell `c`.

Any symbol-F target at distance at most 33 must hit each `W_i`. It can
therefore use at most one cell beyond the mandatory 32. The exact CNF
uses a marker `e_i` for the possible second changed cell in `W_i`:

1. Each `W_i` contains at least one `x_c`; three chosen cells in one
   `W_i` are forbidden.
2. Every pair of chosen cells in `W_i` forces `e_i`.
3. At most one literal among the 32 markers and the 36 cell variables
   outside the union of the selected supports may be true.
4. Every one of the 102 physical odd-cycle supports contains at least
   one `x_c`.

These clauses are satisfiable **if and only if** the 102 supports admit
a hitting set of at most 33 cells. In the forward direction, the 32
disjoint selected supports each consume one cell and item 3 permits at
most one additional cell. In the reverse direction, choose the hitting
set as the true cell variables and set only the marker of a selected
support containing two chosen cells, if any. Item 1 holds because a
33-cell hitting set cannot put three cells in one selected support.

The [dated audit](../repro_runs/2026-09-27_fff18_fft32_equality_screen/README.md)
independently reconstructs all 102 supports and the entire 11,004-clause,
356-variable CNF from the frozen table and certificate. CaDiCaL 3.0.0
reports UNSAT; `drat-trim` independently reports `VERIFIED` on its
SHA-pinned DRAT trace. Hence **every symbol-F Latin square, and thus
every FFF Latin square, on these same labels differs from this source
in at least 34 cells**. A separate 32-cell CNF and trace provide a
redundant negative control for the prior certificate.

There is a 34-cell set hitting all 102 physical odd-cycle supports;
the independent verifier records its cells and confirms the coverage.
It has singleton changed-cell lines and cannot be the difference
support of a second Latin square. Therefore 34 is sharp for the
**support-hitting relaxation only**. The minimum distance to an actual
symbol-F or FFF Latin square may be greater, or no such order-18 FFF
square may exist.

The new 34-cell bound supersedes the earlier 32-cell disjoint-support
bound **numerically for this same source**. The general C255 bad-pair
graph theorem remains valid, but its 24-cell consequence for this source
is weaker still. Common isotopy of source and target transports this
labelled distance statement; it says nothing about arbitrary distant
order-18 squares. The unrestricted order-18 question and the active
research Goal remain open.
