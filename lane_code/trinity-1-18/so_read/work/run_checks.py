"""Run small CPU checks sequentially, retaining exact output and resource usage."""
import ast
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

L=Path('/scratch/jjyeung/orch_n30/so_read')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
out=L/'out/checks';out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'))
results=[]
for name,path in [('cache','work/src/b/tests/test_read_cache.py'),
                  ('journal','work/src/h1eval/tests/test_read_journal.py'),
                  ('kit','out/kit_parity50/test_compare.py')]:
    command=[sys.executable,'-I','-s','-B',str(L/path)]
    result=subprocess.run(command,env=env,cwd=L,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/(name+'.txt')).write_text(result.stdout)
    results.append(dict(name=name,command=command,returncode=result.returncode,output=name+'.txt'))
    assert result.returncode==0,result.stdout
    print(name+': '+result.stdout.strip().splitlines()[-1])

for p in (L/'work/src').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in (L/'out/kit_parity50').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
subprocess.run(['bash','-n',str(L/'out/kit_parity50/array_preempt.template.sh')],check=True)
for command in ([sys.executable,'-I','-s','-B',str(L/'out/kit_parity50/run.py'),
                 str(L/'out/kit_parity50/config.example.json'),'--out',str(L/'work/not-run')],
                [sys.executable,'-I','-s','-B',str(L/'work/src/h1eval/h10/array_worker.py'),
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
(out/'RESULTS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'},sort_keys=True))
