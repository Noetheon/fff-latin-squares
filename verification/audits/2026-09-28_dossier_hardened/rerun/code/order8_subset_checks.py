"""Audit the 230 archived FFF representatives, not the entire ANU census."""
from core_checks import *
from flag_and_smallorder_checks import flag_check

def closure(L):
    inv=inverse(L[0]); H=[tuple(inv[x] for x in row) for row in L]; S=set(H)
    return all(tuple(a[x] for x in b) in S for a in H for b in H)

def halfsubs(L):
    n=len(L);m=n//2;sub=list(combinations(range(n),m));num=0
    for rows in sub:
        for cols in sub:
            vals={L[r][c] for r in rows for c in cols}
            num+=len(vals)==m
    return num

def local_sig(L):
    n=len(L);cols=[list(c) for c in zip(*L)]
    syms=[[inverse(cols[c])[s] for c in range(n)] for s in range(n)]
    bins=[[[0]*(n-1) for _ in range(3)] for _ in range(n*n)]
    for v,fam in enumerate([L,cols,syms]):
        invs=[inverse(p) for p in fam]
        for a,b in combinations(range(n),2):
            p=[invs[b][x] for x in fam[a]]
            for C in cycles(p):
                ell=len(C)
                for pos in C:
                    if v==0:cells=[a*n+pos,b*n+pos]
                    elif v==1:cells=[pos*n+a,pos*n+b]
                    else:cells=[syms[a][pos]*n+pos,syms[b][pos]*n+pos]
                    for cell in cells:bins[cell][v][ell-2]+=1
    for cell in bins:
        assert all(sum(b)==n-1 for b in cell)
        assert cell[0][0]==cell[1][0]==cell[2][0]
    return min(tuple(sorted(tuple(tuple(cell[v]) for v in order) for cell in bins)) for order in permutations(range(3)))

def pair_trace(L):
    n=len(L);pairs=list(combinations(range(n),2));ix={p:i for i,p in enumerate(pairs)};m=len(pairs)
    cols=[list(c) for c in zip(*L)]
    # Matchings of each symbol send row to column.
    sr=[[inverse(L[r])[s] for r in range(n)] for s in range(n)]
    def W(fam):
        w=[[0]*m for _ in range(m)]
        for f in fam:
            for i,(a,b) in enumerate(pairs):w[i][ix[tuple(sorted((f[a],f[b])))]]+=1
        return w
    RC,RS,CS=W(sr),W(cols),W(L)
    assert all(x in (0,1,2) for w in (RC,RS,CS) for row in w for x in row)
    return sum(RC[i][j]*CS[j][k]*RS[i][k] for i in range(m) for j in range(m) if RC[i][j] for k in range(m))

def holonomy_key(record):
    ans=[]
    for order in permutations(range(3)):
        def mm(mask):return sum(((mask>>order[v])&1)<<v for v in range(3))
        ans.append(tuple(sorted((c['faces'],c['chi_atom'],7 in c['exact_masks'],tuple(sorted(mm(m) for m in c['exact_masks']))) for c in record['component_checks'])))
    return min(ans)

def main():
    data=json.loads((ROOT/'inputs'/'order8_230_raw.json').read_text())
    result=[];sigs=Counter();jointw=Counter();jointt=Counter();hkeys=Counter()
    for idx,d in enumerate(data):
        s=d['square'];L=[[int(x) for x in s[r*8:r*8+8]] for r in range(8)]
        s0=scan(L);assert s0['pattern']==scan_alternating_graph(L)=='FFF'
        br=line_rank2(L);hs=halfsubs(L);assert hs==4*((1<<(22-br))-1)
        fl=flag_check(L);sig=local_sig(L);tr=pair_trace(L)
        sigs[sig]+=1;jointw[sig,fl['w6']]+=1;jointt[sig,tr]+=1;hkeys[holonomy_key(fl)]+=1
        result.append({'source_line':d['line_number'],'pattern':s0['pattern'],'I':s0['intercalates'],
          'rank2':br,'order4_subsquares':hs,'group_isotopic':closure(L),
          'flags':fl['flags'],'components':fl['components'],'w6':fl['w6'],'t':tr})
    out={'scope':'230 archived FFF representatives only; not a fresh 283657-main-class census scan',
      'tables':len(result),'group_isotopy_histogram':dict(Counter(r['group_isotopic'] for r in result)),
      'binary_rank_histogram':dict(Counter(r['rank2'] for r in result)),
      'subsquare_histogram':dict(Counter(r['order4_subsquares'] for r in result)),
      'intercalate_min':min(r['I'] for r in result),'intercalate_max':max(r['I'] for r in result),
      'intercalate_min_sources':[r['source_line'] for r in result if r['I']==min(s['I'] for s in result)],
      'intercalate_max_sources':[r['source_line'] for r in result if r['I']==max(s['I'] for s in result)],
      'total_flags':sum(r['flags'] for r in result),'total_components':sum(r['components'] for r in result),
      'holonomy_values':len(hkeys),'holonomy_collision_histogram':dict(Counter(hkeys.values())),
      'local_signature_values':len(sigs),'local_signature_w6_values':len(jointw),'local_signature_t_values':len(jointt),
      't_values':len(set(r['t'] for r in result)),'I_t_values':len(set((r['I'],r['t']) for r in result)),
      'records':result}
    (ROOT/'results'/'order8_230_checks.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
if __name__=='__main__':main()
