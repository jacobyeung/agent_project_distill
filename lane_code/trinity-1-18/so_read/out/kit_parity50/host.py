"""Explicit H100 namespace staging/launch, using A4's authenticated runtime code.

The host entrypoint is Python 3.6 compatible. Runtime code is imported only after
its package payload hash and member pins pass. No downloads, installs or retries.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

# One table owns the public aliases and their prepared logical targets.
# Targets are relative to logical; alias names are relative to logical/d.
ALIASES = (('7.json','d/binding.json'), ('9.json','d/ENVIRONMENT.json'),
           ('a0','p/tree'), ('a1.json','d/p0/config.json'),
           ('a2.pt','d/k/sam3.pt'), ('a3.json','d/k/SAM3_RECEIPT.json'),
           ('a4','d/v/site'))


def private_aliases(logical):
    return {logical+'/'+target:logical+'/d/'+alias for alias,target in ALIASES}


def extract_assets(archive, asset, command, env):
    """Hash exactly the stream sent to tar; publish nothing before both pass."""
    digest=hashlib.sha256();size=0
    with Path(archive).open('rb') as stream:
        with subprocess.Popen(command,stdin=subprocess.PIPE,env=env) as process:
            pipe_open=True
            try:
                for chunk in iter(lambda:stream.read(1024**2),b''):
                    digest.update(chunk);size+=len(chunk)
                    if pipe_open:
                        try:process.stdin.write(chunk)
                        except BrokenPipeError:pipe_open=False
            finally:
                try:process.stdin.close()
                except BrokenPipeError:pass
            code=process.wait()
    if code:raise subprocess.CalledProcessError(code,command)
    if size!=asset['bytes'] or digest.hexdigest()!=asset['sha256']:
        raise ValueError('Prepared asset archive differs')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def stage_runtime(root, assets, S):
    # Unchanged runtime-group/bwrap block from orchard_h10.job.stage:110-117.
    # The prepared d archive supplies all additional inputs, so do not refetch them.
    root=Path(root);receipts={};archives=root/'a';archives.mkdir()
    for i,group in enumerate(assets['groups']):
        parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group]
        dest=archives/str(i)
        receipts[str(i)]=S.copy_parts(parts,dest,lambda p:Path(p['path']).open('rb'))
        S.room(root,dest.stat().st_size);S.unpack(dest,root,links=True)
    bwrap=assets['bwrap_pin']
    receipts['bwrap']=S.copy_parts([bwrap],root/'bwrap',lambda p:Path(p['path']).open('rb'))
    (root/'bwrap').chmod(0o700)
    return receipts


def namespace_command(root, inputs, J, args):
    # Never substitute sys.executable: v/py installs the production site overlay.
    return J.namespace(root)+[inputs['python'],'-B','-I']+list(args)


def gate_environment(root, kit, J):
    env=J.environment(root)
    env.update(XDG_CACHE_HOME=kit+'/u6',HF_HOME=kit+'/u6/u0',TRITON_CACHE_DIR=kit+'/u6/u1',
               MKL_NUM_THREADS='8',U0_ROOT=str(root),U0_KIT=kit)
    return env


def runtime_context(root):
    root=Path(root)
    sys.path.insert(0,str(root/'bootstrap'))
    from orchard_h10.common import template
    S,J,*_=template()
    inputs=json.loads((root/'1.json').read_text())
    sealed=json.loads((root/'2.json').read_text())
    if sha(root/'1.json')!=sealed['inputs']:raise ValueError('Staged inputs changed')
    return inputs,S,J


def authenticate(package):
    package=Path(package)
    public=json.loads((package/'0.json').read_text())
    if sha(package/'0.tgz')!=public['payload_sha256']:raise ValueError('Package payload differs')
    proof=json.loads((package/'a/c/CPU.json').read_text())
    if (proof.get('passed') is not True or proof['payload']!=public['payload_sha256']
            or proof['plan']!=public['plan_sha256'] or proof['inputs']!=sha(package/'a/1.json')):
        raise ValueError('CPU proof does not bind package and inputs')
    with tarfile.open(str(package/'0.tgz')) as archive:
        cfg=json.load(archive.extractfile('9.json'))
    asset=proof['gate_assets']
    if (asset['logical']!=cfg['logical']
            or Path(asset['path']).resolve()!=(package/'a/4.tar').resolve()):
        raise ValueError('Asset receipt logical root/path differs')
    return cfg,proof


def stage(package, root, kit, archive):
    package=Path(package);root=Path(root);archive=Path(archive)
    cfg,proof=authenticate(package)
    asset=proof['gate_assets']
    if archive.stat().st_size!=asset['bytes']:
        raise ValueError('Prepared asset archive differs')
    # Extract only pinned staging code; never import the host's unverified source.
    with tarfile.open(str(package/'0.tgz')) as source:
        for member in source:
            if not member.name.startswith('orchard_h10/'):continue
            if not member.isfile() or '..' in Path(member.name).parts:raise ValueError('Unsafe staging module')
            raw=source.extractfile(member).read();pin=cfg['payload_pins'][member.name]
            if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
                raise ValueError('Staging module pin differs')
            target=root/'bootstrap'/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(raw)
    sys.path.insert(0,str(root/'bootstrap'))
    from orchard_h10.common import template
    S,J,*_=template()
    J.storage_proof(root,job=os.environ['SLURM_JOB_ID'])
    assets=json.loads((root/'bootstrap/orchard_h10/vendor/ORCHARD_ASSETS.json').read_text())
    receipts=stage_runtime(root,assets,S)
    # READY's artifact manifest also authenticates code at logical/p.
    # Reuse job.stage's authenticated payload extraction, preserving that layout.
    archives=root/'a';archives.mkdir(exist_ok=True)
    public=json.loads((package/'0.json').read_text())
    payload=dict(path=str(package/'0.tgz'),bytes=public['payload_bytes'],sha256=public['payload_sha256'])
    receipts['code']=S.copy_parts([payload],archives/'c',lambda p:Path(p['path']).open('rb'))
    with (archives/'c').open('rb') as stream:
        S.extract_stream(stream,J.physical(root,cfg['logical']+'/p'),None,32*1024**2)
    for rel,pin in cfg['payload_pins'].items():
        if sha(J.physical(root,cfg['logical']+'/p/'+rel))!=pin['sha256']:raise ValueError('Code payload differs')
    for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
    data=J.physical(root,cfg['logical']+'/d');data.mkdir(parents=True,exist_ok=False)
    S.room(root,asset['bytes'])
    # Authenticate the extraction stream once; /project stays outside bwrap.
    env=gate_environment(root,kit,J)
    extract_assets(archive,asset,J.namespace(root)+['/bin/tar','-xf','-','-C',cfg['logical']+'/d'],env)
    for name,target in ALIASES:
        (data/name).symlink_to(os.path.relpath(J.physical(root,cfg['logical']+'/'+target),data))
    for path in (kit+'/u6',kit+'/u6/u0',kit+'/u6/u1'):
        J.physical(root,path).mkdir(parents=True,exist_ok=True)
    # The input wrapper path comes from the same a/1.json authenticated by CPU.json.
    raw=(package/'a/1.json').read_bytes()
    with (root/'1.json').open('xb') as stream:stream.write(raw)
    record=dict(inputs=sha(root/'1.json'),payload=proof['payload'],gate_assets=asset,runtime=receipts)
    with (root/'2.json').open('x') as stream:json.dump(record,stream,sort_keys=True)
    return record


def launch(root, kit):
    inputs,S,J=runtime_context(root)
    env=gate_environment(root,kit,J)
    config=kit+'/u0/u2.json'
    subprocess.run(namespace_command(root,inputs,J,[kit+'/u0/u5.py',config]),env=env,check=True)
    return subprocess.run(namespace_command(root,inputs,J,[kit+'/u0/u0.py',config,
        '--out',kit+'/u9','--enable-gpu','--public','--repeat-baseline','--shards','4']),env=env).returncode


def main():
    p=argparse.ArgumentParser();p.add_argument('--enable-namespace',action='store_true')
    modes=p.add_mutually_exclusive_group(required=True);modes.add_argument('--stage',action='store_true');modes.add_argument('--run',action='store_true')
    p.add_argument('--package');p.add_argument('--archive');p.add_argument('--root',required=True);p.add_argument('--kit-root',required=True)
    a=p.parse_args()
    if not a.enable_namespace:p.error('Namespace gate is OFF; pass --enable-namespace')
    root=Path(a.root).resolve()
    if root.parent!=Path('/tmp') or not re.fullmatch('a[0-9a-f]{12,32}',root.name):
        p.error('Use a fresh opaque directory under the job-private /tmp')
    if not re.fullmatch('/scratch/jjyeung/a[0-9a-f]{12,32}',a.kit_root):p.error('Require a fresh opaque kit root')
    if not os.environ.get('SLURM_JOB_ID','').isdigit():p.error('Run on an allocated compute node')
    if a.stage:
        if not a.package or not a.archive:p.error('--stage requires --package and --archive')
        stage(a.package,root,a.kit_root,a.archive);return 0
    return launch(root,a.kit_root)

if __name__=='__main__':raise SystemExit(main())
