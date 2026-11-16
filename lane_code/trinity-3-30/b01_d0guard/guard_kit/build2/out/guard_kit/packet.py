"""Seal a candidate packet and require exact independent review and ORCH GO."""
import argparse
import ast
import base64
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import secrets
import shlex
import sys
import tarfile
import zlib
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
from guard_core import STEPS,check_pin,digest,parse_done,read,sha,write,verify_archive
from transport import regular_tar
from names import scan_json

LIMIT=32*1024*1024

def safe_tar(path):return regular_tar(path,LIMIT)

def submit_argv(config,batch):
    if not re.fullmatch('[a-f0-9]{16}',config['token']):raise ValueError('Token must be fresh hexadecimal')
    return ['sbatch','--parsable','--account=mt01','--partition=general','--gres=gpu:1','--ntasks=1','--nodes=1',
            '--cpus-per-task=16','--mem=200G','--time='+config['time_limit'],
            '--signal=B:USR1@300','--no-requeue','--chdir=/tmp',
            '--job-name=a15_cot_ap'+config['token'],str(batch)]

def order_line(config):return 'ORCH GO a15_cot_ap'+config['token']+' '+str(config['step'])+' '+config['plan_sha256']

def source_identity(family):
    """Compile only the exact identity function from the pinned trainer file."""
    source=check_pin(family['identity_source'])
    if sha(source)!='895772a9f5e0fd09277db72a8a091782728bfe2f525567c301e4d5bf58275471':
        raise ValueError('Trainer identity source is not the backend source')
    parsed=ast.parse(source.read_text())
    nodes=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='identity']
    if len(nodes)!=1:raise ValueError('Trainer identity boundary differs')
    ns={'digest':digest}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
    return SimpleNamespace(identity=ns['identity'])

def packed_files(meta):
    verify_archive(meta['archive']['path'],meta['archive']);regular_tar(meta['archive']['path'],64*1024*1024)
    files={};actual={}
    with tarfile.open(meta['archive']['path'],'r:') as tar:
        for m in tar:
            raw=tar.extractfile(m).read()
            if m.name not in meta['aliases']:raise ValueError('Unknown closure member alias')
            name=meta['aliases'][m.name]
            if name in files:raise ValueError('Closure alias is not injective')
            files[name]=raw;actual[m.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    if actual!=meta['members']:raise ValueError('Closure member inventory differs')
    return files

def authenticate_meta(family,meta,step):
    from closure import authenticate
    # source_seal has only standard-library imports; authenticate its whole trainer tree in the job.
    sys.path.insert(0,str(check_pin(family['identity_source']).parents[1]))
    return authenticate(packed_files(meta),step,source_identity(family),check_pin(family['baseline_artifact']))

def prepare(family_path,done_path,step,metadata_path,destination,token=None):
    family=read(family_path)
    if step not in STEPS:raise ValueError('Candidate step is not admitted')
    done=parse_done(Path(done_path).read_bytes(),'359fcc3c',step)
    token=token or secrets.token_hex(8)
    if not re.fullmatch('[a-f0-9]{16}',token):raise ValueError('Invalid token')
    meta=read(metadata_path)
    if meta.get('schema')!='g2-closure-v1' or meta.get('step')!=step:raise ValueError('Closure step differs')
    admission=authenticate_meta(family,meta,step)
    if admission!=meta['admission']:raise ValueError('Closure admission record differs')
    for pin in family['inputs'].values():check_pin(pin)
    for name,expected in family['code_pins'].items():
        if sha(Path(family['code_root'])/name)!=expected:raise ValueError('Code pin differs: '+name)
    config=dict(schema='g2-plan-v1',token=token,step=step,run='359fcc3c',gpus=1,partition='general',
        family=dict(path=str(Path(family_path).resolve()),sha256=sha(family_path)),
        done=done,done_sha256=sha(done_path),done_file=str(Path(done_path).resolve()),
        closure=dict(path=str(Path(metadata_path).resolve()),sha256=sha(metadata_path)),
        closure_archive_sha256=meta['archive']['sha256'],closure_source_sha256=meta['source_sha256'],
        closure_object=dict(path='/project/community/jjyeung/okh7/8c9d2e74/'+token+'/m.tar',
                            bytes=meta['archive']['bytes'],sha256=meta['archive']['sha256']),
        artifact_sha256=admission['artifact_sha256'],time_limit=family['time_limit'],
        gpu_seconds=family['gpu_seconds'],publication=family['publication'])
    config['plan_sha256']=digest(config)
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    write(dest/'CONFIG.json',config)
    write(dest/'PREPARED.json',dict(status='PREPARED_NOT_AUTHORIZED',config_sha256=sha(dest/'CONFIG.json')))
    return config

def admit(config,family,review,order):
    if config.get('schema')!='g2-plan-v1' or config.get('run')!='359fcc3c' or config.get('step') not in STEPS:
        raise ValueError('Config schema, run or milestone differs')
    if config.get('gpus')!=1 or config.get('partition')!='general':raise ValueError('Allocation shape differs')
    if config['plan_sha256']!=digest({k:v for k,v in config.items() if k!='plan_sha256'}):raise ValueError('Plan seal differs')
    if family.get('schema')!='g2-family-v1' or family.get('release_ready') is not True or family.get('blockers'):
        raise ValueError('Release blocked: '+'; '.join(family.get('blockers',['unvalidated family'])))
    if review.get('verdict')!='ACCEPT' or not review.get('reviewer') or review.get('family_sha256')!=config['family']['sha256']:
        raise ValueError('Independent review does not bind this family')
    if order.splitlines().count(order_line(config))!=1:raise ValueError('Exact ORCH GO is absent')
    for field in ('time_limit','gpu_seconds','publication'):
        if config[field]!=family[field]:raise ValueError('Family contract differs: '+field)
    if scan_json(config) or scan_json(family):raise ValueError('Operational config/family naming scan failed')

def validate_packet(payload):
    p=Path(payload);config=read(p/'CONFIG.json');family=read(p/'FAMILY.json')
    if sha(p/'FAMILY.json')!=config['family']['sha256']:raise ValueError('Packet family hash differs')
    admit(config,family,read(p/'REVIEW.json'),(p/'ORDER.md').read_text())
    for name,expected in family['code_pins'].items():
        if sha(p/'guard_kit'/name)!=expected:raise ValueError('Packet code differs: '+name)
    for name,pin in family['inputs'].items():
        if sha(p/'inputs'/name)!=pin['sha256']:raise ValueError('Packet input differs: '+name)
    if sha(p/'candidate.done')!=config['done_sha256'] or parse_done((p/'candidate.done').read_bytes(),'359fcc3c',config['step'])!=config['done']:
        raise ValueError('Packet done record differs')
    if sha(p/'CLOSURE.json')!=config['closure']['sha256'] or sha(p/'metadata.tar')!=config['closure_archive_sha256']:
        raise ValueError('Packet candidate closure differs')
    meta=read(p/'CLOSURE.json')
    if meta['source_sha256']!=config['closure_source_sha256'] or meta['admission']['artifact_sha256']!=config['artifact_sha256']:
        raise ValueError('Packet closure binding differs')
    return config

def packet(config_path,review_path,order_path,destination):
    config=read(config_path);family_path=check_pin(config['family']);family=read(family_path)
    admit(config,family,read(review_path),Path(order_path).read_text())
    meta_path=check_pin(config['closure']);meta=read(meta_path)
    if authenticate_meta(family,meta,config['step'])!=meta['admission']:raise ValueError('Closure admission changed')
    verify_archive(meta['archive']['path'],meta['archive'])
    if sha(config['done_file'])!=config['done_sha256']:raise ValueError('Done file changed')
    sources={'CONFIG.json':Path(config_path),'FAMILY.json':family_path,'REVIEW.json':Path(review_path),
             'ORDER.md':Path(order_path),'CLOSURE.json':meta_path,
             'candidate.done':Path(config['done_file'])}
    for name,pin in family['inputs'].items():sources['inputs/'+name]=check_pin(pin)
    for name,expected in family['code_pins'].items():
        path=Path(family['code_root'])/name
        if sha(path)!=expected:raise ValueError('Code changed after review')
        sources['guard_kit/'+name]=path
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    archive=dest/'p.tar'
    with tarfile.open(archive,'x',dereference=True) as tar:
        for name,path in sorted(sources.items()):
            m=tarfile.TarInfo(name);m.size=path.stat().st_size;m.mode=0o755 if path.suffix=='.sh' else 0o644
            with path.open('rb') as inp:tar.addfile(m,inp)
    regular_tar(archive,LIMIT)
    from transport import copy_verified
    copy_verified(meta['archive']['path'],dest/'m.tar')
    # The fixed shared path carries the bounded archive; the batch pins its literal hash.
    expected=sha(archive)
    payload_path='/project/community/jjyeung/okh7/8c9d2e74/'+config['token']+'/p.tar'
    bootstrap='''import hashlib,io,json,os,pathlib,tarfile
job=os.environ.get('SLURM_JOB_ID','')
if not job.isdigit():raise ValueError('Assigned job required')
source=pathlib.Path(PAYLOAD)
if source.is_symlink() or not source.is_file() or source.stat().st_size>33554432:raise ValueError('Payload source differs')
raw=source.read_bytes()
if len(raw)>33554432 or hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Payload differs')
root=pathlib.Path('/tmp')/('g2_'+job+'_'+TOKEN)
root.mkdir(mode=0o700)
p=root/'payload';p.mkdir();seen=set();total=0
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
 for m in tar:
  n=pathlib.PurePosixPath(m.name);total+=m.size
  if not m.isfile() or n.is_absolute() or '..' in n.parts or str(n) in seen or total>33554432:raise ValueError('Unsafe payload')
  seen.add(str(n));target=p/str(n);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as out:out.write(tar.extractfile(m).read())
  target.chmod(m.mode&0o755)
c=json.loads((p/'CONFIG.json').read_text())['closure_object']
source=pathlib.Path(c['path'])
if source.is_symlink() or not source.is_file() or source.stat().st_size!=c['bytes'] or c['bytes']>67108864:raise ValueError('Closure object differs')
h=hashlib.sha256()
with source.open('rb') as inp,(p/'metadata.tar').open('xb') as out:
 for block in iter(lambda:inp.read(1048576),b''):
  h.update(block);out.write(block)
if h.hexdigest()!=c['sha256']:raise ValueError('Closure object digest differs')
os.execv('/usr/bin/python3',['/usr/bin/python3','-I','-s','-B',str(p/'guard_kit/worker.py'),'--root',str(root),'--payload',str(p)])
'''
    batch='#!/bin/bash\nset -euo pipefail\numask 077\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1\nunset PYTHONPATH\nexec /usr/bin/python3 -I -s -B - <<\'G2_PY\'\n'
    batch+='PAYLOAD='+repr(payload_path)+'\nEXPECTED='+repr(expected)+'\nTOKEN='+repr(config['token'])+'\n'+bootstrap+'G2_PY\n'
    (dest/'BATCH.sh').write_text(batch);(dest/'BATCH.sh').chmod(0o700)
    for name in ('CONFIG.json','FAMILY.json'):(dest/name).write_bytes(sources[name].read_bytes())
    value=dict(schema='g2-packet-v1',plan_sha256=config['plan_sha256'],family_sha256=config['family']['sha256'],
        closure_sha256=config['closure_source_sha256'],payload=dict(path=payload_path,bytes=archive.stat().st_size,sha256=expected),
        batch_sha256=sha(dest/'BATCH.sh'),submit_argv=submit_argv(config,dest/'BATCH.sh'))
    write(dest/'PACKET.json',value);(dest/'SUBMIT_COMMAND.txt').write_text(shlex.join(value['submit_argv'])+'\n')
    return value

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('prepare')
    for name in ('family','done','metadata','out'):a.add_argument('--'+name,required=True)
    a.add_argument('--step',required=True,type=int);a.add_argument('--token')
    a=s.add_parser('packet')
    for name in ('config','review','order','out'):a.add_argument('--'+name,required=True)
    a=p.parse_args()
    if a.cmd=='prepare':prepare(a.family,a.done,a.step,a.metadata,a.out,a.token)
    else:packet(a.config,a.review,a.order,a.out)
if __name__=='__main__':main()
