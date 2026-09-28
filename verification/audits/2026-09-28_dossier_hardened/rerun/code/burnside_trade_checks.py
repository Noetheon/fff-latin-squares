from core_checks import *

def burnside():
    out=[]
    for d in range(1,5):
        n=1<<d; hist=Counter(); gl=0
        for images in product(range(1,n),repeat=d):
            if rank2(images)!=d: continue
            gl+=1
            linear=[0]*n
            for x in range(1,n):
                bit=x&-x;linear[x]=linear[x^bit]^images[bit.bit_length()-1]
            for u in range(n):
                hist[len(cycles([y^u for y in linear]))]+=1
        gsize=sum(hist.values());total=sum(num*514**c for c,num in hist.items());assert total%gsize==0
        out.append({'d':d,'GL_size':gl,'AGL_size':gsize,'cycle_count_histogram':dict(sorted(hist.items())), 'T_d_514':total//gsize})
    (ROOT/'results'/'burnside.json').write_text(json.dumps(out,indent=2));print('BURNSIDE',json.dumps(out),flush=True)

def trade(a=19,b=0):
    L=sts_loop(); p=[inverse(L[b])[x] for x in L[a]]; cy=cycles(p)
    assert len(cy)==10 and all(len(C)==2 for C in cy)
    spectra={};patterns=Counter(); ranks=Counter();Is=[];rows=[]
    for mask in range(1024):
        K=[r[:] for r in L]
        for bit,C in enumerate(cy):
            if mask>>bit&1:
                for c in C: K[a][c],K[b][c]=K[b][c],K[a][c]
        s=scan(K);patterns[s['pattern']]+=1;Is.append(s['intercalates']);ranks[line_rank2(K)]+=1
        spectra.setdefault(s['spectrum'],[]).append(mask)
        if mask<16 or mask in [341,682,1023]:
            assert scan_alternating_graph(K)==s['pattern']
        rows.append({'mask':mask,'I':s['intercalates'],'pattern':s['pattern']})
    out={'row_pair':[a,b],'patterns':dict(patterns),'distinct_spectra':len(spectra),
       'spectrum_multiplicities':dict(Counter(map(len,spectra.values()))),'all_collisions_complementary':all(len(v)==2 and v[0]^v[1]==1023 for v in spectra.values()),
       'intercalate_range':[min(Is),max(Is)],'binary_line_rank':dict(ranks)}
    controls=[]
    for a0 in [2,8,10,12,18]:
        K=affine(19,a0);s=scan(K);controls.append({'parameter':a0,'pattern':s['pattern'],'I':s['intercalates'],'outside_trade_spectra':s['spectrum'] not in spectra,'binary_rank':line_rank2(K)})
    out['affine_controls']=controls
    (ROOT/'results'/f'trade_{a}_{b}.json').write_text(json.dumps(out,indent=2));print('TRADE',json.dumps(out),flush=True)
if __name__=='__main__':
    burnside();trade()
