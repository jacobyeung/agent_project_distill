"""Whole-worker CPU rehearsal entry point. Requires the supplied production environment.

This harness preserves production validators and source bytes. Its fake allocation,
model load, model forward/prefill, and generation are explicitly fixture boundaries.
It never supplies a production admission or permission to launch.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tarfile
import time

B=Path(__file__).resolve().parents[2]
W=B.parents[1]/'work'
PY=Path(sys.executable)
LOGICAL=Path('/scratch/jjyeung/orch_cd/evalx/work/milestone')
FAMILY=B/'out/c8r/FAMILY_C8R.json'

def load(p):return json.loads(Path(p).read_text())
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as s:
        for chunk in iter(lambda:s.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()
def physical(root,p):
    p=Path(p)
    for old,new in (('/scratch/jjyeung','sj'),
        ('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','fsw'),
        ('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap','fsw/ap')):
        try:return root/new/p.relative_to(old)
        except ValueError:pass
    raise ValueError('Unmapped logical path: '+str(p))
def owned_bytes(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
def limits(dest):
    free=shutil.disk_usage(B).free
    if free<=120*10**9:raise RuntimeError('Rehearsal start requires more than 120 GB free')
    value=dict(free_bytes_start=free,run_budget_bytes=2*1024**3,build_budget_bytes=4000000000,
        df=subprocess.check_output(['df','-B1','/scratch'],universal_newlines=True),fixture=True)
    dump(dest/'LIMITS.json',value)
    if owned_bytes(B)>=4000000000:raise RuntimeError('Build storage budget exceeded')
    return value
def prerequisites():
    absent=[]
    if not PY.is_file():absent.append(str(PY))
    for name in ('masks','geometry','numpy','frames'):
        if not (W/'streams'/(name+'.done')).is_file():absent.append(str(W/'streams'/(name+'.done')))
    return absent
def extract(path,destination,remaining):
    with tarfile.open(str(path)) as archive:
        entries=archive.getmembers()
        required=sum(m.size for m in entries if m.isfile())
        if required>remaining:raise RuntimeError('Archive expansion exceeds owned storage budget')
        for entry in entries:
            name=Path(entry.name)
            if name.is_absolute() or '..' in name.parts or not (entry.isfile() or entry.isdir()):
                raise ValueError('Unsafe archive entry '+entry.name)
            target=destination/name
            if entry.isdir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(entry) as source,target.open('xb') as output:
                shutil.copyfileobj(source,output,1024**2)
            target.chmod(entry.mode&0o755)

def stage(dest):
    family=load(FAMILY)
    prior=load(B.parent/'01_c8/out/c8/FAMILY_C8.json')
    oldcode=next(p for p in prior['assets']['small_objects'] if p['role']=='code')
    shared=B.parent/'01_c8/work/rehearsal_assets'/oldcode['sha256'][:16]
    if load(shared/'STAGED.json')['code_sha256']!=oldcode['sha256']:
        raise ValueError('Shared staging identity differs')
    for part in family['assets']['small_objects']:
        if part['role']!='code' and part!=next(x for x in prior['assets']['small_objects'] if x['role']==part['role']):
            raise ValueError('Shared input descriptor differs')
    if family['assets']['frames_inventory']!=prior['assets']['frames_inventory']:
        raise ValueError('Shared frame inventory differs')
    code=next(p for p in family['assets']['small_objects'] if p['role']=='code')
    path=B/'out/c8r/code_c8r.tar'
    if path.stat().st_size!=code['bytes'] or sha(path)!=code['sha256']:
        raise ValueError('New code object differs')
    root=B/'work/rehearsal_assets'/code['sha256'][:16]
    if not root.exists():
        root.mkdir(parents=True)
        extract(path,root,4000000000-owned_bytes(B))
        physical(root,LOGICAL/'runs').mkdir(parents=True,exist_ok=True)
    dump(dest/'STAGING.json',dict(shared=str(shared),code=str(root),shared_read_only=True))
    return shared

def namespace(root,dest,mode):
    family=load(FAMILY)
    trainer=physical(root,family['assets']['trainer_logical_archive'])
    if not trainer.is_file():raise ValueError('Shared trainer is unavailable')
    if sha(trainer)!=family['assets']['trainer']['sha256']:raise ValueError('Trainer archive differs')
    args=['/usr/bin/bwrap','--unshare-net','--unshare-uts','--hostname','orchard-cpu-fixture']
    for system in ('/usr','/etc','/bin','/sbin','/lib','/lib64','/opt'):
        if os.path.exists(system):args+=['--ro-bind',system,system]
    args+=['--proc','/proc','--dev','/dev','--ro-bind','/dev/shm','/dev/shm','--tmpfs','/tmp','--tmpfs','/scratch',
        '--ro-bind',str(root/'sj'),'/scratch/jjyeung',
        '--ro-bind',str(root/'fsw'),'/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung',
        '--ro-bind',str(root/'fsw/ap'),'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap',
        '--ro-bind',str(B.parents[1]),str(B.parents[1]),'--ro-bind',str(W),str(W),'--bind',str(B),str(B),
        '--ro-bind',str(PY.parent.parent.resolve()),str(PY.parent.parent),
        '--ro-bind',str(W/'tree'),family['assets']['tree_root'],
        '--die-with-parent']
    token='c80000001' if mode=='pilot' else 'c80000002'
    run=LOGICAL/'runs'/token
    code=Path(load(dest/'STAGING.json')['code'])
    mapped_runs=physical(code,run.parent)
    local_runs=dest/'runs';local_run=local_runs/token;local_run.mkdir(parents=True)
    (dest/'cache').mkdir()
    os.symlink('runs/'+token,dest/'run')
    code_part=next(p for p in family['assets']['small_objects'] if p['role']=='code')
    for member in sorted(code_part['members']):
        if not member.startswith('sj/'):raise ValueError('Unexpected code member root')
        logical=Path('/scratch/jjyeung')/member[3:]
        args+=['--ro-bind',str(code/member),str(logical)]
    args+=['--bind',str(local_runs),str(run.parent),'--bind',str(local_runs),str(physical(root,run.parent))]
    base_files=list((W/'base').glob('models--Qwen--Qwen3.5-9B/snapshots/*'))
    if len(base_files)!=1:raise ValueError('Expected one supplied base snapshot')
    model=load(physical(root,family['assets']['model_manifest']['path']))
    args+=['--ro-bind',str(base_files[0]),model['root'],
        '--setenv','HF_HUB_OFFLINE','1','--setenv','TRANSFORMERS_OFFLINE','1',
        '--setenv','HF_HOME',str(dest/'cache'),'--setenv','XDG_CACHE_HOME',str(dest/'cache'),
        '--setenv','TMPDIR',str(dest/'cache'),
        '--setenv','SLURM_JOB_ID','80000000','--setenv','CUDA_VISIBLE_DEVICES','0',
        '--setenv','LEGS1_TREE',family['assets']['tree_root'],
        '--setenv','LEGS1_VENDOR','/scratch/jjyeung/orch_cd/legs1_reads/work/vendor',
        '--chdir',str(B),str(PY),'-I','-s','-B',str(Path(__file__).resolve()),
        '--inside','--mode',mode,'--dest',str(dest),'--stage',str(root)]
    return args

def config_fixture(root,mode):
    sys.path[:0]=[str(LOGICAL/'orchard_native'),str(LOGICAL)]
    import native_common as C
    import native_metrics as M
    cfg=load(W/'p9/metadata/CONFIG.json');family=load(FAMILY)
    token='c80000001' if mode=='pilot' else 'c80000002'
    cfg.update(mode=mode,token=token,logical_run=str(LOGICAL/'runs'/token),
        assets=deepcopy(family['assets']),limits=deepcopy(family['limits'][mode]),
        worker=dict(deepcopy(family['worker_contract']),artifact=cfg['worker']['artifact']))
    controls=Path(cfg['logical_run'])/'fixture_controls';controls.mkdir()
    (controls/'FAMILY.json').write_bytes(FAMILY.read_bytes())
    cfg['family']=C.pin(controls/'FAMILY.json')
    if mode=='full':
        r=load(W/'p9/native/probe/PILOT_REPORT.json')
        r['family_sha256']=cfg['family']['sha256']
        parity=load(W/'p9/native/probe/GPU_PARITY.json')
        complete=dict(family=cfg['family'],mode='pilot',synthetic=False,training_decision_allowed=False,
            artifact=r['artifact'],plan_sha256=r['plan_sha256'])
        receipt=dict(synthetic=False,status='COMPLETE',complete=True,returncode=0,plan_sha256=r['plan_sha256'])
        scenario='none_capped'
        cfg['full_projection']=dict(fixture=True,fixture_source=str(W/'p9/native/probe/PILOT_REPORT.json'),
            report=r,parity=parity,complete=complete,receipt=receipt,
            report_canonical_sha256=C.canonical(r),projection_scenario=scenario,projection=M.project(r,scenario))
    cfg['authorization'].update(mode=mode,token=token,family_sha256=cfg['family']['sha256'])
    if mode=='full':cfg['authorization']['projection_scenario']='none_capped'
    order=controls/'ORDER.md';order.write_text(C.order_line(cfg)+'\n')
    cfg['authorization']['orch_order']=C.pin(order)
    review=controls/'REVIEW.json'
    dump(review,dict(verdict='ACCEPT',reviewer='CPU fixture; no production authority',synthetic=False,
                     family_sha256=cfg['family']['sha256']))
    cfg['review']=C.pin(review);cfg['plan_sha256']=C.plan(cfg)
    dump(controls/'FIXTURE_IDENTITY.json',dict(fixture=True,production_authority=False,
        standins=['allocation identity','model load','forward/prefill heads','token generation'],
        mode=mode,config=cfg))
    return cfg

def install_cloud_fixture(dest):
    bindir=dest/'bin';bindir.mkdir()
    cli=bindir/'gcloud'
    cli.write_text('#!/bin/sh\nexec '+str(PY)+' -I -s -B '+str(B/'out/tests/fake_gcloud.py')+' "$@"\n')
    cli.chmod(0o755)
    os.environ['PATH']=str(bindir)+':'+os.environ['PATH']
    os.environ['C8R_CLOUD_STORE']=str(dest/'cloud')

def inside(args):
    root=Path(args.stage);dest=Path(args.dest)
    overlays=[p for p in (root/'np226').rglob('numpy/__init__.py') if p.parent.name=='numpy' and (p.parents[1]/'scipy').is_dir()]
    if len(overlays)!=1:raise ValueError('Numpy overlay has no unique package root')
    sys.path[:0]=[str(overlays[0].parents[1]),str(W/'pyextra'),str(LOGICAL/'orchard_native'),
                  str(LOGICAL/'native/out2'),str(LOGICAL),str(W/'tree'),str(Path(__file__).parent)]
    import numpy,torch,transformers,coverage
    if (sys.version_info[:2],torch.__version__.split('+')[0],transformers.__version__,numpy.__version__)!=(
        (3,12),'2.11.0','5.12.1','2.2.6'):
        raise RuntimeError('Production interpreter/package versions differ')
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    covdir=B/'out/coverage'/args.mode;covdir.mkdir(parents=True,exist_ok=True)
    cov=coverage.Coverage(branch=True,data_file=str(covdir/'.coverage'),data_suffix=True,
        source=[str(LOGICAL),str(W/'tree')]);cov.start()
    outcome={'fixture':True,'mode':args.mode,'whole_worker_complete':False}
    try:
        import cpu_boundary
        cpu_boundary.install(root,dest)
        cfg=config_fixture(root,args.mode)
        import native_worker as worker
        import native_job as job
        import native_common as C
        import orchard_results as results
        report=worker.run(cfg)
        receipts=job.terminal(root,cfg)
        source=Path(cfg['logical_run'])
        C.dump(source/'COMPLETE.json',dict(schema='evalx-orchard-native-complete-v1',synthetic=False,
            mode=args.mode,plan_sha256=cfg['plan_sha256'],artifact=cfg['worker']['artifact'],family=cfg['family'],
            step=cfg['step'],training_decision_allowed=False,receipts=receipts))
        results.AUTHORIZED_POOL=dest/'pool'
        results.write_test(results.AUTHORIZED_POOL,cfg['token'])
        install_cloud_fixture(dest)
        returned=results.publish(source,results.AUTHORIZED_POOL,cfg['token'],cfg['plan_sha256'],0,
                                 mode=args.mode,cloud_config=cfg['assets']['gcloud_config'])
        archive=results.AUTHORIZED_POOL/cfg['token']/'result.tar.gz'
        results.verify(returned,archive,cfg['plan_sha256'])
        if args.mode=='pilot':
            import native_metrics as M
            M.from_return(results.AUTHORIZED_POOL/cfg['token']/'EXIT.json',archive,
                          cfg['family']['sha256'],cfg['worker']['artifact'],'none_capped')
        outcome.update(whole_worker_complete=True,terminal_receipts=receipts,return_chain_verified=True)
    except Exception as error:
        import traceback
        outcome.update(error=str(error),traceback=traceback.format_exc())
        raise
    finally:
        cov.stop();cov.save()
        combined=coverage.Coverage(branch=True,data_file=str(covdir/'.coverage'))
        combined.combine(keep=True);combined.save()
        combined.json_report(outfile=str(covdir/'coverage.json'))
        outcome['coverage_combine']='coverage combine API, keep=True; one serving process'
        outcome.update(owned_bytes=owned_bytes(dest),free_bytes_end=shutil.disk_usage(B).free)
        dump(dest/'RESULT.json',outcome)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('pilot','full'),required=True)
    p.add_argument('--dest',required=True);p.add_argument('--inside',action='store_true');p.add_argument('--stage')
    p.add_argument('--shards',type=int,default=1)
    args=p.parse_args()
    if args.shards!=1:
        p.error('Production run/merge has no shard protocol; use --shards 1. See out/SHARDING.md.')
    dest=Path(args.dest).resolve()
    try:dest.relative_to(B/'work')
    except ValueError:raise ValueError('Destination must be under this build/work/')
    if args.inside:return inside(args)
    dest.mkdir(parents=True,exist_ok=False)
    limits(dest)
    absent=prerequisites()
    if absent:
        dump(dest/'RESULT.json',dict(status='BLOCKED',fixture=True,whole_worker_complete=False,missing=absent))
        print(json.dumps(dict(status='BLOCKED',missing=absent)));return 2
    probe=subprocess.run(['/usr/bin/bwrap','--ro-bind','/','/','--unshare-net','/bin/true'],capture_output=True,text=True)
    if probe.returncode:
        dump(dest/'RESULT.json',dict(status='BLOCKED',fixture=True,whole_worker_complete=False,
             reason='Namespace unavailable; no staging attempted',returncode=probe.returncode,stderr=probe.stderr))
        return 2
    root=stage(dest)
    command=namespace(root,dest,args.mode)
    dump(dest/'COMMAND.json',dict(command=command,fixture=True))
    with (dest/'worker.log').open('xb') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        while process.poll() is None:
            time.sleep(60)
            if owned_bytes(dest)>2*1024**3 or owned_bytes(B)>4000000000:
                process.terminate()
                process.wait()
                dump(dest/'STORAGE_REFUSAL.json',dict(fixture=True,reason='Owned storage budget exceeded',
                    run_bytes=owned_bytes(dest),build_bytes=owned_bytes(B)))
                return 3
        return process.returncode

if __name__=='__main__':sys.exit(main())
