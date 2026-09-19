# Odd-Cycle-Free Latin Squares

**AI-generated research dossier for critical examination. Not peer reviewed.**

This repository publishes a curated mathematical record and selected computational
evidence about Latin squares whose two-line permutations have no odd cycle of
length greater than one in any of the row, column and symbol views (FFF).

## Read the dossier

- [Project website](https://noetheon.github.io/fff-latin-squares/)
- [Compact reading version (PDF)](papers/FFF_Compact_Research_Dossier.pdf)
- [Full technical record (PDF)](papers/FFF_Long_Research_Dossier.pdf)
- [Editable manuscript sources](manuscript/)
- [Evidence and open questions](EVIDENCE_STATUS.md)
- [Reproducibility and export limitations](REPRODUCIBILITY.md)
- [Observed release checks](verification/RELEASE_VALIDATION.md)

Read the disclosure at the beginning of either PDF before relying on its claims.
The two versions overlap; they are not two independent studies.

## Current evidence boundary

- The record contains written structural proofs, exact finite computations and
  explicitly labelled open questions. These are different evidence classes.
- The order-10 exclusion (internal reference C157) uses a written reduction and
  complete finite master searches. It is not a solver-free proof, a new rerun in
  this release or a proof-assistant certificate.
- The global power-of-two conjecture (C38) remains open. Order 12 is the next
  undecided even non-power-of-two case in this project.
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
python3 -B -m unittest discover -s tests -v
```

These checks verify the public bytes and cross-check the numerical theorem
records; they do not rerun the large order-10 search. A bounded small-order and
order-8 rerun is documented in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Distribution scope

This is a new curated export, not the complete working archive. It contains no
inherited development history or correspondence. Historical source/result paths
are preserved where useful for traceability; selected machine-local strings are
privacy-projected. `PUBLIC_PROJECTION.json` records byte-identical and projected
files. `PUBLIC_MANIFEST.sha256` hashes the actual public files. Historical hashes
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
