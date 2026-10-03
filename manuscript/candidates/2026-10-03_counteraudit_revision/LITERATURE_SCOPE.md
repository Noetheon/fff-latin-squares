# Targeted Autotopism Literature Comparison

Primary source: D. S. Stones, P. Vojtechovsky and I. M. Wanless,
*Cycle structure of autotopisms of quasigroups and Latin squares*,
Journal of Combinatorial Designs 20 (2012), 227-263.
[Author manuscript, arXiv:1509.05655v1](https://arxiv.org/abs/1509.05655v1).
Inspected on 3 October 2026; this is a targeted comparison, not an exhaustive
priority search or independent expert review.

## Relevant Prior Results

| Location (author manuscript) | Relevant content |
| --- | --- |
| Theorem 3.3, p. 6, attributed there to McKay, Meynert and Myrvold | Necessary fixed-point and cycle-structure alternatives for one autotopism |
| Theorem 3.4, p. 6, crediting earlier work by Sade | Exact cycle-structure criterion when one coordinate permutation is identity |
| Lemma 3.6, p. 7 | Pairwise least-common-multiple restrictions on the three cycle lengths incident with a cell |
| Theorem 3.7, pp. 7-8 | Subsquare consequences from strongly lcm-closed cycle-length sets |

These results concern arbitrary Latin squares. The dossier's selected theorem
also assumes a whole order-nine action and row-F. This is a difference in
hypotheses, not a demonstration of novelty or nonderivability from prior work.
Do not label the result the first such theorem or infer a full FFF18 exclusion
from the source's general autotopism restrictions.

## What the Dossier's Proof Actually Adds to Its Own Argument

The [frozen E9 proof](../2026-10-02_e9_symmetry_review/sections/19_e9_free_coordinates.tex)
uses two regular orbits in each free coordinate. A normal subgroup of order
three fixing a three-row orbit gives six quotient positions. Row-F forces
the relative quotient maps to be fixed-point-free and even-cycled. The
six-point product lemma rules out that orbit. A separate fixed-row argument
bounds globally fixed rows by two, whereas their number is divisible by three.

The general Latin hypotheses alone cannot give this conclusion. The fresh
[controls](scripts/check_review_controls.py) construct the Cayley tables of
C9 x C2 and (C3 x C3) x C2. The order-nine subgroup fixes all 18 rows and acts
freely on columns and symbols, but both tables are TTT. All 2916 literal
autotopy equations are checked for each control. These examples distinguish
the hypotheses; they do not settle literature priority.

## Proposed Cyclic Variant: Valid, Not Promoted Here

The same conditional statement can replace E9 by C9. A subgroup of order
three is still normal, so the size-three orbit argument is unchanged.
For globally fixed rows, translations on regular C9 orbits have lengths
1, 3 or 9; all are odd. Thus the two-orbit bound and the divisibility
argument still apply. Only the exponent-three sentence in the existing
proof needs its odd-order generalization.

This is an inference from the dossier's proof, not a statement attributed
to the cited article. Stronger conclusions under full FFF assumptions
require additional premises and are not interchangeable with this row-F
statement. The current release retains the published E9 theorem unchanged
and records this extension only as a reviewed presentation option. It does
not add a theorem label, claim-number upgrade, new exclusion or construction.

## Disposition

Add the primary reference and explicit scope paragraph to the longer editions.
Retain the written proof and its essential hypotheses. Do not infer an
unrestricted result or novelty merely because the wording differs from
earlier literature. Specialist review of the exact implication remains useful.
