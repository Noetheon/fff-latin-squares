# Three Bounded Review Questions

**AI-generated research dossier. Not peer reviewed.** No accountable scholarly
author or independent expert review of the complete work has been established.
The maintainer does not claim mathematical expertise. See
[AI disclosure](AI_DISCLOSURE.md) and [evidence boundaries](EVIDENCE_STATUS.md).
One precise correction or literature reference is useful; a whole-paper review
is not expected. An automated pass is not a referee endorsement.

## 1. Proof: Two-Element Congruence Blocks

Read Theorem 3 in
[the congruence proof note](proof_notes/fff_subsquare_and_congruence_obstructions.md).
Does the argument establish the stated pattern equality in **each** of the row,
column and symbol views, including the converse lifting of an odd quotient
cycle? Is there a missing hypothesis or a counterexample?

Useful response: the exact paragraph, the questionable inference, and either a
replacement argument or an explicit table. The note is historical; its old
order-10-open wording is superseded by [current status](EVIDENCE_STATUS.md).

## 2. Reproducibility: Check a Table, Then the Coverage Boundary

Run the [small example and negative control](examples/README.md). Do the direct
matching equations and cycle reports agree with an independently written checker?
Please report Python version, command, input hash and the first disagreement.

For a deeper optional check, inspect the
[two-master reduction](proof_notes/fff_six_type_master_reduction_degree10.md):
do the disjoint cases cover the claimed scope, and are the exported records
sufficient to identify every dependency needed for an independent rerun?
The public export omits the large master graphs/checkpoints. Its default checks
do **not** rerun the order-10 searches; that archive gap remains explicit.

## 3. Literature: Known Results or Earlier Constructions

For the direct-product pattern formula, the group-isotopy product criterion,
or the explicit order-8 loop, is there an earlier theorem or equivalent
construction that should be cited or should change the novelty framing?
See [direct products](manuscript/sections/04_direct_products.tex) and
[the explicit construction](proof_notes/fff_subsquare_and_congruence_obstructions.md).

Useful response: author, title, year, theorem/page and a stable reference,
together with the precise overlap. Novelty is not established by a failed
keyword search or by AI agreement.

## Respond

Use [Discussions](https://github.com/Noetheon/fff-latin-squares/discussions) for
focused review and literature questions; use
[Issues](https://github.com/Noetheon/fff-latin-squares/issues) for concrete errors.
Distinguish a written argument, executed computation, formal certificate and
human expert review. The global power-of-two conjecture remains open; the
recorded order-10 exclusion does not settle order 12 or higher orders.
