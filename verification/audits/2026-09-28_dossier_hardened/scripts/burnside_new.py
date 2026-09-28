"""Enumerate invertible binary bases, all translations, then count cycles.
No historical AGL histogram is used. Integer Burnside evaluation for both
514 and 1703 colours and exact elementary crosschecks.
"""
from pathlib import Path
from collections import Counter
from math import comb,lcm
from fractions import Fraction
import time,json,sys
if sys.flags.optimize:
    raise RuntimeError('Audit checks require assertions: optimized Python is not supported.')
R=Path(__file__).resolve().parents[1]
def bases(d,cols=(),span=(0,)):
    if len(cols)==d:
        yield cols;return
    for v in range(1,1<<d):
        if v in span:continue
        yield from bases(d,cols+(v,),span+tuple(x^v for x in span))
def main():
    start=time.monotonic();rows=[]
    for d in range(1,5):
        n=1<<d;hist=Counter();gl=0
        for cols in bases(d):
            gl+=1;A=[0]*n
            for x in range(n):
                for j,v in enumerate(cols):
                    if x>>j&1:A[x]^=v
            for u in range(n):
                unseen=(1<<n)-1;c=0
                while unseen:
                    x=(unseen&-unseen).bit_length()-1;c+=1
                    while unseen>>x&1:
                        unseen^=1<<x;x=A[x]^u
                hist[c]+=1
        size=sum(hist.values());expected=(1<<d)
        for i in range(d):expected*=n-(1<<i)
        if size!=expected:raise ValueError('group coverage')
        counts={}
        for colours in [514,1703]:
            numerator=sum(k*colours**c for c,k in hist.items())
            if numerator%size:raise ValueError('nonintegral Burnside')
            counts[str(colours)]=numerator//size
            if d<=2 and counts[str(colours)]!=comb(colours+n-1,n):raise ValueError('symmetric-group crosscheck')
        rows.append({'d':d,'order':20*n,'gl':gl,'agl':size,'cycle_histogram':dict(sorted(hist.items())),'bounds':counts})
    def ord2(m):
        k=1;x=2%m
        while x!=1:k+=1;x=2*x%m
        return k
    N=11**2*41**2
    example={'N':N,'radical':451,'ord11':ord2(11),'ord41':ord2(41),'ord451':ord2(451),'q':2**20,'forbidden_upper':3*(N-1),'large_order':N*2**20,'old_construction_exponent':ord2(11)+ord2(41),'new_exponent':ord2(451)}
    threshold=260*Fraction(15318,1000)**3
    out={'groups':rows,'crt_example':example,'threshold_exact_fraction':str(threshold),'threshold_decimal':str(float(threshold)),'seconds':time.monotonic()-start}
    (R/'results/burnside_and_arithmetic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
