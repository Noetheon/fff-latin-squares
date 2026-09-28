# Row-fibred extensions of Latin squares

**Evidence boundary.** The pattern theorem below is a direct proof for all
finite Latin squares in its stated domain. The finite examples are secondary
controls, not a census or a literature-priority claim. In particular, this
construction does not decide the existence of an FFF square of order 18.

Related index-two block constructions have prior literature: K. W. Johnson,
[*The construction of loops using right division and Ward quasigroups*
(2006)](https://www.math.md/en/publications/qrs/issues/v14-n1/10700/),
describes a dihedral extension with two row-dependent operations over a
binary quotient. We do **not** claim novelty for the layered construction
itself, and have not completed a priority audit of the FFF-pattern theorem
or the numerical lower bound.

Let `B:Y x Y -> Y` be a Latin square, and for each `y in Y` let
`Q_y:X x X -> X` be an arbitrary Latin square on the same set `X`. Define

```text
M((r,y),(c,z)) = (Q_y(r,c), B(y,z)).                         (1)
```

No compatibility, common isotopy, or associativity is assumed among the
fibres `Q_y`. For a pattern, write `OR_y pat(Q_y)` for componentwise Boolean
OR over the fibre patterns.

## Latin property and the pattern theorem

**Theorem.** `M` is Latin. In each of the row, column and symbol views,

```text
pat(M) = pat(B) OR (OR_y pat(Q_y)).                         (2)
```

Consequently `M` is FFF **if and only if** `B` and every `Q_y` are FFF.
Taking all fibres equal to `L` recovers the ordinary direct product
`L x B`, but (2) allows the fibres to be different.

**Proof.** In a fixed row `(r,y)`, the maps `c -> Q_y(r,c)` and
`z -> B(y,z)` are bijections. In a fixed column `(c,z)`, the output second
coordinate determines `y` uniquely, and then the first coordinate
determines `r` uniquely. Thus (1) is Latin.

For a row pair `(r,y),(r',y')`, if `y=y'`, equality of output second
coordinates forces `z'=z`; on every such `z`-fibre the induced permutation
is precisely the row-pair permutation of `Q_y`. If `y!=y'`, the induced map
projects on the `z` coordinate to the row-pair permutation of `B` for lines
`y,y'`. An orbit upstairs has length divisible by the length of its
projected orbit. Therefore, when the row view of `B` is F, every such
cross-fibre orbit has even length. A row witness in any `Q_y` survives
unchanged on every fixed `z`-fibre.

For a column pair `(c,z),(c',z')`, if `z=z'`, equality of output second
coordinates forces the input row quotient coordinate `y` to stay fixed;
the first coordinate follows the column-pair permutation of `Q_y`. If
`z!=z'`, the induced map on input row quotient coordinates projects to the
column-pair permutation of `B` for `z,z'`. Even quotient cycles force even
upstairs cycles. Each column witness in `Q_y` survives in the fixed-`y`
part of a pair of columns with equal `z`.

For a symbol pair `(s,t),(s',t')`, view a symbol line as the bijection from
column positions `(c,z)` to the unique row position `(r,y)` producing that
symbol. If `t=t'`, the quotient column position `z` stays fixed, and the
corresponding quotient row coordinate `y` is the unique solution of
`B(y,z)=t`; the first coordinate follows the symbol-pair permutation of
`Q_y`. Each `y` occurs for exactly one `z`, so every fibre symbol witness
survives. If `t!=t'`, the induced map on quotient column positions projects
to the symbol-pair permutation of `B` for `t,t'`. When the symbol view of
`B` is F, each projected orbit is even, hence each upstairs orbit is even.

The same-quotient cases embed every fibre witness. The cross-quotient
projection cases show that no *new* odd witness can appear unless that
view already fails in `B`. To establish the reverse inclusion for `B`,
we must lift an odd quotient cycle with **one suitable choice** of the
first-coordinate data; an arbitrary upstairs line pair could instead
have an even multiple of the projected cycle.

For a row-view odd cycle of the quotient pair `y,y'`, choose any first
column coordinate `c` and any row `r` of `Q_y`. The Latin column of
`Q_y'` supplies a unique `r'` with
`Q_y(r,c)=Q_y'(r',c)`. Thus the first column coordinate stays fixed
throughout the quotient row-pair cycle, and the upstairs row pair
`(r,y),(r',y')` has an odd cycle of exactly the same length.

For a column-view odd cycle of quotient columns `z,z'`, choose the
upstairs columns `(c,z),(c,z')` with a common first coordinate `c`,
and fix a first-coordinate symbol `s`. At every quotient row `y` along
the cycle, the Latin column of `Q_y` supplies a unique `r_y` with
`Q_y(r_y,c)=s`. The lifted column permutation carries `(r_y,y)` to
`(r_{y'},y')` along the quotient cycle, so its length is the same odd
length.

For a symbol-view odd cycle of quotient symbols `t,t'`, choose the
upstairs symbols `(s,t),(s,t')` with common first coordinate `s`
and fix a first column coordinate `c`. At each quotient column `z`,
the Latin symbol line of `B` determines `y` with `B(y,z)=t`, and the
Latin column of `Q_y` determines `r` with `Q_y(r,c)=s`. Under the
upstairs symbol-pair permutation, `c` stays fixed and `z` follows the
quotient symbol-pair cycle. This again gives an odd cycle of exactly
the quotient length.

Thus every quotient witness survives in the corresponding upstairs
view. Together with the fibre inclusion and the projection upper bound,
this proves equality (2) in all three views. QED.

## Intercalates in the binary case

For `B=C2`, write `M=F(Q_0,Q_1)` and let `I(Q)` count intercalates.
For each ordered choice of a row `r` of `Q_0` and a row `r'` of `Q_1`,
put `pi_(r,r') = row_(Q_1,r')^(-1) row_(Q_0,r)` and let `t_(r,r')`
be its number of two-cycles. Then

```text
I(F(Q_0,Q_1)) = 2 I(Q_0) + 2 I(Q_1) + n^2
                 + 2 sum_(r,r') t_(r,r').                    (4)
```

The within-layer row pairs duplicate each fibre two-cycle, giving the
first two terms. A cross-layer row pair acts on column positions as
`(c,d)->(pi_(r,r')(c),d+1)`. Each fixed point of `pi` gives one
two-cycle upstairs, and each two-cycle of `pi` gives two. Summing fixed
points over all `r,r'` gives exactly `n^2`: for each of the `n` columns
and `n` symbols, there is a unique row in each fibre bearing that symbol
in that column. This proves (4) without an FFF assumption. For
`Q_0=Q_1=L`, the mixed two-cycle sum is `2I(L)`, recovering C246's
`I(L x C2)=8I(L)+n^2`.

## Group-isotopy boundary

**Lemma.** Every Latin subsquare of a group-isotopic Latin square is itself
group-isotopic.

**Proof.** Under the ambient isotopy, a subsquare becomes three sets
`A,D,C` of equal size in a group, with `AD=C` and every product in `C`.
Choose `a0 in A`. For every `a in A`, `aD=C=a0D`, so the `|A|` elements
`a0^(-1)a` lie in the left stabilizer `H={g:gD=D}`. This subgroup acts
freely on `D`, giving `|H|<=|D|=|A|`; hence `A=a0H` and `|H|=|D|`.
It follows that `D=H d0` for any `d0 in D` and `C=a0H d0`.
In these coordinates the restricted multiplication is `(h1,h2)->h1h2`,
the table of `H`, up to isotopy. QED.

For each `y,z`, the rows `X x {y}`, columns `X x {z}`, and symbols
`X x {B(y,z)}` cut out a subsquare equal to `Q_y`. Thus if any fibre is
not group-isotopic, `M` is not group-isotopic.

The quotient has the same one-way property. Fix a base row `(r0,y0)`.
Its row-basis family under C14 consists of decomposable permutations

```text
(c,z) -> ( f_(r0,y0)^(-1) f_(r,y)(c),
           b_y0^(-1) b_y(z) ),
```

where `f_(r,y)(c)=Q_y(r,c)` and `b_y(z)=B(y,z)`.
If this family is closed, its projection onto the second coordinate is
closed under composition. That projection is exactly the row-basis
family of `B`; C14 therefore makes `B` group-isotopic. Consequently,
**if `M` is group-isotopic, both `B` and every `Q_y` are group-isotopic**.
The converse is **false**: group quotient and group fibres can combine
into a nongroup extension.

For example, take `B=C2`, `Q_0=C4` with `Q_0(r,c)=r+c mod 4`, and
`Q_1=C2 x C2` with `Q_1(r,c)=r xor c` on `{0,1,2,3}`. Both fibres and
`B` are FFF group tables, so their extension is FFF of order 8.
Its first row is the identity. In its row-basis family, the two rows
`(0,1)` and `(1,1)` act by `(c,z)->(c,z+1)` and
`(c,z)->(c xor 1,z+1)`. Their composition acts by
`(c,z)->(c xor 1,z)`. No `Q_0` row is the permutation `c->c xor 1`
(the `C4` translation sending `0` to `1` sends `1` to `2`, not `0`).
The row-basis family is therefore not closed; C14 proves that this
explicit FFF order-8 extension is not group-isotopic. This is an
elementary construction, not a claim of a new main class or literature
novelty.

## Scope

Every FFF square has even order by C35, so this construction cannot obtain
order 18 from an order-9 quotient or order-9 fibres: the order-9 factor
would force a failing pattern by (2). No main-class injectivity, class
count, arbitrary-extension classification, or order-18 conclusion follows
from the general theorem alone.

## Exact order-40 lower bound

The [companion finite audit](../repro_runs/2026-09-26_fff_row_fibred_extension/README.md)
uses the 512 previously frozen, spectrum-distinct FFF20 Steiner-trade
representatives as `Q_1`, fixes the untraded Steiner FFF20 square as
`Q_0`, and takes `B=C2`. It checks each resulting order-40 table in two
physical three-view scanners, rechecks its intercalate total directly
and via (4), and computes the **sorted** aggregate cycle spectrum from
every line pair. The 512 mixed extensions have 512 distinct spectra;
511 of those spectra do not occur among the 514 direct-product spectra
from C246's 512 trade representatives and two quadratic controls.
Therefore at least **1025** FFF main classes are represented at order 40.
By C246's injective `C2` spectrum formula, at least **1025** are
represented at every order `40*2^k`, `k>=0`. These are finite lower
bounds, not exact censuses or a general injectivity theorem for (1).
