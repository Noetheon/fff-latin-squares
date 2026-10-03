# Selected E9 Symmetry Extension, 2 October 2026

An internally checked, AI-generated research dossier, **not peer reviewed**.
This successor keeps the [counteraudit predecessor](../2026-09-30_counteraudit_revision/README.md)
and all earlier evidence frozen. It contains the C280 baseline
(`2026-09-30T12:54:17Z`) plus one selected analytic result accepted at
`2026-10-02T14:03:38Z`, not every intervening research campaign.

## Added Result

For a row-F Latin square of order 18 with an actual coordinate-preserving
action of `C3 x C3`, free column and symbol actions force a free row action.
For an FFF square this applies to any placement of the three coordinates.
The [complete proof](sections/19_e9_free_coordinates.tex) includes a six-point
permutation lemma, the three-row odd-fibre quotient, and a separate fixed-row
argument. No solver certificate or full action classification is a premise.

This does **not** force such symmetry, decide free or asymmetric cases, or
settle unrestricted FFF18. C38 remains disproved by the order-12 example.
There is no new global existence/nonexistence claim or numbered register entry.
Literature priority and independent expert review remain unestablished.

## Three Reading Editions

- Compact: 12 total pages. Its complete proof selection is unchanged; the
  status note identifies the selected extension in the longer editions.
- Selected Results: 46 total pages, including the complete new proof.
- Full Research Report: 91 total pages, including the same complete proof.

They share one evidence base and overlap; they are not three independent
papers. The [edition plan](editions.json) and [compiled statement index](THEOREM_EVIDENCE.md)
identify scope and edition-specific numbering.

## Reproduction

Python 3.11+ and the standard library suffice for the new finite control:

```sh
python3 -B tools/check_e9_symmetry.py --output .audit/e9-control
```

The wrapper copies the **byte-identical independently written internal review
script** into a new output directory and compares its result with the frozen
target. Only Python version and measured runtime vary; all mathematical fields,
source identity and coverage must match. The script checks all 1600 ordered
two-`3+3` products, 1600 mixed products, 18 odd-fibre maps, literal E9 quotient
actions and the displayed mixed row-F rectangle. The mixed control prevents
an unjustified extension to `3+1+1+1` factors.

```sh
python3 -B tools/build_paper_editions.py --output .audit/e9-editions
python3 -B tools/check_paper_editions.py --build .audit/e9-editions --render
python3 -B tools/check_current_snapshot.py --output .audit/e9-snapshot.json
python3 -B tools/check_theorem_records.py --output .audit/e9-records
python3 -B -m unittest discover -s tests -v
python3 -B tools/verify_public_release.py --pdf-metadata
```

PDF generation uses the predecessor's reviewed TeX pipeline, with counted
source substitutions and one shared added section. No predecessor is edited.
`SOURCE_DATE_EPOCH` is fixed; byte-identical rebuilds require compatible TeX,
fonts and bibliography tool versions. PDF checks require the optional PDF
dependencies described in the [public reproduction guide](../../../REPRODUCIBILITY.md).

See [review and limits](REVIEW_AND_LIMITATIONS.md),
[source provenance](SOURCE_PROVENANCE.json), and
[release checks](../../../verification/RELEASE_2026-10-02.md).

Rights remain reserved. AI-origin disclosure, the absence of an accountable
scholarly author, and lack of independent human peer review are unchanged.
