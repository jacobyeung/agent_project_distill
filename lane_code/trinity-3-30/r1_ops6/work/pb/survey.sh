#!/bin/bash
set -euo pipefail
# Read-only; safe for bash -s on the login node. No downloads or archive hashing.
export PYTHONDONTWRITEBYTECODE=1
exec timeout --signal=TERM --kill-after=3s 110s python3 -B - <<'PY'
import json, os, shutil, signal, subprocess, sys, tarfile
from pathlib import Path
P=Path('/project/community/jjyeung'); O=P/'okh7'
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'; AL=AS.replace('/scratch/','/lustre/',1)
X=AS+'/ap/8865619b'
def show(v): print(json.dumps(v,sort_keys=True),flush=True)
def info(p):
    p=Path(p)
    try:
        s=p.stat(); show(dict(path=str(p),bytes=s.st_size,exists=True,readable=os.access(p,os.R_OK),link=p.is_symlink()))
    except OSError: show(dict(path=str(p),exists=False))
def load(p):
    p=Path(p)
    if p.stat().st_size>16<<20: raise ValueError('record over limit')
    return json.loads(p.read_text())
def headers(p,wanted=None):
    signal.alarm(8)
    try:
        with tarfile.open(p) as t:
            for i,m in enumerate(t):
                if wanted is None and i<24 or wanted and m.name.lstrip('./') in wanted:
                    show(dict(archive=str(p),member=m.name,bytes=m.size,link=m.linkname))
                if i>=20000 or wanted is None and i>=23: break
    except Exception as e: show(dict(question='Confirm archive layout or requested members',error=type(e).__name__))
    finally: signal.alarm(0)
def expired(sig,frame): raise TimeoutError()
signal.signal(signal.SIGALRM,expired)
show(dict(python=sys.version,requires='Python >= 3.9 for pbjob.sh'))
show(dict(note='No SDK command: it can write token databases even for metadata reads. The job copies SDK state before use.'))
for exe in ('python3','gcloud','squeue','sinfo','timeout','ionice'):
    show(dict(executable=exe,path=shutil.which(exe)))
info(P/'cp4tk_rt/kit/bwrap'); info('/usr/bin/time')
for f in ('active_config','credentials.db','access_tokens.db','application_default_credentials.json','configurations'):
    info(P/'gcloud'/f)
for run,step,key in [('673bc60f',200,'x_69d2930d'),('6ed2c7aa',600,'x_ee227714')]:
    kh=O/key; rr=kh/'runs'/run; rs=O/'r'/run
    show(dict(run=run,step=step,kh=str(kh)))
    for f in ('A.tar','A.json','A.sha256'):
        info(rs/f)
        if f!='A.tar' and (rs/f).is_file(): show(dict(record=f,value=(load(rs/f) if f.endswith('.json') else (rs/f).read_text().strip())))
    marker=kh/'o'/('gcs_'+run+'_m'+str(step)+'.done'); info(marker)
    if marker.is_file(): show(dict(marker=marker.read_text().strip()))
    for f in ['k/0.json','k/launch.json','b/c.sh'] : info(kh/f)
    try:
        cur=load(kh/'k/0.json')
        for k in ('venv','small','closure'):
            show(dict(source_kind=k,record=cur[k])); info(cur[k]['file'])
        if run=='673bc60f': headers(cur['venv']['file'])
        b=load(rr/'binding.json'); pp=b['preparation']['path']
        require_prefix=X+'/runs/'+run+'/'
        if not pp.startswith(require_prefix): raise ValueError('preparation prefix')
        lp=rr/pp[len(require_prefix):]; cfg=load(lp.parent.parent/'config.json'); prep=load(lp)
        show(dict(config=str(lp.parent.parent/'config.json'),preparation=str(lp),trainer_commit=b['trainer_commit']))
        need=[*cfg['streams'].values(),*[s['indices'] for s in prep['streams'].values() if s.get('indices')]]
        if prep.get('model'): need.append(prep['model'])
        small=[]
        for pin in need:
            path=pin['path']; candidates=[]
            if path.startswith(require_prefix): candidates=[rr/path[len(require_prefix):]]
            else:
                if path.startswith(X+'/'): candidates.append(kh/path[len(X)+1:])
                rel=path.removeprefix(AS+'/').removeprefix(AL+'/')
                candidates.append(kh/'in_small'/rel)
            extras=[e for e in cur.get('extra',[]) if e['dest'].replace(AL,AS)==path.replace(AL,AS)]
            show(dict(pin=pin,candidates=[str(c) for c in candidates],extra=extras))
            for c in candidates: info(c)
            for e in extras:
                for f in e['parts']: info(f)
            if not any(c.is_file() for c in candidates) and not extras:
                rel=path.removeprefix(AS+'/').removeprefix(AL+'/')
                small.extend([(a+'/'+rel).lstrip('/') for a in (AS,AL)])
        if small:
            show(dict(question='Confirm each unresolved pin is present in the following archive members; otherwise supply its exact persisted source',members=small))
            headers(cur['small']['file'],set(small))
    except Exception as e:
        show(dict(question='Pool metadata unavailable: confirm closure sources from A.tar on the compute node',run=run,error=type(e).__name__))
info(O/'h_6ed2c7aa/q2_67f8baf1.zip')
for args in [['sinfo','-h','-N','-p','preempt','-o','%N %t %c %m %d %G'],
             ['squeue','-h','-u',str(os.getuid()),'-o','%i %j %T %M']]:
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=12)
        show(dict(command=args,rc=r.returncode,output=r.stdout[:14000],error=r.stderr[:500]))
    except Exception as e: show(dict(command=args,error=type(e).__name__))
show(dict(questions=[
 'sinfo %d is configured TmpDisk in MB, not live free space. Which preempt nodes have enough local /tmp? The job checks df-equivalent free bytes before staging.',
 'Confirm the venv archive begins with rwtrain_torch211_cu129/, includes site-packages and needs only the node system Python/libraries. External links or extra runtime dependencies must be supplied explicitly.',
 'Confirm preempt accepts --gres=none, 16 CPUs and 192G, and that the account can use bwrap user namespaces.',
 'Confirm four part00..03-of-04 objects exist and credentials permit reads; the job verifies their joined size and SHA against the marker.',
 'Confirm the step-600 A slot and export marker are published after the source job leaves the queue.']))
PY
