# Typography and Scholarly-Presentation Audit

This correction responds to a reader-reported defect in the first C280 PDF:
the contents started below the status prose, continued onto the next page, and
the introduction followed immediately. Two-digit section numbers were cramped.
The preceding AI-assisted visual review missed these defects. Its claims of a
completed layout review were too broad; compilation and nonblank pages did not
establish satisfactory page composition.

## Corrections

- Both editions use dedicated pages for title/abstract, status and contents.
  The introduction starts on the next page, with Arabic page 1.
- Front matter has Roman labels. PDF destinations remain clickable.
- Contents are black, regular-weight, with a 2.6 em number column and dot leaders.
- The abstract is one paragraph, below 250 whitespace-delimited words.
  Detailed claims and their qualifications remain in the unmodified body.
- The closing discussion and references start on separate pages.
  References use a readable 10 pt size in the 11 pt article class.
- Widow/orphan controls are explicit. All pages are rerendered, and a new
  PDF-level check verifies the actual page boundaries, labels, blank pages,
  unresolved-reference markers and outer glyph margins.

The template remains standard LaTeX article with AMS mathematics, Latin Modern,
microtype and A4/30 mm margins. It is not a publisher-branded journal template.
An isolated contents page is a deliberate report-layout choice and the user's
requirement, not a universal rule for every mathematical journal.

## Executed Checks

The final editions have 44 compact pages and 89 long pages. The abstract has
205 whitespace-delimited words. Both PDFs put Introduction on physical page 4,
printed page 1; Contents is entirely on physical page 3. References start on
physical pages 44 and 88 respectively.

All 133 pages were rendered and reviewed as contact sheets; front matter,
closing transitions and references were inspected at larger scale. A second
layout build changed only the two closing transitions and contents page in
each edition; those final pages were inspected again. All other page-image
hashes matched the previously inspected renders. The PDF-level margin scan
found no glyphs within 20 points of an outer page edge.

All 63 public standard-library regression tests pass, including negative
controls for the reported page-flow defect and receipt-chain preservation.
Both PDFs rebuild byte-for-byte with no TeX reference, package or box warnings.
The metadata/font check and eight website viewport checks pass.
The public workflow now includes a separate PDF-layout job, so page-flow and
metadata checks apply to the actual committed PDF files, not just the TeX source.
These checks do not imply a new mathematical proof audit.
The check was also run against the exact previously published 88-page PDF:
it rejected the shared status/contents page, introduction placement, numbering
and missing references destination as intended. The negative-control result
is [recorded separately](typography_predecessor_rejection.json), not counted
as a release failure. All four bounded current-snapshot scientific comparisons
also [passed again](typography_current_snapshot.json); heavy solvers and
historical UNSAT proof replays were not rerun for this layout correction.

| Edition | SHA-256 |
| --- | --- |
| Compact | f6cc0b56641b220323c23984eaaf5d6b2c09de8ce715fb02aeefaa9dbbb0d3e6 |
| Long | 836864560ee69c4bbfce14ebbcb848c983f39d0f006c1454c5c22eb58d7be81a |

Machine reports: [compact page flow](typography_compact_layout.json),
[long page flow](typography_long_layout.json), [rebuild](typography_pdf_rebuild.json),
[metadata](typography_pdf_metadata.json), [website](typography_site_checks.json).

## Scientific-Presentation Checklist

| Area | Finding / boundary |
| --- | --- |
| Title, abstract, keywords, MSC | Present. Abstract shortened; no bibliography-dependent citation is required to understand it. |
| Definitions, theorem labels, proofs | Retained exactly from the reviewed C280 source. Presentation changes are not a new proof certification. |
| Computational statements | Reduction, finite evidence and bounded search coverage remain separately labelled. |
| Claim status | C38 remains disproved by the explicit FFF12 witness. Unrestricted FFF18 remains open. No new claim or census. |
| Bibliography and cross-references | BibTeX and repeated TeX passes resolve the cited keys and cross-references; this is not a complete literature-priority assessment. |
| Original source preservation | All 33 inherited section/bibliography files are compared byte-for-byte at build time. Four front-matter/entry/style overrides are explicit. |
| Data and code access | Public reproduction and exact manifests are present. The complete historical solver archive is not shipped; no full archival-reproducibility claim. |
| AI attribution | Disclosed on its own status page; no AI system is assigned scholarly authorship. |
| Accountable authorship | Unresolved. The initiator does not claim mathematical expertise or personal mathematical authorship. No identity or affiliation is invented. |
| Novelty and external expert review | Not established. An AI/code audit is not human peer review. |
| Rights and target journal | Rights reserved; no venue selected, submission made, DOI assigned or acceptance asserted. |
| Accessibility | Searchable text, bookmarks, links and embedded fonts are checked. PDF/UA or tagged-PDF compliance is not certified. |

**Verdict:** a typography-corrected, openly labelled research dossier for
examination, not a certificate that all requirements of an unspecified journal
or all standards of scientific validity have been met. Accountable authorship,
external mathematical assessment, literature priority, rights and a complete
durable evidence deposit remain substantive publication gates.

## External Standards Consulted

The [AMS Author Handbook](https://www.ams.org/arc/journals/packages/proc/proc_amslatex/Author_Handbook_Journals.pdf)
supports a descriptive title, self-contained abstract, classification and
structured top matter. Its journal-specific production rules are not claimed
to govern this independent dossier.

The [SIAM SIOPT author instructions](https://epubs.siam.org/siopt/instructions-for-authors)
request a concise one-paragraph abstract, keywords/classification and black
print text. The 250-word cap is adopted here as an editorial target, not
presented as a universal mathematical standard.

[SIAM's AI guidance](https://www.siam.org/publications/siam-news/articles/a-contract-of-trust-artificial-intelligence-usage-for-siam-journal-submissions/)
emphasizes human responsibility and disclosure. Formatting cannot substitute
for either. Consulted 30 September 2026.
