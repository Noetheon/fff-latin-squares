# Fixed-remainder contraction of all eligible FFF20 row-trade masks

Status: rigorous transfer lemma (A), exact complete family computation
(B), and an independently checked frozen source reference (B). This
is a **construction-family exclusion**, not an order-18 nonexistence
theorem. The [dated package](../repro_runs/2026-09-27_fff20_all_pair_trade_contractions/README.md)
contains the full cover, commands and hashes.

## Transfer of inherited completion spaces

Let `Q` be obtained from a Latin square `L` by a two-row cycle trade in
rows `a,b`. Choose an intercalate deletion with deleted rows exactly
`a,b`, deleted columns `c,d`, and deleted symbol set `{s,t}`. Suppose
the same row/column/symbol sets form an intercalate deletion of `L`.
All cells in retained rows are identical in `L` and `Q`. In each retained
column, the **set** of the two values in deleted rows is identical,
because the trade merely swaps those two entries. The two entries
removed from each retained row are also identical. Therefore the
retained row/column index sets, missing-symbol sets, hole positions,
and every replacement domain coincide. The complete finite sets of
Latin hole fillings are identical, not merely equinumerous. The run
checks equality of the full component-choice profiles for every
instance declared inherited.

The all-zero mask is the frozen source. Complementing all ten trade
components globally swaps the selected rows, so the all-one mask is
isotopic to the source. C251's independently checked source-contraction
reference proves that **all 9,728** Latin completions over all source
intercalates have pattern `TTT`. Thus no source-equivalent or exactly
inherited context can yield FFF18. C251's three-sort transport proof
extends each finite table conclusion to its main class; it does not
make distinct tables with equal cycle spectrum equivalent.

## Complete finite cover and new contexts

C252 enumerates all 22 eligible row pairs and all 1,024 masks per pair
of one frozen FFF20 source. Exactly 19,480 mask instances are FFF.
The companion screen independently revisits every such instance.
Forty-four masks (zero and all-one in each pair family) are source-
equivalent. Among all remaining masks it inspects 10,889,168
intercalate instances and finds 19,532 Latin-feasible deletion contexts.
The exact-choice-profile transfer applies to 19,418 contexts. The
remaining **114** contexts have 21,504 labelled Latin completion paths
and 14,336 distinct order-18 tables across pairs. Two independently
implemented physical three-view scanners agree on every distinct
table's odd-pair counts; every novel table has at least one row-view
odd-cycle pair (zero novel row-F paths). Thus none is FFF.

Hence **no FFF20 table in this complete 22-pair trade-mask family**
produces an FFF18 square via fixed-remainder two-point contraction.
The two separately frozen quadratic FFF20 controls remain excluded by
C251's zero Latin completions. This enlarges the represented input
family covered by the precise contraction obstruction. It does not
screen all FFF20 main classes, all FFF20 tables sharing any of these
spectra, repairs changing retained cells, or arbitrary order-18 Latin
squares. Literature priority and external human review remain open.
