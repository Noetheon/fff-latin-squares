"""Fail on disagreement between freshly computed outputs and reviewed numeric claims."""
from core_checks import *
from formulation_scope_checks import partitions

def get(name):return json.loads((ROOT/'results'/name).read_text())
def main():
    sm=get('smallorders_and_flags.json')['smallorders']
    assert sm['2']['total']==1 and sm['4']['total']==4
    assert sm['6']=={'total':9408,'patterns':{'TTT':6600,'TFF':936,'FTF':936,'FFT':936}}
    a=get('order8_230_checks.json')
    assert a['tables']==230 and a['group_isotopy_histogram']=={'true':5,'false':225}
    assert a['binary_rank_histogram']=={'19':1,'20':10,'21':156,'22':63}
    assert a['subsquare_histogram']=={'28':1,'12':10,'4':156,'0':63}
    assert (a['total_flags'],a['total_components'])==(103040,9768)
    assert a['holonomy_values']==152 and a['holonomy_collision_histogram']=={'1':109,'2':22,'3':12,'4':4,'5':5}
    assert (a['local_signature_values'],a['local_signature_w6_values'],a['local_signature_t_values'],a['t_values'],a['I_t_values'])==(226,230,230,100,188)
    b=get('burnside.json')
    assert [x['T_d_514'] for x in b]==[132355,2942384005,3625556867870760586,73586711420426563009097417622853741216]
    t=get('trade_19_0.json')
    assert t['patterns']=={'FFF':1024} and t['distinct_spectra']==512 and t['all_collisions_complementary']
    assert t['intercalate_range']==[542,676] and t['binary_line_rank']=={'58':1024}
    r=get('order20_rank_certificates.json')
    assert r['tables']==1026 and r['binary_rank']==58 and r['dependency_on_C157'] is False
    assert get('norm_and_36.json')['prime_square']['implicit_returns_checked']==239580
    P=list(partitions(10,2));F=[p for p in P if all(x%2==0 for x in p)]
    Q=[p for p in P if sum(x%4==2 for x in p)%2==1]
    assert len(F)==7 and [p for p in Q if p not in F]==[(2,3,5)]
    palate={'f03':[768,384,384],'f05':[8832,3840,2496,2496],'f06':[2880,1152,864,864],
     'f12':[1920,1152,384,384],'f08':[21120,7680,6720,6720],'f13':[17280,9600,3840,3840],
     'f14':[21312,13056,4128,4128],'f09':[23040,7680,7680,7680],
     'f10':[55680,26880,14400,14400],'f15':[32896,6208,13344,13344]}
    assert all(x[0]==sum(x[1:]) for x in palate.values())
    out={'scope':'Only the explicit assertions in this script; not a universal manuscript-correctness flag.',
      'all_listed_comparisons_passed':True,'order10_even_cycle_types':[list(x) for x in F],
      'five_type_palette_count':math.comb(7,5),'cycle_parity_extra_type':[2,3,5],
      'palette_candidate_sums':palate,'corpus_size_without_order2':4+9408+230+135,'corpus_size_with_order2':1+4+9408+230+135}
    (ROOT/'results'/'report_value_checks.json').write_text(json.dumps(out,indent=2))
    print('PASS: explicitly listed numeric comparisons. No assertion of whole-manuscript correctness.')
if __name__=='__main__':main()
