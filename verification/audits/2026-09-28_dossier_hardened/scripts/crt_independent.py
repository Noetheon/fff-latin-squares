"""Fresh CRT return enumerator and greedy twist constructor from the operation.
No frozen CRT builder, direct-return routine, or twist certificate is imported.
Every pair/orbit is checked; four physical probes isolate constant, slope and
both line coefficients in the K-affine model. No large square is materialized.
"""
from itertools import product,combinations
from pathlib import Path
from collections import Counter
import json,hashlib,time,sys
R=Path(__file__).resolve().parents[1]
def need(c,s):
    if not c:raise ValueError(s)
class Field:
    def __init__(self,q):
        self.q=q;poly={16:19,64:67,256:285}[q];ex=[];x=1
        for i in range(q-1):
            ex.append(x);x<<=1
            if x&q:x^=poly
        need(x==1 and len(set(ex))==q-1,'primitive field polynomial')
        logs={v:i for i,v in enumerate(ex)}
        self.mul=[[0 if not a or not b else ex[(logs[a]+logs[b])%(q-1)] for b in range(q)] for a in range(q)]
        self.inv=[0]+[ex[-logs[a]%(q-1)] for a in range(1,q)]
        self.ex=ex;self.poly=poly
class Model:
    def __init__(self,spec,q):
        self.spec=spec;self.mods=[p for p,r,nu in spec for _ in range(r)];self.G=list(product(*(range(p) for p in self.mods)));self.index={g:i for i,g in enumerate(self.G)};self.n=len(self.G);self.F=Field(q);self.q=q;self.mul=self.F.mul;self.iv=self.F.inv
        self.M=1
        for p,r,nu in spec:self.M*=p
        need((q-1)%self.M==0 and q>3*(self.n-1),'field bound')
        units=[(self.M//p)*pow(self.M//p,-1,p) for p,r,nu in spec]
        def B(x,y):
            out=0;j=0
            for i,(p,r,nu) in enumerate(spec):
                value=x[j]*y[j]
                if r==2:value-=nu*x[j+1]*y[j+1]
                out+=(value%p)*units[i];j+=r
            return out%self.M
        chi=lambda t:self.F.ex[(t%self.M)*((q-1)//self.M)]
        self.B=[chi(B(x,x)) for x in self.G];self.A=[[chi(2*B(x,y)) for y in self.G] for x in self.G]
        self.add=[[self.index[tuple((a+b)%p for a,b,p in zip(x,y,self.mods))] for y in self.G] for x in self.G]
        self.sub=[[self.index[tuple((a-b)%p for a,b,p in zip(x,y,self.mods))] for y in self.G] for x in self.G]
    def step(self,v,a,b,pos):
        A,B,m,iv=self.A,self.B,self.mul,self.iv;n=self.n
        if v==0:
            x,z,y=a,b,pos;yp=self.add[y][self.sub[x][z]];den=iv[B[z]]
            return yp,m[B[x]][den],m[A[x][y]][den],m[A[z][yp]][den],(x*n+y,den),(z*n+yp,den)
        if v==1:
            y,z,x=a,b,pos;xp=self.add[x][self.sub[y][z]];den=iv[A[xp][z]]
            return xp,m[A[x][y]][den],m[B[x]][den],m[B[xp]][den],(x*n+y,den),(xp*n+z,den)
        k,l,y=a,b,pos;x=self.sub[k][y];yp=self.sub[l][x];ratio=m[A[x][yp]][iv[A[x][y]]];coef=m[ratio][iv[B[x]]]
        return yp,ratio,coef,iv[B[x]],(x*n+y,coef),(x*n+yp,iv[B[x]])
    def physical(self,v,a,b,pos,w,la,lb,c,h):
        # Direct evaluation and inversion of cell operations, not use of step().
        A,B,m,iv,n=self.A,self.B,self.mul,self.iv,self.n
        for _ in range(h):
            if v==0:
                x,z,y=a,b,pos;yp=self.sub[self.add[x][y]][z]
                symbol=m[A[x][y]][la]^m[B[x]][w]^c[x*n+y]
                w=m[iv[B[z]]][symbol^m[A[z][yp]][lb]^c[z*n+yp]];pos=yp
            elif v==1:
                y,z,x=a,b,pos;xp=self.sub[self.add[x][y]][z]
                symbol=m[A[x][y]][w]^m[B[x]][la]^c[x*n+y]
                w=m[iv[A[xp][z]]][symbol^m[B[xp]][lb]^c[xp*n+z]];pos=xp
            else:
                x=self.sub[a][pos];y2=self.sub[b][x]
                row=m[iv[A[x][pos]]][la^m[B[x]][w]^c[x*n+pos]]
                w=m[iv[B[x]]][lb^m[A[x][y2]][row]^c[x*n+y2]];pos=y2
        return pos,w

def run(N):
    configs={9:([(3,2,2)],64),15:([(3,1,0),(5,1,0)],256),45:([(3,2,2),(5,1,0)],256),75:([(3,1,0),(5,2,2)],256)}
    started=time.monotonic();spec,q=configs[N];ctx=Model(spec,q);n=ctx.n;m=ctx.mul;forms=[];incidence=[0]*(n*n);closing=[[] for _ in range(n*n)];by_h=Counter();inactive=0
    for v in range(3):
        for a,b in combinations(range(n),2):
            unseen=set(range(n))
            while unseen:
                start=min(unseen);pos=start;steps=[];slope=1;alpha=beta=0
                while True:
                    need(pos in unseen,'orbit overlap');unseen.remove(pos)
                    nxt,s,u,w,c1,c2=ctx.step(v,a,b,pos);steps.append((s,c1,c2))
                    slope=m[s][slope];alpha=m[s][alpha]^u;beta=m[s][beta]^w;pos=nxt
                    if pos==start:break
                h=len(steps);need(h>1 and h%2==1,'odd quotient orbit');need((slope,alpha,beta)==(1,0,0),'return coefficient failure')
                suffix=1;support=[]
                for s,c1,c2 in reversed(steps):
                    for cell,coef in (c1,c2):support.append((cell,m[suffix][coef]))
                    suffix=m[suffix][s]
                need(len({x for x,k in support})==2*h and all(k for x,k in support),'support cancellation');support.sort();idx=len(forms)
                forms.append((v,a,b,start,h,support));closing[support[-1][0]].append(idx)
                for cell,k in support:incidence[cell]+=1
                by_h[h]+=1
                diff=ctx.G[ctx.sub[a][b]]
                if any(x==0 for x in diff):inactive+=1
    need(set(incidence)=={3*(n-1)},'incidence bound')
    twists=[0]*(n*n);max_forbidden=0
    for cell,indices in enumerate(closing):
        forbidden=set()
        for idx in indices:
            support=forms[idx][-1];value=0
            for j,coef in support[:-1]:value^=m[coef][twists[j]]
            forbidden.add(m[value][ctx.iv[support[-1][1]]])
        twists[cell]=next(x for x in range(q) if x not in forbidden);max_forbidden=max(max_forbidden,len(forbidden))
    probes=0
    for v,a,b,start,h,support in forms:
        val=0
        for cell,coef in support:val^=m[coef][twists[cell]]
        need(val!=0,'zero twist return')
        for la,lb,w in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]:
            end,z=ctx.physical(v,a,b,start,w,la,lb,twists,h);need(end==start and z==val^w,'physical probe mismatch');probes+=1
    # A zero twist gives an odd physical orbit at zero labels, so negative control fails F.
    negative=[]
    for v in range(3):
        form=next(f for f in forms if f[0]==v);_,a,b,start,h,sup=form;end,z=ctx.physical(v,a,b,start,0,0,0,[0]*(n*n),h)
        need(end==start and z==0,'negative control');negative.append(h)
    expected={9:324,15:675,45:17010,75:73125};need(len(forms)==expected[N],'coverage count')
    result={'N':n,'field_order':q,'field_modulus':ctx.F.poly,'components':spec,'order':n*q,'returns_checked':len(forms),'cycles_by_quotient_order':dict(by_h),'physical_probes':probes,'all_slope_one':True,'both_label_coefficients_zero':True,'all_twist_forms_nonzero':True,'cell_incidence':3*(n-1),'max_forbidden_field_values':max_forbidden,'zero_twist_odd_cycle_controls':negative,'twists':twists,'twists_sha256':hashlib.sha256(bytes(twists)).hexdigest(),'full_square_materialized':False,'seconds':time.monotonic()-started}
    (R/'results'/f'crt_N{N}.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='twists'}))
if __name__=='__main__':run(int(sys.argv[1]))
