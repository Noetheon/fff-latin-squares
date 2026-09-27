# Three Bounded Review Questions

**AI-generated research dossier. Not peer reviewed.** No accountable scholarly
author or independent expert review of the complete work has been established.
The maintainer does not claim mathematical expertise. See
[AI disclosure](AI_DISCLOSURE.md) and [evidence boundaries](EVIDENCE_STATUS.md).
One precise correction or literature reference is useful; a whole-paper review
is not expected. An automated pass is not a referee endorsement.

## 1. Proof: Intrinsic Layers and the Construction Boundary

Read the [binary quotient descent proof](manuscript/candidates/2026-09-27_research_snapshot/evidence/proofs/fff_binary_quotient_descent_and_dyadic_class_growth.md)
and [affine-orbit classification](manuscript/candidates/2026-09-27_research_snapshot/evidence/proofs/fff_affine_orbit_fibre_classification.md).
Do the quotient-free hypotheses recover the intrinsic layers in all three
views, and do they justify both directions of the stated within-construction
classification? Identify any inference that would improperly become a global
direct-product cancellation claim.

Useful response: the exact paragraph, the questionable inference, and either a
replacement argument or an explicit table. Review the precise hypotheses, not a
claim that all FFF squares belong to this construction.

## 2. Reproducibility: Check a Table, Then the Coverage Boundary

Run the [small example and negative control](examples/README.md). Do the direct
matching equations and cycle reports agree with an independently written checker?
Please report Python version, command, input hash and the first disagreement.
Then run `python3 -B tools/check_current_snapshot.py --output .audit/review.json`:
can an independently written scanner reproduce the explicit order-12 witness
and the distinction between 512 classes in one trade family and a global lower
bound of 514? No global order-20 census is claimed.

For a deeper optional check, inspect the
[two-master reduction](proof_notes/fff_six_type_master_reduction_degree10.md):
do the disjoint cases cover the claimed scope, and are the exported records
sufficient to identify every dependency needed for an independent rerun?
The public export omits the large master graphs/checkpoints. Its default checks
do **not** rerun the order-10 searches; that archive gap remains explicit.

## 3. Literature: Known Results or Earlier Constructions

For the affine prime-successor criterion, row-fibred pattern formula,
or intrinsic-layer classification, is there an earlier theorem or equivalent
construction that should be cited or should change the novelty framing?
See the [current source and evidence map](manuscript/candidates/2026-09-27_research_snapshot/README.md).
The classical prime round-robin construction is explicitly credited rather
than presented as a new construction.

Useful response: author, title, year, theorem/page and a stable reference,
together with the precise overlap. Novelty is not established by a failed
keyword search or by AI agreement.

## Respond

Use [Discussions](https://github.com/Noetheon/fff-latin-squares/discussions) for
focused review and literature questions; use
[Issues](https://github.com/Noetheon/fff-latin-squares/issues) for concrete errors.
Distinguish a written argument, executed computation, formal certificate and
human expert review. The former power-of-two conjecture is disproved by FFF12;
unrestricted order 18 and the full order spectrum remain open.
