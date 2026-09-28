# A fibre-rank bound for matrix-bilinear Latin lifts

**Evidence and scope.** This is a proposed internally proved theorem about
the specified matrix-bilinear lift, not about arbitrary FFF Latin squares,
arbitrary vector-valued block substitutions, or order 18. The finite
[controls](../repro_runs/2026-09-28_fff_matrix_bilinear_rank_bound/README.md)
check small boundary cases but do not replace the proof. The scalar
predecessor is [C263](fff_scalar_bilinear_lift_boundary.md). No
literature-priority or external expert-review claim is made.

## Model and statement

Let `p` be an odd prime, `G=F_p^r` for `r>=1`, and `V=F_2^D` for
`D>=0`. Let `beta:G x G -> GL(V)` be a symmetric bicharacter: it is
multiplicative in each additive argument, `beta(x,y)=beta(y,x)`, and
its image commutes. Let `c:G x G -> V` be arbitrary. Put

```text
 (x,a) * (y,b) = (x+y, beta(x,y)^2 a + beta(x,x)b + c(x,y)).     (1)
```

Both fibre coefficients are invertible, so (1) is Latin for every
`c`. Write `e=ord_p(2)`.

**Theorem (necessary dimension).** If (1) is row-F for even one twist
`c`, then

```text
                         D >= e * ceil(r/2).                    (2)
```

The same necessary bound follows from FFF. Under the additional
inequality `2^e > 3(p^2-1)`, the bound is attained **within (1)**:
there is a choice with `D=e*ceil(r/2)` that is FFF in all three
views. This is not a lower bound on the order or fibre dimension of
arbitrary FFF squares with a quotient `G`.

## An identity diagonal matrix forces an odd row cycle

Suppose `d!=0` and `q=beta(d,d)=I`. Choose quotient rows `x=z+d`
and `z` and physical row-fibre labels `a,b`. The relative row map
from row `(x,a)` to row `(z,b)` sends a column over `y_t=y+td` to a
column over `y_(t+1)`. All its inner maps are affine because (1) is
Latin. Set `A=beta(x,x)`, `B=beta(z,z)`, `T=B^(-1)A`, and
`v=beta(z,d)`. Commutativity and bilinearity give
`T=v^2 q`. If `w_t` is the current inner column position, direct
equality of the two row outputs gives, in characteristic two,

```text
w_(t+1) = T w_t
          + B^(-1) beta(x,y_t)^2 a
          + B^(-1) beta(z,y_(t+1))^2 b
          + B^(-1)(c(x,y_t)+c(z,y_(t+1))).                       (3)
```

All matrices involved have order dividing `p`, so `T^p=I`.
Composing (3) over its full quotient orbit yields an affine return
map with slope `I`. The coefficient of `a` in that return is

```text
A^(-1) beta(x,y)^2 * S(q),     S(q)=sum_(t=0)^(p-1) q^t,       (4)
```

and the coefficient of `b` is

```text
A^(-1) beta(z,y+d)^2 * S(q^(-1)).                              (5)
```

Indeed, `beta(x,d)=v q`; in the sum of transported `a` terms the
ratio between consecutive summands is
`T^(-1) beta(x,d)^2 = q`, while for `b` it is
`T^(-1) beta(z,d)^2 = q^(-1)`. Their initial transported coefficient
is `T^(-1)B^(-1)=A^(-1)`. This derivation uses only commuting
matrices, not scalar division.

When `q=I`, both geometric sums are `pI=I` over `F_2`. In
particular, (5) is invertible. For any starting quotient column
`y`, twist `c`, and first row label `a`, choose the second row label
`b` to cancel the complete translation of the return map. The
return is then the identity on `V`. The quotient position has exact
odd orbit length `p`, so every point above this orbit lies in a
physical `p`-cycle. Hence row-F requires

```text
                    beta(d,d) != I for every d != 0.            (6)
```

Identity in (6) cannot be weakened to "has a fixed vector": if `q`
has a proper fixed subspace, the line-label terms may cancel only
that subspace, while a twist return can remain nonzero in another
summand. For example, a scalar FFF instance from C262 times the
order-two group table adds a trivial one-dimensional character to
this ansatz and stays FFF by the product theorem, although each
`beta(d,d)` then has a fixed vector. The proof uses the **entire**
diagonal matrix being the identity.

## Simultaneous character bound

Every `beta(x,y)` has order dividing `p`. Because the matrices
commute and `p` is odd, they are simultaneously diagonalizable over
`K=F_(2^e)`, which contains all `p`-th roots of unity. Choose a
primitive root `zeta`. Each common eigencharacter has the form

```text
               beta(x,y) -> zeta^(B_i(x,y)),
```

where `B_i:G x G -> F_p` is a symmetric bilinear form. Nontrivial
characters occur in Frobenius-conjugate orbits of length exactly `e`:
on their nonzero exponent forms Frobenius multiplies by `2`, whose
order modulo `p` is `e`. Therefore there are at most
`t=floor(D/e)` nontrivial character orbits, counted with
multiplicity; trivial eigencharacters impose no condition. Put
`Q_i(d)=B_i(d,d)`. Each `Q_i` is homogeneous quadratic.

If `r>2t`, the number of simultaneous zeros of all `Q_i` is
divisible by `p`. One elementary proof sums

```text
            prod_(i=1)^t (1-Q_i(d)^(p-1))
```

over `d in F_p^r`. The product is the indicator of simultaneous
vanishing in `F_p`. Its degree is at most `2t(p-1)<r(p-1)`.
In every monomial some variable has exponent below `p-1`; summing
that variable over `F_p` gives zero modulo `p`, including exponent
zero. Thus the number of common zeros is `0 mod p`. Since the zero
vector is one such zero, a nonzero common zero exists. At this
`d`, every eigenvalue of `beta(d,d)` is one, hence
`beta(d,d)=I`, contradicting (6). Therefore `r<=2t`, so
`floor(D/e)>=ceil(r/2)`, proving (2).

## Attainment under an explicit field-size hypothesis

Partition `G` into `ceil(r/2)` summands of dimension two, with one
dimension-one summand if `r` is odd. For each two-dimensional
summand choose a nonsquare `nu in F_p` and the anisotropic quadratic
form `u_1^2-nu*u_2^2`; for a one-dimensional summand use `u^2`.
Let each corresponding symmetric bilinear form act by scalar
multiplication through an order-`p` character on one additive copy
of `F_(2^e)`. Their direct sum is a matrix bicharacter on a fibre
of dimension `e*ceil(r/2)`. Its diagonal matrix is nonidentity at
every nonzero difference.

More is needed for FFF: condition (6) alone is not sufficient.
Under `2^e>3(p^2-1)`, the [C262 construction](fff_cubefree_crt_common_fiber_lift.md)
provides an FFF twist for each rank-two summand and, since the same
inequality implies `2^e>3(p-1)`, for the possible rank-one summand.
Take their direct product. By the [direct-product theorem](../repro_runs/2026-04-26_direct_product_fff/proof_note_direct_product_fff.md),
it is FFF in row, column and symbol views. Componentwise its
operation is exactly (1) for the direct-sum matrix bicharacter and
the direct-sum twist. The lower bound (2) therefore equals the
attained minimum **for this ansatz under the stated inequality**.
For example, `p=11` has `e=10` and `2^e=1024>360`, so rank three
has minimum `D=20` within (1). This constructs no explicit materialized
order-`11^3*2^20` table; it is a compact existence deduction.

## Boundary

This proof assumes the exact matrix-bilinear form (1). It says
nothing about nonlinear fibres, arbitrary Latin block substitution,
other quotient operations, or arbitrary FFF order spectra. At
`p=3,r=3`, it excludes a four-element fibre in this ansatz, but
does not exclude an FFF square of order `108` by another method.
In particular it does not decide order 18, does not establish
literature priority, and does not complete the active research goal.
