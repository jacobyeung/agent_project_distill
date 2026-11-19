"""Capture exact CPU validation outputs with bounded cores and local caches."""
import json,os,re,subprocess,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round4'
K=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else W/'kit'
label=sys.argv[2] if len(sys.argv)>2 else 'final'
# Six CPUs leave room for the two single-thread header diagnostics when active.
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:6])
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
 OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',READ228_TEST_WORK=str(W/(label+'_fixtures')))
for key,suffix in [('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),('MPLCONFIGDIR','mpl')]:
 p=W/(label+'_cache')/suffix;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
cpu='/scratch/jjyeung/envs/p1cpu/bin/python'
cases=['kit','review','prepare','bootstrap36','review2','stage2','review3','target_refusal']
if label=='interim':cases=cases[:-1]
records=[]
if len(sys.argv)>3:
 start=cases.index(sys.argv[3]);cases=cases[start:]
 records=json.loads((W/'checks'/(label+'_RUNS.json')).read_text())[:start]
 assert all(r['returncode']==0 for r in records)
for case in cases:
 now=subprocess.check_output(['date','-u'],universal_newlines=True).strip();print(now,flush=True)
 py='/usr/bin/python3' if case=='bootstrap36' else cpu
 flags=['-I','-S' if case in ('review3','target_refusal') else '-s','-B']
 command=['nice','-n','10','/usr/bin/time','-v',py]+flags+[str(K/'tests'/('test_'+case+'.py'))]
 path=W/'checks'/(label+'_'+case+'.txt')
 with path.open('w') as stream:r=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT)
 text=path.read_text();match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\n([^\n]+)',text)
 rss=re.search(r'Maximum resident set size \(kbytes\): (\d+)',text)
 row=dict(case=case,utc=now,argv=command,returncode=r.returncode,output=path.name,
  summary=match.group(0) if match else None,maxrss_kb=int(rss.group(1)) if rss else None)
 records.append(row);print(json.dumps(row,sort_keys=True),flush=True)
 (W/'checks'/(label+'_RUNS.json')).write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
 if r.returncode:raise SystemExit(1)
