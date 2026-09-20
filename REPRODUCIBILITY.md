# Reproducibility of This Public Export

## Supported portable checks

For a first, bounded check of one explicit table and a negative control, start
with [the executable example](examples/README.md). It needs no downloads or
packages and does not run the large searches.

The default gate uses Python 3.11+ and its standard library. It does not download
data, install solvers, run historical command files or write into frozen results.

```sh
python3 -B tools/verify_public_release.py
python3 -B tools/check_theorem_records.py --output .audit/theorem-records
python3 -B -m unittest discover -s tests -v
```

The theorem-record adapter runs the historical numerical cross-check in an
isolated output directory. It reports mathematical count/status comparisons
separately from the deliberately incomplete historical package-layout checks.
It is a consistency audit of records, not a fresh proof of all theorems.

## Bounded exact finite rerun

The census is obtained directly from the cited provider, not redistributed here.
The fetcher fails closed unless its SHA-256 matches the frozen input. It does not
infer a redistribution licence or certify census completeness.

```sh
python3 -B tools/fetch_census.py
python3 -I -B tools/run_publication_finite_checks.py --output .audit/finite-rerun
```

This freshly generates all reduced squares of orders 2, 4 and 6; checks Latin,
reduced and unique properties; scans all of them; and scans all 283657 order-8
records with the shipped scanner. It compares every theorem-relevant scan field
and the entire counterexample list against the exported results. Only elapsed
time and the input path are ignored. These are supplied-generator/scanner reruns,
not independent implementations or an independent census enumeration.

The `.audit` directory and fetched archive are ignored by Git. Use a fresh output
directory per rerun. The historical scripts elsewhere in `repro_runs` are supplied
for inspection; they may need additional input packages, solvers, GAP or C++ tools.
Some write into their run folders. Do not run them in place on frozen evidence.

## PDFs

With a local TeX Live installation providing `latexmk`, `pdflatex` and BibTeX:

```sh
python3 -B tools/build_pdfs.py --output .audit/pdf-rebuild
```

The script uses no shell escape and builds in scratch directories. It compares
both generated PDFs with the shipped bytes. Byte identity is expected with the
recorded TeX Live 2026 toolchain; another TeX distribution may produce a byte drift
without changing mathematical content. Such a drift is a failure of byte identity,
not silently normalized as success. No build log containing a local path is part
of the public export. The release PDFs were visually inspected separately.

## Privacy projection and hashes

Original research files remain unchanged in their source collection. This public
tree is an explicit projection, not a replacement for historical scientific
hashes. No inherited Git objects, personal correspondence or environment archives
are included. Machine-local paths and development-revision references are removed
from selected result strings. Numerical, Boolean and null JSON leaves are preserved;
mathematical strings such as cycle types and permutations are not translated.

`PUBLIC_PROJECTION.json` records source-file and public-file hashes and whether
bytes agree. It contains file digests, not previous Git commits. Historical output
records can refer to omitted dependencies or historical hashes. The authoritative
manifest for this release is `PUBLIC_MANIFEST.sha256`, not an old embedded digest.
The manifest intentionally excludes itself and the `.git` / `.audit` directories.

## What is not self-contained

The large master graphs and checkpoint trees, original machine logs, historical
environment snapshots, solver binaries, source-message archives and third-party
census archives are not shipped. A public persistent archive/DOI is not yet
available. The long dossier's historical package catalogue describes a larger
underlying collection than this export. No claim of a full order-10 rerun from
this checkout is made.

The graph identifiers required for a future complete artifact deposit are:

| Master | Bytes | SHA-256 |
| --- | ---: | --- |
| Involution | 4518201626 | `b878a2feddc48629401864c675af6ec6f792290b75df343edd95411fd2326047` |
| Noninvolution | 3716598842 | `3e023c53194d6a60b24ad2f37e746b05b9d7e55c53dec8fcfe3cd8fb6cd09376` |

Recorded negative-search results are evidence to examine, not a substitute for
independently checking complete coverage and the mathematical reduction.
