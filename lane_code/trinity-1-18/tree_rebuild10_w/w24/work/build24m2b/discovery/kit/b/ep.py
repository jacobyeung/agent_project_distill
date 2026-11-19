"""Publish bounded screened diagnostics outside the job view."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import stat
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load, screen


def publish(kit, root, job, status):
    kit,root=Path(kit).resolve(),Path(root).resolve()
    if not job or not job.isascii() or not job.isdigit():raise ValueError('R1_EVIDENCE_JOB_INVALID')
    target=Path(load(kit/'k/p.json')['n_root'])/'o'/job
    if not target.is_absolute() or '..' in target.parts:raise ValueError('R1_EVIDENCE_TARGET_INVALID')
    if any(p.is_symlink() for p in (target,*target.parents)):raise ValueError('R1_EVIDENCE_TARGET_INVALID')
    if any((target.resolve()==p or p in target.resolve().parents) for p in (kit,root)):raise ValueError('R1_EVIDENCE_TARGET_INVALID')
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    policy,white=load(kit/'k/g.json'),load(kit/'b/wh.json')
    entries=[(n,root/n,300_000,'tail') for n in ('q.log','rooms.log','h.log','rv.log','t.log')]
    entries += [('r.log',root/'dr/q.log',300_000,'tail'),('q.steps',root/(job+'.steps'),100_000,'tail')]
    entries += [(n,root/p,100_000,'json') for n,p in (
        ('q0.json','p/q/RESULT.json'),('r0.json','p/r0.json'),('q1.json','dr/p/r0.json'),
        ('q2.json','p/q/host.json'),('RESULT.json','o/RESULT.json'))]
    selected=root/'routing_selection.json'
    if not selected.exists():selected=root/'p/routing_selection.json'
    entries += [('routing_selection.json',selected,2_000_000,'pin')]
    def clean(value):
        if isinstance(value,str):return screen(value,policy,white)
        if isinstance(value,list):return [clean(x) for x in value]
        if isinstance(value,dict):return {screen(str(k),policy,white):clean(v) for k,v in value.items()}
        return value
    payload={};errors=[]
    for name,p,limit,kind in entries:
        if not p.exists():continue
        if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode):errors.append(name+':unusable');continue
        with p.open('rb') as f:
            if kind=='tail':f.seek(max(0,p.stat().st_size-limit))
            raw=f.read(limit+1)
        if len(raw)>limit:errors.append(name+':too_large');continue
        if kind=='tail':raw=screen(raw.decode('utf-8',errors='replace'),policy,white).encode()[-limit:]
        elif kind=='json':
            try:raw=(json.dumps(clean(json.loads(raw)),sort_keys=True)+'\n').encode()
            except (ValueError,UnicodeError):errors.append(name+':invalid');continue
        else:
            try:json.loads(raw)
            except (ValueError,UnicodeError):errors.append(name+':invalid');continue
        if len(raw)>limit:errors.append(name+':too_large');continue
        payload[name]=raw
    discovery=load(kit/'BUILD.json').get('discovery',False)
    record=dict(returncode=int(status),files={n:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in payload.items()},errors=errors)
    if discovery:record.update(discovery=True,claims='nothing')
    payload['r1.json']=(json.dumps(record,sort_keys=True)+'\n').encode()
    if sum(map(len,payload.values()))>=5_000_000:raise ValueError('R1_EVIDENCE_TOO_LARGE')
    fd=os.open(target/'.l',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for name,raw in payload.items():
            tmp=target/(name+'.part')
            fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as f:f.write(raw)
            os.replace(tmp,target/name)
    publish_artifacts(target, root)
    return record


def publish_artifacts(target, root):
    base=root/'dr/p/q/selection'
    if not base.is_dir():base=root/'p/q/selection'
    paths=[base/name for name in ('receipt.json','materialization.json')]
    if not all(p.is_file() and not p.is_symlink() for p in paths):return
    if sum(p.stat().st_size for p in paths)>5_000_000:
        raise ValueError('R1_ROUTING_ARTIFACTS_TOO_LARGE')
    for p in paths:
        raw=p.read_bytes();json.loads(raw)
        fd=os.open(target/(p.name+'.part'),os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
        os.replace(target/(p.name+'.part'),target/p.name)
        print(p.name+' sha256='+hashlib.sha256(raw).hexdigest(),flush=True)


if __name__=='__main__':
    kit,root,job,status=sys.argv[1:5]
    if len(sys.argv)==6 and sys.argv[5]=='--loop':
        while True:
            try:publish(kit,root,job,status)
            except (ValueError,OSError):print('R1_EVIDENCE_COPY_FAILED',flush=True)
            time.sleep(600)
    else:publish(kit,root,job,status)
