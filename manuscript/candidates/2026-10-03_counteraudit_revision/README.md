# Counterreview Revision, 3 October 2026

Three reading editions of an AI-generated research dossier, **not peer
reviewed**. This successor keeps the [E9 predecessor](../2026-10-02_e9_symmetry_review/README.md)
and all earlier evidence unchanged. The research cutoff is still the C280
baseline of 30 September plus the E9 theorem included in the internal
evidence snapshot on 2 October at 14:03:38 UTC.

## Changes and Limits

- Define sign-trade size as k selected cycle positions, hence 2k changed
  cells. The sign identity is unchanged.
- Replace the existence corollary's census premise with eight explicit,
  printed order-8 witnesses and the existing product theorem. The separate
  230-class and 5/225 counts still depend on the census.
- Correct current-source navigation, the three-edition description and the
  meaning of internal acceptance.
- Add a [targeted primary-literature comparison](LITERATURE_SCOPE.md). The
  E9 theorem is retained; the optional C9 variant is not promoted to a new
  published theorem or counted as new unrestricted progress.
- Provide a strict successor comparison tool for the third-party audit:
  missing keys are distinct from null; numeric types, duplicate keys,
  non-finite values, output inventories and declared exclusions are checked.

Compact has **12 total pages**, Selected Results **47**, Full Report **92**.
See the [edition contract](editions.json), [compiled evidence map](THEOREM_EVIDENCE.md)
and [review disposition](REVIEW_AND_LIMITATIONS.md).

**C38 is disproved by the order-12 witness; unrestricted FFF18 is open.**
No new global theorem, claim-register upgrade, full order-8 census, order-10
master replay or second-transversal exclusion is claimed.

## Reproduce the New Controls

Python 3.11+ standard library:

~~~sh
python3 -B manuscript/candidates/2026-10-03_counteraudit_revision/scripts/check_review_controls.py \
  --output .audit/counterreview-controls.json
python3 -O -B manuscript/candidates/2026-10-03_counteraudit_revision/scripts/check_review_controls.py \
  --output .audit/counterreview-controls-optimized.json
python3 -B -m unittest discover -s tests -v
~~~

Normal and optimized control outputs must be byte-identical. These controls
import neither the inherited census scanner nor the third-party scanner.
They check all eight printed tables, their C2 products, malformed tables,
odd/even trades in every view, the six-point lemma and ordinary-Latin
negative examples for the symmetry hypothesis.

The optional [strict audit comparator](../../../tools/compare_external_audit_20261003.py)
accepts the separately obtained frozen audit package and an already completed
replay. It does not execute imported code or certify the optional PDF check:

~~~sh
python3 -B tools/compare_external_audit_20261003.py \
  --package /path/to/FFF_Audit_2026-10-03 \
  --actual /path/to/completed-replay \
  --output .audit/external-comparison.json
~~~

The third-party PDF, ZIP and correspondence are not redistributed here.
The [bounded comparison receipt](results/external_comparison.json) binds the
exact 18 results; the self-contained public controls do not require that ZIP.

## Build and Review the Papers

~~~sh
python3 -B tools/build_paper_editions.py --output .audit/counterreview-build
python3 -B tools/check_paper_editions.py --build .audit/counterreview-build --render
python3 -B tools/check_current_snapshot.py --output .audit/current-snapshot.json
python3 -B tools/check_theorem_records.py --output .audit/theorem-records
python3 -B tools/verify_public_release.py --pdf-metadata
~~~

Use the established TeX and optional PDF dependencies in the
[public reproduction guide](../../../REPRODUCIBILITY.md). Counted substitutions
operate only on new assembled sources. No historical input, scientific hash,
manuscript or result is silently rewritten.

The [release record](../../../verification/RELEASE_2026-10-03.md) describes actual
gates and remaining limitations. Rights, AI-origin disclosure and the absence
of independent human peer review are unchanged.
