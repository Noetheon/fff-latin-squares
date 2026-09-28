# Odd-prime autotopisms and fixed-line orbit quotients

**C224.** The general orbit bound below is a direct proof for an arbitrary
row-F Latin square. Its order-18 prime-support corollary uses the separately
certified C223 obstruction at prime 17. It does **not** decide whether an
FFF Latin square of order 18 exists.

## The fixed-line orbit bound

Let `L:R x C -> S` be a Latin square and let `(alpha,beta,gamma)` be an
autotopism of odd prime order `p`. Suppose `alpha` fixes `f` rows and `beta`
has `k` cycles of length `p`. Assume `f>0` and `k>0`. For every fixed row
`r`, its line bijection `R_r:C -> S` satisfies

```text
R_r beta = gamma R_r.                                      (1)
```

Consequently `beta` and `gamma` have the same cycle type, and `R_r`
induces a bijection `sigma_r` from the `k` moving `beta`-orbits to the
`k` moving `gamma`-orbits. For two distinct fixed rows `r,s`, put
`rho = R_s^-1 R_r`. It commutes with `beta` and projects to the orbit
permutation `sigma_s^-1 sigma_r`.

Suppose this projected permutation has a cycle of odd length `d`. Above
that cycle, `rho^d` commutes with the regular `p`-cycle on one orbit,
and is therefore a power of that cycle. Each physical cycle above it
has length `d` or `dp`; both are odd. Thus if the **row view is F**,
every `sigma_s^-1 sigma_r` has only even cycles. In particular it has
no fixed orbit. For any chosen moving `beta`-orbit `B`, the images
`sigma_r(B)` are then distinct as `r` ranges over the fixed rows.
Hence:

```text
f <= k, and if f >= 2, k is even.                        (2)
```

The second assertion follows because an even-cycle permutation cannot
act on an odd number of orbits. Notice that (2) needs only row-F, not
all three F views. Reversing the coordinate roles gives analogous
statements for fixed columns and symbols.

## Fixed-point subsquare

If all three components of an autotopism have a fixed point, their
fixed-point sets have equal size. Indeed, a fixed row conjugates
`beta` to `gamma` through (1), and a fixed column similarly conjugates
`alpha` to `gamma`. For fixed row `r` and column `c`, the cell
`L(r,c)` is fixed by `gamma`. The fixed rows and fixed columns
therefore form a Latin subsquare on the fixed symbols: each such row
contains exactly all fixed symbols. If `L` is FFF, the subsquare is
FFF by C41. By C35, its order cannot be odd and greater than one.
This gives a second, independent obstruction in suitable cases.

## Order 18

In an FFF square every coordinate-fixed autotopism kernel is a
2-group (C219). Hence an autotopism of odd prime order has no identity
component. On 18 points, a nonidentity component of order `p` has
cycle type `p^k 1^f`, where `f=18-kp`.

For `p=5,7,11,13`, every component has at least one fixed point.
The fixed-point-subsquare argument makes their cycle types identical,
so (2) applies with the following **complete** list:

| `p` | Possible `(k,f)` | Row-F obstruction |
| --- | --- | --- |
| 5 | `(1,13)`, `(2,8)`, `(3,3)` | `f>k`, `f>k`, odd `k` with `f>=2` |
| 7 | `(1,11)`, `(2,4)` | `f>k` in both cases |
| 11 | `(1,7)` | `f>k` |
| 13 | `(1,5)` | `f>k` |

Thus **no** order-18 FFF square has an autotopism of order 5, 7, 11
or 13. Prime 17 has only `(k,f)=(1,1)`, which (2) does not exclude;
it is excluded separately by the C221-dependent C223 theorem.
Cauchy's theorem now yields the conditional group restriction

```text
If L is an FFF Latin square of order 18, then
|Autotopy(L)| = 2^a 3^b for some a,b >= 0.               (3)
```

The proof does not assume that `L` has a nontrivial autotopism.
The identity-only case is allowed. In particular (3) is not an
existence or nonexistence result for arbitrary order-18 squares.

At prime 3, a semiregular component of type `3^6` has no fixed
point, so the equal-fixed-type step cannot be imposed globally.
The orbit bound does not exclude all order-3 autotopisms.

## Finite controls and limitations

The [dated control run](../repro_runs/2026-09-24_fff_odd_prime_autotopy_orbit_bound/README.md)
physically checks an FFF order-8 table with an order-3 automorphism
of type `3^2 1^2` (the sharp `f=k=2` boundary), a non-FFF order-12
table of type `3^3 1^3` whose orbit quotient has a 3-cycle, and a
frozen FFF order-14 table with an order-13 automorphism of type
`13^1 1^1`. Each table is checked in row, column and symbol views;
the autotopism identities and orbit projections are checked cellwise.
These controls test the formulas but do not replace the proof.

The bound is an exclusion of **symmetries**, not of squares without
those symmetries. No literature-priority or external-review claim is made.
