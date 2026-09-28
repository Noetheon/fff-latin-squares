# Hardened Derivative of the C271 Dossier Audit

This is a reviewed, minimally repaired derivative of a user-supplied,
AI-generated external audit. It is **not independent human peer review**.
The original audit archive is unchanged and is not redistributed here.
[DERIVATION.json](DERIVATION.json) records its SHA-256 and the original and
derivative digest of every copied file. New comparator code is explicitly part
of this derivative, not attributed to the original audit.

## What changed

1. Assertion-dependent Python entry points reject `-O`, `-OO`, and optimized
   environment execution. The orchestrator also forces non-optimized children.
2. The two C++ inventory error paths now throw and return failure from `main`.
   The inherited Python runner propagates a failed child's exit status.
3. The reproduction command checks all source/input/reference hashes before
   execution and automatically compares **24 fresh outputs** with frozen
   references. A mismatch or missing output fails the command.
4. Child processes have bounded timeouts. Binaries and logs are created only
   in the fresh work directory, never committed.

The mathematical algorithms and reference results have not been changed. Tests
inject incorrect counts, both C++ errors, missing files, changed array order,
and invalid runtime fields. These failure-path tests complement, rather than
replace, the successful numerical rerun.

## Reproduce

Requirements: Python 3.11+ standard library and a C++17 compiler named `g++`
(Apple Clang's compatible driver was used locally). No network, solver,
pre-generated small-order enumeration or external master graphs are required.
From the repository root:

```sh
python3 -B verification/audits/2026-09-28_dossier_hardened/scripts/reproduce_all.py \
  --work-dir .audit/dossier-audit-rerun
python3 -B -m unittest discover -s tests -p test_audit_corrections.py -v
```

Choose a new work directory for every rerun. Do not run child scripts in place:
they are inherited research programs that write local results. Output isolation
is not an operating-system security sandbox.

The orchestrator executes eleven outer steps, including nine inherited Python
checks and three freshly compiled inherited C++ checkers. Read its fresh
`results/comparison.json` and `results/reproduction_receipt.json` after completion.
The [recorded correction rerun](VALIDATION.json) contains relative commands,
versions, timing and output hashes; machine-local paths are not published.

## Exact comparison contract

- Four files (representatives JSONL, corner CSV, exchange CSV, inventory text)
  are byte-identical comparisons.
- Twenty JSON files retain all scientific fields and array order. JSON object
  key order and serialization whitespace are not significant.
- Only top-level `$.seconds` is excluded in the seven explicitly named files
  in [compare_outputs.py](scripts/compare_outputs.py). It must still exist and
  contain a finite nonnegative number in both records.
- No spectrum, count, rank, cycle, pattern, status flag, or scope is ignored.
  No array-order or field-name normalization is allowed.

The original inventory stdout includes trailing spaces in two histogram rows.
The path-specific `.gitattributes` exception preserves those reference bytes;
it does not relax the byte comparison or any scientific check.

## Results and limits

The complete 22,528-mask family has 19,480 FFF and 3,048 TTT instances and
1,700 distinct FFF spectra. Two quadratic controls and the corner table give
1,703 separated order-20 FFF main classes. All 1,703 physical tables, their
970,710 line pairs and rank-58 certificates pass the independent routines.
These are fixed-family lower bounds, not a census.

The fresh reduced orders 2, 4 and 6, the 230 supplied FFF8 tables, finite affine
corner controls and compact CRT return controls agree with the frozen outputs.
The C157 checker here reproduces only candidate inventories and root orbits,
**not** the master graphs or 7,515,832,479 DFS nodes. The CRT coefficient probes
share their own field kernel and rely on the return-map derivation; they are
not physical scans of all large constructed tables.

C38 is already disproved by FFF12. Order 18, a complete order spectrum,
literature priority, a durable full-data deposit and human expert review remain
outside this audit. No historical UNSAT certificate is newly proof-checked here.
Rights remain [reserved](../../../RIGHTS.md).
