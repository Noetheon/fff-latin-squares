# Typography-Corrected Research Dossier

This is a layout and front-matter successor to the
[frozen C280 research edition](../2026-09-30_research_review/README.md).
It does not introduce a mathematical claim or extend the evidence cutoff
of 30 September 2026, 12:54:17 UTC.

## Template and Page Structure

The class is standard LaTeX article, 11 pt, A4 with 30 mm margins,
Latin Modern text, AMS mathematics, and microtype. This is a neutral
research-report layout, not an AMS or SIAM journal template.

Both editions now have separately paginated front matter:

1. Title, concise abstract, keywords and MSC codes.
2. Status, AI attribution and evidence boundary.
3. Contents on its own page, with adequate two-digit number spacing.
4. Introduction on a fresh page, starting Arabic page 1.

The closing discussion and references each start on a new page;
references use small, not footnotesize.
Links remain clickable but print in black. Widow and orphan controls and
ragged-bottom setting prevent isolated paragraph lines and stretched pages.
Ordinary body sections still flow normally; not every section starts a new page.

## Frozen Sources and Rebuild

Only the two entry sources, paper_setup.tex and the abstract are overridden.
The builder assembles the remaining sources from the frozen C280 package into
fresh .audit/ scratch space. It checks byte identity for every inherited
mathematical section, status declaration and bibliography.
The original package and its manifests are not rewritten.

Run the repository-root tools/build_pdfs.py with --output .audit/typography-rebuild.
The TeX dependencies include tocloft. The existing TeX Live / latexmk
installation is used with shell escape disabled. No local font or private
input is needed. The optional PDF layout audit requires pypdf.

## Review Boundary

The preceding visual review missed the front-matter page-flow defect reported
by the reader. This correction adds explicit PDF page-boundary checks rather
than treating nonblank pages and successful compilation as sufficient.

Scientific validity, literature priority, accountable human authorship,
rights, a target venue, and expert review are not established by typography.
The source-level mathematical review and computational checks remain those
of the C280 edition. Unrestricted FFF18 is still open.
