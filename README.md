# Odd-Cycle-Free Latin Squares

**AI-generated research dossier for critical examination. Not peer reviewed.**

This repository publishes a curated mathematical record and selected computational
evidence about Latin squares whose two-line permutations have no odd cycle of
length greater than one in any of the row, column and symbol views (FFF).

## Read the dossier

- [Project website](https://noetheon.github.io/fff-latin-squares/)
- [Compact reading version (30-page PDF)](papers/FFF_Compact_Research_Dossier.pdf)
- [Full technical record (72-page PDF)](papers/FFF_Long_Research_Dossier.pdf)
- [Current editable sources and bounded audit](manuscript/candidates/2026-09-27_research_snapshot/README.md)
- [Evidence and open questions](EVIDENCE_STATUS.md)
- [Reproducibility and export limitations](REPRODUCIBILITY.md)
- [27 September release scope and checks](verification/RELEASE_2026-09-27.md)

Read the disclosure at the beginning of either PDF before relying on its claims.
The two versions overlap; they are not two independent studies.

**Current edition: 27 September 2026, frozen at 10:52 UTC through C251.**
This is a public research snapshot for critical examination, not a peer-reviewed
article. The earlier September edition is retained as history; its open-C38 and
open-order-12 wording is superseded. Subsequent working results are outside this
edition's reviewed scope.

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
- The new edition includes affine constructions, row-fibred pattern equality,
  binary quotient descent and within-construction affine-orbit classification.
  The order-20 source lower bound of 514 classes is not a complete census;
  higher-order lower bounds use a proved construction, not exhaustive table scans.
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
large order-10 searches or historical UNSAT proof checkers. Additional finite
reruns are documented in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Distribution scope

This is a curated public edition, not the complete working archive. It contains no
inherited development history or correspondence. Historical source/result paths
are preserved where useful for traceability; selected machine-local strings are
privacy-projected. `PUBLIC_PROJECTION.json` records byte-identical and projected
files from the original export. `PUBLIC_SNAPSHOT_2026-09-27.json` separately
records this edition's selected inputs, sources and privacy projections.
`PUBLIC_MANIFEST.sha256` hashes the actual public files. Historical hashes
inside a report still identify historical bytes, not necessarily the projected
file beside it. Do not use those historical hashes as the public manifest.

Large generated graphs, checkpoint trees, third-party census archives, solver
binaries and software environments are not shipped. A complete persistent public
data deposit remains outstanding. This repository is publicly readable, but is
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
