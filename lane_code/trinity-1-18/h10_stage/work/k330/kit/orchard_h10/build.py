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
    add(K/'items/r0dev.json','items/r0dev.json')
    from h1eval.items import R0_PINS
    for name in R0_PINS:add(K/'inputs/r0dev'/name,'inputs/r0dev/'+name)
    # The reviewed reader imports these modules and their native task bindings.
    for folder in ('e2e_reader','heads/selector','heads/selector/sl118','heads/scale','parity_kit'):
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
    """The batch contains only an opaque descriptor and numeric bootstrap names."""
    import hashlib
    text="""#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex(%r)
r=Path('/tmp')/('a'+j+%r)
r.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(b)) as a:
    for e in a:
        n=PurePosixPath(e.name)
        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')
        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)
        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())
os.chdir(r)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])
A
""" % (bundle.hex(),token)
    opaque([text])
    if len(text)>3*1024**2:raise ValueError('Batch exceeds limit')
    return text


def repin_reader(spec, old):
    """An explicit complete inventory is required; no implicit reader refresh."""
    source=Path(spec['source']).resolve();expected=spec['sha256']
    paths={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file()}
    if set(paths)!=set(expected) or any(p.is_symlink() for p in paths.values()):
        raise ValueError('Reader inventory differs')
    if any(sha(p)!=expected[n] for n,p in paths.items()):raise ValueError('Reader hash differs')
    if set(expected)!=set(old):raise ValueError('Reader inventory must match the pinned package')
    return {n:p.read_bytes() for n,p in paths.items()}


def build(destination, token=None, refresh=False, reader_repin=None):
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
    import hashlib
    payload={n:p.read_bytes() for n,p in paths.items()}
    # A refresh keeps the reviewed reader frozen, even if its upstream changed.
    if (destination/'0.tgz').exists():
        with tarfile.open(destination/'0.tgz') as archive:
            old={e.name[2:]:archive.extractfile(e).read() for e in archive
                 if e.isfile() and e.name.startswith('b/e2e_reader/')}
        for n,raw in old.items():payload['b/'+n]=raw
    else:old={n[2:]:raw for n,raw in payload.items() if n.startswith('b/e2e_reader/')}
    if reader_repin:
        new=repin_reader(json.loads(Path(reader_repin).read_text()),old)
        for n,raw in new.items():payload['b/'+n]=raw
    payload['8.py']=(K/'orchard_h10/operator.py').read_bytes()
    pins={n:dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)) for n,raw in payload.items()}
    cfg=dict(schema='h10-orchard-v1',token=token,logical='/scratch/jjyeung/'+token,
             payload_pins=pins,
             template_pins={n:sha(T/n) for n in CORE},
             order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),
             inputs_name='1.json',cpu_check_name='2.json',pool='/project/community/jjyeung/okh7/ae71c903',
             stop_margin=1800,return_margin=1200,budget_gpu_seconds=18000)
    plan=canonical(cfg)
    payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
    raw=L.tar_bytes(payload)
    if len(raw)>8*1024**2:raise ValueError('Code archive exceeds local allowance')
    (destination/'0.tgz').write_bytes(raw)
    public=dict(token=token,payload_sha256=sha(destination/'0.tgz'),payload_bytes=len(raw),plan_sha256=plan)
    boot=("import sys,json,hashlib,tarfile\nfrom pathlib import Path\n"
          "r=Path(sys.argv[1]);c=json.loads((r/'0.json').read_text())\n"
          "a=Path('/project/community/jjyeung')/c['token']/'0.tgz'\n"
          "assert hashlib.sha256(a.read_bytes()).hexdigest()==c['payload_sha256']\n"
          "with tarfile.open(a) as t:\n"
          " for e in t:\n"
          "  if not e.name.startswith('orchard_h10/'):continue\n"
          "  if not e.isfile() or '..' in Path(e.name).parts:raise ValueError('Unsafe input')\n"
          "  p=r/'p'/e.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(e).read())\n"
          "sys.path.insert(0,str(r/'p'))\nfrom orchard_h10.job import main\nmain(r)\n").encode()
    bundle=L.tar_bytes({'0.py':boot,'0.json':json.dumps(public).encode()})
    (destination/'BATCH.sh').write_text(batch(bundle,token))
    write(destination/'CONFIG.json',public)
    (destination/'SUBMIT.cmd').write_text('#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\n'
        'exec /usr/bin/python3 -I -s -B 3.py submit --gpus "${A_N:?Set 1 to 4}" --time "${A_T:?Set HH:MM:SS}" "$@"\n')
    helper="""import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
"""
    opaque([helper]);(destination/'3.py').write_text(helper)
    write(destination/'INPUTS.example.json',dict(schema=1,archives=[],files={},python=None,
        policy=dict(vnice=None,terminator=None),resume=None,
        note='Fill and pin on Orchard; do not submit this unresolved example.'))
    (destination/'0.json').write_text(json.dumps(public,sort_keys=True)+'\n')
    write(destination/'PACKAGE.json',dict(token=token,files={n:sha(destination/n) for n in
          ('0.tgz','BATCH.sh','CONFIG.json','3.py','0.json')}))
    for path in destination.iterdir():
        if path.is_file() and path.name!='0.tgz':opaque([path.name,path.read_text()])
    if reader_repin:
        with (K/'BUILD_REPORT.md').open('a') as report:
            report.write('\nReader repin hashes (old → new):\n\n')
            for n in sorted(old):report.write(f"- `{n}`: `{hashlib.sha256(old[n]).hexdigest()}` → `{pins['b/'+n]['sha256']}`.\n")
    mapping=K/'orchard_h10/TOKENS.json'
    old=json.loads(mapping.read_text()) if mapping.exists() else {}
    old[token]=dict(package=str(destination.relative_to(K)),meaning='step-544 own dev-S1; registered modes; five ordered types')
    write(mapping,old)
    return dict(directory=str(destination),token=token,code_bytes=len(raw),files=len(paths),plan=plan)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--token');p.add_argument('--refresh',action='store_true');p.add_argument('--reader-repin',help='JSON with source directory and complete sha256 inventory')
    a=p.parse_args();print(json.dumps(build(a.out,a.token,a.refresh,a.reader_repin),sort_keys=True))
