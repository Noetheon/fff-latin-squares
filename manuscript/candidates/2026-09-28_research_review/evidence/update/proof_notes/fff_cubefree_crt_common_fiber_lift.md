# A common-fibre FFF lift for every odd cubefree quotient order

**Evidence boundary.** The theorem below is an internal mathematical proof,
with exact finite controls in
[`2026-09-28_fff_cubefree_crt_lift`](../repro_runs/2026-09-28_fff_cubefree_crt_lift/README.md).
It generalizes the prime-square construction C164. An older archive inventory
mentions a similar cubefree assertion, but the archive is not an input to this
proof and is not presently available for a line-by-line comparison. No
literature-priority, external-referee, minimal-threshold, order-18 or paper
release assertion follows.

## Theorem

Let `N>1` be odd and cubefree, let `M=rad(N)`, and put
`e=ord_M(2)`. If `D>0` is a multiple of `e` and

```text
                             2^D > 3(N-1),                       (1)
```

then an FFF Latin square of order `N*2^D` exists. Every induced
two-line cycle in each of the row, column and symbol views has length
`2` or `2h`, where `h` is the odd additive order of a nonzero quotient
difference. In particular,

```text
 h(N) <= min {D>0: e divides D and 2^D>3(N-1)}.                (2)
```

Here `h(N)` is the smallest dyadic exponent for which an FFF square
of order `N*2^h` exists; the theorem does not identify that minimum.

## CRT quotient and anisotropic form

Write `N=prod_p p^(r_p)` with `r_p` equal to `1` or `2`. Let

```text
 G = prod_p F_p^(r_p),                  R = prod_p F_p.
```

Thus `|G|=N`, while the additive group of `R` is cyclic of order
`M=prod_p p`. For `r_p=1`, set `B_p(x,y)=xy`. For `r_p=2`, choose a
nonsquare `nu_p` in `F_p` and set

```text
 B_p(x,y)=x_1*y_1-nu_p*x_2*y_2.
```

Take `B=(B_p)_p:G x G -> R` and `Q(x)=B(x,x)`. In a rank-two component,
`Q_p(d)=0` for nonzero `d` would make `nu_p` a square; in rank one it
would make `d=0`. Consequently

```text
 Q_p(d)!=0 iff d_p!=0,    and    ord_R(Q(d))=ord_G(d)=:h(d).    (3)
```

For every `R`-valued expression formed by pairing with `d`, its
coordinates outside the support of `d` vanish. In each active
coordinate, multiplication by `h(d)` is zero and
`sum_(t=0)^(h(d)-1) t =0`, because that coordinate has odd prime
characteristic dividing `h(d)`.

Let `K=GF(2^D)`. Condition `e|D` gives `M|(2^D-1)`, so there is a
primitive `M`-th root `omega` in `K`. The CRT identification
`R_add ~= Z/MZ` gives an injective additive character
`chi:R -> K^*` with `chi(t)=omega^(CRT(t))`. By (3), `chi(Q(d))`
has exact multiplicative order `h(d)` whenever `d!=0`.

## Latin operation and all three returns

For an arbitrary twist array `c:G x G -> K`, define

```text
 (x,a) * (y,b) =
   (x+y, chi(2B(x,y))*a + chi(Q(x))*b + c(x,y)).              (4)
```

The field has characteristic two. Both fibre coefficients are
nonzero. Fixing either input and the output first determines the
missing quotient coordinate `x` or `y`, then the missing fibre
coordinate by one linear equation. Thus (4) is Latin for **every**
`c`.

Fix a view and two lines whose quotient labels differ. In the row,
column and symbol views, respectively, the quotient relative map
translates a position by `d=x-z`, `d=y-z`, or `d=l-k`, up to the
chosen orientation. Each quotient orbit has length `h=h(d)`.
Writing the current fibre position as `w_t`, direct substitution and
inversion of (4) give the following one-step affine recurrence:

```text
 w_(t+1) = chi(D_t)*w_t + chi(E_t)*a + chi(F_t)*b
           + chi(U_t)*c(cell_1(t)) + chi(V_t)*c(cell_2(t)).   (5)
```

All exponents are in `R`. The table fixes the line-pair orientation
and names the quotient starting point as in C164; `y_t=y+td` and
`x_t=x+td`.

| View | `D_t` | `E_t` | `F_t` | `U_t,V_t`; twist cells |
| --- | --- | --- | --- | --- |
| row lines `x,z`; `d=x-z` | `Q(x)-Q(z)` | `2B(x,y_t)-Q(z)` | `2B(z,y_t+d)-Q(z)` | both `-Q(z)`; `(x,y_t),(z,y_t+d)` |
| column lines `y,z`; `d=y-z` | `2B(x_t,y)-2B(x_t+d,z)` | `Q(x_t)-2B(x_t+d,z)` | `Q(x_t+d)-2B(x_t+d,z)` | both `-2B(x_t+d,z)`; `(x_t,y),(x_t+d,z)` |
| symbol lines `k,l`; `d=l-k`; `y_t=y+td`, `x_t=k-y_t` | `2B(x_t,d)` | `-Q(x_t)+2B(x_t,d)` | `-Q(x_t)` | `U_t=E_t,V_t=F_t`; `(x_t,y_t),(x_t,y_t+d)` |

For clarity, the symbol line at `(k,a)` maps a column `(y,w)` to
the unique row `(k-y,u)` given by

```text
 u = chi(Q(k-y)-2B(k-y,y))*w
     + chi(-2B(k-y,y))*a
     + chi(-2B(k-y,y))*c(k-y,y).                              (6)
```

Inverting the second symbol line in (6) yields the symbol entry of
(5); it is not inferred from row or column symmetry.

In every active prime coordinate, the `D_t` entry is constant or
affine-linear in `t`; inactive coordinates are zero. Since `h` is
divisible by every active prime and every such prime is odd,
`sum_t D_t=0` in `R`. Hence the return slope after `h` steps is one.
When the future slopes are composed into the two line-label terms,
their exponents simplify as follows:

| View | First label after accumulation | Second label after accumulation |
| --- | --- | --- |
| rows | `2B(x,y)-Q(x)+tQ(d)` | `2B(z,y+d)-Q(x)-tQ(d)` |
| columns | `Q(x)-2B(x,y)-tQ(d)` | `Q(x)-2B(x,z)+(t+1)Q(d)` |
| symbols | `-Q(x)-tQ(d)` | `-Q(x)-2B(x,d)+tQ(d)` |

For example, in the row case the later-slope sum is
`(h-1-t)*(Q(x)-Q(z))`. The difference `Q(x)-Q(z)` is supported only
where `d!=0`, so multiplication by `h` vanishes there; expansion of
`Q(x)-Q(z)=2B(z,d)+Q(d)` gives both row formulas.

For the column case put `A=2B(x-z,d)`, where `d=y-z`. Then
`D_t=A+2tQ(d)` and the sum of the slopes *after* step `t` is
`-(t+1)A-t(t+1)Q(d)`. Expanding `Q(x+td)` and `Q(x+(t+1)d)` in
`E_t,F_t` yields the two displayed column exponents. For the symbol
case put `x_t=x-td`. Here `D_t=2B(x,d)-2tQ(d)` and the later-slope
sum is `-2(t+1)B(x,d)+t(t+1)Q(d)`; expansion of `Q(x-td)` gives
the two symbol exponents. These equalities hold in `R`, not merely
after evaluating `chi`: outside the support of `d` every term is zero,
and in each active `F_p` coordinate `h=0`, `2` is invertible, and
`sum_(s=0)^(h-1)s=h(h-1)/2=0`. Thus a **composite** `h` causes no
extra return slope or label term.

By (3), for every `A in R` and either sign,

```text
 sum_(t=0)^(h-1) chi(A +/- tQ(d)) =
   chi(A)*sum_(t=0)^(h-1) chi(Q(d))^(+/-t) = 0.             (7)
```

Thus *both* line-label contributions cancel in all three views,
independently of their fibre labels. Every return map is exactly

```text
                       w -> w + Lambda_C(c),                       (8)
```

where `C` indexes the view, quotient line pair and quotient orbit.

## Nonzero returns and FFF

Each `Lambda_C` is a nonzero `K`-linear form in the `N^2` twist
cells. Its `2h` support cells are distinct: the two old quotient
lines (or, in the symbol view, the two quotient symbols) are
different, and each contributes exactly `h` cells around the orbit.
Every coefficient is a value of `chi`, hence nonzero.

Fix one twist cell. For each of the `N-1` other quotient line labels
in a given view, that cell belongs to exactly one return form.
Therefore the cell occurs in exactly `3(N-1)` forms across the three
views. Order the cells. When assigning one cell, require each form
whose last cell it is to be nonzero. Since its last-cell coefficient
is nonzero, each such form forbids just one value of `K`.
At most `3(N-1)` values are forbidden. Inequality (1) leaves a
choice. Induction supplies `c` making every return in (8) nonzero.

For lines with distinct quotient labels, a quotient cycle of odd
length `h` now lifts through a nonzero translation of the
characteristic-two fibre. That return translation has only 2-cycles,
so the physical cycles have length `2h`. For two lines with the same
quotient label, write their distinct fibre labels as `a,b`. At a
quotient position `(x,y)`, the row-view translation constant is
`chi(2B(x,y)-Q(x))*(a+b)`, and the column-view constant is
`chi(Q(x)-2B(x,y))*(a+b)`. Equation (6) gives the symbol-view
constant `chi(-Q(x))*(a+b)` at `x=k-y`. All are nonzero because
`a+b!=0` and `chi` takes nonzero values. Thus these maps have only
2-cycles too. The row, column and symbol formulas cover every line
pair; the whole square is FFF. QED.

## New scope relative to earlier bounds

For `N=11^2*41^2=203401`, the radical is `451`,
`ord_451(2)=20`, and `2^20=1048576>3(N-1)=610200`.
The theorem therefore gives `h(203401)<=20`, by a compact
construction without materializing its square of order roughly
213 billion. Separately applying C164 to `11^2` and `41^2` and taking
their direct product yields only the recorded upper bound
`10+20=30`; the CRT common fibre saves ten dyadic exponents **against
that particular product construction**, not against all possible
constructions or the unknown minimum.

This theorem includes C164's prime-square statement and also works
for mixed prime components. It does **not** prove a uniform bound on
`h(N)` independent of `N`, settle order 18 (`h(9)=1` is still open),
or classify all FFF orders. The dated controls rebuild the `N=9`
greedy twist element-for-element, audit all returns for `N=15,45,75`, and
physically scan selected row, column and symbol line pairs; the
general theorem rests on the proof, not on those finite tests.
