from core_checks import *

class DSU:
    def __init__(self,n):self.p=list(range(n));self.sz=[1]*n
    def find(self,a):
        while a!=self.p[a]: self.p[a]=self.p[self.p[a]];a=self.p[a]
        return a
    def join(self,a,b):
        a=self.find(a);b=self.find(b)
        if a==b:return
        if self.sz[a]<self.sz[b]:a,b=b,a
        self.p[b]=a;self.sz[a]+=self.sz[b]

def reduced_squares(n):
    L=[[-1]*n for _ in range(n)];full=(1<<n)-1
    for i in range(n):L[0][i]=L[i][0]=i
    rows=[1<<r for r in range(n)];rows[0]=full
    cols=[1<<c for c in range(n)];cols[0]=full
    def walk(r,c):
        if r==n:yield [x[:] for x in L];return
        avail=full^(rows[r]|cols[c])
        while avail:
            bit=avail&-avail;avail^=bit;s=bit.bit_length()-1
            L[r][c]=s;rows[r]|=bit;cols[c]|=bit
            yield from walk(r+1,1) if c==n-1 else walk(r,c+1)
            rows[r]^=bit;cols[c]^=bit
    yield from walk(1,1)

def flag_check(L):
    n=len(L);N=n*n;iv=[inverse(r) for r in L];flags=[]
    for r in range(n):
        for rp in range(n):
            if r==rp:continue
            for c in range(n):
                d=iv[rp][L[r][c]];flags.append((r*n+c,rp*n+d,r*n+d))
    nf=len(flags);assert nf==n*n*(n-1)
    shared=[(0,2),(1,2),(0,1)];opp=[1,0,2]
    alph=[[0]*nf for _ in range(3)];edges=[]
    for v,(i,j) in enumerate(shared):
        bucket={}
        for k,f in enumerate(flags):bucket.setdefault(tuple(sorted((f[i],f[j]))),[]).append(k)
        assert len(bucket)*2==nf and all(len(fs)==2 for fs in bucket.values())
        for e,(f,g) in bucket.items():alph[v][f]=g;alph[v][g]=f
        edges.append(bucket)
    comps=DSU(nf)
    for A in alph:
        for i,j in enumerate(A):comps.join(i,j)
    components={}
    for i in range(nf):components.setdefault(comps.find(i),[]).append(i)
    atoms=[]
    for v in range(3):
        d=DSU(nf)
        for w in range(3):
            if w!=v:
                for f,g in enumerate(alph[w]):d.join(f,g)
        atom={};idx=[]
        for f in range(nf):idx.append(atom.setdefault(d.find(f),len(atom)))
        atoms.append(idx)
    norm=DSU(3*nf)
    for v,(i,j) in enumerate(shared):
        for f,g in enumerate(alph[v]):
            assert flags[f][i]==flags[g][j] and flags[f][j]==flags[g][i]
            norm.join(3*f+i,3*g+j);norm.join(3*f+j,3*g+i)
    cov=[0]*N;tot=[0]*N;intercalates=0;summary=[]
    for fs in components.values():
        aset=[set(atoms[v][f] for f in fs) for v in range(3)];a=sum(map(len,aset))
        nv=set(norm.find(3*f+j) for f in fs for j in range(3))
        Eopp={z:set() for z in nv}
        for v in range(3):
            j=opp[v]
            for f in fs:
                x=norm.find(3*f+j);y=norm.find(3*alph[v][f]+j);Eopp[x].add(y);Eopp[y].add(x)
        seen=set();q=0
        for x in nv:
            if x in seen:continue
            q+=1;stack=[x];seen.add(x)
            while stack:
                for y in Eopp[stack.pop()]:
                    if y not in seen:seen.add(y);stack.append(y)
        assert 1<=q<=3
        chi_cell=len(nv)-len(fs)//2;assert chi_cell<=2 and chi_cell%2==0
        roles=[Counter(flags[f][j] for f in fs) for j in range(3)]
        assert roles[0]==roles[1]==roles[2];t=roles[0]
        exact={}
        for mask in range(8):
            pot={fs[0]:0};stack=[fs[0]];ok=True
            while stack:
                f=stack.pop()
                for v in range(3):
                    g=alph[v][f];b=pot[f]^((mask>>v)&1)
                    if g in pot:ok &= pot[g]==b
                    else:pot[g]=b;stack.append(g)
            if ok:exact[mask]=pot
        assert all(a^b in exact for a in exact for b in exact)
        odd=any(m.bit_count()%2 for m in exact)
        if odd:assert all(x%2==0 for x in t.values())
        pushes={}
        for m,pot in exact.items():
            u=Counter()
            for f in fs:
                for x in flags[f]:u[x]+=1-2*pot[f]
            if m.bit_count()%2:assert not any(u.values())
            for v in range(3):
                if m>>v&1:
                    marg=Counter()
                    for x,w in u.items():
                        r,c=divmod(x,n);lab=(r,c,L[r][c])[v];marg[lab]+=w
                    assert not any(marg.values())
            pushes[m]=u
        if all(m in exact for m in [3,5,6]):
            for x,w in t.items():
                K=-pushes[3][x]*pushes[5][x]*pushes[6][x]
                assert abs(K)<=w**3 and (K-w**3)%4==0
                if w%2==0:assert K%8==0
        for x,w in t.items():tot[x]+=w;cov[x]^=0 if odd else w%2
        # Coloured component cell edge degrees and parity.
        for v in range(3):
            deg=Counter();ee=set()
            for f in fs:
                i,j=shared[v];ee.add(tuple(sorted((flags[f][i],flags[f][j]))))
            for x,y in ee:deg[x]+=1;deg[y]+=1
            assert deg==t
        chi_atom=a-len(fs)//2
        if len(fs)==4:
            assert a==3 and chi_atom==1 and chi_cell==2
            intercalates+=1
        summary.append({'faces':len(fs),'atoms':a,'vertices_normalized':len(nv),'opposite_components':q,
                       'chi_atom':chi_atom,'chi_cell':chi_cell,'exact_masks':list(exact)})
    assert all(w==n-1 for w in tot) and all(w==(n-1)%2 for w in cov)
    s=scan(L);assert intercalates==s['intercalates']
    beta=[alph[0][alph[1][alph[2][f]]] for f in range(nf)]
    assert sum(f==beta[f] for f in range(nf))==4*intercalates
    for v in range(3):
        other=[w for w in range(3) if w!=v];p=[alph[other[0]][alph[other[1]][f]] for f in range(nf)]
        cc=Counter(map(len,cycles(p)));expected=Counter()
        for typ,num in s['profiles'][v].items():
            for ell in map(int,typ.split(',')):expected[ell]+=2*num
        assert cc==expected
    if s['pattern']=='FFF':
        assert all(c['chi_atom']<0 for c in summary if c['faces']!=4)
        assert sum(c['chi_atom'] for c in summary)%2==(n//2)%2
    return {'n':n,'pattern':s['pattern'],'flags':nf,'components':len(summary),'intercalates':intercalates,
      'w6':sum(beta[beta[f]]==f for f in range(nf)),'component_checks':summary}

if __name__=='__main__':
    counts={};samples=[]
    for n in [2,4,6]:
        C=Counter();num=0;seen=set()
        for L in reduced_squares(n):
            key=tuple(map(tuple,L));assert key not in seen;seen.add(key)
            s=scan(L);C[s['pattern']]+=1
            if n<6 or num in [0,1,3,7,17,63,129,511,2048,4096,8191,9407]:samples.append(L)
            num+=1
        counts[n]={'total':num,'patterns':dict(C)}
    samples += [[[ (r+c)%3 for c in range(3)] for r in range(3)],
                [[( ((r//2+c//2)%4)*2 + ((r%2)^(c%2)^int(r//2==c//2==1))) for c in range(8)] for r in range(8)],
                L12,affine(13,4),sts_loop(),affine(19,8)]
    checks=[flag_check(L) for L in samples]
    (ROOT/'results'/'smallorders_and_flags.json').write_text(json.dumps({'smallorders':counts,'flag_controls':checks},indent=2))
    print(json.dumps(counts,indent=2));print('FLAG controls',len(checks),'flags',sum(c['flags'] for c in checks),'components',sum(c['components'] for c in checks))
