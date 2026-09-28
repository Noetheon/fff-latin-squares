"""Direct binary quotient-freeness certificates; no order-10 exclusion imported."""
from core_checks import *
import hashlib

def select_independent_cells(L):
    n=len(L);piv={};picked=[]
    for r in range(n):
        for c in range(n):
            x=(1<<r)|(1<<(n+c))|(1<<(2*n+L[r][c]))
            while x:
                k=x.bit_length()-1
                if k not in piv:piv[k]=x;picked.append(r*n+c);break
                x^=piv[k]
    return picked

def check_minor(L,cells):
    """Separate orientation: explicit 0/1 row elimination on a 58x58 minor.
    Delete the final column-line and symbol-line; keep all row-lines.
    """
    n=len(L);lines=list(range(n))+list(range(n,2*n-1))+list(range(2*n,3*n-1))
    A=[]
    for lab in lines:
        row=[]
        for x in cells:
            r,c=divmod(x,n)
            row.append(int(lab in (r,n+c,2*n+L[r][c])))
        A.append(row)
    assert len(A)==len(cells)==3*n-2
    for j in range(len(cells)):
        piv=next((r for r in range(j,len(A)) if A[r][j]),None)
        assert piv is not None,'Certificate minor is singular'
        A[j],A[piv]=A[piv],A[j]
        for r in range(j+1,len(A)):
            if A[r][j]:
                for c in range(j,len(A)):A[r][c]^=A[j][c]
    return True

def main():
    L=sts_loop();cy=cycles([inverse(L[0])[s] for s in L[19]])
    records=[]
    for mask in range(1024):
        K=[row[:] for row in L]
        for i,C in enumerate(cy):
            if mask>>i&1:
                for c in C:K[19][c],K[0][c]=K[0][c],K[19][c]
        # Complete second scanner for every mask, not only samples.
        assert scan_alternating_graph(K)=='FFF'
        cells=select_independent_cells(K);assert check_minor(K,cells)
        records.append({'kind':'STS19_row_trade','mask':mask,'independent_cell_columns':cells,
           'table_sha256':hashlib.sha256(bytes(x for r in K for x in r)).hexdigest()})
    for a in [2,8]:
        K=affine(19,a);assert scan_alternating_graph(K)=='FFF'
        cells=select_independent_cells(K);assert check_minor(K,cells)
        (ROOT/'inputs'/f'Q19_{a}.json').write_text(json.dumps(K))
        records.append({'kind':'Q19','a':a,'independent_cell_columns':cells,
           'table_sha256':hashlib.sha256(bytes(x for r in K for x in r)).hexdigest()})
    out={'tables':len(records),'binary_rank':58,'determinant_mod2':1,
       'minor_rows':'all 20 row lines, column lines 0..18, symbol lines 0..18',
       'dependency_on_C157':False,'second_graph_scanner_all_tables':'FFF',
       'second_graph_scanner_pairs':len(records)*570,'records':records}
    (ROOT/'results'/'order20_rank_certificates.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
if __name__=='__main__':main()
