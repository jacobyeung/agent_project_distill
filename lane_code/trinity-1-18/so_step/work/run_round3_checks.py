"""Run the authorized local gates serially and retain exact commands and outputs."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
    C1_CPU_PREFETCH='0',C1_DECODED_CACHE_MIB='0',C1_BATCH_METRICS='0',C1_CPU_PREFETCH_FALLBACK='0',
    SO_TEST_TREE=str(ROOT/'work/b21_final/work/tree_r1'))
os.sched_setaffinity(0, range(8))
units=['tests.test_carrier_c1_run','tests.test_so_prefetch','tests.test_so_cache','tests.test_so_metrics',
       'tests.test_so_review','tests.test_so_round2','tests.test_so_round3','tests.test_so_joint']
existing=['tests.test_gx_carrier','tests.test_gf1_cache','tests.test_gf1_contracts',
          'tests.test_gx_s6','tests.test_startup_receipt','tests.test_carrier_c1_final']
related=['tests.test_gx_s7','tests.test_gx_s8','tests.test_carrier_c1_t0.ExportLeg',
         'tests.test_pose_samples','tests.test_carrier_c1_data','tests.test_batch_options']
failures=lambda text:re.findall(r'^(?:ERROR|FAIL): (.*)$',text,re.M)
suites=[('units',['work/run_cpu_tests.py','--local-only',*units]),
        ('existing',['work/run_cpu_tests.py','--local-only',*existing]),
        ('related',['work/run_cpu_tests.py','--local-only',*related]),
        ('parity',['work/test_local_parity.py'])]
suites += [(kind,['work/'+filename]) for kind,filename in (
    ('kits','test_kits.py'),('review_kits','test_review_kits.py'),('utilities','test_kit_utilities.py'),
    ('round2_kits','test_round2_kits.py'),('round3_kits','test_round3_kits.py'))]
checks=[]
for kind,args in suites:
    stamp=subprocess.check_output(['date','-u'],text=True).strip()
    command=['nice','-n','10','taskset','-c','0-7',sys.executable,'-I','-s','-B',*args]
    print(stamp+' START '+kind,flush=True)
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    accepted=result.returncode==0
    if kind in ('existing','related'):
        expected=failures((ROOT/'out/evidence'/('round2_baseline_'+kind+'.txt')).read_text())
        accepted=result.returncode==1 and failures(result.stdout)==expected
    name='round3_'+kind+'.txt'
    (ROOT/'out/evidence'/name).write_text(stamp+'\n$ SO_TEST_TREE='+os.environ['SO_TEST_TREE']+' '+shlex.join(command)+'\n'+result.stdout+'\nEXIT='+str(result.returncode)+'\n')
    checks.append(dict(kind=kind,exit=result.returncode,accepted=accepted,log=name,
                       summary=re.findall(r'^(?:Ran .*|OK.*|FAILED.*)$',result.stdout,re.M)))
    (ROOT/'out/evidence/round3_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(kind+' EXIT='+str(result.returncode)+' ACCEPTED='+str(accepted),flush=True)
    if not accepted: raise SystemExit(1)
print('ROUND3_LOCAL_GATES_PASS_WITH_EIGHT_DECLARED_BASELINE_FAILURES',flush=True)
