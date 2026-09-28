# Exact FFF repair radius around one order-18 FFT table

**Evidence.** The encoding argument below is rigorous. The distance bound is
an exact finite, locally proof-checked computation for **one fixed labelled
source**, not an existence or nonexistence result for unrestricted order 18.
The dated [run](../repro_runs/2026-09-27_fff18_fft34_exact_repair/README.md)
pins the source, generator, CNF and proof hashes. No external human review or
literature-priority determination is asserted.

## Exact neighborhood formula

Let `T` be the frozen Latin table of order `n`, and let `X[r,c,s]` be the
usual exactly-one Latin cell variables. Since precisely one `X[r,c,s]` is
true in each cell, the **signed literal** `not X[r,c,T[r,c]]` is true exactly
when that cell differs from `T`. Thus an at-most-`k` cardinality constraint
on these `n^2` literals is equivalent to `d_H(L,T)<=k` for the decoded
Latin table `L` in the displayed labelling.

The prefix-counter clauses used here make `P[i,j]` true whenever at least
`j` of the first `i` edit literals are true: `edit_i -> P[i,1]`,
`P[i-1,j] -> P[i,j]`, and
`edit_i and P[i-1,j-1] -> P[i,j]`. The final clause forbids
`P[n^2,k+1]`. Induction proves that any assignment with more than `k`
edits is rejected. Conversely, if there are at most `k` edits, assigning
each prefix variable its actual counting truth value satisfies every
clause. The `k=0` and `k=n^2` boundary cases are handled directly. The
signed-literal truth table is independently exhausted in the
[unit test](../tests/test_fff18_fft34_exact_repair.py).

The frozen C245 position-value coloring channel is equivalent to the
absence of odd cycles in **each** row, column and symbol line pair. Its
underlying C39 Latin layer normally adds `2n` reduction unit clauses,
including two copies of `X[0,0,0]`. This run deletes exactly those `2n`
units and no other clauses before adding the Hamming counter. The result
therefore ranges over **all labelled Latin tables**, not just reduced
ones. The channel gauge units are retained: each line-pair coloring may
be globally complemented, so they do not restrict FFF. Combining the
Latin layer, the three-view channel equivalence, and the Hamming lemma
shows that the final CNF is satisfiable if and only if some FFF table
`L` has `d_H(L,T)<=k`.

## Finite result and boundaries

The frozen order-18 source has pattern `FFT`, with respectively
`0,0,34` failing row, column and symbol pairs in two physical scanners.
For `k=16`, the **unrestricted-label** CNF has `27,728` variables and
`755,739` clauses; its SHA-256 is
`5eb4b531d5316d2d4bacaa18b40a30c7a3819e1dca9bf3d8c213d7dcf1684ca1`.
CaDiCaL 3.0.0 returned UNSAT and emitted a DRAT trace with SHA-256
`6dac098ba1277b87caf42b12014760c47c5f3fe9ab58c788d40cabfad514abe5`.
The separately built `drat-trim` checker returned `s VERIFIED`.
Consequently **no FFF Latin table of order 18 differs from this particular
labelled `FFT` source in at most 16 cells**. This is a distance lower
bound for a specified source, not a claim that no FFF18 square exists.

The separate frozen FFF8 table at distance zero is SAT, decoded, and
independently validated as Latin and `FFF`. The same order-18 source at
distance zero is UNSAT with a checked DRAT trace. At `k=18`, CaDiCaL
returned UNSAT **without a checked proof**; at `k=20`, it timed out after
60 seconds. Neither outcome improves the certified `k=16` boundary.
The absence of a close witness says nothing about distant order-18
tables, other source classes or the fourteen canonical row-one cases.
No Goal completion, manuscript upgrade, commit, push or release follows.
