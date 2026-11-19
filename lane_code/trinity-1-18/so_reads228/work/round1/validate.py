"""Capture exact, serialized CPU test outputs and resource measurements under work/."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round1'
K=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else W/'kit'
label=sys.argv[2] if len(sys.argv)>2 else 'final'
logs=W/'checks';logs.mkdir(exist_ok=True)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',
    READ228_TEST_WORK=str(W/(label+'_fixtures')))
cache=W/(label+'_cache');cache.mkdir(exist_ok=True)
for key,suffix in [('HOME','home'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),
                   ('MPLCONFIGDIR','mpl'),('CUDA_CACHE_PATH','nv'),('TMPDIR','tmp')]:
    path=cache/suffix;path.mkdir(exist_ok=True);env[key]=str(path)
cpu='/scratch/jjyeung/envs/p1cpu/bin/python'
cases=[('base',cpu,'test_kit.py',0,{}),('review_after',cpu,'test_review.py',0,{}),
       ('prepare',cpu,'test_prepare.py',0,{}),('bootstrap36','/usr/bin/python3','test_bootstrap36.py',0,{})]
if label=='final':cases.insert(0,('review_before',cpu,'test_review.py',1,{'READ228_REVIEW_KIT':str(L/'out_round0')}))
results=[]
for name,python,test,expected,extra in cases:
    now=subprocess.check_output(['date','-u'],text=True).strip();print(now,flush=True)
    output=logs/(label+'_'+name+'.txt')
    command=['nice','-n','10','/usr/bin/time','-v',python,'-I','-s','-B',str(K/'tests'/test)]
    with output.open('w') as stream:
        got=subprocess.run(command,env=dict(env,**extra),stdout=stream,stderr=subprocess.STDOUT,cwd=L)
    text=output.read_text()
    summary=re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\n([^\n]+)',text)
    row=dict(name=name,utc=now,argv=command,env_overrides={k:v for k,v in dict(env,**extra).items() if os.environ.get(k)!=v},
        returncode=got.returncode,expected_returncode=expected,output=str(output),
        test_summary=summary.group(0) if summary else None)
    for key,pattern in [('maxrss_kb',r'Maximum resident set size \(kbytes\): (\d+)'),
                        ('wall_time',r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([^\n]+)')]:
        match=re.search(pattern,text);row[key]=match.group(1) if match else None
    results.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    if got.returncode!=expected:break
(logs/(label+'_RUNS.json')).write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
if len(results)!=len(cases) or any(r['returncode']!=r['expected_returncode'] for r in results):raise SystemExit(1)
