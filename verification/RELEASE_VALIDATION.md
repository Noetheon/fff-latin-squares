# Public Release Validation

Checked on 19 September 2026. This is automated and AI-assisted publication QA,
not independent expert peer review or a complete mathematical proof certificate.

| Check | Observed result |
| --- | --- |
| New public manifest and file hygiene | Passed; exact file inventory and SHA-256 checks |
| Public verifier regression tests | 4 passed |
| Theorem-to-result numerical consistency | All 13 computational theorem records passed |
| Historical package completeness | Intentionally incomplete in this curated export; not reported as a pass |
| Reduced small-order rerun | 1, 4 and 9408 distinct valid reduced Latin squares freshly generated and completely scanned for orders 2, 4 and 6 |
| Order-8 rerun | All 283657 provider records scanned; all relevant counts and the full counterexample list match |
| External order-8 input | Fetched from the cited provider; exact expected size and SHA-256 verified |
| PDF rebuild | Both files byte-identical from the exported TeX; zero final TeX warnings |
| PDF inspection | 18-page compact and 60-page long dossier; empty author metadata, no attachments, embedded fonts, no detected page-box violations or blank pages |
| Visual inspection | All rendered page contact sheets and detailed front matter examined |
| Website | Desktop 1440px and mobile 390px checks passed; cover image rendered; no horizontal overflow or page errors |
| Maintained relative Markdown links | No missing targets |
| Source-collection audit | 78 tests and the manifest, snapshot, semantic, computational and isolated local gates passed on the final repetition |
| Private-material boundary | Allowlisted export; no inherited Git history, personal correspondence, local account paths or personal author metadata |

The first source-collection audit exceeded its test/manifest time limits during
heavy host load. Separate reruns and the final complete repetition passed. A
timeout was not relabelled as a successful check.

Machine-readable fresh records are in this directory. The public projection
retains numerical, Boolean and null JSON values at their corresponding keys and
positions; only defined non-scientific string metadata is normalized. PDF rendering
and numerical consistency do not establish correctness of every proof.

No new exhaustive order-10 run, full large-artifact restoration, proof-assistant
formalization, independent expert review, DOI deposit or third-party forum posting
was performed as part of this release. Rights/licensing remains a separate decision.
