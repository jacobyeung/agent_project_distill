"""Serialize all CPU checks and retain exact output, argv, environment and RSS."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round3'
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
cases=[(name,'test_'+test+'.py',0,{}) for name,test in
       [('base','kit'),('review1','review'),('prepare','prepare'),('bootstrap','bootstrap36'),
        ('review2','review2'),('stage2','stage2'),('review3','review3')]]
if label=='final':
    cases=[('review3_before','test_review3.py',1,{'READ228_REVIEW3_KIT':str(L/'out_round2')})]+cases
results=[]
for name,test,expected,extra in cases:
    now=subprocess.check_output(['date','-u'],text=True).strip();print(now,flush=True)
    output=logs/(label+'_'+name+'.txt')
    command=['nice','-n','10','/usr/bin/time','-v',cpu,'-I','-S' if test=='test_review3.py' else '-s','-B',str(K/'tests'/test)]
    with output.open('w') as stream:
        got=subprocess.run(command,env=dict(env,**extra),stdout=stream,stderr=subprocess.STDOUT,cwd=L)
    text=output.read_text();summary=re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\n([^\n]+)',text)
    row=dict(name=name,utc=now,argv=command,env_overrides={k:v for k,v in dict(env,**extra).items() if os.environ.get(k)!=v},
        returncode=got.returncode,expected_returncode=expected,output=str(output),test_summary=summary.group(0) if summary else None)
    match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',text);row['maxrss_kb']=int(match.group(1)) if match else None
    results.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    if got.returncode!=expected:break
(logs/(label+'_RUNS.json')).write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
if len(results)!=len(cases) or any(r['returncode']!=r['expected_returncode'] for r in results):raise SystemExit(1)
