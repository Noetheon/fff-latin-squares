# A Small, Executable FFF Check

No solver, census download or Python package is needed. From the repository
root, using Python 3.11+:

```sh
python3 -B tools/demo_fff.py
python3 -B tools/demo_fff.py examples/order3_nonfff.json
```

Expected first lines:

```text
order=8 latin=True reduced=True pattern=FFF FFF=True
order=3 latin=True reduced=True pattern=TTT FFF=False
```

The first input is the explicit twisted loop on `Z4 x F2` in
[Theorem 6](../proof_notes/fff_subsquare_and_congruence_obstructions.md).
Its 64 entries are visible in [order8_fff.json](order8_fff.json).
The second is addition modulo 3, an intentionally non-FFF control.

The checker validates Latin and reduced properties and decomposes **every**
two-line permutation in all three views: 28 pairs per view at order 8,
3 per view at order 3. `F` means no odd cycle; `T` means an odd cycle exists.
For distinct Latin lines these permutations are fixed-point-free.

For the complete list of permutations, cycles and odd-cycle witnesses:

```sh
python3 -B tools/demo_fff.py --output .audit/demo-order8.json
python3 -B tools/demo_fff.py examples/order3_nonfff.json --output .audit/demo-order3.json
```

[expected_results.json](expected_results.json) records both complete expected
results and input hashes. Unit tests compare them and reconstruct the order-8
table from its formula. The checker is a new, small implementation; its tests
are automated sanity checks, not independent expert mathematical review.

**Scope:** these two tables only. This does not rerun the order-8 census, prove
the order-10 exclusion, test group isotopy, or settle the global conjecture.
No mathematical claim or historical result is changed by this demonstration.
