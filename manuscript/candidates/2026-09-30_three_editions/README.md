# Compact, Selected Results, and Full Report

Three local review editions of the same research project, based on the
[frozen C280 source](../2026-09-30_research_review/README.md) and the
[typography correction](../2026-09-30_typography_review/README.md).
The evidence cutoff remains **2026-09-30 12:54:17 UTC**. No new mathematical
claim is added and no research scan or proof status is upgraded.

| Edition | Pages | Content |
| --- | ---: | --- |
| Compact | 12 | Definitions in all three views, odd-order/group boundaries, complete product theorems, binary congruences, an explicit nongroup order-8 loop, small-order data and the displayed order-12 counterexample |
| Selected Results | 44 | The former extended compact companion, renamed without changing its mathematical content |
| Full Research Report | 89 | The previous complete report, byte-identical after the deterministic rebuild |

Compact is limited to **12-18 total pages**, not 12-18 pages plus appendices.
The front matter, readable typography, and complete selected proofs are
retained. Further constructions and local search results are deliberately
left to the longer editions. These are not three independent publications.
See the [maintenance policy](../../../docs/PAPER_EDITION_POLICY.md).
In the byte-preserved Full Report, references to its earlier "compact
companion" mean the 44-page material now called Selected Results, not the
new 12-page Compact. A public release must make this edition-name mapping
visible; the old PDF is not silently relabelled as a newly reviewed text.

## Rebuild

Run from the repository root with Python 3.11+ and TeX Live/latexmk:

```sh
python3 -B tools/build_paper_editions.py --output .audit/three-editions-rebuild
python3 -B manuscript/candidates/2026-09-30_three_editions/scripts/check_compact_examples.py --source .audit/three-editions-rebuild/compact/source --output .audit/three-editions-rebuild/compact_examples.json
```

The output directory must be new. PDFs are written to its `pdfs/` subdirectory
as `FFF_Compact_Research_Dossier.pdf`, `FFF_Selected_Research_Dossier.pdf`, and
`FFF_Long_Research_Dossier.pdf`. The build never writes to a historical
candidate, `paper_release/`, or the public repository. It disables TeX shell
escape, uses a fixed timestamp, rejects compiler warnings and rejects an
out-of-budget Compact. It also requires the full report's expected PDF hash.
The immutable [commands](commands.sh) call this candidate's builder directly
and add the optional rendered-PDF checks. Compact additionally uses the
standard `placeins` package so its table cannot float into a later section.

The [catalogue](editions.json) defines roles, filenames, and the page budget.
The builder imports the previous layout builder, then:

- retains the full report unchanged;
- renames only the reader-facing edition labels in Selected Results;
- assembles Compact from complete shared source spans plus new editorial
  framing and a narrowed order-12 computational statement.

Every extraction is bound to unique boundary markers; a changed or ambiguous
marker fails rather than silently cutting a different proof. Build reports
record source and excerpt hashes. Bibliographies and the reused complete
product/closure proofs are inherited without mathematical rewriting.

## Checks and Limits

The compact finite check scans the displayed order-12 table against its
frozen JSON, all 198 induced line pairs, the explicit twisted order-8 loop,
its closure failure and products of orders 16 and 32. It includes group and
odd-order negative controls and all eight frozen order-8 patterns with their
C2 products. Reading the saved census counts is **not** a fresh census scan.

The source tests check references, source selection, label-only Selected
changes, unchanged Long sources, page-budget rejection, and finite positive
and negative controls. Optional PDF checks use the existing
`tools/check_paper_layout.py` with pypdf and pypdfium2. Actual rendered-page
inspection remains mandatory. Commands and outcomes are in
[the final audit](FINAL_AUDIT.md).

All computational census dependencies remain explicit. The order-10
exclusion is background in Compact, not proved there. Order 18 remains open;
no order spectrum, new main-class count, literature priority, human author,
license, or independent expert review is claimed.

**Local candidate only:** no commit, push, or public alias replacement is
performed as part of preparing these editions. The existing public two-PDF
release remains identifiable until a separately authorized update.
