# An explicit affine FFF order congruent to 2 modulo 8

## Status and scope

This is an exactly checkable **consequence of C165's already written
three-view affine criterion**, not a new general construction theorem.
It includes a fully materialized order-98 table and a separate compact
trillion-order witness. It refutes the proposed shortcut that every order
`n=2 (mod 8)`, apart from two, must fail FFF. It does not construct or
exclude an order-18 FFF square, and it makes no literature-priority claim.

## A physically checked order-98 witness

Put `p=97`, `a=36`, and `b=1-a=62 (mod 97)`. The verifier proves the
primality of 97 by exhaustive trial division through its square root.
Moreover

```text
a^(-1)=62, b^(-1)=36, -b/a=36 (mod 97),
36^3=62^3=96=-1 (mod 97).
```

Thus all three least residues in C165 equation (1) are even and all three
relevant multiplicative orders are even. The same affine formula gives a
Latin loop of order 98. The dated run materializes all `98^2` cells and
checks all `3*binom(98,2)=14259` induced line-pair permutations in the
row, column, and symbol views with two separate cycle scanners. Both find
Latin and `FFF`. This is an explicit small-enough-to-check counterexample
to a universal `n=2 (mod 8)` obstruction.

## A compact trillion-order witness

Put `p=1000000000121` and `a=8` in C165's affine loop. On
`F_p union {infinity}` take `infinity` as identity, set `x*x=infinity`
for finite `x`, and, for distinct finite `x,y`, set

```text
x*y = 8*x - 7*y (mod p).
```

The [dated certificate](../repro_runs/2026-09-26_fff_2mod8_affine_certificate/README.md)
establishes that `p` is prime by a recursive Lucas certificate with complete
factorizations of `q-1` at every prime node. It does not assume a probable
prime test. The same standard-library verifier calculates

```text
b = 1-a = 1000000000114,
a^(-1) = 875000000106,
b^(-1) = 714285714372,
-b/a = 125000000016                  (mod p).
```

The least positive residues `a`, `a^(-1)` and `b^(-1)` are even. Write
`p-1=8*m` with `m=125000000015` odd. Each of `a`, `b` and `-b/a`
has even multiplicative order because its `m`-th power is not one;
the verifier records all three exact residues. Thus every condition of
C165 equation (1) holds, and the proof there covers **row, column and
symbol views**. Therefore this explicitly defined Latin square is FFF
of order

```text
p+1 = 1000000000122 = 2 (mod 8).
```

This second example is a compact algebraic witness. Materializing or scanning its
`(p+1)^2` entries is neither done nor needed for the proof; small-prime
tables are independently scanned in all three views as a control of the
criterion's implementation.

## Consequence for the order-18 search

C165 applies to **every** prime `p>=10^12`, and Dirichlet's theorem gives
infinitely many primes `p=1 (mod 8)`. Consequently FFF squares occur at
infinitely many orders `n=2 (mod 8)`. A universal congruence-only
obstruction for that residue class is false. Any putative order-18
nonexistence proof must use a sharper condition that distinguishes the
small order or its finer structure. Neither this corollary nor the large
explicit example settles the order-18 existence question. The conclusion
inherits C165's internal-proof and external-review boundaries.
