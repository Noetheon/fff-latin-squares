# Binary-quotient descent and dyadic FFF main-class growth

**Evidence boundary.** The quotient-descent and multiset-injection theorems
below are direct proofs for all finite Latin squares satisfying their stated
hypotheses. The numerical bounds use the computer-assisted C157 order-10
exclusion and C246's 514 exactly distinguished FFF20 main classes. They are
lower bounds, not complete censuses or individual scans of every constructed
table. No FFF order-18 existence decision or literature-priority claim is
made. This extends [C248](fff_binary_quotient_rigidity.md) without changing
its frozen run.

## Binary quotient descent

Write a binary three-sorted quotient of a Latin square `Q:R x C -> S` as
surjections `a:R->F2`, `b:C->F2`, `d:S->F2` satisfying

```text
d(Q(r,c)) = a(r)+b(c)  (mod 2).                           (1)
```

The constant-or-onto lemma in C248 says any triple satisfying (1) is
either constant on all three axes or onto on all three axes. The
definition and the assertion are invariant under isotopy and all six
parastrophes, since `a(r)+b(c)+d(s)=0` is symmetric in the three roles.

Let `B:Y_R x Y_C -> Y_S` be any Latin square, and let `Q_y` be a Latin
square on `X` for each row index `y in Y_R`. Its row-fibred extension
from C247 is

```text
M((r,y),(c,z)) = (Q_y(r,c), B(y,z)).                      (2)
```

**Theorem 1 (descent).** If none of the `Q_y` has a binary three-sorted
quotient, then *every* binary quotient triple of `M` is the pullback of
a unique binary quotient triple of `B`. Conversely, every binary
quotient triple of `B` pulls back to one of `M`.

**Proof.** Let `(a,b,d)` satisfy (1) for `M`. For fixed `y,z`, restrict
its three maps to the row layer `X x {y}`, column layer `X x {z}` and
symbol layer `X x {B(y,z)}`. These restricted maps satisfy (1) for
`Q_y`. By the constant-or-onto lemma and the hypothesis, all three
are constant. As `y,z` range over the quotient Latin square, this
shows that `a(r,y)=A(y)`, `b(c,z)=D(z)` and `d(s,t)=E(t)` depend only
on outer coordinates. Surjectivity of the original triple makes
`A,D,E` surjective. Equation (1) for `M` reduces to
`E(B(y,z))=A(y)+D(z)`, so `(A,D,E)` is a binary quotient of `B`.
Its values are uniquely determined by `(a,b,d)`. Pulling back a
quotient of `B` plainly satisfies (1) for `M` and is onto. QED.

The theorem is about *all* binary quotient triples, not only an
existence test. Bit-label complementation can yield distinct triples
with the same underlying partition. The common refinement of their
row, column and symbol partitions is therefore an intrinsic invariant
of `M` under isotopy and parastrophy.

## Elementary abelian outer quotient

Take `B=E=(F2)^d` with `d>=1` and addition as its Latin operation.

**Lemma 2.** The binary quotient partitions of `E` are precisely the
nonzero linear characters `lambda:E->F2`, up to bit-label changes.
There are `2^d-1` distinct partition triples, and the common
refinement of all row (respectively column, symbol) partitions is the
singleton partition of `E`.

**Proof.** If `D(y+z)=A(y)+C(z)`, subtracting the values at zero
shows that `lambda(t)=D(t)+D(0)` satisfies
`lambda(y+z)=lambda(y)+lambda(z)`. The other two maps are the same
linear character plus constants. Surjectivity is equivalent to
`lambda != 0`. Conversely any nonzero character, with compatible
constants, gives a quotient. Distinct nonzero characters have
distinct kernels over `F2`, and characters separate any two distinct
vectors, proving the common-refinement assertion. QED.

By Theorem 1, when all fibres of (2) lack a binary quotient, the common
refinement of **all** binary quotient partitions of `M` recovers the
individual outer layers `X x {y}` on every axis. These partitions are
intrinsic; no labels for `y` are presumed intrinsic.

## Multiset injection

**Theorem 3.** Let `Q_1,...,Q_m` be chosen representatives of distinct
main classes of order-`n` Latin squares, each without a binary
three-sorted quotient. Put `N=2^d`, `d>=1`. For every multiset of
`N` indices drawn from `{1,...,m}`, choose one assignment of its
elements to the `N` row layers of `E=(F2)^d`, and form (2). These

```text
binom(m+N-1,N)
```

extensions belong to pairwise distinct main classes of order `nN`.
If all `Q_i` are FFF, all extensions are FFF.

**Proof.** C247 proves Latinness and the exact componentwise OR
pattern formula. `E` is FFF by C05, so FFF fibres give FFF output.

Theorem 1 and Lemma 2 recover the outer layers as the common refinement
of every binary quotient partition in each of the three sorts. For
each pair of outer row and column layers `(y,z)`, the corresponding
order-`n` block subtable is `Q_y`, with output in the layer `y+z`.
Thus the intrinsic multiset of the `N^2` block *main classes* consists
of `N` copies of `[Q_y]` for each outer row layer `y`. An isotopy
transports all quotient partitions and the resulting blocks. A
parastrophe permutes the three sorts, but still sends each block to
a parastrophe of a block and preserves its main class. Therefore
main-class-equivalent extensions have equal block-main-class
multisets. Since the chosen `[Q_i]` are distinct, equality forces
the same multiplicity of every input class among the `N` fibres.
Different input multisets cannot become main-class-equivalent. QED.

The theorem does **not** assert that different assignments of the same
input multiset yield equivalent extensions, nor that arbitrary choices
of representatives from equivalent input classes are interchangeable.

**Corollary 4 (FFF bounds).** If no FFF square of order `n/2` exists,
then C41 and C248's half-order-block lemma imply that every FFF
square of order `n` is binary-quotient-free. Writing `M_n` for the
number of FFF main classes at order `n`, for each `d>=1` we obtain

```text
M_(n*2^d) >= binom(M_n+2^d-1,2^d),                     (3)
```

with the understanding that a finite known lower bound for `M_n` may
replace its unknown exact value. At `n=20`, C157 excludes FFF10 and
C246 supplies at least 514 FFF20 classes. Hence

```text
M_(20*2^d) >= binom(513+2^d,2^d),  d>=1.             (4)
```

The first values are **132355 at order 40**, **2942384005 at order
80**, and **127564036708401865 at order 160**. These are A+B bounds:
the injection is proved, but its numerical input depends on exact
finite evidence for C157 and C246. The [dated companion run](../repro_runs/2026-09-26_fff_binary_quotient_descent/README.md)
checks quotient-character counts and selected physical extensions.
It does not enumerate the huge output-class families.

## Limitations

The result is an injection from **multisets of chosen quotient-free
input representatives**, not a general cancellation theorem for direct
products, a census, or an unconditional inequality iterated at each
doubling. The 514-class input lower bound is not claimed to be exact.
The order-18 existence question is unaffected. No literature-priority
or independent-human-review conclusion has been established.
