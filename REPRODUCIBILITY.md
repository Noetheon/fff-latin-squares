# Reproducibility of This Public Export

Current edition: **3 October 2026 counterreview revision**. Baseline:
**2026-09-30T12:54:17Z**, through C280 and the completed binary-first-orbit
companion. Only the E9 theorem internally included at **2026-10-02T14:03:38Z** is added.
Other later working campaigns are outside this snapshot.

The new standard-library-only control runs with
`python3 -B tools/check_e9_symmetry.py --output .audit/e9-control`.
It compares all scientific fields with a pinned independent internal audit;
only Python version and measured runtime are omitted from comparison.
This is a permutation/quotient sanity check, not a full Latin18 enumeration.

The [current counterreview controls](manuscript/candidates/2026-10-03_counteraudit_revision/README.md)
independently scan the eight printed pattern witnesses and their products,
check sign-trade support in all three views, and test finite symmetry premises.
Normal and optimized Python outputs must agree. The strict optional external
audit comparator checks exactly 18 already-replayed outputs against a pinned
60-file source package; the third-party archive is not redistributed. Its
named runtime/PDF-status exclusions do not certify the omitted PDF check.
See the source package for exact commands and limitations.

## Supported portable checks

For a first, bounded check of one explicit table and a negative control, start
with [the executable example](examples/README.md). It needs no downloads or
packages and does not run the large searches.

The default gate uses Python 3.11+ and its standard library. It does not download
data, install solvers, run historical command files or write into frozen results.

```sh
python3 -B tools/verify_public_release.py
python3 -B tools/check_theorem_records.py --output .audit/theorem-records
python3 -B tools/check_current_snapshot.py --output .audit/current-snapshot.json
python3 -B -m unittest discover -s tests -v
```

The theorem-record adapter runs the historical numerical cross-check in an
isolated output directory. It reports mathematical count/status comparisons
separately from the deliberately incomplete historical package-layout checks.
It is a consistency audit of records, not a fresh proof of all theorems.

The current-snapshot checker retains the preceding edition's fresh checks of
explicit FFF12/14/36/98 tables
using two algorithms, all eight order-8 pattern controls, 672 coloring truth
tables, 16 fibred controls, 253 affine parameters, all 1024 masks of the selected
order-20 trade family, exact affine-group/Burnside counts through dimension four,
and two physical FFF160 controls. The update additionally reconstructs all 1703
order-20 representatives and rank minors, checks both FFF12 block-return controls,
253 corner-trade parameters and all 91134 frozen CRT returns using 364536
separated coefficient/slope probes. The CRT arithmetic and form enumerator are
shared dependencies, not a wholly independent implementation.

Every scientific result must equal the frozen reference. For the inherited
checks, the comparison report explicitly names ignored fields:
elapsed_seconds for the first two reports,
runtime_seconds for CRT, and the two capture-inventory fields that differ because
the public subset is narrower. Actual public source hashes are checked afresh;
no count, spectrum, certificate, pattern or status is normalized away.
The audit does not call external solvers or access the network. It is not a proof
assistant or a complete order spectrum. Its source and input hashes are public.

The same default snapshot command also invokes the new portable
`audit_new_results.py` checker. It verifies exactly nine hash-bound payloads
and freshly checks the near-type core/triangle premises, alternative 31/13 anchor
counts, mixed-core finite domains, **131,088 small binary twists** and **33,984
selected same-projection pair controls**. Its serialized `scientific` object
must agree exactly with the frozen reference. Only per-twist timings at
`two_plex.full_twist_census_checked[*].seconds` are removed before comparison;
object-key order and tuple/array representation are normalized. No mathematical
count, witness, status or scope flag is ignored. Runtime/provenance metadata is
reported separately from the scientific comparison.

The complete fixed-base first-transversal recount is opt-in and needs a C++17
compiler available as `c++`. This command reruns just the new finite checks plus
that recount; omit `--with-cpp` to replay only the new Python checks:

```sh
python3 -B manuscript/candidates/2026-09-30_research_review/scripts/audit_new_results.py \
  --with-cpp \
  --compare manuscript/candidates/2026-09-30_research_review/results/portable_audit.json \
  --output .audit/new-results-with-cpp.json
```

Use fresh output paths. The temporary binary is deleted after the run. Requested
C++ checks must finish and match all four totals: 181,768 simple two-plexes,
138,486 liftable supports, 72,474,624 labelled first transversals and 18,118,656
free-four representatives. Without `--with-cpp`, the report explicitly marks the
recount as not rerun. This is a complete first count, not complete mate coverage:
only 18 selected supports / 9,216 labelled firsts have separate arbitrary-mate
exclusions; 138,468 liftable supports remain unexcluded by those packages.
The portable checker does not ship or replay all local radius/mate payloads,
historical DRAT traces, or an unrestricted FFF18 search. See the
[new source README](manuscript/candidates/2026-09-30_research_review/README.md)
for the exact commands and evidence boundary.

## Hardened external audit derivative

The [audit derivative](verification/audits/2026-09-28_dossier_hardened/README.md)
ships the reviewed Python/C++ sources, compact inputs, original output references,
and an exact source manifest. It needs a C++17 `g++` driver in addition to Python:

```sh
python3 -B verification/audits/2026-09-28_dossier_hardened/scripts/reproduce_all.py \
  --work-dir .audit/dossier-audit-rerun
```

This command verifies hashes, rejects optimized Python, and performs eleven
steps followed by 24 explicit comparisons. Runtime exclusions are individually
listed in its report. It freshly enumerates all 22,528 masks of the fixed trade
family and checks 1,703 physical tables/minors. It is separate from the earlier
public implementation, but not a human referee or a full order-10 master search.
The default test suite additionally injects both C++ error paths if `g++` is
available; otherwise those compiler-dependent controls are explicitly skipped.

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

The current build assembles the frozen
[30 September scientific sources](manuscript/candidates/2026-09-30_research_review/README.md)
with the [counteraudit revision](manuscript/candidates/2026-09-30_counteraudit_revision/README.md)
and [selected E9 extension](manuscript/candidates/2026-10-02_e9_symmetry_review/README.md),
then applies the [3 October counterreview](manuscript/candidates/2026-10-03_counteraudit_revision/README.md):
12 Compact, 47 Selected Results and 92 Full Report pages. The earlier counted editorial
overlay clarifies the order-10 abstract, the former conjecture's provenance and
two bibliography entries. Complete shared proof blocks are retained; Compact
selects only a coherent subset and narrows the witness statement to order 12.
The E9 successor adds a complete shared proof only to Selected and Full;
Compact keeps its proof selection and identifies the extension in its status note.
The current overlay prints eight explicit pattern witnesses instead of using
the full census for the all-pattern existence corollary. Separate census counts
retain their external completeness dependency. It also clarifies k cycle
positions versus 2k changed cells and updates source and literature pointers.
The previous typography
sources and their historical output hashes remain unchanged.
The original `manuscript/main.tex` and `main_core.tex` are historical September
sources, not the entry points for the current PDFs. Do not rebuild them and
label their open-C38 narrative current.

With a local TeX Live installation providing `latexmk`, `pdflatex` and BibTeX:

```sh
python3 -B tools/build_pdfs.py --output .audit/pdf-rebuild
```

The script uses no shell escape and builds in scratch directories. It compares
all three generated PDFs with the shipped bytes. Byte identity is expected with the
recorded TeX Live 2026 toolchain; another TeX distribution may produce a byte drift
without changing mathematical content. Such a drift is a failure of byte identity,
not silently normalized as success. No build log containing a local path is part
of the public export. The release PDFs were visually inspected separately.

Optional metadata checks use `tools/verify_public_release.py --pdf-metadata`
with Poppler `pdfinfo` and `pdfdetach`. An alternative is
`python3 -B tools/check_pdf_metadata.py --output .audit/pdf-metadata.json`,
which requires `pypdf` outside the default standard-library audit environment.
The release used pypdf 6.10.0 and separately checked text for personal identifiers.
Neither metadata check is a mathematical proof check or a general PDF security audit.

## Privacy projection and hashes

Original research files remain unchanged in their source collection. This public
tree is an explicit projection, not a replacement for historical scientific
hashes. No inherited Git objects, personal correspondence or environment archives
are included. Machine-local paths and development-revision references are removed
from selected result strings. Numerical, Boolean and null JSON leaves are preserved;
mathematical strings such as cycle types and permutations are not translated.

`PUBLIC_PROJECTION.json` records source-file and public-file hashes and whether
bytes agree for the initial export. `PUBLIC_SNAPSHOT_2026-09-28.json` records the
frozen C271 edition. `PUBLIC_SNAPSHOT_2026-09-28_CORRECTIONS.json` names its public
base commit, unchanged C271 scientific cutoff, new source hashes and the exact old/new
digests of the two PDF aliases. `PUBLIC_SNAPSHOT_2026-09-30.json` records the
current C280 intake and its PDF-alias succession; the corresponding release
record is [RELEASE_2026-09-30.md](verification/RELEASE_2026-09-30.md).
The successor PUBLIC_SNAPSHOT_2026-09-30_TYPOGRAPHY.json records only the layout
correction and its PDF replacements. Page-flow checks are independently
replayable with tools/check_paper_layout.py, requiring optional pypdf and
pypdfium2 packages.
A separate CI job installs pinned PDF-check dependencies and checks the actual
committed PDFs for page flow, page labels, glyph margins and metadata.
`PUBLIC_SNAPSHOT_2026-09-30_COUNTERAUDIT.json` adds the third reading edition
and the counted editorial amendments. The three-edition predecessor records
are preserved as historical build records, not claims of current public hashes.
Its `INPUTS.sha256` names the original source collection; the existing public
C280 builder is a privacy/reproduction adapter rather than that original file.
This non-payload difference does not change scientific section bytes. Public
inputs are bound by the current receipt and manifest, not by silently replacing
the predecessor input hash. Use the current successor's reproduction commands.
`PUBLIC_SNAPSHOT_2026-10-02.json` records the selected E9 extension.
`PUBLIC_SNAPSHOT_2026-10-03.json` binds the counterreview successor and exact
three-PDF replacements without changing the evidence cutoff. A strict comparator
and missing-key/type/duplicate-key mutation tests supplement, not replace,
the existing scientific checks.
The default verify job and standard-library test suite remain dependency-free.
Earlier receipts remain unchanged. No historical
digest is silently replaced and no private development history is imported. Historical output
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
