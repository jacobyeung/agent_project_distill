"""Exercise streamed pin checks and same-allocation child execution locally."""
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile

W=Path(__file__).resolve().parent
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
assert sys.executable==PY
os.umask(0o077)
T=Path(tempfile.mkdtemp(prefix='stage_tests_',dir=W))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump=lambda p,v:p.write_text(json.dumps(v,sort_keys=True))
LOG=[]

def tar(path,contents):
    with tarfile.open(path,'w') as f:
        for name,raw in contents.items():
            info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o700 if name.endswith('python') else 0o600
            f.addfile(info,io.BytesIO(raw))

for label in ('success','bad_archive','bad_descriptor','bad_store','bad_record','bad_kit','gpu','child_failure','existing_stage'):
    base=T/label;base.mkdir(mode=0o700)
    k=base/'x_7f1589c1';b=base/'i_7f1589c1'
    for p in (k,b,k/'k',k/'b',k/'b/sa',k/'o'):
        p.mkdir(mode=0o700)
    with tarfile.open(W.parent/'ex_08f3a7b2/t.tar') as f:
        (k/'b/kitx.py').write_bytes(f.extractfile('launch_s1/b/kitx.py').read())
    for name in ('sitecustomize.py','prestage_hooks.py'):
        (k/'b/sa'/name).write_text('# pinned fixture\n')
    asroot='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
    db=base/'d.db';conn=sqlite3.connect(db);conn.execute('create table rows(i integer)');conn.commit();conn.close()
    desc=b/'d.json';dump(desc,dict(database=dict(path=asroot+'ap/69d2930d/d.db',sha256=sha(db))))
    cfg=dict(streams=dict(vqa=dict(path=asroot+'ap/69d2930d/d.json',sha256=sha(desc))))
    dump(k/'k/cfg.json',cfg)
    launch=dict(config=dict(file='k/cfg.json',sha256=sha(k/'k/cfg.json')))
    dump(k/'k/launch.json',launch)
    (k/'k/s1_record.json').write_text('{"fixture":true}')
    tar(base/'venv.tar',{'rwtrain_torch211_cu129/bin/python':b'fixture'})
    tar(base/'closure.tar',{'site_alias/retained.txt':b'archive alias','fixture.py':b'# runtime'})
    tar(k/'k/t.tar',{'entry.py':b'# trainer'})
    tar(k/'k/np.tar',{'overlay.py':b'# overlay'})
    cur=dict(commit='sha256:'+'1'*64,
             venv=dict(file=str(base/'venv.tar'),sha256=sha(base/'venv.tar')),
             closure=dict(file=str(base/'closure.tar'),sha256=sha(base/'closure.tar')),
             trainer=dict(file=asroot+'ap/8865619b/k/t.tar',sha256=sha(k/'k/t.tar')),
             np=dict(file=asroot+'ap/8865619b/k/np.tar',sha256=sha(k/'k/np.tar')),
             record=dict(file=asroot+'ap/8865619b/k/s1_record.json',sha256=sha(k/'k/s1_record.json')),
             extra=[dict(dest=cfg['streams']['vqa']['path'],parts=[str(desc)],sha256=sha(desc)),
                    dict(dest=asroot+'ap/69d2930d/d.db',parts=[str(db)],sha256=sha(db))])
    dump(k/'k/0.json',cur)
    names=[str(p.relative_to(k)) for d in (k/'b',k/'k') for p in d.rglob('*') if p.is_file()]
    (k/'SHA256SUMS.txt').write_text(''.join(sha(k/n)+'  '+n+'\n' for n in sorted(names)))
    dump(k/'ANON_OK.json',dict(status='CLEAN',hits=0,manifest_sha256=sha(k/'SHA256SUMS.txt')))
    # This child runs only after every staging hash succeeds and sees the same job.
    child='''#!/bin/bash
set -euo pipefail
[[ "$2" == --rehearsal && "$SLURM_JOB_ID" == 173001 ]]
[[ -f "$3/aws/u/ap/69d2930d/d.db" && -f "$3/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python" ]]
"PYTHON" -I -B - "$3" "$KH" <<'P'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);k=Path(sys.argv[2])
assert list(root.glob('epochs/*/entry.py'))
assert list(root.glob('c7d31ddd/_jobs/*/site_alias.r172467/retained.txt'))
assert not (root/'k').exists()
with (k/'o/173001.rehearsal.json').open('x') as f:json.dump(dict(status='REHEARSAL_OK',rc=0,job='173001',rehearsal=True),f)
P
exit CHILD_RC
'''.replace('PYTHON',PY).replace('CHILD_RC','7' if label=='child_failure' else '0')
    (b/'p_05b8ac69.sh').write_text(child)
    rootparent=base/'tmp'
    stage=rootparent/'rh2_08f3a7b2_173001/root'
    if label=='bad_archive':(base/'closure.tar').write_bytes((base/'closure.tar').read_bytes()+b'changed')
    if label=='bad_descriptor':desc.write_text('{}')
    if label=='bad_store':db.write_bytes(b'bad db')
    if label=='bad_record':(k/'k/s1_record.json').write_text('{}')
    if label=='bad_kit':(k/'k/cfg.json').write_text('{}')
    if label=='existing_stage':stage.mkdir(parents=True)
    text=(W/'rh2_job.sh').read_text().replace('/project/community/jjyeung/okh7',str(base))
    text=text.replace('/usr/bin/python3',PY).replace('/tmp/jjyeung',str(rootparent))
    text=text.replace('KH='+str(k),'export KH='+str(k))
    script=base/'job.sh';script.write_text(text)
    env=dict(os.environ,SLURM_JOB_ID='173001',SLURM_JOB_NAME='a15_cot_ap05b8ac6a',
             SLURM_JOB_PARTITION='general',SLURM_JOB_NUM_NODES='1',SLURM_GPUS_ON_NODE='1' if label=='gpu' else '0')
    r=subprocess.run(['/bin/bash',str(script)],env=env,capture_output=True,text=True,timeout=30)
    (base/'result.txt').write_text(r.stdout+r.stderr)
    assert (r.returncode==0)==(label=='success'),(label,r.stdout,r.stderr)
    receipt=json.loads((k/'o/173001.rehearsal.json').read_text())
    if label=='child_failure':assert r.returncode==7
    elif label=='success':
        report=json.loads((k/'o/173001.rh2.stage.json').read_text())
        assert report['status']=='STAGED' and len(report['inputs'])==9
        assert sha(stage/'aws/u/ap/69d2930d/d.db')==cur['extra'][1]['sha256']
    else:assert receipt['status']=='REHEARSAL_FAIL' and receipt['steps']['self_stage']=='FAIL'
    LOG.append(label);print('PASS stage',label,flush=True)
dump(T/'results.json',dict(status='PASS',checks=LOG))
print('ARTIFACTS',T)
