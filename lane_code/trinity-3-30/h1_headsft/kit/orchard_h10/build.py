"""Build locally; never stage remotely or invoke Slurm."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import secrets
import shlex
import sys
import tarfile

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from orchard_h10.common import canonical, opaque, sha, valid_token, write

K=Path(__file__).resolve().parents[1]
B=Path('/scratch/jjyeung/orch_n30/b04_e2ehook')
T=K/'tmp/b8/readk_tmpl/launcher'
CORE=('orchard_launcher.py','orchard_job.py','orchard_stage.py','export_stage.py',
      'orchard_results.py','return_io.py','stdout_transfer.py','trace_runtime.py',
      'chain_save.py','ORCHARD_ASSETS.json','MODELS.json','TRANSPORT.json')


def sources():
    files={}
    def add(path, name):
        if path.is_symlink():raise ValueError('Code package must contain regular source: '+str(path))
        if path.stat().st_size>4*1024**2:raise ValueError('Large source file: '+str(path))
        files[name]=path
    for folder in ('tree','h1eval','auth','rows','orchard_h10'):
        for path in sorted((K/folder).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:continue
            if folder=='orchard_h10' and (path.suffix!='.py' or path.parent!=K/folder):continue
            if path.suffix in ('.pyc','.pt','.safetensors','.tar','.gz'):continue
            add(path,str(path.relative_to(K)))
    add(K/'items/devs1_routed.json','items/devs1_routed.json')
    # The reviewed reader imports these modules and their native task bindings.
    for folder in ('e2e_reader','heads/selector','heads/scale','parity_kit'):
        for path in sorted((B/folder).glob('*.py')):add(path,'b/'+str(path.relative_to(B)))
    for name in ('work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl',
                 'work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl',
                 'work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json',
                 'work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/s1_receipt.json',
                 'work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json',
                 'work/n13/ret/native/paired/request.json',
                 'work/c8r/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py'):
        add(B/name,'b/'+name)
    for name in CORE:add(T/name,'orchard_h10/vendor/'+name)
    return files


def batch(bundle, token):
    """Template bootstrap pattern with opaque names and an embedded pinned code tar."""
    import hashlib
    encoded=base64.b64encode(bundle).decode()
    if len(encoded)>3*1024**2:raise ValueError('Embedded batch exceeds the template 3 MiB limit')
    # Contents are exempt; the executable shell and all submission surfaces are scanned.
    text="""#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import base64,hashlib,io,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=base64.b64decode(%r,validate=True)
if hashlib.sha256(b).hexdigest()!=%r:raise ValueError('Digest differs')
r=Path('/tmp')/('a'+j+%r)
r.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(b)) as a:
    seen=set();total=0
    for e in a:
        n=PurePosixPath(e.name);total+=e.size
        if n.is_absolute() or '..' in n.parts or not e.isfile() or e.name in seen or total>33554432:raise ValueError('Unsafe input')
        seen.add(e.name);p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)
        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())
os.chdir(r)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])
A
""" % (encoded,hashlib.sha256(bundle).hexdigest(),token)
    # Python source here is shipped in-job content. Only the shell command is exposed to Slurm.
    opaque(text.split("<<'A'")[0].splitlines())
    return text


def build(destination, token=None, refresh=False):
    from orchard_h10.common import template
    template(T)
    import orchard_launcher as L
    destination=Path(destination).resolve()
    if not destination.is_relative_to(K):raise ValueError('Build output must stay in K')
    if refresh:
        if (destination/'LEDGER.jsonl').exists():raise ValueError('Cannot refresh a submitted package')
        previous=json.loads((destination/'CONFIG.json').read_text())
        token=previous['token'] if token is None else token
        if token!=previous['token']:raise ValueError('Refresh cannot change a package token')
    elif destination.exists() and any(destination.iterdir()):raise ValueError('Require a fresh package directory')
    token=valid_token(token or secrets.choice('abcdef')+secrets.token_hex(6))
    destination.mkdir(parents=True,exist_ok=True)
    paths=sources()
    pins={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in paths.items()}
    raw=L.tar_bytes({n:p.read_bytes() for n,p in paths.items()})
    if len(raw)>8*1024**2:raise ValueError('Code archive exceeds local build allowance')
    (destination/'0.tgz').write_bytes(raw)
    cfg=dict(schema='h10-orchard-v1',token=token,logical='/scratch/jjyeung/'+token,
             payload_sha256=sha(destination/'0.tgz'),payload_bytes=len(raw),payload_pins=pins,
             template_pins={n:sha(T/n) for n in CORE},
             order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),
             inputs_name='1.json',cpu_check_name='2.json',pool='/project/community/jjyeung/okh7/ae71c903',
             stop_margin=1800,return_margin=1200,budget_gpu_seconds=18000)
    cfg['plan_sha256']=canonical(cfg)
    boot=("import sys\nfrom pathlib import Path\nr=Path(sys.argv[1]);sys.path.insert(0,str(r/'p'))\n"
          "from orchard_h10.job import main\nmain(r)\n").encode()
    files={'0.py':boot,'0.json':json.dumps(cfg,sort_keys=True).encode()}
    # The template transport stages the larger code tar from an opaque shared path.
    # Only bootstrap helpers belong in Slurm's size-limited batch body.
    for name in ('__init__.py','common.py','job.py'):
        files['p/orchard_h10/'+name]=(K/'orchard_h10'/name).read_bytes()
    for name in CORE:files['p/orchard_h10/vendor/'+name]=(T/name).read_bytes()
    bundle=L.tar_bytes(files)
    (destination/'BATCH.sh').write_text(batch(bundle,token))
    write(destination/'CONFIG.json',cfg)
    # Internal helper consumes local config; only its validated sbatch argv reaches Slurm.
    (destination/'SUBMIT.cmd').write_text('#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\n'
        'exec /usr/bin/python3 -I -s -B 3.py submit --gpus "${A_N:?Set 1 to 4}" --time "${A_T:?Set HH:MM:SS}" "$@"\n')
    (destination/'3.py').write_text((K/'orchard_h10/operator.py').read_text())
    write(destination/'INPUTS.example.json',dict(schema=1,archives=[],files={},python=None,
        policy=dict(vnice=None,terminator=None),resume=None,
        note='Fill and pin on Orchard; do not submit this unresolved example.'))
    (destination/'0.json').write_text(json.dumps(cfg,sort_keys=True)+'\n')
    write(destination/'PACKAGE.json',dict(token=token,files={n:sha(destination/n) for n in
          ('0.tgz','BATCH.sh','CONFIG.json','3.py','0.json')}))
    mapping=K/'orchard_h10/TOKENS.json'
    old=json.loads(mapping.read_text()) if mapping.exists() else {}
    old[token]=dict(package=str(destination.relative_to(K)),meaning='step-544 own dev-S1; registered modes; five ordered types')
    write(mapping,old)
    return dict(directory=str(destination),token=token,code_bytes=len(raw),files=len(paths),plan=cfg['plan_sha256'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--token');p.add_argument('--refresh',action='store_true')
    a=p.parse_args();print(json.dumps(build(a.out,a.token,a.refresh),sort_keys=True))
