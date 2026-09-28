# A fixed-prefix three-view extension obstruction at order 18

## Scope and logical reading

Let `P` be the ten-row reduced C243 case-14 prefix frozen in the
[partial-row staging run](../repro_runs/2026-09-26_fff18_partial_row_staging/README.md).
Let `A` be the following five cell conditions on the twelfth row
(zero-based row index 11):

`L(11,6)=2`, `L(11,9)=7`, `L(11,10)=6`, `L(11,11)=13`, and
`L(11,16)=3`.

For each set `V` of row, column and symbol views, let `F_13(V)` be
the exact Latin-plus-partial-map-coloring CNF for 13 rows extending
`P`, with the five units `A` appended. The existing
[partial-map lemma](fff_partial_row_closed_cycle_encoding.md) proves
that its table projection is exactly the partial Latin squares in
which no already closed odd cycle occurs in the selected views.

## Exactly computed finite statement

The [dated view-lattice run](../repro_runs/2026-09-27_fff18_five_cell_view_lattice/README.md)
finds a 13-row SAT table for **every proper** subset of the three
views: Latin-only, each singleton view and each pair of views. Each
SAT table has `P` and all five `A` cells, is partial Latin, and passes
an independent physical scanner in every active view. They need not
be the same table; this establishes separate satisfiability, not a
simultaneous solution.

For all three views together, the exact `F_13({row,col,sym})` CNF is
UNSAT with an independently `VERIFIED` CaDiCaL DRAT proof. The
regenerated full CNF and proof hashes match the earlier certified
five-cell core exactly. Therefore, under this **one fixed ten-row
context and these five cells**, the obstruction is genuinely joint:
no proper subset of view requirements suffices to exclude a 13-row
extension, while the full three-view requirement does.

This is an exact finite result backed by explicit SAT controls and an
independently checked UNSAT certificate, **not** a general theorem that
three views are always jointly necessary. It excludes no other five-cell
pattern, no other ten-row prefix, no whole C243 case, and no arbitrary
order-18 FFF Latin square.
