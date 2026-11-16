"""Production coordinator: staged proof, candidate canary/read, admission and return."""
import argparse
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from guard_core import read,write,sha,digest
from guard_backend import CORE
from transport import Publisher,archive_result,copy_verified

PUBLICATION_RESERVE=300
REPORT_SHA256='e673f856ed5562d680e69ab205a184baf0a5a0a1034dc1283bcedad35525cd04'

def report_command(config,script,candidate,step544,output,self_pair=False):
    """Bind every report invocation to the selected CONFIG artifact and source."""
    artifact=config['artifact_sha256']
    if not re.fullmatch('[0-9a-f]{64}',artifact):raise ValueError('Invalid report artifact pin')
    if sha(script)!=REPORT_SHA256:raise ValueError('Report source pin differs')
    return [sys.executable,'-I','-s','-B',str(script),'--candidate',str(candidate),
            '--candidate-artifact',artifact,'--step544',str(step544),'--out',str(output)]+(['--self-pair'] if self_pair else [])

def retain_stage_receipts(root,config,output):
    """Retain the exact stager bytes before a checkpoint process can start."""
    root,output=Path(root),Path(output)
    stage=root/'CANDIDATE_STAGE.json'
    check=root/'exports'/('359fcc3c_m'+str(config['step']))/'CHECK.json'
    staged,checked=read(stage),read(check)
    if (staged.get('status')!='complete' or checked.get('status')!='VERIFIED'
            or staged.get('run')!='359fcc3c' or staged.get('step')!=config['step']
            or checked.get('step')!=config['step'] or staged.get('checker')!=checked
            or staged.get('artifact_sha256')!=config['artifact_sha256']
            or checked.get('artifact',{}).get('sha256')!=config['artifact_sha256']):
        raise ValueError('Candidate stage/checker receipt identity differs')
    sources={'CANDIDATE_STAGE.json':stage,'CHECK.json':check}
    # C8r emits STAGING.json; retain any separate historical-export receipts too.
    for relative in ('STAGING.json','CHECK.json','exports/469ddece_m544/RECEIPT.json',
                     'exports/469ddece_m544/CHECK.json'):
        source=root/relative
        if source.exists():sources['step544/'+relative]=source
    pins={name:copy_verified(source,output/name) for name,source in sources.items()}
    write(output/'STAGE_RECEIPTS.json',dict(schema='g4-stage-receipts-v1',
          step=config['step'],artifact_sha256=config['artifact_sha256'],members=pins))

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

def coordinate(root,config,output,publisher,prepare,environment,fixture=False):
    """The production and CPU boundary runners share this complete phase lifecycle."""
    root,output=Path(root),Path(output);error=None;phases={}
    deadline=time.monotonic()+config['gpu_seconds']-PUBLICATION_RESERVE
    try:
        commands=prepare()
        if set(commands)!={'proof','candidate'}:raise ValueError('Checkpoint commands differ')
        retain_stage_receipts(root,config,output)
        for role in ('proof','candidate'):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('No checkpoint budget remains before publication reserve')
            phases[role]=child(commands[role],environment,output,publisher,role,remaining)
        if phases['proof']['pid']==phases['candidate']['pid']:raise ValueError('Checkpoint processes were not distinct')
        write(output/'COMPLETE.json',dict(status='PASS',plan_sha256=config['plan_sha256'],fixture=fixture,processes=phases))
    except Exception as exc:
        error=str(exc);write(output/'FAILED.json',dict(status='FAIL',error=error,phases=phases))
        if not (output/'PROOF.json').exists():
            write(output/'PROOF.json',dict(status='FAIL',candidate_started=False,backend_identity_proven=False,fixture=fixture,error=error))
            publisher(output/'PROOF.json')
        elif read(output/'PROOF.json').get('status')=='PASS' and not (output/'CANARY.json').exists():
            write(output/'CANARY.json',dict(status='FAIL',full_started=False,fixture=fixture,error=error))
            publisher(output/'CANARY.json')
    finally:
        # A caught allocation signal must not interrupt the bounded return attempt.
        if not fixture:
            for number in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1):signal.signal(number,signal.SIG_IGN)
        archive_result(output,root/'returned',config['plan_sha256'],fixture=fixture,error=error)
        publisher(root/'returned/result.tar.gz');publisher(root/'returned/EXIT.json')
    return dict(status='FAIL' if error else 'PASS',error=error,phases=phases)

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
    def interrupted(number,frame):raise RuntimeError('Allocation signal '+str(number))
    for number in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1):signal.signal(number,interrupted)
    def prepare():
        from staging import stage
        stage_config,records=stage(root,config,payload)
        runtime=records['runtime_spec']
        entry=Path(__file__).parent/'checkpoint.py'
        runtime['entrypoints'][entry.name]=dict(path=str(entry),sha256=sha(entry))
        write(root/'RUNTIME.json',runtime)
        environment['G2_CORE']='/scratch/jjyeung/orch_cd/evalx/work/milestone'
        vnice=stage_config['assets']['vnice']
        if sha(S.physical(root,vnice['path']))!=vnice['sha256']:raise ValueError('Priority wrapper pin differs')
        base=S.namespace(root,stage_config)+['--bind',str(output),str(output),
            '/bin/bash',vnice['path'],runtime['python']['path'],'-I','-s','-B',str(CORE/'native_bootstrap.py'),
            '--spec',str(root/'RUNTIME.json'),'--',str(entry),'--config',str(root/'WORKER.json'),'--out',str(output)]
        return {role:base+['--role',role] for role in ('proof','candidate')}
    result=coordinate(root,config,output,publisher,prepare,environment)
    return 1 if result['error'] else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--payload',required=True);a=p.parse_args()
    sys.exit(run(a.root,a.payload))
