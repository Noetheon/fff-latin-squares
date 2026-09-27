# Affine prime-successor FFF bound: independent internal audit

**Evidence status.** The argument below is a written proof conditional only on the
published mixed-character-sum estimate explicitly cited in Section 3. The finite
controls are secondary. This is an independent rederivation of a statement
supplied in an untracked research archive, **not** a priority claim or an
externally peer-reviewed theorem. It does not decide order 18.

## 1. The exact three-view criterion

Let `p` be an odd prime, `a in F_p \ {0,1}`, and `b=1-a`. On
`Q=F_p union {infinity}` put `infinity` in the identity role, set
`x*x=infinity` for finite `x`, and set `x*y=ax+by` for distinct finite
`x,y`. Every row and column is a permutation: the affine map in a finite
row (or column) fixes its label, and the construction replaces that value by
`infinity` while adding the old label in the new column (or row).

Consider this construction with a generic parameter `t` and `c=1-t`.
The permutation of a finite row relative to the `infinity` row consists of
one 2-cycle and `(p-1)/ord_p(c)` cycles of length `ord_p(c)`.
Translations and nonzero scalar maps of `F_p`, extended to fix `infinity`,
are automorphisms and are 2-transitive on finite labels. Thus for two
distinct finite rows it is enough to compare rows 0 and 1. Write their
relative permutation as `P=r_1^{-1}r_0`, and let `D=-t/c`. Direct substitution
gives

```text
P(infinity)=D,  P(0)=1,  P(c^{-1})=infinity,
P(y)=y+D at every other finite y.
```

The translation by `D` is a single `p`-cycle. Number its finite points
`jD`, `j in Z_p`, and put `k=[-t^{-1}]_p` (`1<=k<=p-2`). Then
`c^{-1}=kD` and `1=(k+1)D`. Redirecting the three displayed arrows splits
the old `p`-cycle into cycles of lengths `p-k` and `k+1`. These are both even
exactly when `[t^{-1}]_p` is even. In the column view the same construction
has parameter `b`. For the symbol view, the line of a finite symbol `z`,
viewed as a map from columns to rows, swaps `z` with `infinity`; at another
finite column `y` it returns `a^{-1}z-(b/a)y`. Its parameter is therefore
`a^{-1}` and its other coefficient is `-b/a`. The `infinity` symbol line is
the identity. Consequently the square is FFF **if and only if**

```text
[a]_p, [a^{-1}]_p, [b^{-1}]_p are even, and
ord_p(a), ord_p(b), ord_p(-b/a) are even.                 (1)
```

This derivation covers every pair in each of the row, column and symbol
views. In particular, the failure of (1) for `p=17` excludes only this
affine family at order 18, not all order-18 Latin squares.

## 2. A sufficient multiplicative mask

Write `U=F_p \ {0,1}`. If `p=3 (mod 4)`, let `chi` be the quadratic
character and require `chi(a)=chi(b)=-1`. Since `chi(-1)=-1`, all three
elements `a,b,-b/a` are nonsquares and have even order. On `U` the mask is
`W(a)=(1-chi(a))(1-chi(b))/4`. Its character expansion has coefficient
`l1` norm 1 and constant coefficient `1/4`.

If `p=1 (mod 4)`, let `chi` have exact order four and require
`chi(a) in {i,-i}` and `chi(b)=-1`. Write `p-1=2^s m` with `s>=2` and `m`
odd, and choose a primitive root `g`; write `a=g^A`, `b=g^B`. The conditions
say `A` is odd and `B=2 (mod 4)`. Thus `a` has even order, `b` has order
divisible by `2^(s-1)`, and the exponent `(p-1)/2+B-A` of `-b/a` is odd,
so `-b/a` also has even order. The mask is

```text
W(a)=(1-chi(a)^2)/2 * (1-chi(b)+chi(b)^2-chi(b)^3)/4.
```

Its eight coefficients have absolute value `1/8`, so its `l1` norm is 1
and its constant coefficient is `1/8`. Both masks are only sufficient;
they need not contain every affine FFF parameter.

## 3. The mixed-sum estimate and endpoints

Let `psi(z)=exp(2*pi*i*z/p)`. For `d=2` or `4`, `0<=j,k<d`, and
`u,v,w in F_p`, define

```text
S(j,k;u,v,w) = sum_{a in U} chi(a)^j chi(1-a)^k
                  psi(u*a+v/a+w/(1-a)).
```

The all-zero tuple has `S=p-2`; every other tuple satisfies
`|S|<=4 sqrt(p)`. Here is an explicit application of [Katz, *Estimates
for Mixed Character Sums*, Theorem 1.5](https://web.math.princeton.edu/~nmk/charsum15.pdf).
When `u != 0`, take its degree-one polynomial phase `f(a)=ua`, rational
remainder `r(a)=v/a+w/(1-a)`, and multiplicative polynomial
`g(a)=a^j(1-a)^k`. Every finite pole is simple; `r` has pole order 0 at
infinity, strictly below the degree 1. At a zero of `g` that is not a pole,
the corresponding nonzero exponent lies strictly below `d`, so the required
power of `chi` is nontrivial. If `t` of the points 0 and 1 are poles and
`e` are zeros of `g` not also poles, Katz bounds the sum over `F_p` by
`(2t+e)sqrt(p)`. Omitting the remaining `2-t-e` endpoints changes the sum
by at most `2-t-e`. Since `t+e<=2` and `p>=3`, the total is at most
`4sqrt(p)`. This makes the endpoint correction explicit.

When `u=0,v!=0`, substitute `z=1/a`; when `u=v=0,w!=0`, substitute
`z=1/(1-a)`. Each maps `U` bijectively to itself, makes the phase a
nonzero linear polynomial plus a rational function with at most one simple
finite pole, and changes the Kummer factor into
`chi(z)^J chi(z-1)^K` up to a constant, with `J,K` reduced modulo `d`.
The same degree-one argument applies. When `u=v=w=0` but `(j,k)!=(0,0)`,
the sum is an ordinary Jacobi sum (or a one-character endpoint sum), with
absolute value at most `sqrt(p)`. No degree-zero invocation of Katz is
needed. The possible poles at 0, 1 and infinity have distinct principal
parts, so there is no hidden cancellation that makes a nonzero phase
constant.

## 4. Fourier parity and counting

Let `E(z)` indicate the nonzero even least residues `2,4,...,p-1`.
With normalized Fourier coefficients, geometric summation gives

```text
Ehat(0)=(p-1)/(2p),
|Ehat(h)|=1/(2p |cos(pi*h/p)|) for h != 0.
```

Pairing `h` with `p-h`, using `sin x >= 2x/pi` on `[0,pi/2]`, and
integrating the decreasing sequence `1/(2r+1)` yields

```text
L_p := sum_h |Ehat(h)| <= 3/2 + (1/2) log p.
```

Let `N_p` count parameters in `U` satisfying the mask and the three
parity conditions in (1). Expanding the mask and the three Fourier series
leaves one all-trivial term. The character coefficient norm is 1, the
constant coefficient is at least `1/8`, and Section 3 bounds every
nontrivial mixed sum. Hence

```text
N_p >= (p-2)(p-1)^3/(64p^3)
       - 4 sqrt(p) (3/2+(1/2)log p)^3.                  (2)
```

The main term is at least `(p-5)/64`, and for `p>=325` this is at least
`p/65`. Put `L(x)=3/2+(1/2)log x`. The logarithmic derivative of
`sqrt(x)/L(x)^3` is `(1/2-3/(2L(x)))/x`, positive when `L(x)>3`.
At `x=10^12`, `log 10<2.303` implies `L(x)<15.318`. The logarithm bound
follows, for example, from the exact rational inequality
`sum_{k=0}^9 (2303/1000)^k/k! > 10`. The exact
rational comparison `260*(15.318)^3 < 935000 < 10^6` holds. Therefore,
for every prime `p>=10^12`, `260 L(p)^3/sqrt(p)<0.935`. The error in (2)
is then less than `(0.935/65)p`, giving `N_p>p/1000`.

**Internally proved conclusion.** Every prime `p>=10^12` has more than
`p/1000` affine parameters producing an FFF Latin loop of order `p+1`.
This is a parameter count, not a count of isomorphism or main classes;
it covers prime-successor orders only. It is mathematically far beyond a
finite scan, but the source theorem was supplied in an archive, and no
independent literature-priority or expert review has been completed.

## 5. Algebraic consequences for these loops

For `p>3`, each loop `Q_p(a)` is nonassociative. Indeed, associativity at
`(0,0,1)` would give `1=(0*0)*1=0*(0*1)=b^2`, so `b=-1` because `b!=1`.
Associativity at `(1,0,0)` similarly gives `a^2=1`, hence `a=-1`.
Then `a+b=1` would force `p=3`. In a loop with identity, closure of its
left-translation family implies associativity: if `L_x L_y=L_z`, evaluating
at the identity gives `z=x*y`. Thus the group-isotopy closure criterion
C14 shows that all these loops with `p>3` are non-group-isotopic.

They are also simple as loops. Let `H` be a subloop and let
`S=H\{infinity}`. For each `x in S`, the affine bijection
`h_x(y)=ax+by` maps `S` to itself (including `h_x(x)=x`), hence permutes
it. If `x,z in S` are distinct, `h_z^{-1}h_x` is a nonzero translation
of the prime field, so it acts transitively and `S=F_p`. Thus every proper
nontrivial subloop has size 2. If a proper nontrivial loop congruence
existed, its identity class would be such a two-element subloop
`{infinity,x}`. Since `x` represents the quotient identity, left and
right multiplication by `x` preserve each congruence class; all their
cycles would have length at most 2. Their cycles outside the swapped
`{infinity,x}` pair have lengths `ord_p(b)` and `ord_p(a)` respectively.
Hence both orders would be at most 2, forcing `a=b=-1` and `p=3`, a
contradiction. The argument uses the usual loop congruence compatible
with multiplication and both divisions.

At most one parameter, `a=b=1/2`, is commutative. Since Section 4 gives
more than `p/1000` successful parameters when `p>=10^12`, it gives
noncommutative, simple, non-group-isotopic FFF loops at every such order.
This strengthens the nature of the produced examples, not the set of
orders covered.

## 6. Quantitatively many distinct main classes

The parameter count above does not *by itself* count classes. The following
separate argument turns almost all of those parameters into distinct
isotopy classes and then a main-class lower bound.

For `p>=5`, the row-view type of each pair involving the `infinity` row
is `X_R=(2,ord_p(b)^((p-1)/ord_p(b)))`. Every pair of finite rows has
type `Y_R=([a^{-1}]_p,p+1-[a^{-1}]_p)`. These types can coincide only if
`ord_p(b)=p-1` and `[a^{-1}]_p` is `2` or `p-1`; in particular their
coincidence forces `a` to be `(p+1)/2` or `p-1`. The column-view types
are `X_C=(2,ord_p(a)^((p-1)/ord_p(a)))` and
`Y_C=([b^{-1}]_p,p+1-[b^{-1}]_p)`. Their coincidence forces `a` to be
`(p+1)/2` or `2`. Consequently, for every successful parameter outside

```text
                  {2, (p+1)/2, p-1},                        (3)
```

the `infinity` row is the unique row incident to `p` same-type row-pair
edges, and the `infinity` column is similarly unique. Every finite row
or column has one special edge and `p-1` finite-finite edges of a different
type. An isotopy preserves the cycle type of every two-line permutation
in each view, up to relabeling the lines. Therefore an isotopy between
two squares with parameters outside (3) must send their `infinity` rows
to one another and their `infinity` columns to one another.

Let `(alpha,beta,gamma)` be such an isotopy from `Q_p(a)` to `Q_p(a')`.
The loop identities give `alpha(infinity)=beta(infinity)=infinity` and
then, by evaluating the isotopy equation on the identity row and column,
`gamma=beta=alpha`. It is an isomorphism fixing `infinity` and restricts
to a bijection `f:F_p -> F_p`. The finite multiplication equation is

```text
f(ax+by)=a'f(x)+(1-a')f(y)  for all x,y in F_p.          (4)
```

It holds also at `x=y`, since both affine operations are idempotent.
Put `h(x)=f(x)-f(0)`. Setting one argument of (4) to zero gives
`h(ax)=a'h(x)` and `h(by)=(1-a')h(y)`. Inverting the nonzero scalars
`a,b,a',1-a'` in these two identities and substituting arbitrary
`u=ax,v=by` into (4) yields `h(u+v)=h(u)+h(v)`. Every additive bijection
of the prime field is multiplication by a nonzero scalar; the first
identity then forces `a=a'`. Thus distinct successful parameters outside
(3) give **pairwise nonisotopic** Latin squares.

Write `N_p` for the Section 4 sufficient-mask count and `M_p` for the
number of FFF main classes at order `p+1`. At most three of the counted
parameters lie in (3). A main class, formed by isotopy and coordinate
permutation, contains at most six isotopy classes, one per parastrophe.
Therefore the rigorous quantitative consequence is

```text
M_p >= ceil((N_p-3)/6) > p/6000 - 1/2     (p>=10^12 prime). (5)
```

The strict real inequality is understood alongside the integer lower
bound. This is a lower bound on genuine main classes, not a claim of
exact classification or of six-to-one parameter orbits. The argument is
new relative to the supplied large-prime statement, which explicitly did
not count isomorphism or main classes. It is still **not** a literature
priority claim or a substitute for independent expert review.

## 7. Exact main-class classification within the affine family

The conservative bound in Section 6 can be sharpened to a classification of
*which members of this family* share a main class. This does **not** classify
all Latin squares of order `p+1`.

Let `p>=5` and write `b=1-a`. Interchanging the input coordinates turns
`Q_p(a)` into `Q_p(b)`. Solving `x*y=z` for `x`, respectively `y`, turns the
relation into the operations with parameters `a^{-1}`, respectively
`-a/b=a/(a-1)`. These identities include the cases involving `infinity`:
the relation contains `(infinity,x,x)`, `(x,infinity,x)` and
`(x,x,infinity)` for every finite `x`, so every coordinate permutation
again has identity `infinity` and finite diagonal value `infinity`.
The six parastrophe parameters are therefore

```text
A(a) = {a, 1-a, 1/a, 1/(1-a), a/(a-1), (a-1)/a}.          (6)
```

Every parameter in `A(a)` is visibly main-class equivalent to `a`.
Conversely, let a paratopy identify `Q_p(a)` with `Q_p(a')`. First perform
its coordinate permutation, leaving an isotopy between `Q_p(t)` and
`Q_p(a')` for some `t in A(a)`. Put
`E={2, 1/2, -1}` in `F_p`. Formula (6) preserves `E`, and its three
members form a single orbit. Outside `E`, the row and column identity
lines are both intrinsic by Section 6. If `t,a' notin E`, the remaining
isotopy fixes both identity lines and the argument of (4) forces `t=a'`.
If exactly one of `t,a'` is in `E`, either that member has an equal
special-versus-finite pair type in the row or column view, which an
isotopy cannot map to the unequal types of the other member, or both
identity lines remain intrinsic and (4) again forces equality, a
contradiction. If both lie in `E`, they are already related by (6).
Thus, for **all** `a,a' in F_p\{0,1}`,

```text
Q_p(a) and Q_p(a') are main-class equivalent
       if and only if a' belongs to A(a).                  (7)
```

The same calculation gives an isomorphism-level corollary without any
exceptional-parameter restriction. Every loop isomorphism fixes its
identity, so (4) applies immediately. It forces `a=a'` and
`f(x)=u*x+v` on `F_p` with `u!=0`; conversely every such affine map,
extended by `f(infinity)=infinity`, preserves `Q_p(a)` because `a+b=1`.
Thus the `p-2` parameters are pairwise nonisomorphic, and each loop has
automorphism group `AGL(1,p)` of order `p(p-1)`. This statement concerns
isomorphism, not the coarser main-class relation (7).

The orbits in (6) have size six, except for `E` (size three) and the
roots of `a^2-a+1=0` (one orbit of size two when they exist). This follows
because the three nonidentity involutions among the six fractional-linear
maps fix only `1/2`, `2`, and `-1`, respectively, while either nonidentity
order-three map fixes precisely the roots of `a^2-a+1`. For `p>=5` these
fixed-point sets are disjoint and there is no orbit of size one. Let `S_p`
be the **full** set of parameters passing
the exact FFF criterion (1), not merely the sufficient mask. Since FFF
is invariant under parastrophy, `S_p` is a union of these orbits. Set
`e_p=1` if `E` passes (1), otherwise zero, and `h_p=1` if the two
roots of `a^2-a+1` pass (1), otherwise zero. The number of FFF main
classes **represented by this affine family** is exactly

```text
             C_p^aff = (|S_p| + 3e_p + 4h_p)/6.             (8)
```

In particular `C_p^aff >= |S_p|/6 >= N_p/6 > p/6000` for every prime
`p>=10^12`. This improves Section 6's lower bound on the global number
of FFF main classes, but says nothing about how many additional classes
other constructions contribute. Equations (7) and (8) were derived
here beyond the archive-supplied parameter theorem. They are internal
mathematical results, not established claims of priority in the
literature or substitutes for expert review.

## 8. Finite controls and remaining scope

The companion [run](../repro_runs/2026-09-23_fff_affine_prime_successor_audit/README.md)
directly constructs all 253 affine tables for odd primes through 43,
compares (1) with a three-view cycle scanner, checks the sufficient masks,
checks the special-versus-finite pair cycle types for every small FFF
parameter, verifies both generating parastrophies directly, enumerates
the anharmonic orbits and checks (8), and numerically checks the Fourier
identities. These finite
controls also include two compact formula certificates at
`p=1000000000039`: `a=86` and `a=96` both satisfy (1), lie in distinct
six-element orbits (6), and neither lies in (3). The script checks
primality by every odd trial divisor through
`floor(sqrt(p))=1000000`, records the inverse residues and three
odd-part modular powers, and thus certifies two distinct main classes of
FFF loops of order `1000000000040` *by the proved criterion*. It does
not materialize or directly scan either enormous table. These checks do not
prove Katz's estimate or the uniform threshold. The first open order 18
remains open: the `p=17` case only rules out the scalar affine prolongation.
