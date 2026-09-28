"""Second implementation: physical bipartite components plus row-elimination minors.
Consumes newly enumerated tables, not old pass reports; reconstructs all invariants.
"""
import json, hashlib, time, sys
from pathlib import Path
from collections import Counter
from itertools import combinations
R=Path(__file__).resolve().parents[1]
def need(x,m):
    if not x:raise ValueError(m)
def physical(L):
    n=len(L);full=list(range(n));need(all(sorted(r)==full for r in L),'row');need(all(sorted(c)==full for c in zip(*L)),'column')
    total=Counter(); patterns=[]; ints=[]
    for view in range(3):
        fam=[[] for _ in range(n)]
        for r in range(n):
            for c in range(n):
                xyz=(r,c,L[r][c]);rest=[xyz[k] for k in range(3) if k!=view];fam[xyz[view]].append((rest[0],n+rest[1]))
        bad=False;I=0
        for a,b in combinations(range(n),2):
            parent=list(range(2*n));size=[1]*(2*n)
            def find(x):
                while parent[x]!=x:
                    parent[x]=parent[parent[x]];x=parent[x]
                return x
            degree=[0]*(2*n)
            for u,v in fam[a]+fam[b]:
                degree[u]+=1;degree[v]+=1;u=find(u);v=find(v)
                if u!=v:
                    if size[u]<size[v]:u,v=v,u
                    parent[v]=u;size[u]+=size[v]
            need(all(k==2 for k in degree),'bad link degree')
            typ=tuple(sorted(size[x]//2 for x in range(2*n) if parent[x]==x))
            need(sum(typ)==n,'component coverage');bad|=any(k%2 for k in typ);I+=typ.count(2);total[typ]+=1
        patterns.append('T' if bad else 'F');ints.append(I)
    need(len(set(ints))==1,'intercalate coupling');return ''.join(patterns),tuple(sorted(total.items())),ints[0]
def minor(L,cells):
    n=len(L);need(len(cells)==58 and len(set(cells))==58,'minor size/dup')
    need(all(type(i)is int and 0<=i<400 for i in cells),'invalid minor cell')
    rows=list(range(39))+list(range(40,59));mat=[]
    for line in rows:
        mat.append(sum(1<<i for i,cell in enumerate(cells) if line in (cell//n,n+cell%n,2*n+L[cell//n][cell%n])))
    for c in range(58):
        k=next((k for k in range(c,58) if mat[k]>>c&1),None);need(k is not None,'singular')
        mat[c],mat[k]=mat[k],mat[c]
        for k in range(c+1,58):
            if mat[k]>>c&1:mat[k]^=mat[c]
    return True
def main():
    t=time.monotonic();spectra=set();hashes=set();count=0;ints=[];bindings=[]
    for line in (R/'results/expanded_representatives.jsonl').read_text().splitlines():
        rec=json.loads(line);L=rec['table'];pat,sp,I=physical(L)
        need(pat=='FFF','nonFFF');need(sp==tuple((tuple(t),k) for t,k in rec['spectrum']),'spectrum discrepancy');need(I==rec['intercalates'],'I discrepancy');need(sp not in spectra,'spectral collision');spectra.add(sp)
        minor(L,rec['minor_cells']);h=hashlib.sha256(bytes(x for r in L for x in r)).hexdigest();need(h not in hashes,'duplicate table');hashes.add(h)
        bindings.append({'id':count,'origin':rec['origin'],'a':rec['a'],'b':rec['b'],'mask':rec['mask'],'sha256_raw_table_bytes':h,'minor_cells':rec['minor_cells']});count+=1;ints.append(I)
    need(count==1703,'coverage');(R/'results/verified_certificates.json').write_text(json.dumps(bindings,indent=2))
    result={'tables':count,'all_latin_fff':True,'independent_exact_spectra':len(spectra),'all_minors_nonsingular':True,'intercalates_min':min(ints),'intercalates_max':max(ints),'line_pairs_checked':count*570,'bipartite_edges_processed':count*570*40,'seconds':time.monotonic()-t}
    (R/'results/secondary_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
