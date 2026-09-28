from core_checks import *
from field_checks import Field

def partitions(n,minimum=1):
    if n==0:yield ();return
    for a in range(minimum,n+1):
        for p in partitions(n-a,a):yield (a,)+p

def channel_check():
    counts={}
    # f_a is identity. Every permutation can be realized as f_b after value relabeling.
    # h=e is forced by the first family, so enumerate the remaining 2^n choices.
    for n in range(1,7):
        tested=0
        for fb in permutations(range(n)):
            cs=cycles(fb);want=all(len(c)%2==0 for c in cs)
            solutions=[]
            for e in product([0,1],repeat=n):
                if all(e[i]==1-e[fb[i]] for i in range(n)):
                    solutions.append(e)
                    assert sum(e)*2==n
            assert bool(solutions)==want
            assert any(e[0]==0 for e in solutions)==want
            if want:assert len(solutions)==2**len(cs)
            tested+=1
        counts[n]=tested
    for A,B,e,h in product([False,True],repeat=4):
        clauses=((not A)or(not e)or h) and ((not A)or e or(not h)) and ((not B)or e or h) and ((not B)or(not e)or(not h))
        meaning=((not A)or(e==h)) and ((not B)or(e!=h))
        assert clauses==meaning
    return counts

def row_fibred(B,Qs):
    m=len(B);n=len(Qs[0]);assert len(Qs)==m
    return [[Qs[y][r][c]*m+B[y][z] for c in range(n) for z in range(m)] for r in range(n) for y in range(m)]

def main():
    P=list(partitions(9));ret=[tuple(2*x for x in p) for p in P if len(p)%2==0]
    survivors=[a for a in range(1,16) if (-a)%17%2==0 and (-pow(a,-1,17))%17%2==0]
    symbols=[(a*pow(a+1,-1,17))%17 for a in survivors]
    testcases=[]
    for m,n in [(2,4),(3,4),(4,3),(2,20)]:
        B=[[(y+z)%m for z in range(m)] for y in range(m)]
        if n==20:Q=[sts_loop(),affine(19,8)]
        else:
            Q0=[[(r+c)%n for c in range(n)] for r in range(n)]
            Q=[[[Q0[(r+y)%n][c] for c in range(n)] for r in range(n)] for y in range(m)]
        M=row_fibred(B,Q);bits=[scan(B)['pattern']]+[scan(q)['pattern'] for q in Q]
        expected=''.join('T' if any(s[i]=='T' for s in bits) else 'F' for i in range(3))
        got=scan(M);assert got['pattern']==scan_alternating_graph(M)==expected
        testcases.append({'outer':m,'inner':n,'pattern':expected,'rank2':line_rank2(M)})
    # Clarification control: m=3 is impossible for K=F4 in the stated minimal-field setting,
    # but not for arbitrary larger binary fields.
    F=Field(4);r=F.exp[5];H=[F.power(r,i) for i in range(3)];t=[0,1,2]
    assert 2 not in (0,1,r,F.power(r,2))
    si=[F.mul(H[i],t[i]) for i in range(3)]
    L=[[((i+j)%3)*16+(a^F.mul(H[i],b)^F.mul(si[i],H[j])) for j in range(3) for b in range(16)] for i in range(3) for a in range(16)]
    s=scan(L);assert s['pattern']==scan_alternating_graph(L)=='FFF'
    out={'position_value_permutations':channel_check(),'conditional_clause_truth_rows':16,
         'partitions_of_9':len(P),'order18_positive_sign_root_types':ret,
         'C225_affine_survivors':survivors,'C225_symbol_residues':symbols,
         'row_fibred_controls':testcases,
         'm3_scope_control':{'field_order':16,'field_polynomial':F.poly,'r':r,'t':t,'order':48,'pattern':s['pattern'],
            'interpretation':'Not a counterexample to Remark 8.4 when its K=F4 scope is retained.'}}
    (ROOT/'results'/'formulation_scope.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
