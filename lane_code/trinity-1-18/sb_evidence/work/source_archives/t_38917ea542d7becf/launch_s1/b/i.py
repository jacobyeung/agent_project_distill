"""Authenticate one operation and supervise its workers."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from v import checked, sha, write

ARMS={'a':'0','b':'1','c':'2','d':'3','e':'4'}
CONFIGS={'a':'a14f07c2','b':'b72d09e3','c':'c39e16b5'}

GPU={'o':0,'p':0,'d':0,'j':0,'c':1,'s':8,'t':8,'u':8,'x':8,'e':1,'l':1,'q':1,'g':1,'h':1,'n':1}
REVISION='1db216004d1812ef86986ac3feb026905416e45a'

def load(path): return json.loads(Path(path).read_text())

def granted(auth,mode,arm=None):
    # new_gpus: one count, a count per mode, or per mode a count per arm (a world-8 arm beside a world-4 arm).
    new=auth['new_gpus']
    value=new.get(mode) if isinstance(new,dict) else new
    return value.get(arm) if isinstance(value,dict) else value

def allocation_gpus(mode,cfg):
    if mode not in ('t','u','x'): return GPU[mode]
    world=cfg.get('world_size',cfg.get('recipe',{}).get('world_size',8))
    if type(world) is not int or world not in (4,8,16,32):
        raise ValueError('World size must be 4, 8, 16 or 32')
    if cfg.get('recipe',{}).get('world_size')!=world:
        raise ValueError('Recipe world size differs')
    return world

def job_matches(job,mode,arm,cfg):
    return job['mode']==mode and job['arm']==arm and job['gpus']==allocation_gpus(mode,cfg)

def pick(auth,field,arm):
    value=auth.get(field)
    if isinstance(value,dict) and value and 'path' not in value and set(value)<=set(ARMS.values()):
        return value.get(arm)
    return value

def authorize(root,mode,arm):
    from student_pilot import rehearsal
    if rehearsal.enabled():
        return rehearsal.authorize(root,mode,arm)
    auth=load(root/'k/4.json');cur=load(root/'k/0.json')
    arms=auth['arm'] if isinstance(auth['arm'],list) else [auth['arm']]
    if (mode not in GPU or arm not in arms or len(set(arms))!=len(arms)
            or not set(arms)<=set(ARMS.values()) or mode not in auth['modes']):
        raise ValueError('Operation not authorized')
    key=load(root/'k/1.json')[arm];cfg=load(root/f'k/{key}.json')
    if cfg.get('training_mode')!='final' and auth['source_revision']!=cur['commit']:
        raise ValueError('Revision differs')
    if mode in ('g','h') and (arm not in ('0','2') or cur['commit']!=REVISION):
        raise ValueError('Check scope differs')
    end=datetime.datetime.fromisoformat(auth['allow_until_utc'].replace('Z','+00:00'))
    if end.tzinfo is None or end<=datetime.datetime.now(datetime.timezone.utc): raise ValueError('Expired')
    gpus=allocation_gpus(mode,cfg)
    other=auth['other_running_and_pending_gpus'];new=granted(auth,mode,arm)
    cap=auth['gpu_cap'];total=[granted(auth,mode,a) for a in arms]
    if (type(other) is not int or other<0 or type(new) is not int or new!=gpus or type(cap) is not int
            or any(type(n) is not int or n<0 for n in total) or not 0<cap<=128 or sum(total)+other>cap):
        raise ValueError('Allocation differs')
    nodes=max(1,gpus//8)
    if gpus and (os.environ.get('SLURM_JOB_NUM_NODES')!=str(nodes)
            or int(os.environ.get('SLURM_GPUS_ON_NODE','0'))!=min(gpus,8)): raise ValueError('Resources differ')
    if mode!='o' and cfg.get('training_mode')!='final' and not load(root/'k/7.json').get('clean'):
        raise ValueError('Source closure incomplete')
    from x import ready, routing_input
    launch_path=root/'k/launch.json'
    if mode in ('t','u','x') and launch_path.is_file() and load(launch_path).get('in_job_admission'):
        from d import effective
        cfg=effective(root,cfg)
    ready(cfg,mode,auth)
    if cfg.get('training_mode')=='final' and mode=='j':
        routing_input(root,load(root/'k/8.json')['input'])
    if mode=='l':
        if not cfg['readout'].get('contiguous_clips'): raise ValueError('Input selection unbound')
        checked(cfg['readout']['contiguous_clips'])
    if mode in ('d','s'):
        guard=load(checked(pick(auth,'guard',arm)))
        if (guard.get('status')!='PASS' or guard.get('source_revision')!=cur['commit']
                or guard.get('placement')!=cfg['carrier_placement'] or guard.get('rows')!=32
                or guard.get('steps')!=200 or not 0<=guard.get('rotation_deg',180)<30):
            raise ValueError('Learning guard required')
    if arm=='2' and mode in ('d','s'):
        from b3900003 import admitted
        kernel=load(checked(pick(auth,'kernel',arm)))
        if not admitted(guard,kernel,cur['commit'],identity(cfg),cfg['carrier_placement']):
            raise ValueError('Measured checks required')
    return auth,cfg

def identity(cfg):
    import hashlib
    value={k:v for k,v in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in value:
        value['readout']={k:v for k,v in value['readout'].items() if k!='contiguous_clips'}
    if value.get('frame_layout')=='spread': value.pop('frame_layout')
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def descendants(pid):
    try: children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
    except OSError: return []
    result=[]
    for child in children:
        result.append(int(child)); result.extend(descendants(int(child)))
    return result

def relay(pid):
    # Send only to rank processes; the launcher must survive the signal.
    for child in descendants(pid):
        try:
            env=Path(f'/proc/{child}/environ').read_bytes().split(b'\0')
            if any(v.startswith(b'LOCAL_RANK=') for v in env): os.kill(child,signal.SIGUSR1)
        except ProcessLookupError: pass
        except FileNotFoundError: pass

def launcher(root,mode,arm,cfg):
    command=[sys.executable,'-B']
    gpus=allocation_gpus(mode,cfg)
    if gpus>=4:
        nodes=max(1,gpus//8)
        command+=['-m','torch.distributed.run','--nproc-per-node='+str(min(gpus,8))]
        if nodes==1:
            command+=['--standalone','--nnodes=1']
        else:
            node=int(os.environ['SLURM_NODEID'])
            if not 0<=node<nodes: raise ValueError('Node rank differs')
            command+=['--nnodes='+str(nodes),'--node-rank='+str(node),
                      '--rdzv-backend=c10d','--rdzv-endpoint='+os.environ['MASTER_ADDR']+':'+os.environ['MASTER_PORT'],
                      '--rdzv-id='+os.environ['SLURM_JOB_ID']]
    return command+[str(root/'b/w.py'),str(root),mode,arm]

def main(root,mode,arm,*extra):
    if extra: raise ValueError('Unexpected arguments')
    root=Path(root)
    stop_file=root/'o'/(os.environ.get('SLURM_JOB_ID','local')+'.stop')
    if stop_file.exists(): raise SystemExit(75)
    auth,cfg=authorize(root,mode,arm)
    from student_pilot import rehearsal
    job=rehearsal.attempt_id()
    if not rehearsal.enabled() and not job.isdecimal(): raise ValueError('Allocation absent')
    command=launcher(root,mode,arm,cfg)
    # Each node supervises eight ranks; only node zero publishes the receipt.
    if GPU[mode] and int(os.environ.get('SLURM_NODEID','0'))==0:
        write(root/'o'/(job+'.3.json'),dict(config_sha256=identity(cfg),new_gpus=granted(auth,mode,arm),
              job_id=job,verdict='GO', **({'rehearsal': True, 'production_authorized': False} if rehearsal.enabled() else {})))
    if mode in ('t','u','x'):
        from sg import normalize, supervise
        normalize(cfg.get('stall_guard'))
    if stop_file.exists(): raise SystemExit(75)
    child=subprocess.Popen(command)
    signal.signal(signal.SIGUSR1,lambda *_:child.send_signal(signal.SIGUSR1) if mode=='p' else relay(child.pid))
    if mode in ('t','u','x'):
        rc=supervise(child,cfg['output'],relay,cfg.get('stall_guard'))
    else:
        rc=child.wait()
    if rc: raise SystemExit(rc)

if __name__=='__main__': main(*sys.argv[1:])
