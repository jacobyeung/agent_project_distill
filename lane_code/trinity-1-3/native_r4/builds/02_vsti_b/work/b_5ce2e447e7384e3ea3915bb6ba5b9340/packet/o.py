"""Sealed packet and allocation wrapper using the accepted staging and return code."""
import argparse
from copy import deepcopy
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from adapter import *
from budget import DEFAULT,Budget
from venue import extract

PREFIX='/project/community/jjyeung/okh7/d9c35d0a/'
CLOUD='q8/d9c35d0a/'


def imports():
    import paths
    sys.path.extend([str(paths.CORE/'orchard_native'),str(paths.CORE)])
    import native_stage,orchard_stage,orchard_results,native_job,native_bootstrap
    return native_stage,orchard_stage,orchard_results,native_job,native_bootstrap


def validate_additions(records):
    if set(records)!={'a','b','c','d'}:raise ValueError('four pinned additions required')
    for key,r in records.items():
        if r.get('path')!=PREFIX+key+'.tar' or r.get('name')!=CLOUD+key+'.tar':raise ValueError('opaque asset location differs')
        if not re.fullmatch('[0-9a-f]{64}',r.get('sha256','')) or type(r.get('bytes')) is not int or r['bytes']<=0:
            raise ValueError('asset SHA and size required')
        if not str(r.get('generation','')).isdigit():raise ValueError('verified second-copy generation required')
        if r.get('verified') is not True:raise ValueError('both upload copies must be verified')
    return records


def packet(family_path,receipt_path,dest,token,deadline=DEFAULT,resume=None):
    if not re.fullmatch('[a-f0-9]{24,32}',token):raise ValueError('opaque token required')
    family=load(family_path);records=validate_additions(load(receipt_path))
    for key in ('c','d'):
        if records[key]['sha256']!=family['added'][key]['sha256']:raise ValueError('packet asset differs from family')
    for key in ('a','b'):
        expected=family['added'].get(key,{}).get('sha256')
        if expected and records[key]['sha256']!=expected:raise ValueError('late asset differs from family')
    out=Path(dest);out.mkdir(parents=True,exist_ok=False)
    config=dict(schema='a15-v1',token=token,deadline_utc=deadline,added=records,family=family,
                resume=resume,limits=family['limits']['full'])
    config['binding']=digest(config);dump(out/'a.json',config)
    # Only the small wrapper is read before staging the pinned archives.
    for name in ('o.py','adapter.py','budget.py','venue.py','paths.py'):
        (out/name).write_bytes((Path(__file__).parent/name).read_bytes())
    text='#!/bin/bash\n#SBATCH --account=mt01\n#SBATCH --partition=general\n#SBATCH --gres=gpu:h100:1\n#SBATCH --time=07:00:00\n#SBATCH --job-name=a15_cot_ap'+token+'\n'
    text+='#SBATCH --output='+str(out.resolve())+'/a.log\nset -euo pipefail\n'
    import shlex
    text+='exec /usr/bin/python3 -s -B '+shlex.quote(str(out.resolve()/'o.py'))+' run --config '+shlex.quote(str(out.resolve()/'a.json'))+'\n'
    (out/'a.sh').write_text(text);dump(out/'b.json',dict(config=pin(out/'a.json'),batch=pin(out/'a.sh'),submitted=False))
    return config


def staged_addition(record,root,key,S,H):
    archive=Path(root)/('x'+key+'.tar')
    # A missing primary copy selects the pinned cloud copy; failures are never retried.
    if Path(record['path']).is_file():receipt=S.copied(record,archive)
    else:
        receipt=H.copy_parts([record],archive,lambda p:H.process_stream(
            ['/usr/bin/gcloud','storage','cat',S.cloud_uri(p)],H.cloud_environment('/project/community/jjyeung/gcloud'),Path(root)/'a.log'),expected_sha=record['sha256'])
    if receipt['bytes']!=record['bytes']:raise ValueError('asset length differs')
    target=Path(root)/key;extract(archive,target,record.get('expanded_bytes',100_000_000_000))
    return receipt


def return_members(source):
    """Keep every committed read artifact under the inherited size limits."""
    source=Path(source);result={};total=0
    for p in sorted(source.rglob('*')):
        if p.is_symlink():raise ValueError('return contains a link')
        if not p.is_file():continue
        if p.suffix not in ('.json','.jsonl','.npz','.md','.log'):
            raise ValueError('unexpected return member')
        total+=p.stat().st_size
        if total>512*1024**2 or len(result)>=10000:raise ValueError('expanded return exceeds cap')
        result[str(p.relative_to(source))]=p
    return result


def publish_read(module,source,token,binding,code):
    original=module.S.members
    module.S.members=return_members
    try:return module.publish(source,module.AUTHORIZED_POOL,token,binding,code,synthetic=False,mode='full')
    finally:module.S.members=original


def run(config_path):
    config=load(config_path)
    if digest({k:v for k,v in config.items() if k!='binding'})!=config['binding']:raise ValueError('packet binding differs')
    validate_additions(config['added'])
    job=os.environ.get('SLURM_JOB_ID','')
    if not job.isdigit() or os.environ.get('SLURM_JOB_PARTITION')!='general':raise ValueError('general allocation required')
    root=Path('/tmp')/('a15_'+job+'_'+config['token']);root.mkdir()
    # Bootstrap only the authenticated code archive, then import its inherited stage modules.
    code_record=config['added']['c'];source=Path(code_record['path'])
    if source.stat().st_size!=code_record['bytes'] or sha(source)!=code_record['sha256']:raise ValueError('code archive differs')
    extract(source,root/'c',20_000_000)
    if sha(__file__)!=sha(root/'c/o.py'):raise ValueError('packet wrapper differs from code archive')
    for n in ('adapter','budget','venue'):
        if sha(sys.modules[n].__file__)!=sha(root/'c'/(n+'.py')):raise ValueError('packet helper differs from code archive')
    sys.path.insert(0,str(root/'c'));sys.modules.pop('paths',None)
    S,H,R,J,B=imports();J.card(require_empty=True)
    original=deepcopy(config['family']['parent_config'])
    runtime=None;rc=1;runroot=root/'run';runroot.mkdir();failure=None
    try:
        J.J.storage_proof(root,job=job)
        old=S.stage(root,original)
        for key in ('a','b','d'):staged_addition(config['added'][key],root,key,S,H)
        # Place the historical return at the exact paths authenticated by its request.
        request=load(root/'d/native/paired/request.json')
        logical=Path(request['grounding']['geometry_manifest']['path']).parents[2]
        import shutil
        shutil.copytree(root/'d/native/geometry',S.physical(root,logical)/'native/geometry',dirs_exist_ok=False)
        tower=root/'a/model.safetensors'
        from importlib.util import spec_from_file_location,module_from_spec
        # Weight/config hashes are the trainer's frozen constants, also sealed in the family.
        for name,h in config['family']['tower_members'].items():
            if sha(root/'a'/name)!=h:raise ValueError('frozen member differs')
        dump(root/'a/model.safetensors.RECEIPT.json',dict(sha256=sha(tower),bytes=tower.stat().st_size))
        spec=dict(tree=original['assets']['tree_root'],artifact=request['artifact'],config=request['config'],data_receipt=request['data_receipt'],
                  device='cuda:0',weights='/a/model.safetensors',tower_config='/a/config.json',proof_core='/scratch/jjyeung/orch_cd/evalx/work/milestone')
        dump(root/'d/s.json',spec)
        (root/'e').mkdir()
        for n in ('c.json','d.json','e.json','s.json','f.jsonl','g.jsonl'):(root/'e'/n).write_bytes((root/'d'/n).read_bytes())
        segment='j0';resume=[]
        if config.get('resume'):
            descriptor=config['resume'];archive=checked(descriptor)
            extract(archive,runroot,1_000_000_000)
            prior=load(runroot/'RESULT.json');resume=prior.get('segments',[prior['segment']]);segment='j'+str(len(resume))
            resume=['/r/'+n for n in resume]
        for name in ('home','temp','cache'):(root/name).mkdir(exist_ok=True)
        runtime=old['runtime_spec'];runtime['entrypoints']={n:dict(path='/x/'+n,sha256=sha(root/'c'/n)) for n in ('a.py','p.py')}
        dump(root/'z.json',runtime)
        worker=dict(bootstrap=str(root/'c/sj/orch_cd/evalx/work/milestone/native_bootstrap.py'),runtime=str(root/'z.json'),segment=segment,resume=resume)
        dump(root/'w.json',worker)
        S.physical(root,original['logical_run']).mkdir(parents=True,exist_ok=True);(root/'shm').mkdir()
        # Proof sees the original inputs; the read sees only its frames, heads and tower.
        proof_ns=S.namespace(root,original)
        proof_ns+=['--bind',str(runroot),'/r','--ro-bind',str(root/'c'),'/x','--ro-bind',str(root/'d'),'/d',
                   '--bind',str(root/'shm'),'/dev/shm']
        from venue import namespace,FSW,AP
        bindings=[(root/'fsw',FSW,False),(root/'m/ap',AP,False),
                  (S.physical(root,original['assets']['tree_root']),original['assets']['tree_root'],False),
                  (root/'c','/x',False),(root/'c',root/'c',False),(root/'a','/a',False),
                  (root/'b','/b',False),(root/'e','/d',False)]
        for value in runtime['import_paths'].values():bindings.append((value,value,False))
        venv=Path(runtime['python']['path']).parent.parent
        bindings += [(venv,venv,False),(root/'z.json',root/'z.json',False),(root/'w.json',root/'w.json',False)]
        for n in ('home','temp','cache'):bindings.append((root/n,root/n,True))
        # Authenticated runtime overlays use physical paths under the job-local root.
        read_ns=namespace(root,bindings,gpu=0)
        tail=[runtime['python']['path'],'-I','-s','-B',worker['bootstrap'],'--spec',worker['runtime'],'--']
        env=J.environment(root);env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1'
        budget=Budget(config['deadline_utc']);gpu_started=time.monotonic()
        phases=[(read_ns, '/x/a.py',['--config',str(root/'w.json'),'--deadline-utc',config['deadline_utc'],'--phase','prepare'])]
        if not resume:
            phases.append((proof_ns,'/x/p.py',['--reference','/d/a.json','--request','/d/native/paired/request.json',
                                            '--spec','/d/s.json','--out','/r/p']))
        phases.append((read_ns,'/x/a.py',['--config',str(root/'w.json'),'--deadline-utc',config['deadline_utc'],'--phase','read']))
        with (root/'b.log').open('w') as stream:
            for prefix,entry,args in phases:
                remaining=min(budget.remaining(),21600-(time.monotonic()-gpu_started))
                if remaining<=0:raise TimeoutError('deadline before next phase')
                result=subprocess.run(prefix+tail+[entry]+args,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining)
                rc=result.returncode
                if rc:raise RuntimeError('worker failed; see b.log')
        result=load(runroot/'RESULT.json');result['segments']=[Path(p).name for p in resume]+[segment];dump(runroot/'RESULT.json',result)
    except BaseException as error:
        failure=str(error);dump(runroot/'FAILURE.json',dict(error=failure));rc=rc or 1
    finally:
        # Return the journal and prepared geometry, not frame pixels or raw tower caches.
        returned=root/'return';returned.mkdir()
        for p in runroot.rglob('*'):
            if not p.is_file() or '/store/' in str(p) or ('/g/raw/' in str(p) and p.suffix=='.npz') or p.relative_to(runroot).parts[0]=='v' or p.name.endswith('.next'):continue
            target=returned/p.relative_to(runroot);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
        for name in ('a.log','b.log','STAGING.json'):
            if (root/name).is_file():(returned/name).write_bytes((root/name).read_bytes())
        dump(returned/'COMPLETE.json',dict(complete=rc==0,partial=bool(load(runroot/'RESULT.json').get('missing')) if (runroot/'RESULT.json').exists() else True,
            failure=failure,plan_sha256=config['binding'],synthetic=False))
        return publish_read(R,returned,config['token'],config['binding'],rc)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('packet')
    for n in ('family','receipts','out','token'):q.add_argument('--'+n,required=True)
    q.add_argument('--deadline-utc',default=DEFAULT);q.add_argument('--resume')
    q=sub.add_parser('run');q.add_argument('--config',required=True)
    a=p.parse_args()
    if a.command=='packet':return packet(a.family,a.receipts,a.out,a.token,a.deadline_utc,load(a.resume) if a.resume else None)
    return run(a.config)
if __name__=='__main__':main()
