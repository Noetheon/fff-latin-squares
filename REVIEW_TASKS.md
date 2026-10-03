# Three Bounded Review Questions

**AI-generated research dossier. Not peer reviewed.** No accountable scholarly
author or independent expert review of the complete work has been established.
The maintainer does not claim mathematical expertise. See
[AI disclosure](AI_DISCLOSURE.md) and [evidence boundaries](EVIDENCE_STATUS.md).
One precise correction or literature reference is useful; a whole-paper review
is not expected. An automated pass is not a referee endorsement.

Current scope: baseline **2026-09-30T12:54:17Z**, through C280 and the completed
binary-first-orbit companion, plus the selected E9 theorem internally included at
**2026-10-02T14:03:38Z**. Other later campaigns are not included.

An additional focused review target is the
[two-free-coordinate proof](manuscript/candidates/2026-10-02_e9_symmetry_review/sections/19_e9_free_coordinates.tex):
does the odd-fibre argument justify a row-F three-row rectangle without
assuming that it is a full Latin quotient? The displayed mixed rectangle
limits the stronger interpretation. This does not replace the three entry
questions below or request a whole-paper review.

## 1. Check the Two Illustrated Cycles

**Question:** comparing row 0 with row 1, do equal-symbol matches give
`0 -> 1 -> 0` in the [order-8 table](examples/order8_fff.json), and
`0 -> 2 -> 1 -> 0` in the [order-3 table](examples/order3_nonfff.json)?
These are column labels, not symbol values. This can be checked by hand.

Optional code check, from the repository root with Python 3.11+:

```sh
python3 -B tools/demo_fff.py
python3 -B tools/demo_fff.py examples/order3_nonfff.json
```

The complete checks should report `pattern=FFF FFF=True` for order 8 and
`pattern=TTT FFF=False` for order 3. See the
[expected permutations and cycles](examples/expected_results.json).
One illustrated pair does not establish FFF: every pair in all three views
must pass. This is a check of two tables, not a census or an order-10 proof.

**Useful response:** one matching step or cycle that disagrees, with the row
and column labels. For a code discrepancy, include the command, Python version
and input hash. An independently written checker is welcome, not required.

## 2. Check One Step in the Product Proof

**Question:** in the pattern-product theorem, does holding the other factor's
line fixed correctly preserve an odd cycle from a factor in the product?

Read the identity-factor paragraph and its use in the
[direct-product proof](manuscript/candidates/2026-09-30_research_review/sections/04_direct_products.tex).
The induced permutation is a product of two permutations. With one line fixed,
that factor is the identity, and a cycle of length `m` pairs with a fixed point
to give length `lcm(m,1)=m`. Check that the two product lines remain distinct.

The [statement index](manuscript/candidates/2026-09-30_counteraudit_revision/THEOREM_EVIDENCE.md#direct-products)
locates the theorem in each PDF (Compact Theorem 4.2). Checking this one step
is not a review of the converse, the other views or the full dossier.

**Useful response:** a missing hypothesis, a precise explanation of why the
step holds, or a counterexample to that step. A whole-paper review is not expected.

## 3. Identify an Earlier FFF Criterion

**Question:** is the exact three-view criterion for the classical prime
round-robin table already in the literature, perhaps under different terminology?

The [statement and construction](manuscript/candidates/2026-09-30_research_review/sections/08_nonpower_fff.tex)
use an odd prime `p` and the midpoint table on `F_p` together with an infinity
symbol. The stated criterion is FFF if and only if `p = 3 (mod 8)`.
See `thm:prime-round-robin-fff` in the
[statement index](manuscript/candidates/2026-09-30_counteraudit_revision/THEOREM_EVIDENCE.md#non-power-of-two-examples-and-lift-bound).

The round-robin construction is classical and explicitly credited. The question
is the precise overlap with this additional all-three-view cycle condition,
not whether the construction itself is new. Literature priority is not established.

**Useful response:** author, title, year, theorem/page and a stable reference,
with a short explanation of the overlap. An unsuccessful search or agreement
between AI systems does not establish novelty.

## Further Optional Audits

Choose one item; these are not prerequisites for answering the questions above.

- [Triangle and anchor proofs](manuscript/candidates/2026-09-30_research_review/sections/16_crossview_near_triangles.tex):
  audit one finite premise or one of the distinct 31/13 normalization covers.
- [Binary-fibre theorem](manuscript/candidates/2026-09-30_research_review/sections/17_binary_transversal_lifts.tex):
  audit one of component parity, the lift count, or the same-projection obstruction.
- [Portable reproduction](REPRODUCIBILITY.md): independently check FFF12 or the
  1703 represented order-20 classes; these are not a global order-20 census.
- The fixed-base count of 72,474,624 labelled firsts / 18,118,656 free-four
  representatives is not mate coverage. Only 18 selected supports / 9,216 firsts
  have arbitrary-mate exclusions; 138,468 liftable supports remain outside them
  at this snapshot. Check that boundary separately from any first-transversal count.
- [Order-10 reduction](proof_notes/fff_six_type_master_reduction_degree10.md):
  audit coverage of the two disjoint masters. The public export omits the large
  master graphs/checkpoints; default checks do **not** replay those searches.

## Respond

Use [Discussions](https://github.com/Noetheon/fff-latin-squares/discussions) for
focused review and literature questions; use
[Issues](https://github.com/Noetheon/fff-latin-squares/issues) for concrete errors.
Distinguish a written argument, executed computation, formal certificate and
human expert review. The former power-of-two conjecture is disproved by FFF12;
unrestricted order 18 and the full order spectrum remain open.
