# The sharp quotient-group boundary of the scalar bilinear FFF lift

**Scope.** This is a theorem about the *specific* scalar bilinear lift used
in [C262](fff_cubefree_crt_common_fiber_lift.md), not about all FFF Latin
squares or all lifts. In particular it neither excludes nor constructs an
FFF square of order 18. The finite [companion controls](../repro_runs/2026-09-28_fff_scalar_bilinear_boundary/README.md)
are secondary to the proof.

## Model and theorem

Let `G` be a finite abelian group of odd order `N>1`, let `K` be a finite
field of characteristic two, and let
`beta:G x G -> K^*` be a symmetric bicharacter. For any twist array
`c:G x G -> K`, define a Latin operation on `G x K` by

```text
 (x,a) * (y,b) = (x+y, beta(x,y)^2 a + beta(x,x)b + c(x,y)).       (1)
```

Both fibre coefficients are nonzero, so (1) is Latin for every `c`.

**Theorem.** If *any* twist makes (1) row-F, then every Sylow subgroup of
`G` is elementary abelian of rank at most two. Conversely, for every odd
abelian `G` of that type, a sufficiently large characteristic-two field,
one symmetric bicharacter, and one twist make (1) FFF in all three views.
Thus the scalar bilinear ansatz admits an FFF instance for a group of order
`N` exactly when `G` is a product of `F_p` and `F_p^2` components. An order
`N` admits *some* such group exactly when `N` is cubefree.

The necessity holds for every field and every twist, no matter how large.
The converse is the explicit C262 construction, including its field-size
condition; it does **not** say that every bicharacter or twist works.

## An isotropic difference forces an odd row cycle

Put `q(d)=beta(d,d)`. Suppose `d!=0` and `q(d)=1`. Choose distinct quotient
rows `x=z+d` and `z`, and let `h=ord(d)`, which is odd and greater than one.
The relative row map, oriented as inverse row `z` after row `x`, sends a
column quotient `y_t=y+td` to `y_(t+1)`. Its fibre map is

```text
 w_(t+1) = alpha*w_t + A_t*a + B_t*b + C_t,
 alpha = beta(x,x)/beta(z,z),
 A_t = beta(x,y_t)^2/beta(z,z),
 B_t = beta(z,y_t+d)^2/beta(z,z),
 C_t = [c(x,y_t)+c(z,y_t+d)]/beta(z,z).                       (2)
```

Because `x=z+d`, bicharacter identities give
`alpha^h=1` and `q(d)^h=1`. Composing (2) for the full quotient orbit
yields a unit slope. Expanding the two line-label coefficients, exactly as
in C262's row-return derivation, gives

```text
 A = beta(x,y)^2/beta(x,x) * sum_(t=0)^(h-1) q(d)^t,
 B = beta(z,y+d)^2/beta(x,x) * sum_(t=0)^(h-1) q(d)^(-t).     (3)
```

The remaining term `Lambda_y(c)` depends on the twist and quotient orbit,
but not on `a,b,w`. When `q(d)=1`, both sums in (3) equal `h*1=1` in
characteristic two. Hence `A,B` are nonzero. Fix any quotient orbit `y`
and any first row-fibre label `a`. Choosing the second label
`b=B^(-1)*(A*a+Lambda_y(c))` makes the return exactly the identity on
the fibre. The two physical rows are distinct because `x!=z`, even if
their fibre labels coincide. Every position over this quotient orbit now
lies on an odd relative cycle of length `h`. Thus row-F is impossible.

Notice that the twist cannot repair this obstruction: it changes only
`Lambda_y(c)`, and the freely chosen second line label cancels that value.
The argument proves the necessary condition

```text
                  beta(d,d) != 1 for every d != 0.             (4)
```

## Which odd groups can satisfy (4)?

First suppose `G` contains an element `u` of order `p^2` for an odd prime
`p`. Then `d=pu` is nonzero, but biadditivity gives

```text
 beta(d,d)=beta(u,u)^(p^2)=beta(p^2*u,u)=1.
```

Therefore every Sylow subgroup must have exponent `p`.

Now suppose an elementary `p`-subgroup has rank at least three. Restrict
`beta` to a three-dimensional `F_p`-subspace `V`. Its values lie in the
group of `p`-th roots of unity in `K^*`. If that group is trivial, every
nonzero vector is isotropic. Otherwise choose a primitive root `omega`
and write `beta(v,v)=omega^(Q(v))`, with `Q` a homogeneous quadratic form
`V -> F_p`. This form has a nonzero zero. For completeness, the number
of zeros is congruent modulo `p` to

```text
             sum_(v in F_p^3) (1-Q(v)^(p-1)).                 (5)
```

The constant sum is `p^3=0 (mod p)`. Every monomial in the expansion of
`Q^(p-1)` has total degree `2(p-1)<3(p-1)`, so some variable has exponent
strictly below `p-1`. Its sum over `F_p` is zero modulo `p` (including
exponent zero). Thus (5) is zero modulo `p`. Since the zero vector is one
zero, there are at least `p` zeros, including a nonzero one. This
contradicts (4). Every Sylow rank is therefore at most two.

Conversely, for such a `G`, choose the anisotropic rank-one square and
rank-two quadratic norm on each `F_p` component, combine them by CRT, and
choose the faithful scalar character into `GF(2^D)^*` exactly as in C262.
Its diagonal value is nonidentity for every nonzero `d`. If `D` is a
positive multiple of `ord_rad(N)(2)` and `2^D>3(N-1)`, C262's all-three-
view return proof and greedy twist assignment make (1) FFF. This proves
the converse and the theorem.

## Consequence and boundary

For `G=F_3^3`, *every* scalar symmetric bicharacter has an isotropic
nonzero difference, although the quotient is elementary abelian. For
`G=Z/9Z`, the difference `3` is isotropic for *every* bicharacter,
although the group has cubefree order. The contrast with the anisotropic
`F_3^2` norm is checked exhaustively in the companion run.

This explains why enlarging the **same scalar bilinear construction**
beyond cubefree quotient orders cannot work by merely choosing a larger
field or a better twist. It does not rule out vector-valued fibres,
non-bilinear coefficients, nonabelian quotients, direct products of other
FFF constructions, or an FFF Latin square of order 18. In particular,
it is a scoped structural no-go theorem, **not** the active Goal's
unrestricted breakthrough or a publication-priority assertion.

For order 18 specifically, the binary field has trivial multiplicative
group, so every bicharacter in (1) is trivial and this obstruction is
immediate. The earlier [C42 binary-quotient pattern equality](fff_subsquare_and_congruence_obstructions.md)
already rules out **every** two-point-fibre Latin quotient of odd order,
and [C209](fff_pairblock_odd_subgroup_coset_obstruction.md) separately
rules out broad one-view affine pair-block families. A one-view pair-block
system need not itself be a three-sorted binary quotient. C263 therefore
does **not** close a previously open order-18 search branch.
