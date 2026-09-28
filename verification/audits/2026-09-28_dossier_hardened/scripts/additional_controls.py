"""New checks: block return formula, quadratic obstructions, paired binary blocks,
certificate corruptions, and the still-unqualified singleton-block sentence."""
from pathlib import Path
from collections import Counter
from itertools import combinations,product
import json,sys,time,copy,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'rerun/code'))
from core_checks import L12,scan,cycles,inverse
from verify_representatives import minor

def req(b,s):
    if not b:raise ValueError(s)
def linefamilies(L):
    n=len(L);cols=list(map(list,zip(*L)));sym=[[0]*n for _ in range(n)]
    for r in range(n):
        for c in range(n):sym[L[r][c]][c]=r
    return [L,cols,sym]
def block_test():
    L=L12;Q=[[L[4*a][4*b]//4 for b in range(3)] for a in range(3)];result=[]
    req(scan(Q)['pattern']=='TTT','outer control')
    for a,b in product(range(3),repeat=2):
        req(all(L[4*a+x][4*b+y]//4==Q[a][b] for x,y in product(range(4),repeat=2)),'block projection')
        req(scan([[L[4*a+x][4*b+y]%4 for y in range(4)] for x in range(4)])['pattern']=='FFF','inner control')
    shape_counts=Counter();tested=0
    for fam in linefamilies(L):
        for a,b in combinations(range(12),2):
            iv=inverse(fam[b]);p=[iv[s] for s in fam[a]];outer=[p[4*x]//4 for x in range(3)];pred=[]
            req(all(p[4*x+y]//4==outer[x] for x in range(3) for y in range(4)),'fiber inconsistency')
            for C in cycles(outer):
                ret=[]
                for z in range(4):
                    x=4*C[0]+z
                    for _ in C:x=p[x]
                    req(x//4==C[0],'return escaped');ret.append(x%4)
                rc=cycles(ret)
                pred.extend(len(C)*len(X) for X in rc)
                shape_counts[str((len(C),tuple(sorted(map(len,rc)))))]+=1
            req(sorted(pred)==sorted(map(len,cycles(p))),'return decomposition');tested+=1
    return {'tables':1,'pairs':tested,'outer_pattern':scan(Q)['pattern'],'inner_blocks':9,'whole_pattern':scan(L)['pattern'],'outer_return_shapes':dict(shape_counts)}
def quadratics():
    result=[]
    for p in [3,5]:
        points=list(product(range(p),repeat=3));monomials=[(x*x%p,y*y%p,z*z%p,x*y%p,x*z%p,y*z%p) for x,y,z in points];counts=Counter()
        for coefficients in product(range(p),repeat=6):
            zeros=sum(sum(c*m for c,m in zip(coefficients,v))%p==0 for v in monomials)
            req(zeros>=p and zeros%p==0,'Chevalley-Warning control');counts[zeros]+=1
        result.append({'p':p,'all_homogeneous_quadratic_forms':p**6,'all_have_nonzero_zero':True,'zero_counts':dict(counts)})
    return result
def paired():
    out=[]
    for m in [1,2,3]:
        hist=Counter()
        for mask in range(1<<(m*m)):
            L=[[2*((r//2+c//2)%m)+(r%2 ^ c%2 ^ (mask>>(r//2*m+c//2)&1)) for c in range(2*m)] for r in range(2*m)]
            s=scan(L);I=s['intercalates'];req(I>=m*m and (I-m*m)%2==0,'paired block formula');hist[(s['pattern'],I)]+=1
        out.append({'m':m,'all_twists':1<<(m*m),'counts':{str(k):v for k,v in hist.items()}})
    return out
def certificates():
    first=json.loads((R/'results/expanded_representatives.jsonl').read_text().splitlines()[0]);L=first['table'];cells=first['minor_cells'];minor(L,cells)
    cases={'short':cells[:-1],'duplicate':[cells[0]]*58,'out_of_range':cells[:-1]+[400],'negative':cells[:-1]+[-1],'boolean':cells[:-1]+[False],'singular_distinct':list(range(58))};rejected={}
    for name,bad in cases.items():
        try:minor(L,bad)
        except ValueError as ex:rejected[name]=str(ex)
        else:raise ValueError('bad certificate accepted '+name)
    return {'invalid_minor_cases_rejected':len(rejected),'cases':rejected,'scope':'New explicit row-elimination function; not a full run of project verifier.'}
def main():
    start=time.monotonic();out={'block_return':block_test(),'rank_three_quadratics':quadratics(),'paired_blocks':paired(),'negative_minor_controls':certificates(),'singleton_congruence_counterexample':{'table':[[0,1],[1,0]],'pattern':scan([[0,1],[1,0]])['pattern'],'block_size':1,'formal_theorem_unaffected':True},'seconds':time.monotonic()-start}
    (R/'results/additional_controls.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
