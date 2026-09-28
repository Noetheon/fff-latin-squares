from core_checks import *

def pmod(a,b):
    while a and a.bit_length()>=b.bit_length():a^=b<<(a.bit_length()-b.bit_length())
    return a

def pgcd(a,b):
    while b:a,b=b,pmod(a,b)
    return a

def mul_poly(a,b,poly):
    ans=0; top=1<<(poly.bit_length()-1)
    while b:
        if b&1:ans^=a
        b>>=1;a<<=1
        if a&top:a^=poly
    return ans

def pow_poly(a,k,poly):
    ans=1
    while k:
        if k&1:ans=mul_poly(ans,a,poly)
        a=mul_poly(a,a,poly);k>>=1
    return ans

def irreducible(f):
    e=f.bit_length()-1;x=2;v=x
    for i in range(1,e+1):
        v=mul_poly(v,v,f)
        if i<=e//2 and pgcd(v^x,f)!=1:return False
    return v==x

class Field:
    def __init__(self,e,poly=None):
        self.e=e;self.q=1<<e
        if poly is None:poly=next(f for f in range(self.q+1,2*self.q,2) if irreducible(f))
        assert irreducible(poly)
        self.poly=poly
        # Build logarithms from an independently found primitive element.
        divs=[d for d in range(2,self.q) if (self.q-1)%d==0 and all(d%k for k in range(2,math.isqrt(d)+1))]
        gen=next(g for g in range(2,self.q) if all(pow_poly(g,(self.q-1)//d,poly)!=1 for d in divs))
        self.exp=[];self.log=[-1]*self.q;x=1
        for i in range(self.q-1):self.exp.append(x);self.log[x]=i;x=mul_poly(x,gen,poly)
        assert x==1 and len(set(self.exp))==self.q-1
    def mul(self,a,b):return 0 if not a or not b else self.exp[(self.log[a]+self.log[b])%(self.q-1)]
    def power(self,a,k):
        if not a: return 1 if k==0 else 0
        return self.exp[(self.log[a]*k)%(self.q-1)]
    def inv(self,a):assert a;return self.power(a,-1)

def ord2(m):
    a=2%m;e=1
    while a!=1:a=a*2%m;e+=1
    return e

def threepoint(m,materialize=False):
    e=ord2(m);F=Field(e);r=F.exp[(F.q-1)//m]
    allchecks=[]; chosen=None
    for root in [r,F.inv(r)]:
        H=[F.power(root,i) for i in range(m)];u=F.inv(root^1)
        t={x:1 if x==1 else F.inv(x^1) for x in H};t[1]=u;t[root]=F.mul(u,u);t[F.mul(root,root)]=1
        assert len(set(t.values()))==m
        checks=[]
        for ell in range(3,m+1,2):
            if m%ell:continue
            step=m//ell
            for j in range(step):
                C=[H[(j+k*step)%m] for k in range(ell)];S=T=0
                for x in C:S^=F.mul(x,t[x]);T^=F.mul(F.inv(x),t[x])
                checks.append((ell,j,S,T))
        bad=[c[:2] for c in checks if not c[2] or not c[3]]
        allchecks.append({'root':root,'cosets':len(checks),'bad_cosets':bad})
        if not bad and chosen is None:chosen=(root,H,t)
    assert chosen is not None,(m,allchecks)
    out={'m':m,'e':e,'field_polynomial':F.poly,'order':m*F.q,'root_checks':allchecks}
    if materialize:
        root,H,t=chosen;s=[F.mul(x,t[x]) for x in H];q=F.q
        L=[[((i+j)%m)*q+(a^F.mul(H[i],b)^F.mul(s[i],H[j])) for j in range(m) for b in range(q)] for i in range(m) for a in range(q)]
        out['physical_scan']=scan(L);assert out['physical_scan']['pattern']=='FFF'
    return out

if __name__=='__main__':
    out=[threepoint(m,m in [5,7,15]) for m in [5,7,9,15,21,25,27,31,33,35,45,51,63,85,127,255] if ord2(m)<=12]
    (ROOT/'results'/'threepoint_checks.json').write_text(json.dumps(out,indent=2))
    print(json.dumps([{k:v for k,v in o.items() if k!='physical_scan'} for o in out],indent=2))
