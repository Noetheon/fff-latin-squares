# C271 Reviewed Research Edition

28 September 2026, evidence captured through C271 at 10:24:49 UTC.
This is an AI-generated research dossier for critical examination, not a
peer-reviewed article. Order 18 remains open; C38 was disproved by FFF12.

The compact and long PDFs have 38 and 80 pages. Both integrate the review
corrections and the block-return, common-fibre CRT and corner-trade results.
Freshly checked 1703 represented FFF20 classes give a lower bound, not a census;
their direct rank certificates support the 1450956 order-40 bound without C157.

## Entry Points

- [Long TeX source](main.tex) and [compact source](main_core.tex).
- [Expanded-family/block/corner report](results/update_audit.json).
- [Separated-coefficient CRT report](results/crt_update_audit.json).
- [Inherited finite controls](results/snapshot_audit.json).
- [Exact update input inventory](evidence/update_capture.json).
- [Release review and limitations](../../../verification/RELEASE_2026-09-28.md).

From the public repository root, with Python 3.11+ standard library:

```sh
python3 -B tools/check_current_snapshot.py --output .audit/current-fresh.json
python3 -B -m unittest discover -s tests -v
```

For a byte-comparing PDF rebuild with latexmk and TeX Live:

```sh
python3 -B tools/build_pdfs.py --output .audit/pdf-fresh
```

Only newly written scratch reports are compared to frozen results. No solvers,
network access, giant table construction or historical command files are run by
the bounded checker. Earlier capture counts refer to the larger source intake;
the rebuilt public inventories cover only the selected distribution.

All three views and both positive and negative controls remain explicit.
The new matrix bound has its odd-prime and dimension hypotheses; the Steiner
contraction summary excludes only FFF completions for parent order at least eight.
The revised CRT prose keeps inactive-coordinate constant offsets, and the new
checker separately probes each label coefficient. Historical proof notes are
not rewritten. The unique-intercalate literature is credited; no novelty claim
is inferred from an internally successful audit.

The large C157 master graphs/checkpoints are not fully shipped. External expert
review, accountable authorship, rights/licensing and a durable complete archive
remain separate gates. Rights remain RESERVED.
