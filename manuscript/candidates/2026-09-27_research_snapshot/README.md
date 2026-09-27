# Research Snapshot: 27 September 2026

Public review edition, frozen at **10:52 UTC through C251**. Not peer reviewed.
This English package supersedes the former open-C38 narrative: the shipped
FFF12 witness disproves C38; order 10 is excluded; unrestricted order 18 is open.
Later working results are outside this edition. Rights remain reserved.

- [Compact source](main_core.tex), corresponding to the 30-page reading PDF.
- [Full source](main.tex), corresponding to the 72-page technical PDF.
- [Evidence map and limitations](THEOREM_EVIDENCE.md).
- [Public selection and source/public hashes](../../../PUBLIC_SNAPSHOT_2026-09-27.json).
- [Release review record](../../../verification/RELEASE_2026-09-27.md).

## What This Edition Adds

Explicit FFF12/14/36/98 controls; finite-field and norm lift bounds;
the exact affine prime-successor criterion; row-fibred pattern equality;
binary quotient recovery and within-construction affine-orbit classification;
an order-20 source lower bound of 514 classes; exact position/value coloring;
and explicitly restricted order-18 exclusions. No order-20 census, universal
product cancellation, complete spectrum or unrestricted order-18 decision is
claimed. Higher-order class lower bounds follow from construction theorems,
not exhaustive enumeration of all higher-order tables.

## Reproduce the Shipped Checks

From the repository root, using Python 3.11+ standard library only:

```sh
python3 -B tools/check_current_snapshot.py --output .audit/current-snapshot.json
python3 -B tools/verify_public_release.py
python3 -B -m unittest discover -s tests -v
```

With TeX Live and latexmk, rebuild both public PDFs in a new scratch directory:

```sh
python3 -B tools/build_pdfs.py --output .audit/pdf-rebuild
```

The build disables shell escape and compares exact PDF bytes with the shipped
edition. A different TeX toolchain may cause a reported byte-identity failure;
it is not silently accepted as a semantic match. Source, evidence and the bounded
checker are frozen. Fresh results always go to `.audit/`, not into evidence.

## Evidence Scope

The 35 selected evidence objects include explicit input tables, proof notes and
finite result records. All are hashed. The TeX and mathematical checker are
byte-identical to the examined local edition. Two result files have only local
path strings projected; the public projection record preserves both digests.
Private registers, source messages and private Git history are not distributed.

The checker freshly covers six positive tables in orders 12/14/36/98 using
permutation and alternating-matching algorithms; all eight order-8 patterns;
672 coloring truth tables; 16 fibred controls; 253 affine parameters; all 1024
selected trade masks; exact affine-group/Burnside counts through dimension four;
and both physical order-160 controls, comparing exact spectra rather than hashes
alone. Every scientific output must equal the retained reference.

Historical order-10 master searches and order-18 UNSAT proof checks are **not**
rerun. Selected certificates' metadata are inspectable, but their large proof
payloads and all original solver environments are not shipped. Imported proof
notes preserve their original relative-reference layout; some refer to omitted
historical runs. Use the curated evidence map for shipped entry points.
The full report's historical package catalogue describes a larger research
collection, not a promise that this public checkout includes every package.

## Review and Publication Limits

The proof text and checks were internally audited using AI-assisted workflows.
This is not independent expert human review. Novelty/priority, durable complete
data archiving, accountable scholarly attribution and venue-specific declarations
remain separate gates. No author identity, DOI, open-source licence or journal
acceptance is asserted. See the root AI disclosure and rights statement.
