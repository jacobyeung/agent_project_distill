from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

L=Path(__file__).resolve().parents[2];D=L/'work/build24f';root=D/'rehearsal2';ns='/tmp/q_22c714e1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(D)]
import joblib as J
from student_pilot.source_seal import create,inventory
from student_pilot.p3_provenance import source_files


def rss(pid):
    try:
        status=Path(f'/proc/{pid}/status').read_text()
        total=int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')))*1024
        children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        return total+sum(rss(int(p)) for p in children)
    except (OSError,StopIteration):return 0


os.environ.setdefault('TK_JOB_START',str(int(time.time())))
records=[]
def run(stage,cmd,phase='fresh'):
    env={**os.environ,'TK_REHEARSAL_PHASE':phase,'S1_REHEARSAL_ATTEMPT':'b24f_'+phase}
    if phase=='budget':env['TK_JOB_START']=str(int(time.time())-90000)
    elif phase=='resume':env['TK_JOB_START']=str(int(time.time()))
    else:env['TK_JOB_START']=os.environ['TK_JOB_START']
    logpath=root/(stage+'.log');peak=0
    with logpath.open('w') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        while p.poll() is None:
            peak=max(peak,rss(os.getpid()))
            if peak>19_000_000_000:
                os.killpg(p.pid,signal.SIGTERM)
                p.wait(timeout=30)
                raise RuntimeError('Rehearsal exceeded the aggregate 19 GB guard')
            time.sleep(1)
    records.append(dict(stage=stage,returncode=p.returncode,log=str(logpath),peak_rss_bytes=peak,TK_JOB_START=env['TK_JOB_START']))
    J.write(root/'STAGES.json',records);print(stage,p.returncode,flush=True)
    if p.returncode:raise RuntimeError(stage+' refused; see '+str(logpath))


def main():
    prepared=root/'PREPARED.json'
    if '--finish-preparation' in sys.argv:
        previous=J.load(root/'STAGES.json')
        assert [(v['stage'],v['returncode']) for v in previous]==[('canary',0),('rooms',0),('v_config',1)]
        assert 'R1_HOST_RECEIPT_MISSING' in (root/'v_config.log').read_text()
        assert not (root/'PREPARATION_INITIAL_STAGES.json').exists()
        J.write(root/'PREPARATION_INITIAL_STAGES.json',previous)
        (root/'v_config.log').rename(root/'v_config_initial.log')
        records.extend(previous[:2])
        args=J.load(root/'VIEW.json');kit=L/'out/kit_n_go';py=sys.executable
        finish_preparation(args,kit,py,prepared)
        return
    if prepared.exists():
        v=J.load(prepared)
        assert v['tree']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
        args=J.load(root/'VIEW.json');kit=L/'out/kit_n_go';py=sys.executable
        assert not (root/'fresh_rank0.json').exists(), 'Rehearsal already ran; preserve its output before a repeat'
        records.extend(J.load(root/'STAGES.json'))
        if '--prepare-only' in sys.argv:return
        return training(args,kit,py)
    if (root/'STAGES.json').exists():raise RuntimeError('Incomplete rehearsal output exists; preserve the evidence before another run')
    root.mkdir(parents=True,exist_ok=True)
    cfg=J.load(L/'work/build24d/go/input2.json')
    cfg['output']=ns+'/train';cfg['r1_training']['stop_after_step']=6
    from student_pilot.checkpoint_space import plan
    cfg['checkpoint_disk_guard']=plan(cfg['recipe'],reserve_bytes=0,retained_archive_copies=1)
    tree=L/'work/tree_r1';files=inventory(tree)
    closure={str(p.relative_to(tree)):J.sha(p) for p in source_files([tree/'student_pilot/carrier_c1_run.py'])}
    archive=next(D.glob('t_*.tar'))
    cfg['code']=J.write(root/'code.json',create(tree,archive,closure,{}))
    pin=J.write(root/'input.json',cfg)
    request=J.load(L/'work/build24d/go/r2.json');request['config']=pin;request['staged_pins']=[pin]
    J.write(root/'r.json',request);J.write(root/'r2.json',request);J.write(root/'n.json',cfg)
    # Existing fixture bind sources are node-local. The final mount owns all writes.
    # Existing stores, kits and previous evidence are strictly read-only.
    args=['--ro-bind' if x=='--bind' else x for x in J.load(L/'work/build24d/GO_VIEW.json')]+['--bind',str(root),str(root),'--bind',str(root),ns,'--ro-bind',str(L/'work/build24d/go/p'),ns+'/p']
    J.write(root/'VIEW.json',args)
    kit=L/'out/kit_n_go';py=sys.executable
    # Every native producer/reader in the canary runs; the byte stores and frame host are fixture boundaries.
    run('canary',args+[py,'-B',str(D/'rehearsal_boundary.py'),str(kit/'b/a.py'),'q',ns+'/p2',ns+'/r2.json'])
    result=J.load(root/'p2/q/RESULT.json');assert result['status']=='ADMIT'
    run('rooms',args+[py,'-B',str(kit/'b/d.py'),ns+'/p2/s',ns+'/r2.json',ns+'/n.json',ns+'/rooms.json'])
    finish_preparation(args,kit,py,prepared)
    if '--prepare-only' in sys.argv:return
    training(args,kit,py)


def finish_preparation(args,kit,py,prepared):
    run('v_config',args+[py,'-B',str(D/'rehearsal_handoff.py'),ns+'/p2',ns+'/v.json'])
    run('fixture_gates',args+[py,'-B',str(D/'rehearsal_gates.py')])
    J.write(prepared,dict(tree=J.load(L/'out/TREE_SEAL.json')['tree_sha256'],kit=J.seal(kit),canary=J.sha(root/'p2/q/RESULT.json')))


def training(args,kit,py):
    # This process is the batch driver. The copier never runs inside a trainer.
    copier=subprocess.Popen([py,'-I','-B',str(D/'rehearsal_copier.py')])
    try:
        for phase in ('fresh','budget','resume'):
            if phase!='fresh':
                run('authorize_'+phase,args+[py,'-B',str(D/'rehearsal_authorize.py'),phase],phase)
            run('train_'+phase,args+[py,'-B',str(D/'rehearsal_boundary.py'),str(kit/'b/t.py'),ns+'/p2',ns+'/v.json'],phase)
    finally:
        copier.send_signal(signal.SIGTERM);copier.wait(timeout=60)


if __name__=='__main__':main()
