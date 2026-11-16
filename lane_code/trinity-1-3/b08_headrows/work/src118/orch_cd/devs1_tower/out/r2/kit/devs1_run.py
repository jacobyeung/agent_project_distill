"""Node-independent one-card launcher. A stalled or failed run never retries itself."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import time
from devs1_anchors import build,verify_frames,save,sha

KIT=Path(__file__).resolve().parent

def local(path):
    p=Path(path).resolve()
    if str(p).startswith(('/home/','/data/','/data2/','/data3/')):raise ValueError('Require node-local path: '+str(p))
    return p

def checkpoints(bundle,config,artifact,g3t,mdg):
    bp=local(bundle);bp=bp/'BUNDLE.json' if bp.is_dir() else bp
    paths=[bp,local(config),local(artifact.rsplit('@',1)[0]),local(g3t)/'config.json',local(g3t)/'model.safetensors',local(mdg)/'mdg.json',local(mdg)/'mdg.pt']
    for p in paths:
        if not p.is_file() or p.stat().st_size==0:raise ValueError('Missing checkpoint/config: '+str(p))
    b=json.loads(bp.read_text())
    if b.get('schema')!='mdg-t0-bundle-v1':raise ValueError('Invalid bundle schema')
    for name in b['files']:
        name_path=Path(name)
        if name_path.is_absolute() or '..' in name_path.parts:raise ValueError('Invalid bundle member')
        p=local(Path(b['artifact_dir'])/name.removeprefix('artifact/') if name.startswith('artifact/') else bp.parent/name)
        if not p.is_file() or not p.stat().st_size:raise ValueError('Missing bundle checkpoint: '+str(p))
    if not re.fullmatch(r'.+@[0-9a-f]{64}',artifact):raise ValueError('Require artifact path@sha256')
    if sha(paths[2])!=artifact.rsplit('@',1)[1]:raise ValueError('Artifact pin differs')
    return bp

def free_card(card,query=subprocess.check_output):
    if not re.fullmatch(r'[0-9]+|GPU-[A-Za-z0-9-]+',str(card)):raise ValueError('Require one card ID')
    line=query(['nvidia-smi','-i',str(card),'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()
    if len(line)!=1:raise ValueError('Card not unique')
    uuid,memory,util=[x.strip() for x in line[0].split(',')]
    apps=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    if float(memory)>256 or float(util)>0 or any(r.split(',')[0].strip()==uuid for r in apps.splitlines()):raise ValueError('Card is busy')

def free_disk(path,min_gib=100,usage=shutil.disk_usage):
    p=local(path)
    while not p.exists():p=p.parent
    if usage(p).free < min_gib*1024**3:raise ValueError('Insufficient free disk; reserve 100 GiB')

def verify_seal():
    for line in (KIT/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        p=(KIT/name).resolve()
        if not p.is_relative_to(KIT) or sha(p)!=digest:raise ValueError('Kit seal differs: '+name)


def preflight(a,plan):
    if socket.gethostname().split('.')[0]=='trinity':raise ValueError('Head node refused')
    verify_seal()
    local(a.frame_root);local(a.out);local(a.mdg_root);local(a.vnice);local(sys.executable)
    if not Path(a.vnice).is_file() or not (Path(a.vnice).parent/'terminator.sh').is_file():raise ValueError('Missing local vnice wrapper or terminator')
    if not (Path(a.mdg_root)/'student_pilot/mdg_eval.py').is_file():raise ValueError('Missing MDG source')
    local(a.plan)
    bp=checkpoints(a.bundle,a.t0_config,a.artifact,a.g3t_weights,a.mdg)
    free_disk(a.out);free_card(a.card)
    total=verify_frames(plan,a.frame_root)
    return dict(frame_bytes=total,bundle_sha256=sha(bp),plan_sha256=sha(a.plan),artifact=a.artifact,frame_root=str(Path(a.frame_root).resolve()),mdg_sha256=sha(Path(a.mdg)/'mdg.json'),config_sha256=sha(a.t0_config),g3t=str(Path(a.g3t_weights).resolve()),kit_sha256=sha(KIT/'SHA256SUMS'))

def guarded(command,progress,log,sources=(),timeout=1200,poll=2,env=None):
    """Only changed worker journals count as progress; log chatter cannot defeat the guard."""
    progress,log=Path(progress),Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    progress.write_text(json.dumps(dict(event='start',command=command,time=time.time()))+'\n')
    observed={str(p): (Path(p).stat().st_size,Path(p).stat().st_mtime_ns) if Path(p).exists() else None for p in sources}
    proc=None
    def stop():
        if proc and proc.poll() is None:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
    try:
        with log.open('a') as stream:
            proc=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=env)
            while proc.poll() is None:
                for p in sources:
                    p=Path(p);state=(p.stat().st_size,p.stat().st_mtime_ns) if p.exists() else None
                    if state!=observed[str(p)]:
                        observed[str(p)]=state
                        with progress.open('a') as f:f.write(json.dumps(dict(event='worker_progress',source=str(p),time=time.time()))+'\n')
                if time.time()-progress.stat().st_mtime>=timeout:
                    stop();raise RuntimeError('STALL: no progress for '+str(timeout)+' seconds; no automatic retry')
                time.sleep(poll)
            if proc.returncode:raise RuntimeError('Stage exited '+str(proc.returncode)+'; no automatic retry')
    except BaseException:
        stop();raise
    with progress.open('a') as f:f.write(json.dumps(dict(event='complete',time=time.time()))+'\n')

def merge_anchors(out,plan,group):
    root=out/'anchors'/group;selections=[];members=[];clips={};dense=None
    for c in plan['captures']:
        if c['group']!=group:continue
        p=root/c['scene'].replace('/','__')
        selections+=json.loads((p/'A_MANIFEST.json').read_text())['selections']
        members+=json.loads((p/'MEMBERSHIP.json').read_text())['items']
        dense=json.loads((p/'DENSE.json').read_text());clips.update(dense['clips'])
    if dense is None:return None
    save(root/'A_MANIFEST.json',dict(selections=selections));save(root/'MEMBERSHIP.json',dict(items=members));save(root/'DENSE.json',dict(dense,clips=clips))
    return root

def run(a):
    plan=json.loads(Path(a.plan).read_text());binding=preflight(a,plan);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    with (out/'RUN.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (out/'HALTED.json').exists():
            halted=json.loads((out/'HALTED.json').read_text())
            if not halted.get('reviewed') and not a.resume_after_review:raise ValueError('Run halted; operator review and --resume-after-review required')
            if a.resume_after_review:save(out/'HALTED.json',dict(halted,reviewed=True,review_time=time.time()))
        request=out/'REQUEST.json'
        if request.exists() and json.loads(request.read_text())!=binding:raise ValueError('Resume request changed')
        save(request,binding)
        if a.preflight_only:print(json.dumps(binding));return
        env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(a.card),RK_MDG_ROOT=str(local(a.mdg_root)))
        for name,sub in [('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TORCH_HOME','torch'),('TRITON_CACHE_DIR','triton'),('CUDA_CACHE_PATH','cuda'),('TMPDIR','tmp')]:
            p=out/sub;p.mkdir(exist_ok=True);env[name]=str(p)
        try:
            build(plan,a.frame_root,out/'anchors')
            for group in ['g3s64','g3s32']:
                anchors=merge_anchors(out,plan,group)
                if anchors is None:continue
                root=out/group;root.mkdir(exist_ok=True)
                stages=[('export',['-m','rk.export','run','--manifest',str(anchors/'A_MANIFEST.json'),'--membership',str(anchors/'MEMBERSHIP.json'),'--png-root',a.frame_root,'--bundle',a.bundle,'--t0-config',a.t0_config,'--artifact',a.artifact,'--mdg',a.mdg,'--out',str(root/'export'),'--device','cuda:0','--rank','0','--world','1'],[root/'export/export-0.jsonl']),
                    ('g3t',['-m','e0k.g3t_dense','--dense',str(anchors/'DENSE.json'),'--weights',a.g3t_weights,'--out',str(root/'g3t'),'--device','cuda:0'],[root/'g3t/journal_0.jsonl'])]
                for name,args,sources in stages:
                    free_disk(out)
                    guarded(['bash',a.vnice,shlex.join([sys.executable,'-B',*args])],out/'PROGRESS.jsonl',out/'logs'/(group+'_'+name+'.log'),sources,env=env)
                    if name=='g3t':
                        status=json.loads((root/'g3t/rank_0.json').read_text())
                        if status['failures']:raise RuntimeError('G3T failures: '+str(status['failures']))
                from devs1_heads import heads
                result=heads(root/'g3t',root/'export/heads_own',out,group)
                expected=sum(c['group']==group for c in plan['captures'])
                if result['completed']+result['resumed']!=expected:raise ValueError('Incomplete capture coverage')
            save(out/'COMPLETE.json',dict(captures=len(plan['captures']),binding=binding))
        except BaseException as e:
            save(out/'HALTED.json',dict(error=str(e),time=time.time(),instruction='Operator review required; do not retry automatically'))
            raise

def main():
    def interrupted(signum, frame):raise KeyboardInterrupt('Received signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser()
    for n in ['frame-root','bundle','t0-config','artifact','g3t-weights','mdg','mdg-root','vnice','out','card']:p.add_argument('--'+n,required=True)
    p.add_argument('--plan',default=str(KIT/'PLAN.json'));p.add_argument('--preflight-only',action='store_true');p.add_argument('--resume-after-review',action='store_true')
    run(p.parse_args())

if __name__=='__main__':main()
