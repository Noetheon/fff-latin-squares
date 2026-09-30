# Counteraudit Release Record

## What Changed

The scientific cutoff remains **30 September 2026, 12:54:17 UTC, through C280**.
No claim has been promoted and no current unreviewed research has been imported.

- Compact is now a genuinely short 12-page edition with complete selected
  proofs and direct small-table controls.
- Selected Results retains the former extended Compact's broader content
  in 44 pages. The Full Research Report has 89 pages.
- The order-10 abstract identifies the actual palette/orbit/master chain,
  without presenting the separate primitive-group condition as a search filter.
- The former power-of-two-only conjecture is explicitly a project working
  conjecture, not attributed to prior authors.
- Two bibliography entries have visible, checked publication locators.
- A compiled [theorem/evidence index](../manuscript/candidates/2026-09-30_counteraudit_revision/THEOREM_EVIDENCE.md)
  maps 103 labelled statements to the numbers/pages of each edition, with
  separate entries for important local computational bounds and exclusions.
- The site distinguishes all three reading routes, preserves the evidence
  and AI-origin disclosures, and links directly to the evidence index.

The [critical review](../manuscript/candidates/2026-09-30_counteraudit_revision/REVIEW_AND_LIMITATIONS.md)
distinguishes accepted corrections from unsupported conclusions. The
[candidate audit](../manuscript/candidates/2026-09-30_counteraudit_revision/FINAL_AUDIT.md)
states the mathematical scope of the new Compact review.

## Checked Artifacts

| Check | Result and retained evidence |
| --- | --- |
| Deterministic public rebuild | Three warning-free PDFs, byte-identical; [report](counteraudit_pdf_rebuild.json) |
| Layout/metadata | Front-matter separation, body numbering, embedded fonts, no author metadata, attachments or active content; [metadata](counteraudit_pdf_metadata.json) and candidate `results/edition_checks.json` |
| Bounded scientific replay | Four exact scientific comparison groups pass; [rules and result](counteraudit_current_snapshot.json) |
| Hardened finite audit | 54 source/input/reference hashes, 11 successful stages, 24/24 reference comparisons; [comparison details](counteraudit_finite_comparison.json) |
| Fixed-base transversal counter | Independent C++ rebuild and all four counts match; [report](counteraudit_binary_first.json) |
| Browser checks | Eight viewport sizes, 320 to 1920 pixels; no text clipping/overflow or missing images, keyboard navigation/disclosures pass, zero external runtime requests; [report](counteraudit_site_checks.json) |
| Privacy | Known private-identifier/path scan including PDF text/metadata and PNG metadata; [scope and result](counteraudit_privacy.json) |

All 145 PDF pages were inspected in contact sheets, with enlarged changed
pages, title/status pages, bibliography and reproduction commands. The
website and social preview were visually checked on desktop and mobile.
The default standard-library regression suite and manifest validator are
rerun on the final payload and a clean export before pushing. CI records the
same public gates for the actual published commit.

## Reproduction

From the repository root, with the dependencies in
[Reproducibility](../REPRODUCIBILITY.md):

```sh
python3 -B tools/verify_public_release.py
python3 -B -m unittest discover -s tests -v
python3 -B tools/check_theorem_records.py --output .audit/theorem-records
python3 -B tools/check_current_snapshot.py --output .audit/current-snapshot.json
python3 -B tools/build_pdfs.py --output .audit/pdf-rebuild
python3 -B tools/check_pdf_metadata.py --output .audit/pdf-metadata.json
```

Use new scratch output paths. Build and finite-example commands for the
three editions are in the [dated package](../manuscript/candidates/2026-09-30_counteraudit_revision/commands.sh).
All shipped files are bound by `PUBLIC_MANIFEST.sha256`; the new successor
receipt preserves the earlier receipt chain and permits exactly the two
updated PDF aliases plus the new Selected Results alias.

## What This Does Not Certify

These are internal AI-assisted and computational checks, not independent
human peer review. No full ANU census, complete order-10 master/graph replay,
fresh sweep of historical DRAT proofs or unrestricted order-18 search was
run. The inherited theorem-record audit still reports missing historical
package layout outside the curated public subset; the numerical/status
records pass, which does not repair that separate archive dependency.

The root historical manuscripts are not the current release sources.
C38 is disproved by the explicit order-12 witness. Unrestricted order 18,
literature priority and the full order spectrum remain open. Rights,
authorship, DOI and venue decisions are unchanged. Raw audit archives and
correspondence, private Git history, binaries and local execution logs are
not included in this publication.
