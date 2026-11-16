"""Sealed packet and allocation wrapper using the accepted staging and return code."""
import argparse
from copy import deepcopy
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import shutil
import stat
import tarfile
import tempfile
import traceback
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
    if resume and not str(resume.get('path','')).startswith('/project/community/'):
        raise ValueError('resume archive must be on shared project storage')
    for key in ('a','b','c','d'):
        check_packet_tar(records[key]['path'])
    out=Path(dest);out.mkdir(parents=True,exist_ok=False)
    shared=Path(PREFIX)/'p'/token
    config=dict(schema='a15-v1',token=token,deadline_utc=deadline,added=records,family=family,
                resume=resume,limits=family['limits']['full'])
    config['binding']=digest(config);dump(out/'a.json',config)
    # Only the small wrapper is read before staging the pinned archives.
    for name in ('o.py','adapter.py','budget.py','venue.py','paths.py'):
        (out/name).write_bytes((Path(__file__).parent/name).read_bytes())
    text='#!/bin/bash\n#SBATCH --account=mt01\n#SBATCH --partition=general\n#SBATCH --gres=gpu:h100:1\n#SBATCH --time=07:00:00\n#SBATCH --job-name=a15_cot_ap'+token+'\n'
    text+='#SBATCH --output=/dev/null\nset -euo pipefail\n'
    import shlex
    text+='exec /usr/bin/python3 -s -B '+shlex.quote(str(shared/'o.py'))+' run --config '+shlex.quote(str(shared/'a.json'))+'\n'
    (out/'a.sh').write_text(text);dump(out/'b.json',dict(config=pin(out/'a.json'),batch=pin(out/'a.sh'),submitted=False))
    return config


def check_packet_tar(path):
    """Admit only the entry types that the addition extractor can stage."""
    with tarfile.open(path) as archive:
        for member in archive:
            if not (member.isfile() or member.isdir()):
                raise ValueError('input tar contains a non-file/non-directory member: '+str(path)+': '+member.name)


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


def exception_record(error):
    return dict(error=type(error).__name__+': '+str(error),
                traceback=''.join(traceback.format_exception(error)))


def omitted_prepare(path):
    parts=path.parts
    return ('store' in parts or parts[0]=='v' or path.name.endswith('.next')
            or (parts[:3]==('cell','g','raw') and path.suffix=='.npz'))


def optional_geometry(path):
    # The report verifies i/ metadata and bound proof, but never loads these arrays.
    return path.parts[:3]==('cell','g','scaled') and path.suffix=='.npz'


def inventory(runroot,selected):
    records=[]
    for p in sorted(runroot.rglob('*')):
        info=p.lstat()
        if stat.S_ISDIR(info.st_mode):continue
        rel=str(p.relative_to(runroot))
        row=dict(path=rel,bytes=info.st_size,suffix=p.suffix,excluded=rel not in selected)
        if stat.S_ISREG(info.st_mode) and info.st_size<50_000_000:
            try:row['sha256']=sha(p)
            except OSError as error:row['hash_error']=exception_record(error)
        records.append(row)
    return dict(files=records,excluded=[r['path'] for r in records if r['excluded']])


def attach(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    try:os.link(source,target)
    except OSError:shutil.copyfile(source,target)


def build_return(root,runroot,dest,config,rc,failure,phase_error=None,return_error=None,minimal=False,trim=False):
    dest.mkdir(parents=True,exist_ok=False);selected={}
    protected={'RESULT.json','MERGED.json','COMPLETE.json','PROOF.json','CANARY.json'}
    for p in sorted(runroot.rglob('*')):
        rel=p.relative_to(runroot)
        if p.is_symlink():
            if minimal:continue
            raise ValueError('return contains a link: '+str(rel))
        if not p.is_file():continue
        keep=not omitted_prepare(rel)
        if trim and optional_geometry(rel):keep=False
        if minimal:
            keep=(p.name in protected or p.suffix=='.jsonl' and rel.parts[0].startswith('j')
                  or str(rel)=='PHASES.json')
        if p.name=='FAILURE.json' and (phase_error or return_error):continue
        if keep:selected[str(rel)]=p
    # Preflight before attaching files or creating the archive.
    if not minimal and not trim and (sum(p.stat().st_size for p in selected.values())>512*1024**2
                                      or len(selected)>9990):
        selected={n:p for n,p in selected.items() if not optional_geometry(Path(n))}
    for rel,p in selected.items():
        if rel=='COMPLETE.json':continue  # The wrapper owns the top-level completion marker.
        attach(p,dest/rel)
    for name in ('a.log','b.log','STAGING.json'):
        source=root/name
        if source.is_file():
            if minimal and name.endswith('.log'):
                with source.open('rb') as stream:
                    stream.seek(max(0,source.stat().st_size-2*1024**2))
                    (dest/name).write_bytes(stream.read())
            else:attach(source,dest/name)
    if minimal:
        for name in ('a.log','b.log'):
            if not (dest/name).exists():(dest/name).write_text('')
        if not (dest/'STAGING.json').exists():dump(dest/'STAGING.json',dict(unavailable=True))
        if not (dest/'PHASES.json').exists():dump(dest/'PHASES.json',[])
    if phase_error or return_error:
        dump(dest/'FAILURE.json',dict(error=failure or (phase_error or {}).get('error'),phase_error=phase_error,return_error=return_error))
        if (runroot/'FAILURE.json').exists():selected['FAILURE.json']=runroot/'FAILURE.json'
    dump(dest/'INVENTORY.json',inventory(runroot,selected))
    partial=True
    if not minimal and (runroot/'RESULT.json').exists():partial=bool(load(runroot/'RESULT.json').get('missing'))
    dump(dest/'COMPLETE.json',dict(complete=rc==0 and not minimal,partial=partial,
        failure=failure,plan_sha256=config['binding'],synthetic=False))
    return dest


def finish_return(module,root,runroot,config,rc,failure,phase_error=None):
    """A return failure must not hide the phase error or bypass both channels."""
    try:
        if phase_error is None and (runroot/'FAILURE.json').is_file():
            phase_error=load(runroot/'FAILURE.json').get('phase_error')
        source=build_return(root,runroot,root/'return',config,rc,failure,phase_error)
        try:
            value=publish_read(module,source,config['token'],config['binding'],rc)
        except module.S.BudgetError:
            # A compressed cap may be reached even when the expanded cap passes.
            if not any(optional_geometry(p.relative_to(source)) for p in source.rglob('*.npz')):raise
            source=build_return(root,runroot,root/'return_trimmed',config,rc,failure,phase_error,trim=True)
            value=publish_read(module,source,config['token'],config['binding'],rc)
        if value.get('returned') is False:raise RuntimeError('full return was not published: '+str(value))
        return value
    except BaseException as error:
        return_error=exception_record(error)
    # A fresh directory keeps partial full archives out of the fallback.
    try:
        source=build_return(root,runroot,root/'return_minimal',config,rc or 1,failure,
                            phase_error,return_error,minimal=True)
        value=publish_read(module,source,config['token'],config['binding'],rc or 1)
        if value.get('returned') is False:raise RuntimeError('minimal return was not published: '+str(value))
        return value
    except OSError as error:
        # Independent local storage also covers ENOSPC while the publisher archives.
        return_error=dict(return_error, fallback_storage_error=exception_record(error))
        emergency=Path(tempfile.mkdtemp(prefix='a15_return_'+config['token']+'_',dir='/dev/shm'))
        source=build_return(root,runroot,emergency/'return',config,rc or 1,failure,
                            phase_error,return_error,minimal=True)
        return publish_read(module,source,config['token'],config['binding'],rc or 1)


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
    S,H,R,J,B=imports()
    original=deepcopy(config['family']['parent_config'])
    runtime=None;rc=1;runroot=root/'run';runroot.mkdir();failure=None;phase_error=None
    try:
        J.card(require_empty=True)
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
                  device='cuda:0',deadline_utc=config['deadline_utc'],weights='/a/model.safetensors',tower_config='/a/config.json',proof_core='/scratch/jjyeung/orch_cd/evalx/work/milestone')
        dump(root/'d/s.json',spec)
        (root/'e').mkdir()
        for n in ('c.json','d.json','e.json','s.json','f.jsonl','g.jsonl'):(root/'e'/n).write_bytes((root/'d'/n).read_bytes())
        segment='j0';resume=[]
        if config.get('resume'):
            descriptor=config['resume'];archive=checked(descriptor)
            extract(archive,runroot,1_000_000_000)
            prior=load(runroot/'RESULT.json')
            if prior.get('failure'):raise ValueError('failed phase requires operator review')
            resume=prior.get('segments',[prior['segment']]);segment='j'+str(len(resume))
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
        read_ns=namespace(root,bindings,gpu=os.environ['CUDA_VISIBLE_DEVICES'])
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
                if '--deadline-utc' in args:
                    args=list(args);args[args.index('--deadline-utc')+1]=budget.worker_deadline(remaining)
                rc=run_phase(prefix+tail+[entry]+args,entry,runroot,env,stream,remaining)
        result=load(runroot/'RESULT.json');result['segments']=[Path(p).name for p in resume]+[segment];dump(runroot/'RESULT.json',result)
    except BaseException as error:
        failure=str(error);phase_error=exception_record(error);rc=rc or 1
        try:
            dump(runroot/'FAILURE.json',dict(error=failure,phase_error=phase_error,return_error=None))
            journals=sorted(runroot.glob('j*/COMPLETE.json'))
            done={k for p in journals for k in load(p).get('keys',[])}
            dump(runroot/'RESULT.json',dict(complete=False,missing=[k for k in config['family']['inputs']['keys'] if k not in done],
                segments=[p.parent.name for p in journals],failure=failure))
        except BaseException as receipt_error:
            phase_error['receipt_error']=exception_record(receipt_error)
    finally:
        return finish_return(R,root,runroot,config,rc,failure,phase_error)


def run_phase(command,entry,runroot,env,stream,remaining):
    """A proof failure is a receipt; other phase failures stop the job."""
    try:
        result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining)
        if result.returncode:raise RuntimeError('worker exit '+str(result.returncode)+'; see b.log')
        if entry=='/x/p.py':
            proof=load(Path(runroot)/'p/PROOF.json')
            if proof.get('synthetic') is not False or proof.get('items')!=10 or not all(k in proof for k in ('identical_count','equal_token_share','records','proven')):
                raise ValueError('proof receipt is incomplete')
    except Exception as error:
        if entry!='/x/p.py':raise
        details=exception_record(error)
        dump(Path(runroot)/'FAILURE.json',dict(error=str(error),phase_error=details,return_error=None))
        dump(Path(runroot)/'p/PROOF.json',dict(status='failed',failed=True,synthetic=False,items=10,
            identical_count=None,equal_token_share=None,records=[],proven=False,
            error=type(error).__name__+': '+str(error)))
    return 0


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
