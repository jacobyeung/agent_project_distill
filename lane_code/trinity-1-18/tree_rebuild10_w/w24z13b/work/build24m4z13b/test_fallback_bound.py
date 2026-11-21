import os,sys,time,json,subprocess,signal,resource
from pathlib import Path
J=Path(__file__).resolve().parents[2];W=J/'work/build24m4z13b'
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
case=W/'fallback_bound';case.mkdir();local=case/'tmp';local.mkdir();x=W/'x';job='89000'
pub=x/'o'/job;pub.mkdir(parents=True);os.mkfifo(pub/'j2.fallback.log',0o600)
s=(J/'out/jn5.sh').read_text().replace('X="/project/community/jjyeung/okh7/x_22c714e1"','X="'+str(x)+'"')
(case/'run.sh').write_text(s)
env=dict(os.environ,PATH=str(W/'bin')+':/usr/bin:/bin',SLURM_JOB_ID=job,SLURM_TMPDIR=str(local),
         TMPDIR=str(W/'tmp'),T_CASE=str(case),T_X=str(x),T_EVENTS=str(case/'events.jsonl'),T_GPUS='0',
         T_MODE='gpu',T_PFAIL='fail',T_SIGNAL='',T_FINAL_SIGNAL='',T_TICKS='0',
         OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
t=time.monotonic()
with (case/'console.log').open('wb') as f:
    p=subprocess.Popen(['bash',str(case/'run.sh')],env=env,stdout=f,stderr=f,start_new_session=True)
    rc=p.wait(timeout=18)
elapsed=time.monotonic()-t;events=[json.loads(l) for l in (case/'events.jsonl').read_text().splitlines()]
assert rc==3 and 15<elapsed<18,(rc,elapsed)
assert sum(e['event']=='publish.once' for e in events)==1
assert [e['args'][:2] for e in events if e['event']=='timeout']==[['--signal=KILL','120s'],['--signal=KILL','15s']]
result=dict(PASS=True,status=rc,seconds=round(elapsed,3),once=1,published=False,reason='fallback target intentionally blocks; status preserved within 15-second fallback bound')
(case/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
