# Affine-orbit classification of quotient-free row-fibred extensions

**Evidence boundary.** The classification below is a direct theorem about
main classes of a specified family of Latin squares. The numerical FFF
bounds use C157's computer-assisted order-10 exclusion and C246's exact
514-class FFF20 source lower bound. This is not a classification of all
Latin squares or FFF squares at the output order, an order-18 decision,
or an established literature-priority or externally reviewed result.

## Intrinsic quotient layers and their block colors

Choose order-`n` Latin squares `Q_1,...,Q_m` from pairwise distinct
*main classes*, each without a binary three-sorted quotient. Let
`E=(F2)^d`, `d>=1`, with `N=|E|`. For every function
`f:E->{1,...,m}`, define

```text
M_f((r,y),(c,z))=(Q_(f(y))(r,c), y+z).                 (1)
```

C249 proves that every binary quotient of `M_f` is pulled back from
`E`. The `N-1` nonzero characters of `E` separate points, so the
common refinement of their three-sorted quotient partitions recovers
the row, column and symbol layers `X x {y}` intrinsically.

Each outer cell `(y,z,t=y+z)` determines an order-`n` Latin block
whose main class is `[Q_(f(y))]`. We call this the *block-coloring* of
the outer Latin net. It is preserved by isotopy and by all six
parastrophes, up to the induced permutation of the three sorts; the
colors are main classes, not labels of inner symbols.

## Which colorings can be equivalent?

**Lemma 1 (outer affine action).** Every isotopism or parastrophism of
the Latin group table of `E` acts on each of its three sorts by an
affine permutation with a common invertible linear part. In
particular, its action on any specified sort lies in `AGL(d,2)`.

**Proof.** Since `y+z=t` is symmetric under permuting the three
coordinates in characteristic two, first undo any parastrophe. An
isotopism is then a triple of bijections `alpha,beta,gamma` satisfying
`gamma(y+z)=alpha(y)+beta(z)`. Put `u=alpha(0)`, `v=beta(0)` and
`A(w)=gamma(w)+u+v`. Evaluating at `(y,0)` and `(0,z)` gives
`alpha(y)=A(y)+u` and `beta(z)=A(z)+v`. The original identity becomes
`A(y+z)=A(y)+A(z)`. Bijectivity makes `A` an invertible linear map.
QED.

**Lemma 2 (the varying sort is intrinsic).** Suppose `f` is
nonconstant and `M_f` is main-class-equivalent to some `M_g` of the
form (1). Then `g` is nonconstant, and the induced outer net
parastrophy must map the source **row** sort to the target **row** sort.

**Proof.** Main-class equivalence transports all binary quotient
partitions, hence their common-refinement layers and the colored
outer net. On the source net the block color at `(y,z,y+z)` is the
nonconstant function `[Q_(f(y))]` of the row coordinate alone. If
the source row sort were transported to the target column sort, then
for a fixed target row the source row coordinate would range over
all `E` as the target column varies. If it were transported to the
target symbol sort, the same is true because the symbol coordinate
is target row plus target column, followed by a bijection. In either
case its nonconstant block color would vary along a fixed target
row, while the target color `[Q_(g(y'))]` is constant there. This is
impossible. If `g` were constant, the target colored net would have
one color and could not match a nonconstant source. QED.

**Theorem 3 (exact orbit classification within the family).** For any
two functions `f,g:E->{1,...,m}`, the constructed squares `M_f` and
`M_g` are main-class-equivalent **if and only if** `f` and `g` lie in
the same orbit of `AGL(d,2)` acting on the argument `E`.

**Proof.** If `f` is nonconstant and the squares are equivalent,
Lemma 2 makes the induced outer row map an affine permutation
`alpha(y)=A(y)+u` by Lemma 1. Equality of the transported block
main-class colors gives `g(alpha(y))=f(y)` for every `y`, because the
chosen input main classes are distinct. If `f` is constant, the
intrinsic colored net is constant, so `g` is the same constant
function and the same orbit condition holds.

Conversely, if `g(Ay+u)=f(y)` for an invertible linear `A` and
`u in E`, choose any `v in E`. The three coordinate bijections

```text
(r,y) -> (r,Ay+u),
(c,z) -> (c,Az+v),
(s,t) -> (s,At+u+v)
```

give an explicit isotopism from `M_f` to `M_g`. Thus equality of
affine orbits is sufficient as well. QED.

The classification concerns these **chosen, fixed input
representatives**. It does not claim all representatives from an
input main class yield equivalent extensions, nor that every output
FFF main class has this form.

## Burnside count and FFF consequence

Let `c(h)` be the number of cycles of `h` on the `N` points of `E`.
Burnside's lemma applied to the functions `E->{1,...,m}` gives the
exact number of main classes **represented by this constructed
family**:

```text
T_d(m) = (1 / |AGL(d,2)|) * sum_(h in AGL(d,2)) m^(c(h)),
|AGL(d,2)| = 2^d * product_(i=0 to d-1) (2^d-2^i).     (2)
```

In particular, `T_d(m) >= m^(2^d)/|AGL(d,2)|`; the multiset bound of
C249 is weaker or equal because affine orbits refine ordinary
multisets. If the inputs are FFF, C247 and C05 make every output FFF.

At `n=20`, C41 and C157 make each FFF20 input binary-quotient-free,
and C246 supplies `m=514` chosen, pairwise distinct FFF20 classes.
Consequently `M_(20*2^d) >= T_d(514)` for every `d>=1`. In dimensions
one and two `AGL(d,2)` is the full symmetric group on `E`, so the
bound equals C249's multiset count. For `d>=3` it is strictly
stronger. Exact finite Burnside counts yield **3625556867870760586**
represented classes at order 160 (`d=3`) and
**73586711420426563009097417622853741216** at order 320 (`d=4`),
versus C249's respective multiset bounds of
127564036708401865 and 1429479460926722276944455652465.
Selected physical controls are in the
[dated run](../repro_runs/2026-09-26_fff_affine_orbit_fibres/README.md).
Two selected order-160 outputs use the same four-plus-four input
multiset and even have the same sorted aggregate three-view cycle
spectrum, but their four-point color sets are respectively an affine
plane and an affine tetrahedron. Those lie in disjoint `AGL(3,2)`
orbits, so Theorem 3 separates their main classes where C246's
cycle-spectrum invariant does not.

## Scope

Equation (2) counts main classes **within the fixed construction**;
it is still only a lower bound for all FFF main classes at that order.
No global direct-product cancellation, FFF18 existence result,
complete census, literature novelty or independent expert review is
claimed.
