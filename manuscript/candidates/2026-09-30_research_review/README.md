# Reviewed Research Dossier: 30 September 2026

This successor starts from the audit-corrected 28 September edition.
Its fixed evidence intake is **2026-09-30 12:54:17 UTC**, through C280 and
the completed binary-first-orbit census companion. It excludes the unfinished
streaming-first-masks campaign and any later work. Older editions stay frozen.

**Unrestricted FFF18 remains open. C38 is disproved by the FFF12 example.**
The inherited order-10 exclusion, the 1,703 represented FFF20 main classes,
and direct rank-based 1,450,956-class lower bound at order 40 are unchanged.
These are lower bounds, not complete higher-order censuses.

## New Manuscript Content

Both versions now prove the near-type cross-view triangle obstruction, with
its finite degree-ten premise explicitly labelled, and distinguish the 31
dual-positive and 13 longest-cycle anchor normalizations. They also prove
the binary-fibre component-parity lift/count theorem, equal-projection
double-prolongation obstruction, and canonical-FIRST-only normalization.

The long version additionally states the six/four-line homogeneous bounds,
the conditional mixed-core orbit/count theorem, the reusable first-touch
lemma, and precisely limited numerical trade-radius applications. A clean
12-row rectangle or its fixed-leaf exclusion is not an FFF18 decision.
The same is true of a complete first-transversal count without mate coverage.

For one fixed FFF16 base: 181,768 simple quotient two-plexes; 138,486
liftable; 72,474,624 labelled first transversals; 18,118,656 free-four
representatives. Only 18 supports / 9,216 labelled firsts have complete
separate arbitrary-mate exclusions at this intake. The remaining 138,468
liftable supports are not excluded by those packages. Selection was not random.

## Reproduce The New Finite Premises

From the repository root:

```sh
python3 -B manuscript/candidates/2026-09-30_research_review/scripts/audit_new_results.py \
  --with-cpp \
  --compare manuscript/candidates/2026-09-30_research_review/results/portable_audit.json \
  --output .audit/fresh-20260930-audit.json
```

Use a fresh output path. Python 3.11+ is sufficient without `--with-cpp`;
that option adds a small C++17 recount of the fixed-base transversal census.
Temporary executables stay under `.audit/` and are deleted. No SAT solver,
large census download, private path, or raw chat is required.

The [source manifest](evidence/source_manifest.json) binds nine selected,
byte-identical checker/data inputs. The wrapper calls pure checker functions;
historical checkers' path-dependent CLIs are not the public entry points.
Fresh checks cover all 18,900 near degree-ten candidates; 13,440 degree-18
templates and their two 6,720-orbits; the sixteen companion witnesses;
13/31 case arithmetic; mixed finite domains in both directions;
131,088 small binary twists and the retained same-projection pair controls.

Semantic comparison means exact agreement of the serialized `scientific`
object. Only object-key order and tuple-to-array representation are normalized.
The per-twist runtime field is removed at the explicitly listed path. No
theorem count, candidate list, witness, status or scope flag is ignored.
Requested C++ counts are separately required to finish and match all four
exact expected totals. The report distinguishes omitted optional checks.

## Build Both Papers

```sh
python3 -B manuscript/candidates/2026-09-30_research_review/scripts/build_pdfs.py \
  --candidate-only --output .audit/fresh-20260930-pdfs
```

Requires the existing `latexmk`, pdfLaTeX, BibTeX and Poppler toolchain.
The fixed source-date epoch makes independent builds byte-identical with the
same toolchain. `--candidate-only` does not claim equality to published PDFs.
Without that flag the two public `papers/` aliases must match exactly.
See [FINAL_AUDIT.md](FINAL_AUDIT.md) for actual release checks and limits.

## Evidence And Publication Limits

Fresh portable proof-premise checks are not reruns of the historical order-10
master searches or every DRAT trace. Source-specific radius reports and
arbitrary-mate certificates are retained and rechecked in the private research
checkpoint; they are not all duplicated in this small public package.
The sealed two-plex run has a representation-only comparator erratum; its
maintained private replay is `tools/replay_fff_two_plex_voltage_lifts.py`.
The public wrapper avoids the faulty comparison and checks the literal data.

This remains an AI-generated, internally audited dossier for critical expert
examination, not independently human-peer-reviewed science. Literature
priority, accountable scholarly authorship, rights/licensing, declarations,
complete durable external evidence delivery and a DOI remain separate gates.
Rights remain RESERVED. Public GitHub distribution is not journal acceptance.
