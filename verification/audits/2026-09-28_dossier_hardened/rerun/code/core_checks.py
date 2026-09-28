"""Independent checks derived directly from the 2026-09-27 manuscripts.
No project-specific search routines or stored result JSON is imported.
Standard library only. Outputs preserve actual calculations, not pass-only flags.
"""
from itertools import combinations, product, permutations
from collections import Counter
from pathlib import Path
from fractions import Fraction
import json, math, time, sys
if sys.flags.optimize:
    raise RuntimeError('Audit checks require assertions: optimized Python is not supported.')
ROOT=Path(__file__).resolve().parents[1]

def cycles(p):
    n=len(p); seen=[False]*n; ans=[]
    for x in range(n):
        if not seen[x]:
            C=[]; y=x
            while not seen[y]:
                seen[y]=True; C.append(y); y=p[y]
            assert y==x, 'Not a permutation'
            ans.append(C)
    return ans

def inverse(p):
    q=[0]*len(p)
    for i,x in enumerate(p): q[x]=i
    return q

def scan(L):
    n=len(L); full=set(range(n))
    assert all(len(r)==n and set(r)==full for r in L)
    cols=[list(c) for c in zip(*L)]
    assert all(set(c)==full for c in cols)
    sym=[[] for _ in range(n)]
    for c in cols:
        for s,r in enumerate(inverse(c)): sym[s].append(r)
    profiles=[]
    for family in (L,cols,sym):
        invs=[inverse(p) for p in family]; C=Counter()
        for a,b in combinations(range(n),2):
            p=[invs[b][x] for x in family[a]]
            typ=tuple(sorted(map(len,cycles(p))))
            assert 1 not in typ
            C[typ]+=1
        profiles.append(C)
    pat=''.join('T' if any(any(t%2 for t in typ) for typ in C) else 'F' for C in profiles)
    combined=sum(profiles,Counter())
    I=sum(typ.count(2)*num for typ,num in profiles[0].items())
    assert all(sum(typ.count(2)*num for typ,num in C.items())==I for C in profiles)
    return {'n':n,'pattern':pat,'pairs':3*n*(n-1)//2,'intercalates':I,
            'profiles':[{','.join(map(str,k)):v for k,v in sorted(C.items())} for C in profiles],
            'spectrum':tuple(sorted(combined.items()))}

def scan_alternating_graph(L):
    """Second physical implementation: connected components of two factor matchings.
    Constructs all three bipartite link views directly from cell triples.
    Each component has 2*cycle_length vertices and must have size divisible by four.
    """
    n=len(L); out=[]
    for v in range(3):
        fam=[[] for _ in range(n)]
        for r in range(n):
            for c in range(n):
                xyz=(r,c,L[r][c]); other=[xyz[k] for k in range(3) if k!=v]
                fam[xyz[v]].append((other[0],n+other[1]))
        bad=False
        for a,b in combinations(range(n),2):
            adj=[[] for _ in range(2*n)]
            for u,w in fam[a]+fam[b]: adj[u].append(w);adj[w].append(u)
            assert all(len(x)==2 for x in adj)
            vis=set()
            for start in range(2*n):
                if start in vis: continue
                stack=[start];sz=0;vis.add(start)
                while stack:
                    x=stack.pop();sz+=1
                    for y in adj[x]:
                        if y not in vis: vis.add(y);stack.append(y)
                bad|=sz%4!=0
        out.append('T' if bad else 'F')
    return ''.join(out)

def affine(p,a):
    assert 1<a<p
    return [[y if x==p else x if y==p else p if x==y else (a*x+(1-a)*y)%p for y in range(p+1)] for x in range(p+1)]

def primes(n):
    return [p for p in range(3,n+1,2) if all(p%d for d in range(2,math.isqrt(p)+1))]

def order(a,p):
    x=a%p;k=1
    while x!=1: x=x*a%p;k+=1
    return k

def criterion(p,a):
    b=(1-a)%p
    return all(x%2==0 for x in [a,pow(a,-1,p),pow(b,-1,p),order(a,p),order(b,p),order(-b*pow(a,-1,p),p)])

def sts_loop():
    # Erskine--Griggs, arXiv:2405.07750, section 3.2.
    # STS points: A_i=i, B_i=6+i, C_i=12+i, infinity=18;
    # added loop identity=19.
    starters=[(18,0,3),(18,6,9),(18,12,15),(0,1,6),(0,2,13),
              (6,7,13),(6,8,4),(12,13,8),(12,14,4),(0,9,12),(0,7,15)]
    shift=lambda x,k:18 if x==18 else (x//6)*6+(x%6+k)%6
    triples=set(tuple(sorted(shift(x,k) for x in t)) for t in starters for k in range(6))
    assert len(triples)==57
    L=[[-1]*20 for _ in range(20)]
    for x in range(20): L[19][x]=L[x][19]=x
    for x in range(19): L[x][x]=19
    for T in triples:
        for a,b,c in permutations(T):
            assert L[a][b]==-1 or L[a][b]==c
            L[a][b]=c
    return L

def rank2(rows):
    piv={}
    for x in rows:
        while x:
            k=x.bit_length()-1
            if k not in piv: piv[k]=x;break
            x^=piv[k]
    return len(piv)

def line_rank2(L):
    n=len(L)
    return rank2([(1<<r)|(1<<(n+c))|(1<<(2*n+L[r][c])) for r in range(n) for c in range(n)])

L12=[list(map(int,line.split())) for line in '''0 1 2 3 4 5 6 7 8 9 10 11
1 0 3 2 5 4 7 6 10 11 8 9
2 3 0 1 7 6 5 4 9 8 11 10
3 2 1 0 6 7 4 5 11 10 9 8
4 7 5 6 8 11 9 10 3 0 2 1
5 6 4 7 9 10 8 11 2 1 3 0
6 5 7 4 10 9 11 8 1 2 0 3
7 4 6 5 11 8 10 9 0 3 1 2
8 9 10 11 3 2 1 0 6 7 4 5
9 8 11 10 0 1 2 3 4 5 6 7
10 11 8 9 2 3 0 1 5 4 7 6
11 10 9 8 1 0 3 2 7 6 5 4'''.splitlines()]

def basic():
    results={'L12':scan(L12)}
    assert results['L12']['pattern']==scan_alternating_graph(L12)=='FFF'
    results['L12']['second_implementation']='FFF'
    results['L12']['binary_line_rank']=line_rank2(L12)
    (ROOT/'inputs'/'L12_transcribed.json').write_text(json.dumps(L12))
    tested=0; parameters={}
    for p in primes(43):
        Sp=[]
        for a in range(2,p):
            s=scan(affine(p,a));tested+=1
            assert (s['pattern']=='FFF')==criterion(p,a),(p,a,s)
            if s['pattern']=='FFF': Sp.append(a)
        parameters[p]=Sp
    results['affine_all_through_43']={'tested':tested,'prime_count':len(parameters),'FFF_parameters':parameters}
    results['Q97_36']=scan(affine(97,36));assert results['Q97_36']['pattern']==scan_alternating_graph(affine(97,36))=='FFF'
    results['Q97_36']['second_implementation']='FFF'
    results['round_robin']=[]
    for p in primes(101):
        s=scan(affine(p,pow(2,-1,p))); assert (s['pattern']=='FFF')==(p%8==3)
        results['round_robin'].append({'p':p,'pattern':s['pattern']})
    K=sts_loop();results['STS19_loop']=scan(K)
    (ROOT/'inputs'/'STS19_loop_from_published_starters.json').write_text(json.dumps(K))
    assert results['STS19_loop']['pattern']=='FFF'
    results['arithmetic']={'order8_total':sum([230,81,40,315,133,209,232,282417]),
        'order6_total':6600+936*3, 'noninv_pairs':math.comb(172368,2),'inv_pairs':math.comb(190080,2),
        'p11_conditions':3*math.comb(121,2)*11,'p11_order':121*1024,
        'cutoff_rational':str(260*Fraction(15318,1000)**3),
        'exp_taylor_above_10':sum(Fraction(2303,1000)**k/math.factorial(k) for k in range(10))>10,
        'n18_colors_plus_cells':3*math.comb(18,2)*36+18**3,
        'n18_clauses_with_54_anchor_units':3*math.comb(18,2)*4*18**2+3*18**2*(1+math.comb(18,2))+3*math.comb(18,2)+54}
    (ROOT/'results'/'core_results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({k:v if k=='arithmetic' else {a:b for a,b in v.items() if a not in ('profiles','spectrum')} if isinstance(v,dict) else v for k,v in results.items()},indent=2),flush=True)

if __name__=='__main__': basic()
