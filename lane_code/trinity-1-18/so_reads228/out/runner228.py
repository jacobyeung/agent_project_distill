"""One A10b read on one idle RTX 6000 Ada card; no transfers, scheduler, or retry."""
import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *
from gpu228 import card_name,idle_gate,require_idle,snapshot
from stage228 import stage_check
from return228 import package_return,new_return_identity
from namespace228 import operator_command

def extensions():
    source=HERE/'extensions'
    expected=read(HERE/'so_read/EXTENSION_PINS.json')
    if not source.is_dir():raise Refusal('ON needs prepared so_read overlays: run install_extensions228.py')
    actual={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file()}
    if set(actual)!=set(expected):raise Refusal('so_read extension inventory differs; see SO_READ_CONSISTENCY.json')
    for name,p in actual.items():
        if p.is_symlink() or sha(p)!=expected[name]:raise Refusal('so_read overlay pin differs: '+name)
    return source

def probe_operator(root,cfg,inputs):
    command=operator_command(inputs,'--probe',str(Path(cfg['logical'])/'p'))
    env=clean_environment(STAGE/'operator_probe')
    try:
        result=subprocess.run(command,env=env,text=True,capture_output=True,timeout=120)
        proof=dict(passed=result.returncode==0,returncode=result.returncode,argv=command,
                   stdout=result.stdout,stderr=result.stderr,utc=utc())
    except (OSError,subprocess.TimeoutExpired) as error:
        proof=dict(passed=False,returncode=None,argv=command,error=str(error),utc=utc())
    write(STAGE/'OPERATOR_PROBE.json',proof)
    if not proof['passed']:
        raise Refusal('Operator import probe failed before card access: '+str(proof.get('error') or proof['stderr'][-4000:]))
    return proof

def run_one(a):
    target_host();card_name(a.card)
    if a.items is not None and not 1<=a.items<=636:raise Refusal('--items must be in 1..636')
    root,cfg,inputs,export=deployment(a.package)
    out=local(a.out)
    from orchard_h10.common import opaque
    opaque([str(out)])
    if out.exists():raise Refusal('Output exists; use a fresh directory, never rerun a killed job')
    ext=extensions() if a.on else None
    # Refuse missing or wrong weights before creating GPU contexts or waiting for a card.
    proof=stage_check(root,cfg,inputs,export,prepare=True)
    probe=probe_operator(root,cfg,inputs)
    out.mkdir(parents=True,exist_ok=False);(out/'telemetry').mkdir();(out/'metadata').mkdir()
    write(out/'metadata/STAGE_CHECK.json',proof)
    lockroot=STAGE/'locks';lockroot.mkdir(parents=True,exist_ok=True)
    # UUID locks serialize this kit's users on the card, but do not reserve it against other programs.
    first=snapshot(a.card);require_idle(first)
    with (lockroot/(first['uuid']+'.lock')).open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Refusal('Another read228 launcher holds this card')
        print(utc()+' Waiting for the second idle reading (five minutes).',flush=True)
        gpu=idle_gate(first['uuid'],out/'telemetry/IDLE.json')
        card=gpu['uuid']
        ret=out/'ret';(ret/'metadata').mkdir(parents=True)
        identity=new_return_identity(out,cfg)
        (ret/'logs').mkdir()
        prepare_log=STAGE/'prepare/prepare.log'
        (ret/'logs/0.log').write_bytes(prepare_log.read_bytes() if prepare_log.is_file() else b'Local stage verification passed.\n')
        (ret/'logs/1.log').write_text('Local sealed operator launch; worker output is reads/0/logs/30.log.\n')
        from orchard_h10.common import template
        _,storage,_,_,_=template()
        write(ret/'metadata/STORAGE.json',dict(storage.storage_proof(out),job=identity['job'],execution_backend='trinity-local'))
        write(ret/'metadata/INPUTS.json',inputs);write(ret/'metadata/EXPORT_PIN.json',export)
        write(ret/'metadata/CARDS.json',dict(visible=[card],snapshot=gpu))
        write(ret/'metadata/LOCAL_RUN.json',dict(backend='trinity-local',host='trinity-2-28',mode='ON' if a.on else 'OFF',
            requested_items=a.items,orchard_reference_job='173060',operator_sha256=sha(root/'tower_sequence.py'),
            source_payload_sha256=cfg['payload_sha256'],adapter_sha256=sha(__file__),
            actual_python=inputs['python'],runtime_environment=proof['environment'],
            namespace=proof['namespace'],bwrap=proof['namespace']['bwrap'],
            operator_probe=probe,operator_execution='package_namespace',policy=inputs['policy'],
            archive_path_map=str(HERE/'STAGE_PLAN.json'),utc=utc(),same_instrument=False))
        p=Path(cfg['logical'])/'p';data=Path(cfg['logical'])/'d'
        run_cfg=dict(export_pin=str(data/'6.json'),export_cache=str(out/'metadata/export_cache.json'),
            allocation=identity['job'],package=str(p),output=str(ret),python=inputs['python'],
            export=str(data/'e'),binding=str(data/'binding.json'),settings=str(data/'settings.json'),
            plan_sha256=cfg['plan_sha256'],inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
            types=inputs['types'],stop_margin=cfg['stop_margin'],return_margin=cfg['return_margin'],
            prefix=['bash',inputs['policy']['vnice']],operator_sha256=sha(root/'tower_sequence.py'))
        stop=ret/'metadata/STOP';end=time.time()+cfg['budget_gpu_seconds']
        dispatch=out/'metadata/operator.json'
        write(dispatch,dict(out=str(out),config=run_cfg,card=card,end=end,on=a.on,items=a.items,
                            extensions=str(ext) if ext else None,operator=str(root/'tower_sequence.py')))
        command=operator_command(inputs,'--execute',str(dispatch))
        write(out/'metadata/OPERATOR_COMMAND.json',dict(argv=command,namespace=proof['namespace']))
        def stop_requested(number,frame):stop.write_text('Signal '+str(number)+'; finish current item\n')
        old={n:signal.signal(n,stop_requested) for n in (signal.SIGINT,signal.SIGTERM,signal.SIGUSR1)}
        failure=None;summary=None
        try:
            with (ret/'logs/1.log').open('ab') as log:
                process=subprocess.run(command,env=clean_environment(out,card),stdout=log,stderr=subprocess.STDOUT)
            result_path=out/'metadata/OPERATOR_RESULT.json'
            if result_path.is_file():
                got=read(result_path);summary=got['summary'];failure=got['failure']
            if process.returncode and not failure:failure='Package operator exited '+str(process.returncode)
            if summary is None and not failure:failure='Package operator did not return a summary'
        except BaseException as error:
            failure=str(error);traceback.print_exc()
        finally:
            for n,handler in old.items():signal.signal(n,handler)
        requested_ok=(not failure and summary and a.items is not None and summary['completed']==a.items)
        rc=0 if not failure and summary and (summary['complete'] or requested_ok) else (42 if (out/'telemetry/OOM.json').exists() else 1)
        if summary is None:
            summary=dict(completed=0,expected=636,complete=False,failure=failure or 'Worker did not run',reads=[])
        summary['requested_items']=a.items
        summary['requested_prefix_complete']=bool(requested_ok)
        write(ret/'metadata/ALLOCATION.json',dict(end=end,plan=cfg['plan_sha256'],failure=failure,summary=summary))
        result=package_return(out,cfg,summary,rc,failure=failure)
        write(out/'RESULT.json',dict(**result,returncode=rc,mode='ON' if a.on else 'OFF',same_instrument=False,
             validation='Requires compare228 against the Orchard return; no hardware-parity claim is made by the launcher'))
        print(json.dumps(dict(**result,returncode=rc),sort_keys=True),flush=True)
        return rc

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package');p.add_argument('card');p.add_argument('out')
    p.add_argument('--items',type=int);p.add_argument('--on',action='store_true')
    a=p.parse_args(argv);print(utc(),flush=True);return run_one(a)

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
