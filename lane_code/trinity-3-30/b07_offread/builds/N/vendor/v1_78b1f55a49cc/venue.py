"""Construct a local namespace and sealed operator packet without launching it."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
from adapter import *

SJ='/scratch/jjyeung'
FSW='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
AP='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'


def physical(root,path):
    for prefix,folder in ((FSW,'fsw'),(AP,'m/ap'),(SJ,'sj')):
        try:return Path(root)/folder/Path(path).relative_to(prefix)
        except ValueError:pass
    raise ValueError('logical path not registered')

def extract(archive,dest,budget,include=None):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);total=0
    with tarfile.open(archive) as stream:
        for member in stream:
            name=Path(member.name)
            if name.is_absolute() or '..' in name.parts:raise ValueError('archive path escapes root')
            if include is not None and not include(member.name):continue
            if member.isdir():continue
            if not member.isfile():raise ValueError('archive entry requires explicit link plan')
            total+=member.size
            if total>budget:raise ValueError('archive exceeds expansion allowance')
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():raise ValueError('archive destination exists')
            with stream.extractfile(member) as inp,target.open('xb') as out:
                for block in iter(lambda:inp.read(1024**2),b''):out.write(block)
            target.chmod(member.mode&0o755)
    return total

def stage_local(root,assets,budget=8000000000):
    """Stage local archives using the inherited bounded archive reader."""
    import paths
    sys.path.extend([str(paths.CORE),str(paths.CORE/'orchard_native')])
    import orchard_stage as S
    import native_stage as N
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    used=0;receipts={};result=dict(assets)
    if assets.get('base_root') and not Path(assets['base_root']).is_dir():
        source=checked(assets['base_archive'])
        if source.stat().st_size>budget:raise ValueError('base archive exceeds stage budget')
        used+=extract(source,root/'base',budget)
        result['base_root']=str(root/'base')
        result['base_bindings']=[(str(root/'base/m/ap'),AP)]
        receipts['base']=dict(source=assets['base_archive'],owned_bytes=used)
    for role in ('metadata','model','runtime','fla'):
        source=assets.get(role+'_archive')
        if source is None:raise ValueError('missing local archive descriptor: '+role)
        archive=Path(source['path']) if role=='fla' else checked(source)
        if archive.stat().st_size>budget-used:raise ValueError('archive cannot fit the stage budget')
        destination=root/role
        if destination.exists():raise ValueError('staging phase already exists: '+role)
        if role in ('metadata','model'):
            used+=extract(archive,destination,budget-used,include=lambda name:name.startswith(('fsw/','m/')))
            if role=='metadata':result['base_bindings']=list(result.get('base_bindings',[]))+[(str(destination/'fsw'),FSW)]
            else:
                for file in destination.rglob('*'):
                    if file.is_file():
                        rel=file.relative_to(destination);prefix=FSW if rel.parts[0]=='fsw' else AP
                        result['base_bindings'].append((str(file),str(Path(prefix).joinpath(*rel.parts[1:]))))
        elif role=='fla':
            manifest=checked(assets['fla_manifest'])
            wanted={'ebe69df8/p/'+name:dict(destination='p/'+name,sha256=value) for name,value in N.manifest_files(manifest).items()}
            inventory=N.extract_named(archive,destination,wanted)
            used+=sum(r['bytes'] for r in inventory.values());result['fla_root']=str(destination/'p')
        else:
            destination.mkdir()
            saved=S.RUNTIME_ABSOLUTE_LINKS
            try:
                if role=='runtime':S.RUNTIME_ABSOLUTE_LINKS=N.runtime_links(archive)
                with archive.open('rb') as stream:
                    inventory=S.extract_stream(stream,destination,None,budget-used,links=role=='runtime')
            finally:S.RUNTIME_ABSOLUTE_LINKS=saved
            used+=sum(r['bytes'] for r in inventory.values())
            relative=assets[role+'_relative_root'];candidate=destination/relative
            if not candidate.is_dir():raise ValueError('archive layout differs: '+role)
            result['runtime_root' if role=='runtime' else 'fla_root']=str(candidate)
        receipts[role]=dict(source=source,owned_bytes=used)
        dump(root/'STAGING.json',receipts)
    # The original export is a read-only child mount over the staged metadata namespace.
    result['base_bindings']=[v for v in result['base_bindings'] if v[1]!=assets['export_logical']]+[(assets['export_root'],assets['export_logical'])]
    dump(root/'ASSETS.json',result);return result

def namespace(root,bindings,gpu=None,cpu=False,host_bwrap=False):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    for name in ('shm','tmp','cache','run'): (root/name).mkdir(exist_ok=True)
    args=['/usr/bin/bwrap' if host_bwrap else str(root/'bwrap'),'--unshare-net','--die-with-parent']
    for name in ('usr','etc','bin','sbin','lib','lib64','sys','opt','run'):
        p=Path('/')/name
        if p.is_symlink():args+=['--symlink',os.readlink(p),str(p)]
        elif p.exists():args+=['--ro-bind',str(p),str(p)]
    args+=['--proc','/proc','--dev','/dev','--bind',str(root/'shm'),'/dev/shm',
           '--bind',str(root/'tmp'),'/tmp','--bind',str(root/'cache'),'/cache',
           '--bind',str(root/'run'),'/r','--dir','/scratch']
    for source,target,writable in bindings:
        args+=['--bind' if writable else '--ro-bind',str(source),str(target)]
    if not cpu:
        # Device files only; host shared memory never enters the namespace.
        for p in sorted(Path('/dev').glob('nvidia*')):
            args+=['--dev-bind',str(p),str(p)]
    args+=['--setenv','XDG_CACHE_HOME','/cache','--setenv','HF_HOME','/cache/hf',
           '--setenv','TRITON_CACHE_DIR','/cache/triton','--setenv','TORCH_HOME','/cache/torch',
           '--setenv','OMP_NUM_THREADS','4','--setenv','OPENBLAS_NUM_THREADS','4',
           '--setenv','MKL_NUM_THREADS','4','--setenv','PYTHONDONTWRITEBYTECODE','1',
           '--setenv','CUDA_VISIBLE_DEVICES','' if cpu else str(gpu),'--chdir','/r']
    return args

def trinity_plan(root,assets,gpu=0,cpu=False,host_bwrap=True):
    base=Path(assets['base_root']);bindings=[];missing=[]
    for n in ('base_root','tree','numpy','code','inputs'):
        if not Path(assets[n]).exists():missing.append(assets[n])
    # Bind only the model and export locations from the shared base namespace.
    # Evaluation cohorts, masks and geometry are absent from this allowlist.
    for source,target in assets.get('base_bindings',[]):
        if not Path(source).exists():missing.append(source)
        bindings.append((source,target,False))
    bindings += [(assets['code'],'/c',False),(assets['tree'],assets.get('tree_logical',assets['tree']),False),
                 (assets['numpy'],'/n',False),(assets['inputs'],'/i',False)]
    if cpu:
        bindings.extend((p,p,False) for p in assets['cpu_roots'])
        python=assets['cpu_python'];overlay='/n:'+assets['pyextra']
    else:
        for n in ('runtime_root','fla_root','weights','tower_config'):
            if not Path(assets[n]).exists():missing.append(assets[n])
        bindings.extend([(assets['runtime_root'],'/e',False),(assets['fla_root'],'/f',False),
                         (assets['weights'],'/w/weights',False),(assets['tower_config'],'/w/config.json',False)])
        receipt=assets['weights']+'.RECEIPT.json'
        if not Path(receipt).exists():missing.append(receipt)
        bindings.append((receipt,'/w/weights.RECEIPT.json',False))
        if assets.get('interpreter_root'):
            bindings.append((assets['interpreter_root'],assets['interpreter_root'],False))
            bindings.append((str(Path(assets['interpreter_root'])/'bin/python3.12'),'/usr/bin/python3.12',False))
        python='/e/bin/python3.12';overlay='/n:/f'
    argv=namespace(root,bindings,gpu,cpu,host_bwrap=host_bwrap)+['--setenv','PYTHONPATH',overlay,'--setenv','READ_OVERLAY',overlay,
                                        python,'-s','-B','/c/entry.py']
    return dict(argv=argv,missing=sorted(set(missing)),bindings=bindings,cpu=cpu,
                vnice=[] if cpu else ['/data3/shared/scripts/vnice/vnice.sh'],gpu=gpu,
                host_shm_bound=False,unexecuted=True)

def packet(family_path,assets_path,out,token):
    if not __import__('re').fullmatch('[a-f0-9]{24,32}',token):raise ValueError('token must be opaque')
    family=load(family_path)
    if family['limits']['full']['gpu_seconds']!=21600:raise ValueError('full limit differs')
    dest=Path(out);dest.mkdir(parents=True,exist_ok=False)
    config=dict(schema='read-packet-v1',family=dict(path='FAMILY.json',sha256=sha(family_path)),assets=dict(path='ASSETS.json',sha256=sha(assets_path)),token=token,
                return_pool='/project/community/jjyeung/okh7/n2r/'+token,
                return_gcs='gs://cmu-gpucloud-jjyeung/q8/n2r/'+token+'/',seconds=21600)
    (dest/'FAMILY.json').write_bytes(Path(family_path).read_bytes())
    (dest/'ASSETS.json').write_bytes(Path(assets_path).read_bytes())
    dump(dest/'CONFIG.json',config)
    # Packet construction is local. Submission and staging are separate operator actions.
    text='#!/bin/bash\n'
    text+='#SBATCH --account=mt01\n#SBATCH --partition=general\n#SBATCH --gres=gpu:1\n#SBATCH --time=07:00:00\n'
    text+='set -euo pipefail\n'
    text+=': "${READ_CODE:?set the staged code directory}"\n: "${READ_ASSETS:?set the local asset manifest}"\n: "${READ_ROOT:?set the private local root}"\n'
    text+=': "${READ_CONFIG:?set the packet configuration path}"\n'
    text+='exec nice -n 10 /usr/bin/python3 -s -B "$READ_CODE/orchard.py" --config "$READ_CONFIG" --assets "$READ_ASSETS" --root "$READ_ROOT"\n'
    (dest/'BATCH.sh').write_text(text)
    dump(dest/'PACKET.json',dict(config=config,batch=pin(dest/'BATCH.sh'),ready=False,
         blockers=family.get('blockers',[]),transport='inherited return-pool and GCS locations; upload not executed'))
    return config

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('stage')
    for k in ('root','assets'):q.add_argument('--'+k,required=True)
    q.add_argument('--budget',type=int,default=8000000000)
    for name in ('plan','run'):
        q=sub.add_parser(name)
        for k in ('root','assets'):q.add_argument('--'+k,required=True)
        q.add_argument('--gpu',type=int,default=0);q.add_argument('--cpu',action='store_true');q.add_argument('args',nargs=argparse.REMAINDER)
    q=sub.add_parser('packet')
    for k in ('family','assets','out','token'):q.add_argument('--'+k,required=True)
    a=p.parse_args()
    if a.command=='stage':return stage_local(a.root,load(a.assets),a.budget)
    if a.command=='packet':return packet(a.family,a.assets,a.out,a.token)
    plan=trinity_plan(a.root,load(a.assets),a.gpu,a.cpu);dump(Path(a.root)/'PLAN.json',plan)
    if a.command=='plan':return
    if plan['missing']:raise ValueError('assets missing: '+repr(plan['missing']))
    tail=a.args[1:] if a.args[:1]==['--'] else a.args
    subprocess.run(plan['vnice']+plan['argv']+tail,check=True)
if __name__=='__main__':main()
