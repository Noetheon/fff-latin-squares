import subprocess,time,json,sys,os
from pathlib import Path
if sys.flags.optimize:
 raise RuntimeError('Audit checks require assertions: optimized Python is not supported.')
p=Path(__file__).resolve().parent
scripts=['core_checks','burnside_trade_checks','field_checks','norm_and_witness_checks','flag_and_smallorder_checks','order8_subset_checks','order20_rank_certificates','formulation_scope_checks','check_report_values']
r=[]
for s in scripts:
 t=time.monotonic()
 with (p/'results'/f'{s}.log').open('w') as f:
  v=subprocess.run([sys.executable,'-B','code/'+s+'.py'],cwd=p,stdout=f,stderr=subprocess.STDOUT,
                   timeout=600,env=dict(os.environ,PYTHONOPTIMIZE='0',PYTHONDONTWRITEBYTECODE='1'))
 r.append({'script':s,'returncode':v.returncode,'seconds':time.monotonic()-t});print(r[-1],flush=True)
 (p/'results'/'execution_log.json').write_text(json.dumps(r,indent=2))
 if v.returncode: raise SystemExit(v.returncode)
