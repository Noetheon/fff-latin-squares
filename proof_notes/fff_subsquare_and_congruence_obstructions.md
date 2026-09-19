# FFF Subsquare And Congruence Obstructions

Status: rigorous structural extension of the FFF theory.

## Evidence Labels

- Pattern monotonicity from Latin subsquares: **(a) rigorously proved**.
- Odd congruence blocks force pattern `TTT`: **(a) rigorously proved**.
- Pattern equality with a quotient having two-element congruence blocks:
  **(a) rigorously proved**.
- Every FFF quasigroup of order `2p`, for odd prime `p`, is congruence-simple
  in every isotope: **(a) rigorously proved**.
- The order-6 extension enumeration and order-8 subsquare census in the
  associated repro run: **(b) exactly computed**.

Throughout, a quasigroup congruence is an equivalence relation compatible
with multiplication and the two division operations. Its classes therefore
form a Latin quotient and all classes have the same size.

## Theorem 1: Latin Subsquare Pattern Monotonicity

Let `M` be a Latin subsquare of a Latin square `L`. Write its row, column and
symbol sets as `R0`, `C0` and `S0`, respectively. Then

```text
pat(M) <= pat(L)
```

componentwise, where `False < True`.

### Row view

Take `a,b in R0`. For the ambient square, let

```text
rho(c)=d  iff  L(a,c)=L(b,d).
```

If `c in C0`, then `L(a,c) in S0`. Row `b` of the subsquare contains that
symbol at a unique column `d in C0`. Hence `rho(C0)=C0`, and the restriction
of `rho` to `C0` is exactly the row-view permutation induced by rows `a,b` in
`M`. Every odd cycle of `M` is therefore an ambient odd cycle of `L`.

### Column view

The same argument with rows and columns interchanged shows that the ambient
column-view permutation induced by two columns in `C0` preserves `R0` and
restricts to the corresponding permutation of `M`.

### Symbol view

For a symbol `u`, let `s_u(c)` be the row containing `u` in column `c`. If
`u,v in S0` and `c in C0`, then `s_u(c) in R0`. The unique column `d` for
which `s_v(d)=s_u(c)` also lies in `C0`, because row `s_u(c)` contains `v`
inside the subsquare. Thus the ambient symbol-view permutation

```text
s_v^(-1) s_u
```

preserves `C0` and restricts to the symbol-view permutation of `M`.

This proves all three components.

### Corollaries

1. Every Latin subsquare of an FFF square is FFF.
2. An FFF square contains no Latin subsquare of odd order greater than one,
   by the odd-order `TTT` lemma C35.
3. Using the exact order-6 result C06, an FFF square contains no Latin
   subsquare of order 6. This third consequence is a rigorous implication
   from the computational input C06, not a purely theoretical theorem.

## Theorem 2: Odd Congruence Blocks Force TTT

Let `L` be a finite quasigroup with a congruence having blocks of odd size
`b>1`. Then

```text
pat(L)=TTT.
```

### Row view

Choose distinct rows `x,x'` in one congruence block `A`, and fix any column
block `B`. Compatibility of the congruence implies that both left
translations

```text
y -> x*y,     y -> x'*y
```

map `B` bijectively onto the same product block `A*B`. Consequently the
induced row permutation

```text
L_(x')^(-1) L_x
```

preserves `B`. It has no fixed point: a fixed `y` would give
`x*y=x'*y`, contradicting right cancellation. Its restriction to the odd set
`B` is therefore a fixed-point-free permutation of odd degree, so it has a
nontrivial odd cycle. The row bit is true.

### Column and symbol views

A quasigroup congruence is also a congruence for every parastrophe, because
it is compatible with multiplication and both divisions. Applying the row
argument to the row-column and row-symbol parastrophes proves the column and
symbol bits. Hence all three bits are true.

## Theorem 3: Binary Quotient Pattern Equality

Let `L` have a congruence whose blocks all have size two, and let `Q` be the
Latin quotient. Then

```text
pat(L) = pat(Q)
```

componentwise.

### Binary extension coordinates

Label every congruence block by `(i,0),(i,1)`, where `i` is its quotient
element. For fixed quotient elements `i,j`, multiplication restricted to the
two input blocks is a Latin square of order two in the output block. Every
binary Latin square has the form XOR or complemented XOR. Hence there is a
function `f: Q x Q -> F2` such that

```text
(i,a) * (j,b) = (i*j, a + b + f(i,j))
```

with all second coordinates calculated in `F2`.

### Cycle structure above a quotient cycle

First compare two rows whose quotient coordinates agree, say `(i,0)` and
`(i,1)`. Their induced permutation fixes every quotient column and exchanges
the two points in each fiber. It therefore consists only of transpositions
and contributes no odd cycle.

Now compare rows `(i,a)` and `(i',a')` with `i != i'`. Above every cycle of
the quotient row permutation, of length `ell`, the lifted permutation has one
of exactly two forms:

```text
voltage 0: two cycles of length ell;
voltage 1: one cycle of length 2*ell.
```

Consequently, an odd cycle in the ambient row permutation can occur only
above an odd cycle in the quotient.

For the converse, suppose quotient rows `i,i'` induce an odd cycle

```text
C=(j_0,j_1,...,j_(ell-1)),   ell>1 odd,
```

where the quotient row permutation maps `j_t` to `j_(t+1)`. Compare the two
rows `(i,a)` and `(i',a')` in `L`. Above a quotient column `j`, their induced
permutation maps

```text
(j,b) -> (pi(j), b + delta(j)),
```

where

```text
delta(j) = a + a' + f(i,j) + f(i',pi(j)).
```

The voltage around `C` is

```text
V(a,a') = sum_(j in C) delta(j)
        = a + a' + S,
```

because `ell` is odd and `S` is the sum of the two `f` terms around the
cycle. If `V=0`, the lift of `C` consists of two cycles of length `ell`; if
`V=1`, it is one cycle of length `2*ell`. Choosing `a+a'=S` makes `V=0`.
Thus some pair of lifted rows contains an odd cycle whenever the quotient row
view does. The two implications prove equality of the row bits.

Applying the complete cycle argument to the parastrophes proves equality of
the column and symbol components. This proves the theorem.

### Odd quotient corollary

If `Q` has odd order greater than one, C35 gives `pat(Q)=TTT`, so every
two-element-block extension of `Q` is itself `TTT`, independently of the
twisting function `f`.

## Theorem 4: Order `2p` FFF Squares Are Isotopically Simple

Let `p` be an odd prime. If a quasigroup of order `2p` has a nontrivial
congruence, the common block size and quotient order are either

```text
(block size, quotient order) = (p,2) or (2,p).
```

In the first case Theorem 2 applies because `p` is odd. In the second case
Theorem 3 and C35 apply because the quotient has odd order `p`. In either
case the square is `TTT`, and in particular is not FFF.

Therefore every FFF quasigroup of order `2p` is congruence-simple. Since FFF
is isotopy invariant by C03, the same argument applies to every isotope:

```text
Every isotope of an FFF square of order 2p is congruence-simple.
```

For `p=5`, any hypothetical order-10 FFF square must therefore be
isotopically congruence-simple. This is a strict structural reduction of C38,
not a decision of order 10.

## Theorem 5: Prime-Factor Congruence-Series Dichotomy

Suppose a finite quasigroup `L=L_0` admits a quotient chain

```text
L_0 -> L_1 -> ... -> L_t,
```

where `L_t` has order one and every map is induced by a congruence whose
blocks have prime size. Then:

1. if every prime block size is two, `L` is FFF;
2. if at least one prime block size is odd, `L` is TTT.

For a two-element kernel, Theorem 3 preserves the complete pattern. For an
odd prime kernel, Theorem 2 makes the current quotient stage TTT regardless
of the next quotient. Moving upward through the chain, every binary stage
preserves TTT and every further odd stage is TTT directly. This proves the
dichotomy.

Hence C38 holds for the broad class of quasigroups admitting such a
prime-factor congruence series. This is not a proof for congruence-simple
quasigroups.

## Theorem 6: An Explicit Nongroup FFF Loop Of Order 8

On `Z_4 x F_2`, define

```text
(i,a) * (j,b) = (i+j mod 4, a+b+1_((i,j)=(1,1))).
```

The element `(0,0)` is an identity. The first-coordinate blocks form a
two-element-block congruence with quotient `C_4`. Since the Cayley table of
`C_4` is FFF by C05, Theorem 3 makes this loop FFF.

It is not associative, since

```text
((1,0)*(1,0))*(2,0) = (0,1),
(1,0)*((1,0)*(2,0)) = (0,0).
```

At the identity base row, the C14 basis family is the family of left
translations. If it were closed, evaluating a relation `L_x L_y=L_z` at the
identity would force `z=x*y`, so closure would give
`L_x L_y=L_(x*y)` and hence associativity. The displayed failure therefore
gives a closure failure. By C14 the loop is not group-isotopic.

This is a fully theoretical construction of a non-group-isotopic FFF Latin
square of order 8. It does not rely on the order-8 census C10.

## Half-Order Subsquare Quartet

Let `L` have order `2m` and contain an order-`m` subsquare on
`R0 x C0` with symbols `S0`. Let `R1,C1,S1` be the complements. Counting each
symbol once in a row and column forces the four blocks to use symbol sets

```text
R0 x C0 -> S0,    R0 x C1 -> S1,
R1 x C0 -> S1,    R1 x C1 -> S0.
```

Each block is therefore an order-`m` Latin subsquare. Half-order subsquares
occur in complementary quartets. Combined with Theorem 1, an FFF square can
have such a decomposition only when the half-order subsquares are FFF.

## Scope And Open Limitations

- These results do not prove the power-of-two conjecture C38.
- They exclude all congruence-imprimitive order-`2p` candidates, but simple
  quasigroups remain possible.
- The binary quotient equality is special to blocks of size two; larger even
  blocks have non-unique fiber Latin squares and require a different
  argument.
- No timeout or finite sample is used as proof.
