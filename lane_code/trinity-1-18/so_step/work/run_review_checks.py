"""Serialize every local test; preserve exact commands, stdout/stderr and exit status."""
import datetime
import os
from pathlib import Path
import shlex
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
 MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',SO_TEST_TREE=str(ROOT/'work/tree'))
if hasattr(os,'sched_getaffinity'):
 os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:8])
checks=[
 ('review1_final_units.txt',['work/run_cpu_tests.py','--local-only','tests.test_so_prefetch','tests.test_so_cache','tests.test_so_metrics','tests.test_so_joint','tests.test_so_review']),
 ('review1_final_parity.txt',['work/test_local_parity.py']),
 ('review1_final_kits.txt',['work/test_kits.py']),
 ('review1_final_kit_regressions.txt',['work/test_review_kits.py']),
 ('review1_final_utilities.txt',['work/test_kit_utilities.py']),
 ('review1_final_measurements.txt',['work/recheck_measurements.py']),
 ('review1_final_source_audit.txt',['work/audit_review_sources.py']),
]
for name,args in checks:
 command=['nice','-n','10',sys.executable,'-I','-s','-B',*args]
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 print(stamp+' START '+name,flush=True)
 result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 text='$ '+shlex.join(command)+'\n'+result.stdout+'\nEXIT='+str(result.returncode)+'\n'
 (ROOT/'out/evidence'/name).write_text(text)
 print(name+' EXIT='+str(result.returncode),flush=True)
 if result.returncode: raise SystemExit(result.returncode)
print('ALL_LOCAL_CHECKS_PASS',flush=True)
