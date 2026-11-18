from pathlib import Path
import subprocess,os,json
W=Path(__file__).resolve().parent;env=dict(os.environ,PATH='/usr/bin:/bin',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(W/'tmp'))
for k in ('b1','b2'):
 for suite,name in [('tests/test_package.py','package'),('tests/test_constraints.py','constraints'),('work/test_sequence.py','sequence'),('work/test_operator_memory.py','memory')]+([('work/test_cpu_helper.py','cpu_helper')] if k=='b2' else [])+([('test_tower_pair.py','tower_pair'),('test_b1_report.py','return_stop')] if k=='b1' else []):
  with (W/'out'/k/('base_'+name+'.log')).open('w') as f:
   r=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B','run_suite.py','verify/'+k+'/'+suite,'out/'+k+'/base_'+name+'_result.json'],env=env,stdout=f,stderr=subprocess.STDOUT)
  print(k,name,r.returncode,flush=True)
 with (W/'out'/k/'base_guard.log').open('w') as f:
  r=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B','bundle_regression.py','verify/'+k],env=env,stdout=f,stderr=subprocess.STDOUT)
 (W/'out'/k/'base_guard_result.json').write_bytes((W/'verify'/k/'tests_guard_result.json').read_bytes())
 print(k,'guard',r.returncode,flush=True)
