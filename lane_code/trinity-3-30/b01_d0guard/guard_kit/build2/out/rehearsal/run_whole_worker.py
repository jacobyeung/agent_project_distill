"""Operator entry: local staging, two checkpoint processes, publish/fetch/report."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work';K=B/'out/guard_kit'
sys.path[:0]=[str(K),str(Path(__file__).parent)]
from guard_core import read,write,sha,digest
from transport import Publisher,archive_result,copy_verified,verify_return,extract
from worker import coordinate
from prepare_whole import prepare
LOGICAL=Path('/scratch/jjyeung/orch_cd/evalx/work/milestone')
SHARED=W/'from113/builds/01_c8/work/rehearsal_assets/d03de829ae52386f'

def namespace(dest,fixture):
    cfg=read(fixture/'WORKER.json');prep=read(fixture/'PREPARATION.json')
    model=read(SHARED/'fsw/ap/e84d901c/arm/frozen/6f27ae81/model.json')
    base=W/'from113/work/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
    args=['/usr/bin/bwrap','--unshare-net','--unshare-uts','--hostname','g2-cpu-fixture']
    for name in ('usr','etc','bin','sbin','lib','lib64','opt'):
        p=Path('/')/name
        if p.exists():args+=['--ro-bind',str(p),str(p)]
    args+=['--proc','/proc','--dev','/dev','--ro-bind','/dev/shm','/dev/shm','--tmpfs','/tmp','--tmpfs','/scratch',
        '--ro-bind',str(SHARED/'sj'),'/scratch/jjyeung',
        '--ro-bind',str(SHARED/'fsw'),'/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung',
        '--ro-bind',str(SHARED/'fsw/ap'),'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap',
        '--ro-bind',str(B.parents[1]),str(B.parents[1]),'--bind',str(B),str(B),
        '--ro-bind','/scratch/jjyeung/envs','/scratch/jjyeung/envs',
        '--ro-bind','/scratch/jjyeung/uv-python','/scratch/jjyeung/uv-python',
        '--ro-bind',str(W/'from113/work/tree'),cfg['baseline']['assets']['tree_root'],
        '--ro-bind',str(base),model['root']]
    # Overlay code files individually, preserving the supplied non-code staged inputs.
    for p in sorted((K/'sj').rglob('*')):
        if p.is_file():args+=['--ro-bind',str(p),str(Path('/scratch/jjyeung')/p.relative_to(K/'sj'))]
    root='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/'
    args+=['--ro-bind',str(fixture/'metadata/runs/359fcc3c'),root+'runs/359fcc3c']
    for p in sorted((fixture/'metadata/k').iterdir()):
        if p.is_file():args+=['--ro-bind',str(p),root+'k/'+p.name]
    for role,step,run in [('proof',544,'469ddece'),('candidate',50,'359fcc3c')]:
        args+=['--ro-bind',str(fixture/role/('m'+str(step))),root+'runs/'+run+'/m'+str(step)]
    args+=['--setenv','LEGS1_TREE',cfg['baseline']['assets']['tree_root'],
        '--setenv','LEGS1_VENDOR','/scratch/jjyeung/orch_cd/legs1_reads/work/vendor',
        '--setenv','G2_CORE',str(LOGICAL),'--setenv','HF_HUB_OFFLINE','1','--setenv','TRANSFORMERS_OFFLINE','1',
        '--setenv','HF_HOME',str(dest/'cache'),'--setenv','XDG_CACHE_HOME',str(dest/'cache'),
        '--setenv','TMPDIR',str(dest/'cache'),'--die-with-parent','--chdir',str(B)]
    return args

def split_mounts(args):
    """bwrap 0.4 cannot create a mountpoint inside a read-only bind; split such binds along the later targets."""
    ops=[];i=0;one={'--unshare-net','--unshare-uts','--die-with-parent'};two={'--ro-bind','--bind','--setenv','--symlink'}
    while i<len(args):
        a=args[i]
        if a in two:ops.append(args[i:i+3]);i+=3
        elif a in one or not a.startswith('--'):ops.append([a]);i+=1
        else:ops.append(args[i:i+2]);i+=2
    out=[]
    def under(d,later):return [m for m in later if m[0] in('--ro-bind','--bind') and m[2].rstrip('/')!=d.rstrip('/') and m[2].startswith(d.rstrip('/')+'/')]
    def emit(kind,src,dst,later):
        if not os.path.isdir(src) or os.path.islink(src) or not under(dst,later):
            out.extend([kind,src,dst]);return
        out.extend(['--dir',dst])
        for c in sorted(os.listdir(src)):
            s2=os.path.join(src,c);d2=dst.rstrip('/')+'/'+c
            if os.path.islink(s2):out.extend(['--symlink',os.readlink(s2),d2])
            else:emit(kind,s2,d2,later)
    for n,o in enumerate(ops):
        if o[0] in('--ro-bind','--bind'):emit(o[0],o[1],o[2],ops[n+1:])
        else:out.extend(o)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--out');p.add_argument('--prepare-only',action='store_true');p.add_argument('--mismatch',action='store_true');a=p.parse_args()
    dest=Path(a.out).resolve() if a.out else B/'out/rehearsal/whole'/uuid.uuid4().hex
    if not dest.is_relative_to(B):raise ValueError('Rehearsal writes must stay inside the build')
    dest.mkdir(parents=True,exist_ok=False);fixture=dest/'fixture';prep=prepare(fixture)
    (dest/'cache').mkdir();output=dest/'run';output.mkdir()
    report=dict(status='PREPARED',whole_worker_complete=False,fixture=True,model_weights_loaded=False,
        preparation=str(fixture/'PREPARATION.json'),tested_steps=[],not_checked=['GPU model restoration','Orchard allocation','GCS transport'])
    write(dest/'RESULT.json',report)
    if a.prepare_only:return 0
    ns=split_mounts(namespace(dest,fixture));write(dest/'NAMESPACE.json',dict(argv=ns))
    probe=subprocess.run(ns+['/bin/true'],capture_output=True,text=True)
    (dest/'namespace.stderr').write_text(probe.stderr)
    if probe.returncode:
        report.update(status='BLOCKED',error='Namespace unavailable',returncode=probe.returncode)
        write(dest/'RESULT.json',report);return 2
    publisher=Publisher(dict(kind='local',root=str(dest/'store')),'ca1150ca1150ca11',dest/'publication')
    environment=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    environment.pop('PYTHONPATH',None)
    def stage_and_prepare():
        # Stage both tiny export objects with the real tensor-header/hash checker.
        for role,step,run in [('proof',544,'469ddece'),('candidate',50,'359fcc3c')]:
            exported=prep['assets'][role]
            check=dest/(role+'_CHECK.json')
            command=ns+[sys.executable,'-I','-s','-B',str(K/'reviewed/checker/export_check.py'),
                '--export','/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/'+run+'/m'+str(step)+'/artifact.json',
                '--sha256',exported['artifact']['sha256'],'--base',exported['base'],'--step',str(step),'--output',str(check)]
            subprocess.run(command,check=True,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        report['tested_steps'].append('stage')
        base=ns+[sys.executable,'-I','-s','-B',str(Path(__file__).parent/'inside_whole.py'),
            '--config',str(fixture/'WORKER.json'),'--out',str(output)]
        return {role:base+['--role',role]+(['--mismatch'] if a.mismatch and role=='proof' else [])
                for role in ('proof','candidate')}
    lifecycle=coordinate(dest,dict(plan_sha256=digest(read(fixture/'CONFIG.json')),gpu_seconds=7500),
        output,publisher,stage_and_prepare,environment,fixture=True)
    phases,error=lifecycle['phases'],lifecycle['error']
    report['coordinator']=dict(path=str(K/'worker.py'),sha256=sha(K/'worker.py'),shared_with_production=True)
    fetched=dest/'fetched';fetched.mkdir()
    for name in ('result.tar.gz','EXIT.json'):copy_verified(dest/'store/ca1150ca1150ca11'/name,fetched/name)
    if error:
        report.update(status='EXPECTED_REFUSAL' if a.mismatch and (output/'PROOF.json').exists() and not (output/'CANARY.json').exists() else 'FAIL',error=error,phases=phases)
        write(dest/'RESULT.json',report);return 0 if report['status']=='EXPECTED_REFUSAL' else 1
    verify_return(read(fetched/'EXIT.json'),fetched/'result.tar.gz',digest(read(fixture/'CONFIG.json')),allow_fixture=True)
    extract(fetched/'result.tar.gz',fetched/'x',300_000_000)
    script=B.parents[1]/'guard_kit/report/guard_read.py';before=sha(script)
    command=[sys.executable,'-I','-s','-B',str(script),'--candidate',str(fetched/'x/R1.json'),
        '--step544',str(B.parents[1]/'guard_kit/report/tests/fixtures/R1_544_COMPACT.json'),'--out',str(dest/'report')]
    with (dest/'report.log').open('w') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if sha(script)!=before:raise ValueError('Report source changed')
    # Twenty items are intentionally insufficient for the frozen full-list report.
    report.update(status='PASS_WITH_EXPECTED_REPORT_REFUSAL' if result.returncode==3 else 'FAIL',
        whole_worker_complete=False,checkpoint_pipeline_complete=True,production_packet_rehearsed=False,
        phases=phases,report_returncode=result.returncode,report_argv=command,
        report_source_sha256=before,report_scope='Incomplete fixture; no guard verdict',
        tested_steps=['stage','prepare','proof','canary','native_subset','merge','admit','publish','fetch','report'])
    write(dest/'RESULT.json',report);return 0 if result.returncode==3 else 1
if __name__=='__main__':sys.exit(main())
