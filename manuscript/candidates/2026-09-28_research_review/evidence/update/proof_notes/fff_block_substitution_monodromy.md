# Three-view monodromy for Latin block substitutions

**Status (C260).** The formula below is a direct all-order theorem. The dated
[finite audit](../repro_runs/2026-09-27_fff_block_substitution_monodromy/README.md)
checks two frozen order-12 examples and two small controls. It is not a
decision of unrestricted FFF existence at order 18, a novelty or priority
claim, or an independently reviewed paper result.

## Block substitution

Let `Q:A x A -> A` be a Latin square of order `m`. For every `(a,b)` let
`F_ab:B x B -> B` be a Latin square on the same set `B` of order `k`.
No isotopy, linearity, or dependence on only one outer coordinate is
assumed. Define a square on `A x B` by

```text
H((a,x),(b,y)) = (Q(a,b), F_ab(x,y)).                         (1)
```

This is Latin: for fixed `(a,x)` and desired output `(s,z)`, the equation
`Q(a,b)=s` determines `b`, then `F_ab(x,y)=z` determines `y`.
The column argument is identical.

For a view `v` in `{row,col,sym}`, each line is a bijection from its
position set to its value set. For distinct lines `u,w`, write
`P_v(u,w)=f_w^(-1) f_u` on positions. Its odd-cycle witness bit is
`bad_v(u,w)`. Quotient and lifted views use the same convention; all
three coordinate sets are labelled in outer-inner order.

## Exact cycle formula

**Theorem.** Fix any view `v` of `H`.

1. Two lifted lines with the same outer line label preserve every outer
   position. Over each outer position, their relative permutation is a
   two-line permutation in exactly one of the blocks `F_ab` in view `v`.
   As the common outer line label and the outer position vary, every
   block and every one of its line pairs occurs.
2. For lifted lines with distinct outer labels, their relative
   permutation projects to the quotient relative permutation `pi` in
   view `v`. Let `C=(c_0,...,c_(d-1))` be any cycle of `pi`. Each step
   above `c_i` induces a bijection `h_i:B -> B` on the inner position.
   The return map at `c_0` is the monodromy

   ```text
   Omega_C = h_(d-1) o ... o h_1 o h_0.                     (2)
   ```

   If `Omega_C` has a cycle of length `e`, its lift is one cycle of
   length `d*e`. This accounts for every cycle above `C`.

Consequently, with `cross_v` meaning that some distinct-outer-line pair
has an odd quotient cycle whose monodromy has an odd cycle,

```text
pat_v(H) = (OR_(a,b) pat_v(F_ab)) OR cross_v.                (3)
```

In particular, if `Q` is FFF, then
`pat(H)=OR_(a,b) pat(F_ab)` componentwise, so `H` is FFF exactly when
all its blocks are FFF. For arbitrary `Q`, every FFF `H` still has
FFF blocks, while a bad quotient cycle can be masked by an even-cycle
monodromy. Formula (3), not a simple quotient OR, is the general rule.

**Proof.** In the row view, a line `(a,x)` maps `(b,y)` to
`(Q(a,b),F_ab(x,y))`. With the same `a` but different `x`, equality of
outer outputs for two columns forces the second outer column to equal
`b`, and the inner relative map is that of rows `x,x'` in `F_ab`.
With different outer rows `a,a'`, equality forces the second outer
column to be `pi(b)`, where `pi` is the quotient row-pair permutation.
The inner map from the column over `b` to the column over `pi(b)` is
`F_(a',pi(b))(x',-)^(-1) F_(a,b)(x,-)`, hence is bijective.

In the column view exchange rows and columns: same outer column `b`
leaves each outer row `a` fixed and reads the column-pair permutation
inside `F_ab`; different outer columns project to the corresponding
quotient column-pair permutation.

In the symbol view, regard a symbol line as mapping each column to the
unique row bearing that symbol. For two symbols `(s,z),(s,z')`, the
outer column `b` stays fixed; the outer row is uniquely determined by
`Q(a,b)=s`, and the inner relative map is the symbol-pair permutation
of `F_ab`. For `(s,z),(s',z')` with `s!=s'`, the outer column follows
the quotient symbol-pair permutation. The inner map is bijective
because both symbol lines of each involved block are bijections.

In each view, the first return to outer position `c_0` is exactly the
composition (2). A point on an `e`-cycle of that return map closes
after `e` returns, each taking `d` lifted steps; it cannot close before
the outer coordinate returns. Its cycle length is therefore `d*e`.
This proves both parts and (3). QED.

## The smallest failing-quotient example in the frozen evidence

Both frozen C158 order-12 FFF tables are already labelled in three
contiguous blocks of four rows, columns and symbols. The dated audit
checks directly that each `4 x 4` block maps into one four-symbol block,
that the resulting quotient is a Latin square of order three and hence
`TTT` by C35, and that all nine inner blocks are FFF. It then verifies
every physical cycle against (2) in all three views. This is a concrete
counterexample to extending C247's row-fibred quotient-OR equality to
arbitrary cell-dependent block squares. It does **not** contradict C247:
these blocks vary with both outer coordinates.

Under the locally established small-order facts C06 and C157, order
12 is the smallest possible order of an FFF square with a non-FFF
Latin quotient: FFF has even order; orders 6 and 10 have none; and
the only proper nontrivial quotient orders below 12 for FFF squares
of orders 4 or 8 are 2 or 4, whose Latin squares are FFF by C06.
This minimality statement inherits C06/C157's computational evidence.

The binary-kernel case remains special: C42 proves that when `k=2`,
`pat(H)=pat(Q)` for any such extension. Thus an odd-order quotient
cannot be masked by two-point fibres. At order 18 a hypothetical FFF
square is isotopically congruence-simple by C186; in particular this
block-substitution construction with quotient nine and fibre two cannot
produce one. The theorem supplies a general cycle language, **not** an
FFF18 construction, obstruction beyond C186, or completion of the
active order-18 goal.
