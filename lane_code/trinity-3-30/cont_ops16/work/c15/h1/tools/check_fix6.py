"""Run the requested CPU suite serially, retaining prior evidence without deletion."""
import ast,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parents[1];out=H/'evidence/fix6';out.mkdir(exist_ok=True)
retained=H/'evidence/fix6_before/outputs';retained.mkdir(exist_ok=True)
for n in ('derivation','staging_test','stop_bridge','fix1_tests','review/out','review/gate','fix4_sealed_modes','fix4_listing','fix5_gate','fix5_patch'):
 p=H/'evidence'/n
 if p.exists():
  dst=retained/n;dst.parent.mkdir(parents=True,exist_ok=True);p.rename(dst)
py='/scratch/jjyeung/envs/p1cpu/bin/python'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
cases=[('test_derivation',['tests/test_derivation.py']),('test_gate_binding',['tests/test_gate_binding.py']),('test_staging',['tests/test_staging.py']),('fallback',['tests/run_fallback.py','fallback_fix6']),('test_stop_bridge',['tests/test_stop_bridge.py']),('test_fix1',['tests/test_fix1.py']),('test_visible_names',['tests/test_visible_names.py']),('test_sealed_modes',['tests/test_sealed_modes.py']),('test_runtime_inventory',['tests/test_runtime_inventory.py']),('test_gate_sandbox',['tests/test_gate_sandbox.py']),('test_gate_patch',['tests/test_gate_patch.py']),('test_config_patch',['tests/test_config_patch.py'])]
cases += [(n,['tests/review/'+n+'.py']) for n in ('rv_mut','rv_g_a2','rv_gate','rv_g_fx')]
results=[]
for name,args in cases:
 with (out/(name+'.log')).open('w') as log:r=subprocess.run([py,'-B',*args],cwd=H,env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append(dict(name=name,status='PASS' if r.returncode==0 else 'FAIL',exit=r.returncode))
 (out/'tests.json').write_text(json.dumps(results,indent=2)+'\n');print(name,results[-1]['status'],flush=True)
for p in (H/'tests/review').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
subprocess.run(['/bin/bash','-n',str(H/'tests/RERUN_CHAIN.sh')],check=True)
print('Review harness syntax PASS; distributed harness not executed.',flush=True)
sys.exit(any(r['exit'] for r in results))
