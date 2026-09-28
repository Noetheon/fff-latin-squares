# Audit-Corrected C271 Dossier

This is the current editable source for both public PDFs. It is a dated
successor to the [frozen C271 edition](../2026-09-28_research_review/README.md),
not a rewrite of that edition or its scientific hashes. The scientific intake
remains **28 September 2026, 10:24:49 UTC, through C271**.

## Corrections

- The compact introduction now requires an odd congruence block size **greater
  than one**. The formal theorem already had this hypothesis. The order-two
  FFF table with singleton equality blocks is the negative control.
- Both versions explicitly tabulate the existing fixed-family consequences of
  1,703 certified inputs, at orders 40, 80, 160 and 320. These are lower bounds,
  not census counts or fresh scans of those very large output families.
- The status note identifies this correction separately from new research.
  C38 remains disproved by the explicit FFF12 example; order 18 remains open.

The sources import no later claims. Their mathematical inputs and finite
reference outputs remain in the [preceding evidence package](../2026-09-28_research_review/README.md).
The independently authored AI audit has a
[hardened derivative](../../../verification/audits/2026-09-28_dossier_hardened/README.md)
with explicit comparison and regression tests; this is not human peer review.

## Rebuild

From the repository root, with TeX Live 2026, `latexmk`, `pdflatex`, and BibTeX:

```sh
python3 -B tools/build_pdfs.py --output .audit/pdf-rebuild
```

Use a new output directory. The normal command checks warnings and byte
identity with the shipped PDFs. `--candidate-only` is for inspecting a proposed
successor and does **not** verify publication bytes. Compiler logs remain in
ignored scratch space, never in the public payload.

Rights remain reserved. Accountable authorship, external mathematical review,
literature priority and a persistent full-data deposit are still open gates.
