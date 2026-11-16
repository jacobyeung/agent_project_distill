"""Production coordinator: staged proof, candidate canary/read, admission and return."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from guard_core import read,write,sha,digest
from guard_backend import CORE
from transport import Publisher,archive_result

def child(command,environment,output,publisher,role,timeout):
    """A checkpoint process cannot continue past a receipt before publication."""
    output=Path(output);receipt='PROOF' if role=='proof' else 'CANARY'
    started=time.monotonic();acknowledged=False
    with (output/(role+'.log')).open('xb') as log:
        process=subprocess.Popen(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
        try:
            while True:
                ready=output/(receipt+'.ready.json')
                if not acknowledged and ready.exists():
                    target=output/(receipt+'.json')
                    if read(ready)!=dict(path=str(target)):raise ValueError('Receipt rendezvous path differs')
                    publisher(target)
                    write(output/(receipt+'.ack.json'),dict(status='PASS',sha256=sha(target)))
                    acknowledged=True
                code=process.poll()
                if code is not None:break
                if time.monotonic()-started>timeout:raise TimeoutError('Checkpoint process exceeded its budget')
                time.sleep(.5)
            if code or not acknowledged:raise RuntimeError('Checkpoint process failed: '+role)
            if read(output/(receipt+'.json')).get('status')!='PASS':raise ValueError('Checkpoint receipt failed')
        except BaseException:
            if process.poll() is None:
                process.terminate();process.wait(timeout=30)
            raise
    return dict(pid=process.pid,seconds=time.monotonic()-started,returncode=code)

def run(root,payload):
    root,payload=Path(root),Path(payload)
    config=read(payload/'CONFIG.json')
    from packet import validate_packet
    validate_packet(payload)
    sys.path[:0]=[str(CORE/'orchard_native'),str(CORE)]
    import native_stage as S
    import native_job as J
    import orchard_job as O
    job=os.environ.get('SLURM_JOB_ID','')
    if (not job.isdigit() or not os.uname().nodename.startswith('orchard-')
            or os.environ.get('SLURM_JOB_PARTITION')!='general'
            or root.resolve()!=Path('/tmp')/('g2_'+job+'_'+config['token'])):
        raise ValueError('Assigned Orchard job and private root required')
    if __import__('pwd').getpwuid(os.getuid()).pw_name!='jjyeung':raise ValueError('Allocation user differs')
    O.storage_proof(root,job=job);J.card(require_empty=True)
    for name in ('cache','temp','home'):(root/name).mkdir()
    environment=J.environment(root)
    output=root/'result';output.mkdir()
    publisher=Publisher(config['publication'],config['token'],root/'publication')
    error=None;phases={}
    try:
        from staging import stage
        stage_config,records=stage(root,config,payload)
        runtime=records['runtime_spec']
        entry=Path(__file__).parent/'checkpoint.py'
        runtime['entrypoints'][entry.name]=dict(path=str(entry),sha256=sha(entry))
        write(root/'RUNTIME.json',runtime)
        environment['G2_CORE']='/scratch/jjyeung/orch_cd/evalx/work/milestone'
        base=S.namespace(root,stage_config)+['--bind',str(output),str(output),
            runtime['python']['path'],'-I','-s','-B',str(CORE/'native_bootstrap.py'),
            '--spec',str(root/'RUNTIME.json'),'--',str(entry),'--config',str(root/'WORKER.json'),'--out',str(output)]
        for role in ('proof','candidate'):
            phases[role]=child(base+['--role',role],environment,output,publisher,role,config['gpu_seconds'])
        if phases['proof']['pid']==phases['candidate']['pid']:raise ValueError('Checkpoint processes were not distinct')
        write(output/'COMPLETE.json',dict(status='PASS',plan_sha256=config['plan_sha256'],fixture=False,processes=phases))
    except Exception as exc:
        error=str(exc);write(output/'FAILED.json',dict(status='FAIL',error=error,phases=phases))
        if not (output/'PROOF.json').exists():
            write(output/'PROOF.json',dict(status='FAIL',candidate_started=False,backend_identity_proven=False,error=error))
            publisher(output/'PROOF.json')
    finally:
        receipt=archive_result(output,root/'returned',config['plan_sha256'],error=error)
        publisher(root/'returned/result.tar.gz');publisher(root/'returned/EXIT.json')
    return 1 if error else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--payload',required=True);a=p.parse_args()
    sys.exit(run(a.root,a.payload))
