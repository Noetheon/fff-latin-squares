# Position-value coloring channel for three-view FFF

**Status.** The equivalence below is a general rigorous encoding lemma.
It does not decide whether an FFF Latin square of order 18 exists.
The [dated run](../repro_runs/2026-09-26_fff18_value_color_channel/README.md)
tests the implementation on frozen positive and negative controls and
one bounded C243 row-1 case.

## Two bijective lines

In any of the three views, each line `a` is a bijection
`f_a:P -> Q` from `n` positions to `n` values. For `a != b`, the
induced two-line permutation on positions is

```text
pi = f_b^(-1) o f_a.
```

It has no fixed point because two different lines of a Latin square
cannot have the same value at the same position. Introduce one color
`e_i in {0,1}` for every `i in P` and one color `h_v in {0,1}` for
every `v in Q`. Impose

```text
e_i = h_{f_a(i)},          e_i = 1 - h_{f_b(i)}     for all i in P.   (1)
```

These equations hold if and only if `pi` has only even cycles. Indeed,
for `j=pi(i)` we have `f_a(i)=f_b(j)`, so (1) implies
`e_j=1-e_i`. Conversely, if colors `e` toggle along `pi`, set
`h_v=e_{f_a^(-1)(v)}`. The first half of (1) is immediate. For the
second, `f_a^(-1)(f_b(i))=pi^(-1)(i)` and toggling along an edge also
gives `e_i=1-e_{pi^(-1)(i)}`. Existence of a toggling coloring is
equivalent to all cycles being even by C39. Simultaneously
complementing `e` and `h` preserves (1), so `e_0=0` is a harmless
gauge.

**Balance is automatic.** Because both lines are bijections, the first
equation gives `sum_i e_i=sum_v h_v`, while the second gives
`sum_i e_i=n-sum_v h_v`. Hence both sums equal `n/2`. There is no need
for an explicit exact-cardinality encoding. In odd order these
equations are impossible, in agreement with C35.

## All three views and CNF clauses

Use the ordinary Latin cell variable `X[r,c,s]` to mean `L(r,c)=s`.
For pair `a<b`, position `i`, and value `v`, let `A` and `B` be the
antecedents asserting `f_a(i)=v` and `f_b(i)=v`:

| View | `P` | `Q` | `A` | `B` |
| --- | --- | --- | --- | --- |
| row | columns | symbols | `X[a,i,v]` | `X[b,i,v]` |
| col | rows | symbols | `X[i,a,v]` | `X[i,b,v]` |
| sym | columns | rows | `X[v,i,a]` | `X[v,i,b]` |

For `e=e_i`, `h=h_v`, the four CNF clauses are

```text
not A or not e or h,      not A or e or not h,
not B or e or h,          not B or not e or not h.
```

The first two implement `A -> (e=h)` and the last two implement
`B -> (e!=h)`. Latin exactly-one constraints make each line a
bijection and activate exactly the intended value for every
position. Applying the two-line proof independently to every pair
in row, column and symbol views therefore gives a CNF satisfiable
**if and only if** the fixed reduced context contains an FFF square.
The converse extends each FFF square by the independently chosen
colors of each line pair. Reduction of an unrestricted square for
existence is justified by C03. A fixed nonreduced input may be
isotoped to reduced form by relabelling its first-row symbols and
then permuting rows according to their first-column symbols;
this preserves all three witness bits.

For even `n`, the channel needs `2n` color variables, `4n^2`
conditional ternary clauses and one gauge unit per line pair in a
view. It uses no physical-arc variables or explicit balance
auxiliaries. This is a representation improvement, not a claim of
faster solving: SAT performance and the order-18 existence question
require separate computation or proof.
