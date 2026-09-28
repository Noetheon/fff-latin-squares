# A 35-cell necessary-mask bound around one FFT18 source

**Evidence boundary.** This is a source-relative distance theorem. The
general odd-cycle-support and Latin change-mask implications are rigorous;
the numerical exclusion at 34 cells relies on an exact CNF with an
independently checked DRAT trace. No order-18 FFF table is constructed
or globally excluded. Literature priority and external review remain open.

## Three necessary conditions

Fix the `FFT18` source `S` of C256, with SHA-256
`1ed0abb7bae546375fe9595f408b7ede9c95fb02bae582e99d80ebbe4a9764d8`,
and let `T` be any Latin
square on the same labelled rows, columns and symbols. Let `B` be its
changed-cell set relative to `S`. If `T` is symbol-F, `B` meets all
102 physical supports of the source's odd symbol-pair cycles by the
[general support lemma](fff18_p17_symbol_cell_packing_bound.md).

Every row, column and source-symbol line has either zero or at least
two cells in `B`. Moreover, for every `(r,c) in B`, the replacement
symbol `t=T(r,c)` differs from `S(r,c)` and the old `t`-cell of source
row `r` and the old `t`-cell of source column `c` both belong to `B`.
The [replacement-domain note](fff_source_change_mask_replacement_domains.md)
proves both conditions for any pair of Latin squares. They are only
necessary: a satisfying mask need not admit a Latin completion.

## Exact at-most-34 encoding

The C256 certificate contains 32 pairwise disjoint odd-cycle supports
`W_i` occupying 288 of the 324 cells. A hitting mask of size at most
34 has at most **two** cells beyond one mandatory cell per `W_i`.
For each group `W_i`, introduce markers `e_i` and `f_i` for a possible
second and third chosen cell:

- each `W_i` has at least one changed cell;
- every chosen pair in `W_i` forces `e_i`;
- every chosen triple forces `f_i`, and `f_i` forces `e_i`;
- every chosen quartet is forbidden;
- at most two of all `e_i`, `f_i`, and changed-cell variables outside
  the union of the `W_i` may be true.

The last condition uses the standard sequential at-most-two counter.
These clauses project **exactly** to masks of size at most 34 that meet
all selected supports. Indeed, a group with one, two or three chosen
cells costs respectively zero, one or two markers; a fourth cell is
forbidden. Every outside chosen cell costs one. Conversely, any such
mask assigns the markers according to its group sizes and satisfies
the counter. This encoding uses 588 variables before replacement
domains. The 102 support-hit clauses and three no-singleton line
families are then added.

For each cell `(r,c)` and candidate `t!=S(r,c)`, a choice variable
implies that the cell and the old `t`-cells in its row and column are
changed. Every changed cell requires at least one such choice. This is
exactly the displayed local replacement-domain condition, not a full
Latin-table encoding. The complete necessary CNF has **6,096 variables
and 51,914 clauses**.

The [dated audit](../repro_runs/2026-09-27_fff18_fft34_compact_degree_screen/README.md)
independently reconstructs every physical odd-cycle support and the
compact base clause multiset. It verifies that the added **16,848**
domain clauses match the earlier independently validated generator
clause-for-clause in the same order. CaDiCaL 3.0.0 reports UNSAT, and
`drat-trim` independently reports `VERIFIED` for the SHA-pinned trace.

Therefore **every symbol-F Latin target, hence every FFF Latin target,
has `d_H(S,T)>=35`**. The older support-only bound 34 (C256) remains
correct but is numerically superseded for this same source.

## Controls and limitations

The compact support-only and support-plus-line-degree models are SAT
at 34 cells. Their decoded masks physically meet all 102 odd-cycle
supports; the latter has no singleton row, column or source-symbol
line. Nevertheless **28** of its cells lack any available replacement
symbol, so it cannot be a Latin difference support. Thus the final
UNSAT is not caused by merely requiring one changed cell per selected
support or by the no-singleton conditions alone. The previous
replacement-domain run contains genuine small FFF-positive controls;
the new audit checks exact identity of that clause family.

No claim is made about distance 35 being attainable by a Latin or FFF
table. This source-relative obstruction, like C254-C256, excludes only
a Hamming neighbourhood of a single labelled source and its common
isotopes. It does not decide the unrestricted order-18 question or
complete the active breakthrough Goal.
