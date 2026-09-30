# Odd-Cycle-Free Latin Squares

**AI-generated research dossier for critical examination. Not peer reviewed.**

This repository publishes a curated mathematical record and selected computational
evidence about Latin squares whose two-line permutations have no odd cycle of
length greater than one in any of the row, column and symbol views (FFF).

## Read the dossier

- [Project website](https://noetheon.github.io/fff-latin-squares/)
- [Compact starting point (12-page PDF)](papers/FFF_Compact_Research_Dossier.pdf)
- [Selected Results (44-page PDF)](papers/FFF_Selected_Research_Dossier.pdf)
- [Full technical record (89-page PDF)](papers/FFF_Long_Research_Dossier.pdf)
- [Current revision and reproduction](manuscript/candidates/2026-09-30_counteraudit_revision/README.md)
- [Theorem numbers, proof sources and evidence](manuscript/candidates/2026-09-30_counteraudit_revision/THEOREM_EVIDENCE.md)
- [Critical counteraudit: confirmed findings and limits](manuscript/candidates/2026-09-30_counteraudit_revision/REVIEW_AND_LIMITATIONS.md)
- [Unchanged C280 scientific sources and bounded audit](manuscript/candidates/2026-09-30_research_review/README.md)
- [Typography and scholarly-presentation audit](verification/TYPOGRAPHY_AND_SCHOLARLY_AUDIT_2026-09-30.md)
- [Evidence and open questions](EVIDENCE_STATUS.md)
- [Reproducibility and export limitations](REPRODUCIBILITY.md)
- [30 September release scope and checks](verification/RELEASE_2026-09-30.md)
- [Historical 28 September release](verification/RELEASE_2026-09-28.md)
- [Historical audit corrections](verification/RELEASE_2026-09-28_CORRECTIONS.md)

Read the disclosure at the beginning of each PDF before relying on its claims.
The three reading editions overlap; they are not independent studies.
The former 44-page Compact is now **Selected Results**. The new Compact
contains complete selected proofs and stays within 12-18 total pages.
This counteraudit revision clarifies dependencies and references without
extending the scientific cutoff or adding a mathematical claim.

**Current edition: 30 September 2026 snapshot; scientific intake is frozen at
2026-09-30T12:54:17Z through C280 and the completed binary-first-orbit companion.**
This is a public research snapshot for critical examination, not a peer-reviewed
article. The earlier September edition is retained as history; its open-C38 and
open-order-12 wording is superseded. Subsequent working results are outside this
edition's reviewed scope.
The new structural proofs and bounded finite checks do not establish external
expert review or decide order 18. Historical DRAT traces are not freshly rerun
by the public snapshot checks.

## Start with one table

Clone this repository and run, with Python 3.11+ and no additional packages:

```sh
python3 -B tools/demo_fff.py
```

Expected: `order=8 latin=True reduced=True pattern=FFF FFF=True`.
The checker examines all 84 row/column/symbol pairs of an explicit table.
The [example, negative control and complete cycle reports](examples/README.md)
make this small check inspectable. It is not a census or an order-10 rerun.

**Help examine one result:** [three bounded review questions](REVIEW_TASKS.md)
cover a proof step, reproducibility and prior literature. Corrections are more
useful than an unqualified endorsement.
The [pinned review discussion](https://github.com/Noetheon/fff-latin-squares/discussions/1)
is the shared starting point for focused feedback.

## Current evidence boundary

- The record contains written structural proofs, exact finite computations and
  explicitly labelled open questions. These are different evidence classes.
- The order-10 exclusion (internal reference C157) uses a written reduction and
  complete finite master searches. It is not a solver-free proof, a new rerun in
  this release or a proof-assistant certificate.
- An explicit order-12 FFF table **disproves the former power-of-two conjecture
  (C38)**. Two independent scanning methods check every line pair of the
  shipped order-12/14/36/98 controls. **Order 18 remains open.**
- The new edition includes general block-return maps, a common-fibre cubefree
  CRT lift and an affine corner trade preserving all three pattern bits.
  Fresh checks give **1,703 represented classes at order 20** and an associated
  lower bound of **1,450,956 at order 40**. These are not censuses. Explicit
  rank certificates remove the C157 dependency from these fixed-family bounds.
- The corner construction supplies generic unique-intercalate tables and an
  explicit fixed-remainder noncontraction obstruction. Its large-prime FFF
  existence corollary depends on a published character-sum estimate; unique
  intercalate squares were already studied in the literature. No priority is claimed.
- Near-type triangles (one 4-cycle and otherwise 2-cycles on each pair)
  force an odd companion-view cycle at orders
  `n >= 6`, `n = 2 (mod 4)`, using an explicit finite core premise. For FFF18,
  the 31 dual-positive and 13 longest-cycle anchor cases are alternative
  normalizations, not solved cases; the latter does not impose column positivity.
- For arbitrary binary-fibre Latin bases, component parity exactly characterizes
  simple two-plex transversal lifts and their count. Standard double prolongation
  along disjoint transversals with the same projected two-plex is non-FFF;
  different-projection pairs are outside that obstruction.
- For one fixed FFF16 base, the complete count is **72,474,624 labelled first
  transversals / 18,118,656 free-four representatives**, not main classes or
  complete mate coverage. Only **18 selected supports / 9,216 labelled firsts**
  have complete arbitrary-mate exclusions; **138,468 liftable supports remain
  unexcluded** by those packages. The long dossier also records scoped
  homogeneous-line, mixed-core and local trade-radius results.
- Census completeness and the primitive-group classification are cited external
  dependencies. Same-binary decompositions are not independent implementations.
- A timeout or partial SAT table is never evidence of a complete exclusion or
  an FFF example.

## Origin and authorship

The mathematical development, proof text, software and scientific writing were
produced through OpenAI ChatGPT/Codex workflows. The human role was project
initiation and provision of time and computing resources, not claimed personal
scientific authorship or expert validation. No accountable scholarly author or
independent expert human review of the complete work has been established.
AI systems are tools, not listed authors. See [AI disclosure](AI_DISCLOSURE.md).

## Verify what is actually shipped

Python 3.11 or later, standard library only, is sufficient for the default gate:

```sh
python3 -B tools/verify_public_release.py
python3 -B tools/check_theorem_records.py --output .audit/theorem-records
python3 -B tools/check_current_snapshot.py --output .audit/current-snapshot.json
python3 -B -m unittest discover -s tests -v
```

These checks verify the public bytes, cross-check historical numerical records,
and freshly rerun the current edition's bounded controls. They do not rerun the
large order-10 searches or historical UNSAT proof checkers. The snapshot checker
also invokes `audit_new_results.py` from the current source package. It binds
nine exact payloads and includes 131,088 small binary twists and 33,984 selected
same-projection pair controls. The opt-in `--with-cpp` complete first-count
recount and comparison rules are documented in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Distribution scope

This is a curated public edition, not the complete working archive. It contains no
inherited development history or correspondence. Historical source/result paths
are preserved where useful for traceability; selected machine-local strings are
privacy-projected. `PUBLIC_PROJECTION.json` records byte-identical and projected
files from the original export. `PUBLIC_SNAPSHOT_2026-09-30.json` records the
current C280 snapshot and PDF-alias succession. The frozen C271 receipt
`PUBLIC_SNAPSHOT_2026-09-28.json` and its audit-correction successor
`PUBLIC_SNAPSHOT_2026-09-28_CORRECTIONS.json` remain unchanged, as do earlier receipts.
`PUBLIC_MANIFEST.sha256` hashes the actual public files. Historical hashes
inside a report still identify historical bytes, not necessarily the projected
file beside it. Do not use those historical hashes as the public manifest.

Large generated graphs, checkpoint trees, third-party census archives, solver
binaries and software environments are not shipped. The new portable checker
covers finite proof premises, but not every local radius or arbitrary-mate payload.
A complete persistent public data deposit remains outstanding. This repository
is publicly readable, but is
not advertised as a fully self-contained research archive or as open-source
licensed software. [Rights remain reserved](RIGHTS.md) pending a separate decision.

## Feedback

Specific mathematical counterexamples, missing assumptions, reproducibility
failures and literature references are welcome through Issues or Discussions.
Please identify the exact statement, file and reproducible check. The maintainer
does not claim subject-matter expertise; responses may require outside expertise.
See [review guidance](CONTRIBUTING.md) and [community venues](COMMUNITY_OUTREACH.md).

The website is a static, English-only reading interface with no JavaScript,
third-party fonts or analytics. See [website maintenance and checks](WEBSITE.md).
