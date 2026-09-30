# Three Reading Editions: Final Internal Audit

Date: 30 September 2026. Scope: editorial selection and reproducible local
PDF candidates, not a new mathematical campaign or a public release.

## Verdict

The three-reading-edition arrangement is suitable for local critical review:
Compact has **12 total pages**, Selected Results **44**, and the Full Research
Report **89**. The latter is byte-identical to the preceding typography PDF.
All share the C280 evidence cutoff of 12:54:17 UTC. They are overlapping
reading editions, not independent publications.

The candidate is **not** described as journal-ready or externally refereed.
No commit, push, licence change, author attribution, or public PDF replacement
is part of this task. The active primary research checkout and the public
repository remain outside the edit scope.

## Scientific Selection Review

- Compact contains the complete three-view definitions and invariance proof,
  odd-order and group-table boundaries, closure criterion, pattern OR proof,
  group-isotopy product equivalence and the binary-congruence argument needed
  for the explicit nongroup order-8 example. Its referenced results are present.
- The small-order and order-8 statements remain labelled computational and
  retain their census dependency. Asymmetric ordered patterns are not described
  as main-class invariants. The higher-order product consequence is existence,
  not a count or an injectivity claim.
- The order-12 statement is narrowed to the displayed, directly checked table;
  it refutes the former power-of-two-only conjecture. The order-10 result is
  explicitly imported background, not a proof supplied by Compact. Order 18
  remains open.
- Selected Results changes only the edition labels in four assembled files.
  Full mathematical sections and bibliographies are inherited. Historical
  files and the claim register are unchanged.
- The unchanged Full PDF retains the old companion terminology. Its former
  compact companion corresponds to Selected Results; the new Compact is a
  separate, narrower reading edition. This mapping is documented rather
  than claiming every internal cross-edition phrase has been modernized.
- No fresh novelty assessment, exhaustive order-8 scan or order-10 master
  rerun is claimed. Internal checking is not independent human peer review.

## Executed Checks

- Three warning-free latexmk builds at 11 pt on A4; fixed epoch and disabled
  shell escape. Fresh repeated builds agree in all three PDF hashes.
- Source selection rejects missing/ambiguous markers, and checks reference
  closure, retained mathematical sources and the strict 12-18 total-page
  budget. Six new regression tests pass, including negative controls.
- Fresh literal scans confirm the displayed order-12 input and all 198 pairs;
  the explicit nongroup order-8 loop and its nonassociativity/closure failure;
  nongroup FFF products of orders 16 and 32; a group control; an odd-order
  negative control; all eight frozen order-8 patterns and their C2 products.
- PDF checks pass for all three: distinct title/status/contents/body pages,
  Roman front matter followed by Arabic page 1, reference destinations,
  no unresolved references or empty pages, and no glyphs outside the safety
  margins. Author metadata is empty, all fonts are embedded, and there are no
  attachments, JavaScript or launch actions.
- Rendered review covers every Compact page and the changed Selected title,
  declarations, introduction and reproducibility pages. A sample of the
  unchanged Full PDF is checked; its complete byte identity is the preservation
  guarantee, not a claim of a new line-by-line 89-page mathematical review.
- `make audit` passes: 1146 tests, 13 documented prerequisite-dependent skips,
  historical manifests, knowledgebase snapshot, dated nonpower gate, semantic
  and computational checks, diff checks, and tracked-evidence preservation.
  Skips concern absent ignored CNF/proof artifacts and an optional PySAT check.

During preview, math-mode heading text caused PDF-bookmark warnings and a table
crossed the next section. The final version uses a plain bookmark heading,
keeps the census heading/table together, enlarges the order-12 table, and
confines floats to their sections. Body sections flow normally; a forced
discussion break was removed to avoid a nearly empty continuation page.

## Explicitly Not Performed

`make audit-full` and heavy historical solver reruns are not part of this
editorial task. The cheap audit correctly still reports
`publication_ready=false` and `blocked_historical_manuscript` for the old
root manuscript. That historical gate is not bypassed or rebranded by these
new candidate checks. A public three-PDF release, portable evidence delivery,
accountable authorship, rights decision, venue requirements, priority and
independent review remain separate work.

## Records

The [build and check commands](commands.sh), [catalogue](editions.json),
[build record](results/edition_build.json),
[PDF checks](results/edition_checks.json),
[finite controls](results/compact_examples.json), and
[repository/rebuild summary](results/repository_and_rebuild_summary.json)
record the reproducibility boundary. `INPUTS.sha256` is relative to the
repository root; `MANIFEST.sha256` is relative to this candidate; the PDF
filenames in `OUTPUTS.sha256` are relative to a build's `pdfs/` directory.
