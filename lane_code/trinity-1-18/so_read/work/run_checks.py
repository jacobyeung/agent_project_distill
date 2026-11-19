"""Run small CPU checks sequentially, retaining exact output and resource usage."""
import ast
import hashlib
import re
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

L=Path('/scratch/jjyeung/orch_n30/so_read')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
out=L/'out/checks';out.mkdir(parents=True,exist_ok=True)
# Pins are derived from the delivered files and cross-checked with MANIFEST at packaging.
pins={str(p.relative_to(L/'work/src')):hashlib.sha256(p.read_bytes()).hexdigest()
      for p in sorted((L/'work/src/u0').rglob('*')) if p.is_file()}
(L/'out/kit_parity50/EXTENSION_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
env=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'),
         READ_MEMORY_RECEIPT=str(out/'MEMORY.json'),READ_OFF_RECEIPT=str(out/'OFF_BYTES.json'))
results=[]
for name,path in [('cache','work/src/u0/tests/test_read_cache.py'),
                  ('journal','work/src/u0/tests/test_read_journal.py'),
                  ('off','work/src/u0/tests/test_off.py'),
                  ('public','work/src/u0/tests/test_public.py'),
                  ('round1','work/src/u0/tests/test_round1.py'),
                  ('round2','work/src/u0/tests/test_round2.py'),
                  ('kit','out/kit_parity50/test_compare.py'),
                  ('kit_launch','out/kit_parity50/test_run.py')]:
    command=[sys.executable,'-I','-s','-B',str(L/path)]
    result=subprocess.run(command,env=env,cwd=L,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/(name+'.txt')).write_text(result.stdout)
    results.append(dict(name=name,command=command,returncode=result.returncode,output=name+'.txt'))
    assert result.returncode==0,result.stdout
    print(name+': '+result.stdout.strip().splitlines()[-1])

command=[sys.executable,'-I','-s','-B',str(L/'work/src/u0/tests/test_round1.py')]
result=subprocess.run(command,env=dict(env,READ_REVIEW_BEFORE='1'),cwd=L,
                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(out/'round1_before.txt').write_text(result.stdout)
assert result.returncode==1 and 'FAILED (failures=8)' in result.stdout,result.stdout
print('PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.')
command=[sys.executable,'-I','-s','-B',str(L/'work/src/u0/tests/test_round2.py')]
result=subprocess.run(command,env=dict(env,READ_ROUND2_BEFORE='1'),cwd=L,
                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(out/'round2_before.txt').write_text(result.stdout)
assert result.returncode==1 and 'FAILED (failures=13, errors=1)' in result.stdout,result.stdout
print('PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).')
assert (L/'work/src/u0/a9.py').read_bytes()==(L/'out/kit_parity50/a9.py').read_bytes()
assert (L/'work/src/u0/a10.py').read_bytes()==(L/'out/kit_parity50/compare.py').read_bytes()
assert (L/'work/src/u0/tests/test_compare.py').read_bytes()==(L/'out/kit_parity50/test_compare.py').read_bytes()
assert (L/'work/src/u0/tests/u0.json').read_bytes()==(L/'out/kit_parity50/sample50.json').read_bytes()
assert (L/'work/src/u0/tests/u1.json').read_bytes()==(L/'out/kit_parity50/array_config.example.json').read_bytes()

for p in (L/'work/src').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in (L/'out/kit_parity50').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
subprocess.run(['bash','-n',str(L/'out/kit_parity50/array_preempt.template.sh')],check=True)
for command in ([sys.executable,'-I','-s','-B',str(L/'out/kit_parity50/run.py'),
                 str(L/'out/kit_parity50/config.example.json'),'--out',str(L/'work/not-run')],
                [sys.executable,'-I','-s','-B',str(L/'work/src/u0/a7.py'),
                 str(L/'out/kit_parity50/array_config.example.json')]):
    result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    assert result.returncode==2 and ('OFF' in result.stdout or 'requires --enable-gpu' in result.stdout),result.stdout
assert not (L/'work/not-run').exists()
print('PASS: Python syntax, shell syntax, and default-off execution guards.')
import torch
import transformers
torch.set_num_threads(8)
report=dict(results=results,torch=torch.__version__,transformers=transformers.__version__,
            cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),torch_threads=torch.get_num_threads(),
            max_child_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,
            workspace_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))
assert report['workspace_bytes']<3*1024**3
assert report['max_child_rss_bytes']<30*1024**3
(out/'RESULTS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'},sort_keys=True))

with (L/'work/STATUS.md').open('a') as f:
    stamp=subprocess.check_output(['date','-u'],text=True)
    f.write(stamp+'All workspace suites and both reviewed-baseline regressions completed; exact outputs in out/checks.\n')
