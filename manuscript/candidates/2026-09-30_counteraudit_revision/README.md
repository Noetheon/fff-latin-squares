# Counteraudit Revision and Three Reading Editions

This is the current editorial successor to the frozen C280 dossier.
The mathematical intake remains **2026-09-30T12:54:17Z**. No new theorem,
solver decision, census or claim upgrade is introduced.

| Edition | Total pages | Intended use |
| --- | ---: | --- |
| Compact | 12 | Complete product proofs, required structural lemmas, explicit nongroup order-8 and FFF12 examples |
| Selected Results | 44 | Broader constructions and established structural results; formerly the extended Compact |
| Full Research Report | 89 | Detailed proofs, computational reductions, scoped historical research ledger |

These are three overlapping reading editions, not independent papers.
The short edition's budget is 12-18 total pages, including references.
The [theorem/evidence index](THEOREM_EVIDENCE.md) maps 103 compiled statement
labels to the numbers and printed pages in each edition, plus the important
unnumbered computational claims through C280.

## Corrections Accepted After Independent Checking

- The abstract now names the cycle-type palette reduction and residual-group
  orbit covers; the separate primitive-group necessary condition is not a
  filter used by the master searches.
- C38 is identified as this project's earlier working conjecture. It is not
  attributed to the classical stricter factorization theorem.
- The Cheng--Sgueglia arXiv identifier is actually printed, rather than stored
  only in BibTeX fields ignored by the bibliography style.
- The Erskine--Griggs reference includes its journal version and DOI while
  retaining the precise preprint locator for the rotational starters.
- The new 12-page Compact receives its own proof/dependency and literal-table
  checks; the external review of the former 44/89-page files is not transferred
  to it as an endorsement.
- Literal build commands use verbatim typesetting, preserving double hyphens
  and shell line continuation when copied from the PDF.

The [review and limitations](REVIEW_AND_LIMITATIONS.md) distinguishes confirmed
findings from the external audit's own coverage gaps. Frozen predecessors
are not rewritten. The builder applies counted, fail-closed replacements to
new scratch sources only and records all before/after strings and hashes.

## Reproduce

With Python 3.11+, TeX Live/latexmk and Poppler `pdfinfo`, from the repo root:

```sh
python3 -B tools/build_paper_editions.py --output .audit/paper-check
python3 -B manuscript/candidates/2026-09-30_three_editions/scripts/check_compact_examples.py --source .audit/paper-check/compact/source --output .audit/paper-check/compact_examples.json
python3 -B manuscript/candidates/2026-09-30_counteraudit_revision/scripts/build_evidence_index.py --build .audit/paper-check --output .audit/paper-check/THEOREM_EVIDENCE.md
```

Compare the three generated PDFs with the hashes in `OUTPUTS.sha256`, and
the generated evidence index with the retained index. Fixed-epoch builds
disable shell escape. `tools/check_paper_editions.py --build .audit/paper-check
--render` additionally needs pypdf and pypdfium2. It checks actual PDF flow,
fonts/metadata and the finite examples. Visual inspection is a separate step.

Public clone users may also use `tools/build_pdfs.py`, which checks generated
bytes against the current three PDF aliases. Original scientific sources
remain the [C280 package](../2026-09-30_research_review/README.md); the
[three-edition predecessor](../2026-09-30_three_editions/README.md) records the
editorial extraction. Its original output hashes describe its own earlier
outputs, not this amendment.

The current [edition policy](../../../docs/PAPER_EDITION_POLICY.md) governs
future updates. The successor does not silently edit predecessor bytes.

## Evidence Boundary

C38 is disproved by the directly checked order-12 witness. C157 remains the
historical order-10 computational exclusion; the counteraudit does not rerun
its entire palette/graph/master chain. The represented-class lower bounds
1703/1450956 at orders 20/40 are not censuses. Unrestricted order 18 is open.
Author/rights decisions are unchanged. This is an AI-assisted research
dossier for critical examination, not a refereed article or a claim that
all publication gates have been met.
