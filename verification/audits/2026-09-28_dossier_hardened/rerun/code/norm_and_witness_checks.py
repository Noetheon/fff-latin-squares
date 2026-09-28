from field_checks import *
import csv,hashlib

def norm_certificate_check():
    src=ROOT/'inputs'/'norm_p11_q1024_greedy_certificate.json';J=json.loads(src.read_text())
    p=J['prime'];F=Field(J['field_degree'],J['field_modulus']);om=J['omega'];nu=J['nonsquare'];N=p*p
    assert F.power(om,p)==1 and om!=1 and pow(nu,(p-1)//2,p)==p-1
    # Use only input parameters/twists, not the old pass flags or histogram.
    coords=[(i%p,i//p) for i in range(N)]
    add=lambda x,y: ((coords[x][0]+coords[y][0])%p)+p*((coords[x][1]+coords[y][1])%p)
    neg=lambda x:((-coords[x][0])%p)+p*((-coords[x][1])%p)
    adds=[[add(x,y) for y in range(N)] for x in range(N)]
    sub=[[adds[x][neg(y)] for y in range(N)] for x in range(N)]
    B=lambda x,y:(coords[x][0]*coords[y][0]-nu*coords[x][1]*coords[y][1])%p
    Q=[B(x,x) for x in range(N)];assert all(Q[x] for x in range(1,N))
    powers=[F.power(om,k) for k in range(p)]
    alpha=[[powers[(2*B(x,y))%p] for y in range(N)] for x in range(N)]
    ia=[[F.inv(a) for a in row] for row in alpha]
    beta=[powers[q] for q in Q];ib=[F.inv(b) for b in beta]
    ct=J['twists'];assert len(ct)==N*N and all(0<=x<F.q for x in ct)
    c=[ct[i*N:(i+1)*N] for i in range(N)]
    mul=F.mul; checked=0; hist=Counter();inc=[0]*(N*N)
    for view in range(3):
        for a,b in combinations(range(N),2):
            d=sub[a][b] if view<2 else sub[b][a]
            seen=set()
            for start in range(N):
                if start in seen:continue
                loc=start;S=1;U=V=W=0;support=[]
                for _ in range(p):
                    seen.add(loc);nxt=adds[loc][d]
                    if view==0:
                        inv=ib[b];s=mul(beta[a],inv);u=mul(alpha[a][loc],inv);v=mul(alpha[b][nxt],inv);w=mul(c[a][loc]^c[b][nxt],inv)
                        support.extend([a*N+loc,b*N+nxt])
                    elif view==1:
                        inv=ia[nxt][b];s=mul(alpha[loc][a],inv);u=mul(beta[loc],inv);v=mul(beta[nxt],inv);w=mul(c[loc][a]^c[nxt][b],inv)
                        support.extend([loc*N+a,nxt*N+b])
                    else:
                        x=sub[a][loc];s=mul(alpha[x][nxt],ia[x][loc]);u=mul(s,ib[x]);v=ib[x];w=mul(u,c[x][loc])^mul(v,c[x][nxt])
                        support.extend([x*N+loc,x*N+nxt])
                    S=mul(s,S);U=mul(s,U)^u;V=mul(s,V)^v;W=mul(s,W)^w;loc=nxt
                assert loc==start and len(set(support))==2*p
                assert (S,U,V)==(1,0,0),(view,a,b,start,S,U,V)
                assert W!=0,(view,a,b,start)
                for x in support:inc[x]+=1
                hist[W]+=1;checked+=1
    assert len(set(inc))==1 and inc[0]==3*(p*p-1)
    return {'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'input_encoding':'x0 + p*x1; row-major twists',
      'order':N*F.q,'implicit_returns_checked':checked,'identity_linear_part':True,'both_label_coefficients_zero':True,
      'zero_twist_returns':hist[0],'cell_incidence':inc[0],'distinct_nonzero_returns':len(hist),
      'note':'No full 123904-by-123904 Latin table was materialized.'}

def witness36():
    out=[]
    for src in sorted((ROOT/'inputs').glob('FFF36_seed*.csv')):
        L=[list(map(int,row)) for row in csv.reader(src.open())];s=scan(L);assert scan_alternating_graph(L)==s['pattern']=='FFF'
        out.append({'file':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'second_physical_scanner':'FFF',**s})
    return out

if __name__=='__main__':
    out={'recovered_order36':witness36(),'prime_square':norm_certificate_check()}
    (ROOT/'results'/'norm_and_36.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v if k=='prime_square' else [{'file':s['file'],'pattern':s['pattern'],'pairs':s['pairs']} for s in v] for k,v in out.items()},indent=2))
