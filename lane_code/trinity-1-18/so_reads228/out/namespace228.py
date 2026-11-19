"""Use the authenticated package namespace with the target's root-owned bwrap."""
import os
from pathlib import Path
import stat
import subprocess
from common228 import HERE,Refusal,checked,load_module,local,read,sha,write

BWRAP=Path('/usr/bin/bwrap')
AP='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'
FSW='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
UV='/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'

def package_namespace():
    source=HERE/'A10b/src';pins=read(HERE/'A10b_PINS.json')['source']
    for name in ('orchard_job.py','orchard_stage.py','orchard_results.py','chain_save.py'):
        rel='orchard_h10/vendor/'+name;checked(source/rel,pins[rel])
    return load_module(source/'orchard_h10/vendor/orchard_job.py','read228_orchard_namespace')

def bwrap_identity():
    value=BWRAP.stat()
    if not stat.S_ISREG(value.st_mode) or value.st_uid!=0 or value.st_mode&0o022 or not os.access(str(BWRAP),os.X_OK):
        raise Refusal('Require root-owned, non-writable /usr/bin/bwrap')
    result=subprocess.run([str(BWRAP),'--version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          universal_newlines=True,timeout=10)
    if result.returncode or result.stdout.strip()!='bubblewrap 0.4.0':
        raise Refusal('Target bwrap version differs from coordinator ruling: '+result.stdout+result.stderr)
    assets=read(HERE/'A10b/src/orchard_h10/vendor/ORCHARD_ASSETS.json')
    return dict(executed=dict(path=str(BWRAP),bytes=value.st_size,sha256=sha(BWRAP),uid=value.st_uid,
                             version=result.stdout.strip()),package_pin=assets['bwrap_pin'],
        selection='Execute /usr/bin/bwrap by coordinator ruling; package bwrap pin is recorded, not executed.')

def namespace_command(plan=None):
    plan=plan or read(HERE/'STAGE_PLAN.json');root=local(Path(plan['stage_root'])/'runtime')
    if not (root/'sj').is_symlink() or (root/'sj').resolve()!=Path('/scratch/jjyeung'):
        raise Refusal('Run --check-namespace to establish the package sj bind')
    argv=package_namespace().namespace(root)
    # Keep the package binds; overlay only its logical root with this kit's private copy.
    argv[0]=str(BWRAP)
    if plan.get('private_logical'):
        private=local(plan['private_logical'])
        if private.is_symlink() or not private.is_dir():raise Refusal('Private logical root must be a real directory')
        argv+=['--bind',str(private),plan['logical']]
    receipt=local(Path(plan['stage_root'])/'NAMESPACE.json')
    if receipt.is_file():
        proof=read(receipt)
        if not proof.get('passed') or proof.get('argv')!=argv or proof['bwrap']['executed']['sha256']!=sha(BWRAP):
            raise Refusal('Namespace command or system bwrap changed since its probe')
    return argv

def operator_command(inputs,*args,plan=None):
    """Probe and operator use the same namespace, wrapper, flags and entry file."""
    return namespace_command(plan)+[inputs['python'],'-B','-I',str(HERE/'operator228.py')]+list(args)

def check_namespace(plan,env):
    root=local(Path(plan['stage_root'])/'runtime');root.mkdir(parents=True,exist_ok=True)
    sj=root/'sj'
    if not sj.exists() and not sj.is_symlink():sj.symlink_to('/scratch/jjyeung',target_is_directory=True)
    if not sj.is_symlink() or sj.resolve()!=Path('/scratch/jjyeung'):
        raise Refusal('Existing runtime/sj is not the required bind alias; preserved')
    for name in ('fsw','m/ap'):
        path=root/name
        if path.is_symlink():raise Refusal('Namespace source directory is a symlink')
        path.mkdir(parents=True,exist_ok=True)
    if plan.get('private_logical'):
        private=local(plan['private_logical'])
        if private.is_symlink():raise Refusal('Private logical root is a symlink')
        private.mkdir(parents=True,exist_ok=True)
    identity=bwrap_identity();argv=namespace_command(plan)
    result=subprocess.run(argv+['/usr/bin/true'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          universal_newlines=True,timeout=30)
    proof=dict(passed=result.returncode==0,argv=argv,bwrap=identity,returncode=result.returncode,
               stdout=result.stdout,stderr=result.stderr,mode='package_namespace',
               namespace_source_sha256=sha(HERE/'A10b/src/orchard_h10/vendor/orchard_job.py'),
               logical_bind=dict(source=plan.get('private_logical'),destination=plan.get('logical')))
    write(local(Path(plan['stage_root'])/'NAMESPACE.json'),proof)
    if not proof['passed']:raise Refusal('Package namespace failed on target; no automatic relocation or retry. See NAMESPACE.json')
    return proof

def host_path(path,plan,_depth=0):
    """Resolve only package logical prefixes to their physical scratch destinations."""
    path=Path(path)
    if _depth>32:raise Refusal('Runtime symlink cycle')
    if not path.is_absolute() or '..' in path.parts:raise Refusal('Unsafe runtime probe path')
    mappings=[]
    if plan.get('private_logical'):mappings.append((plan['logical'],Path(plan['private_logical'])))
    if plan.get('environment',{}).get('local_base_python'):
        mappings.append((UV,Path(plan['environment']['local_base_python']).parents[1]))
    if plan.get('stage_root'):
        mappings.extend(((AP,Path(plan['stage_root'])/'runtime/m/ap'),(FSW,Path(plan['stage_root'])/'runtime/fsw')))
    for prefix,target in mappings:
        try:relative=path.relative_to(prefix)
        except ValueError:continue
        path=target/relative;break
    # Absolute archive links name namespace paths that do not exist on the host.
    # Translate those links before common.local resolves the physical file.
    local(path.parent)
    if path.is_symlink():
        link=os.readlink(str(path))
        target=link if Path(link).is_absolute() else os.path.normpath(str(path.parent/link))
        return host_path(target,plan,_depth+1)
    return local(path)
