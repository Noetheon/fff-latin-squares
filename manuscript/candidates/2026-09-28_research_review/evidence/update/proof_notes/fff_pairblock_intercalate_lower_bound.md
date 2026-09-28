# Intercalates forced by a one-view pair-block system

## Evidence boundary

The theorem below is a direct proof for any Latin square of order `2m`.
It does not assume FFF. The order-18 consequence is only a necessary
condition for the still-open pair-imprimitive branch. No order-18
existence or nonexistence conclusion follows.

## Theorem

Let `L` be a Latin square of order `2m`. Suppose the normalized line
permutations in **one** of its three views preserve a partition of their
domain into `m` pairs. If `I(L)` is the number of intercalates, then

```text
                 I(L) = m^2 + 2K for some integer K >= 0.        (1)
```

In particular, `I(L) >= m^2` and `I(L) = m (mod 2)`.

### Proof in the row view

Use a base-row isotopy to identify columns and symbols so that every
row map preserves the given pair partition. Label both sets by
`[m] x F_2`. Every row `g` then has the form

```text
L(g,(x,t)) = (phi_g(x), t + f_g(x)).
```

Let `J(y,u)=(y,u+1)` flip every symbol pair, and let `C_(x,t)` be the
column map from rows to symbols. Then

```text
C_(x,1) = J C_(x,0).                                           (2)
```

For each `x`, the relative permutation of the two columns in the same
block is

```text
C_(x,1)^(-1) C_(x,0) = C_(x,0)^(-1) J C_(x,0).
```

It has exactly `m` transpositions. Each transposition in a column-pair
permutation is one intercalate using that column pair. The `m`
within-block column pairs therefore contribute exactly `m^2` distinct
intercalates.

For two distinct column blocks `x,z`, there are four physical column
pairs. By (2), the relative permutations of `(x,0),(z,0)` and
`(x,1),(z,1)` are identical. Those of `(x,0),(z,1)` and
`(x,1),(z,0)` are also identical. Indeed,
`(J C_z)^(-1)(J C_x)=C_z^(-1)C_x`, while
`(J C_z)^(-1)C_x=C_z^(-1)J C_x` and
`C_z^(-1)(J C_x)=C_z^(-1)J C_x`.
Each cross-block transposition count is consequently counted twice.
Its total contribution is even and nonnegative, giving (1).

For a column- or symbol-view block system, apply the row argument to
the corresponding parastrophe. An intercalate is the same four-cell
configuration under permutation of the three coordinate sorts, so
`I(L)` is unchanged. This proves the three-view statement. QED.

## Order-18 consequence and limits

If a hypothetical FFF square of order 18 has a pair-imprimitive
normalized view group, then `m=9` and necessarily

```text
                         I(L) >= 81 and I(L) is odd.           (3)
```

Conversely, if an order-18 FFF square had `I(L) <= 80` **or** even
`I(L)`, none of its three normalized view groups could preserve a
pair partition. C207 then makes all three groups primitive, conditional
on C06's exact order-6 exclusion. With the separate external catalogue
assumption of C206, each would be `A18` or `S18`, with at least one
`S18`. This is conditional reasoning about a *hypothetical* square,
not an order-18 result.

The converse to (1) is false: parity and a large intercalate count do
not imply a pair-block system. The frozen FFF order-14 table has only
13 intercalates, below the pair-block threshold 49, consistent with
its previously checked lack of pair imprimitivity. Finite controls in
the [dated run](../repro_runs/2026-09-28_pairblock_intercalate_bound/README.md)
test the theorem across all 9,408 reduced order-6 squares, the 230
frozen FFF order-8 representatives, and order-14/order-16 controls.
They are independent checks of the statement, not its proof. No
literature-priority or external expert-review claim is made.
