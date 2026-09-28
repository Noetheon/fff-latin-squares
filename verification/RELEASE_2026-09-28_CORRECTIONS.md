# Audit-Corrected C271 Release

Date: 28 September 2026. Scientific intake unchanged at 10:24:49 UTC, C271.
Internal AI-assisted counteraudit and bounded execution, not human peer review,
journal acceptance, novelty clearance or a decision at order 18.

## Confirmed Corrections

| Finding | Resolution | Evidence boundary |
| --- | --- | --- |
| Compact introduction omitted the nontrivial odd block size hypothesis | Added "greater than one" in the dated successor | Formal theorem was already qualified; C2 with singleton equality blocks remains FFF |
| Assertion checks could vanish under Python optimization | Reject optimized interpreters and force non-optimized children | Tested `-O`, `-OO`, environment optimization and a deliberately corrupted count |
| Two C++ inventory errors returned success | Exceptions reach a nonzero `main` exit | Both actual branches fault-injected in scratch copies |
| Inner Python runner did not propagate failure | Child failure now terminates orchestration | Injected exit 7 propagates with a saved partial receipt |
| Audit reproduction did not compare references automatically | Hash preflight plus 24 mandatory fresh/reference comparisons | Only explicitly named runtime fields excluded; altered counts, missing output and array reordering fail |
| Unexpected binary file crashed public verification | Report forbidden or non-text payload without a decode crash | `.DS_Store`, invalid UTF-8, NUL content and secret-marker controls |
| Current source links and strengthened bounds were incomplete | Corrected links, edition notice and T_d(1703) table in both papers | No new theorem or higher-order census |

The original AI audit was critically checked rather than accepted on authority.
Its original archive SHA-256 is
`ea24f632dc6519d73e3557c731a333ee0c4488cacc013fcc4f74486716ed4a65`.
The [derivative provenance](audits/2026-09-28_dossier_hardened/DERIVATION.json)
separates original and repaired source hashes. Neither private conversation nor
the raw archive is published.

## Executed Checks

- The [external derivative rerun](audits/2026-09-28_dossier_hardened/VALIDATION.json)
  completed all eleven steps, nine inherited Python checks and three compiled
  inherited C++ programs. All 24 explicit reference comparisons pass. Its
  outer-step runtime was 48.278601 seconds on arm64 macOS with Python 3.14.6
  and Apple Clang 21.0.0. This is a reproducibility observation, not a benchmark.
- All 22,528 fixed-family masks were enumerated afresh: 19,480 FFF, 3,048 TTT,
  and 1,700 FFF spectra. Three additional controls give the lower bound 1,703.
  All 1,703 physical tables, 970,710 line pairs and rank-58 certificates pass.
- The existing [public scientific auditors](corrections_scientific_controls.json)
  also pass and exactly match their mathematical reference fields, including
  91,134 CRT returns and 364,536 coefficient/slope probes. These share some
  arithmetic code; do not call them wholly independent constructions.
- Thirteen historical theorem records pass their numerical/status adapter.
  The intentionally incomplete historical package layout is still reported
  separately, not hidden as a full legacy reproduction success.
- All 36 regression tests pass locally, including the optimization and C++
  fault injections; none was skipped. Public payload hashes, PDF author and
  attachment checks, staged privacy/file-scope checks and local links pass.
  Poppler's full executable directory was added to the local PATH for the
  metadata check after the initial PATH lacked `pdfdetach`.
- The [PDF rebuild](corrections_pdf_rebuild.json) produces **38 compact pages
  and 80 long pages**, no TeX warnings, and byte-identical results on a second
  clean build with the fixed epoch and TeX Live 2026.
- [Rendering checks](corrections_pdf_visual_review.json): all 118 pages rendered
  nonblank and inspected in overview, with detailed inspection of the corrected
  introduction, status note and strengthened table. No clipping or overlap was
  observed. This is a layout review, not a formal mathematical proof.
- [Website checks](corrections_site_checks.json): eight viewports, working PDF
  previews and links, keyboard controls, and no overflow. Current page previews
  and the site's social-preview asset were regenerated from the actual PDFs.
  The separate GitHub repository-preview setting is not changed by this commit.

## Frozen Sources and Alias Reconciliation

[The new receipt](../PUBLIC_SNAPSHOT_2026-09-28_CORRECTIONS.json) binds the exact
preceding receipt and keeps **196 historical source/input/output files unchanged**.
Only its two public PDF aliases are superseded, with explicit old/new digests.
All preceding dated sources, scientific reference outputs and receipts remain
read-only. The package-wide derived manifest records the new public payload.

The public history remains separate from the private research repository.
Concurrent, unreviewed private research changes are not imported. No raw chats,
archives, binaries, personal Git identity or software environment are included.

## Reproduction and Gates

From the repository root, using fresh output directories:

```sh
python3 -B tools/verify_public_release.py --pdf-metadata
python3 -B -m unittest discover -s tests -v
python3 -B tools/check_theorem_records.py --output .audit/theorem-corrections
python3 -B tools/check_current_snapshot.py --output .audit/science-corrections.json
python3 -B verification/audits/2026-09-28_dossier_hardened/scripts/reproduce_all.py \
  --work-dir .audit/external-corrections
python3 -B tools/build_pdfs.py --output .audit/pdf-corrections
git diff --check
git diff --cached --check
```

Poppler is needed for `--pdf-metadata`, C++17 for the external rerun, and TeX Live
for PDF rebuilding. The default Python audit requires no third-party packages.
The compiler-dependent fault injections explicitly skip when `g++` is absent.
CI runs the bounded external audit in a separate job; this does not launch the
large search archive or any solver.

C38 remains disproved by FFF12. **Order 18 remains open.** The full C157 master
graph/search replay, old proof-certificate chains, new full ANU census rerun,
literature priority, accountable authorship, independent expert review and a
durable complete archive were not completed by this correction. Rights remain
reserved. No claim register status is changed.
