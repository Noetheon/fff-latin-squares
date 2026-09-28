# Binary-quotient rigidity for row-fibred FFF extensions

**Evidence boundary.** The quotient-rigidity and main-class injection below
are direct theorems about finite Latin squares. The numerical order-40
corollary also uses C157's computer-assisted order-10 exclusion and
C246's exact 514-class lower bound at order 20. It is **not** a census,
an order-18 existence result, a claim about all higher `40*2^k` orders,
an established literature-priority result, or an externally reviewed proof.

## Three-sorted binary quotients

For a Latin square `Q:R x C -> S`, a *binary net quotient* is a triple of
surjections `a:R->F2`, `b:C->F2`, `d:S->F2` such that

```text
d(Q(r,c)) = a(r) + b(c)  (mod 2)                         (1)
```

for every cell. Any quotient onto an order-two Latin square can be
relabelled to (1). Two such triples give the same *quotient partitions*
when their row, column and symbol fibers coincide; changing bit labels
does not change the partitions. The notion is preserved by independent
row/column/symbol relabelings and by permuting the three roles. Indeed,
`a(r)+b(c)+d(s)=0` is symmetric in the three bit coordinates.

**Lemma 1 (constant or onto).** Suppose three maps to `F2`, not assumed
surjective, satisfy (1) on a Latin square. Then they are either all
constant or all surjective.

**Proof.** Fix a column `c`. As `r` varies, `Q(r,c)` runs through all
symbols, so `a(R)` and `d(S)` are the same set up to addition of the
constant `b(c)`. Fixing a row similarly identifies `b(C)` and `d(S)`
up to a translate. Thus all three images have the same cardinality,
which is either one or two. QED.

**Lemma 2 (half-order blocks).** If an order-`n` Latin square has a
binary net quotient, then `n` is even, each of the six color classes
has size `n/2`, and each of the four row-color/column-color rectangles
is a Latin subsquare of order `n/2` with the prescribed symbol color.

**Proof.** For a row of color `i`, its bijection from columns to symbols
maps the column class of color `j` onto the symbol class of color
`i+j`. Both row colors occur, so the two symbol classes have equal
sizes and each has size `n/2`; both column classes have the same size.
Repeating the argument with a fixed column shows both row classes
have size `n/2`. Every row and column of a block contains each symbol
of its designated symbol class exactly once. QED.

In particular, if `Q` is FFF and no FFF square of order `n/2` exists,
then `Q` has **no** binary net quotient: Lemma 2 and C41 would
otherwise give an FFF order-`n/2` subsquare. This implication depends
on the cited nonexistence result when that result is computational.

## Unique quotient of a binary row-fibred extension

Let `Q_0,Q_1` be Latin squares on the same set `X`, each **without** a
binary net quotient. Write the binary row-fibred extension of C247 as

```text
M((r,y),(c,z)) = (Q_y(r,c), y+z),  y,z in F2.            (2)
```

It has the evident binary net quotient given by the three outer
coordinates. We claim its three quotient partitions are unique.

**Theorem 3 (rigidity).** Every binary net quotient of `M` has row,
column and symbol partitions equal to the outer-coordinate partitions
in (2). The bit labels may differ, but the three partitions do not.

**Proof.** Let `a,b,d` be a quotient triple for `M`. Restrict (1) to
the block of rows `X x {y}`, columns `X x {z}`, and symbols
`X x {y+z}`. With

```text
a_y(r)=a(r,y), b_z(c)=b(c,z), d_(y+z)(s)=d(s,y+z),
```

the restriction reads

```text
d_(y+z)(Q_y(r,c)) = a_y(r)+b_z(c).                     (3)
```

By Lemma 1 these three restricted maps are either all constant or all
surjective. The latter would be a binary net quotient of `Q_y`, which
is excluded. Hence, for every `y,z`, all three restricted maps are
constant. Thus `a(r,y)=A_y`, `b(c,z)=B_z`, and `d(s,t)=D_t` depend only
on the outer coordinates. Since the original three maps are onto,
`A_0 != A_1`, `B_0 != B_1`, and `D_0 != D_1`. Their partition fibers
are therefore exactly `X x {0}` and `X x {1}` on each axis. QED.

The theorem concerns **unique partitions**, not a unique bit-labelled
quotient map or all congruences of the square.

## Main-class injection

**Theorem 4.** Let `Q_1,...,Q_m` be chosen representatives of `m`
distinct main classes of order-`n` Latin squares, none with a binary
net quotient. For each unordered index pair `{i,j}`, including `i=j`,
form `F(Q_i,Q_j)` by (2). Then the resulting `m(m+1)/2` order-`2n`
tables belong to pairwise distinct main classes. If all `Q_i` are FFF,
so are all resulting tables.

**Proof.** C247 gives Latinness and FFF preservation. By Theorem 3,
the binary quotient partitions of each extension are intrinsic. Its
four quotient-block subtables (two row blocks times two column blocks)
have main classes, as a multiset,

```text
{[Q_i], [Q_i], [Q_j], [Q_j]}.                         (4)
```

An isotopy transports a binary quotient to a binary quotient; a
parastrophe permutes the three quotient axes. By uniqueness, every
main-class equivalence must transport the intrinsic quotient
partitions. It therefore permutes the four block subtables and may
parastrophize them, but preserves the multiset of their **main**
classes. Since the chosen `[Q_i]` are distinct, equality of the
multisets (4) forces equality of the unordered index pairs. QED.

This is an injection for the **chosen representatives**. It does not
assert that arbitrary representatives of one input main class always
give equivalent extensions.

**Corollary 5.** If no FFF Latin square of order `n/2` exists, then for
the number `M_n` of FFF main classes at order `n` (with even `n`),

```text
M_(2n) >= binom(M_n+1,2).                              (5)
```

This is an inequality, not a recurrence that can automatically be
iterated: the new order-`2n` extensions possess a binary quotient and
need not satisfy Theorem 4's input hypothesis at the next step.

At `n=20`, C157 excludes FFF order 10 and C41 forbids FFF10
subsquares. Hence **every** FFF20 square has no binary net quotient.
C246 supplies 514 pairwise main-class-distinct FFF20 squares via
independently checked three-view cycle spectra. Taking those as the
chosen representatives in Theorem 4 yields

```text
M_40 >= binom(515,2) = 132355.                        (6)
```

The [dated controls](../repro_runs/2026-09-26_fff_binary_quotient_rigidity/README.md)
freshly check the 514 source spectra, enumerate all binary quotient
partitions in small positive/negative controls, and independently scan
selected order-40 extensions. The number (6) is proved from the
injection and the 514 verified inputs; it is **not** a physical scan
of all 132355 output tables.

## Limitations and priority

C247's earlier 1025-class lower bound at order 40 is sharpened by (6),
but its separate bound at all orders `40*2^k` is **not** automatically
sharpened. In particular, no cancellation or main-class injectivity
of subsequent `C2` direct products is proved here. No order-18
existence/nonexistence inference is possible. A targeted literature
screen has not established novelty of the quotient-rigidity argument
or the lower bound; independent expert review remains necessary.
