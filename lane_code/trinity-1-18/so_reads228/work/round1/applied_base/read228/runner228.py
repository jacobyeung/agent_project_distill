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
from gpu228 import card_name,idle_gate,require_idle,snapshot,Sampler
from stage228 import stage_check
from return228 import package_return,new_return_identity

def extensions():
    source=HERE/'extensions'
    expected=read(HERE/'so_read/EXTENSION_PINS.json')
    if not source.is_dir():raise Refusal('ON needs prepared so_read overlays: run install_extensions228.py')
    actual={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file()}
    if set(actual)!=set(expected):raise Refusal('so_read extension inventory differs; see SO_READ_CONSISTENCY.json')
    for name,p in actual.items():
        if p.is_symlink() or sha(p)!=expected[name]:raise Refusal('so_read overlay pin differs: '+name)
    return source

def run_one(a):
    target_host();card_name(a.card)
    if a.items is not None and not 1<=a.items<=636:raise Refusal('--items must be in 1..636')
    root,cfg,inputs,export=deployment(a.package)
    out=local(a.out)
    if out.exists():raise Refusal('Output exists; use a fresh directory, never rerun a killed job')
    ext=extensions() if a.on else None
    # Refuse missing or wrong weights before creating GPU contexts or waiting for a card.
    proof=stage_check(root,cfg,inputs,export,prepare=True)
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
            archive_path_map=str(HERE/'STAGE_PLAN.json'),utc=utc(),same_instrument=False))
        p=Path(cfg['logical'])/'p';data=Path(cfg['logical'])/'d'
        install_imports(p)
        operator=load_module(root/'tower_sequence.py','read228_sealed_operator')
        from orchard_h10 import runner
        run_cfg=dict(export_pin=str(data/'6.json'),export_cache=str(out/'metadata/export_cache.json'),
            allocation=identity['job'],package=str(p),output=str(ret),python=inputs['python'],
            export=str(data/'e'),binding=str(data/'binding.json'),settings=str(data/'settings.json'),
            plan_sha256=cfg['plan_sha256'],inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
            types=inputs['types'],stop_margin=cfg['stop_margin'],return_margin=cfg['return_margin'],
            prefix=['bash',str(VNICE)],operator_sha256=sha(root/'tower_sequence.py'))
        if a.on:
            chosen=read(run_cfg['settings'])
            chosen.update(read_processor_only='off',read_processor_cache='on',read_vision_cache='on',
                          read_sam_cache='on',read_cache_bytes=12*1024**3)
            path=out/'metadata/settings_on.json';write(path,chosen);run_cfg['settings']=str(path)
        stop=ret/'metadata/STOP';end=time.time()+cfg['budget_gpu_seconds']
        def stop_requested(number,frame):stop.write_text('Signal '+str(number)+'; finish current item\n')
        old={n:signal.signal(n,stop_requested) for n in (signal.SIGINT,signal.SIGTERM,signal.SIGUSR1)}
        failure=None;summary=None;worker_rc=None
        def execute(chosen,cards,deadline,*,prefix):
            def launch(argv,**kwargs):
                config=read(Path(kwargs['cwd'])/argv[-1])
                # The sealed runner wrote a/30.json and supplies the dispatch; keep it unchanged.
                write(out/'metadata/WORKER_ARGS.json',runner.worker_args(config))
                worker_file=out/'metadata/worker.json'
                write(worker_file,dict(worker=config,adapter=dict(out=str(out),on=a.on,
                    items=a.items,extensions=str(ext) if ext else None)))
                worker_env=clean_environment(out,card)
                command=['nice','-n','10','bash',str(VNICE),inputs['python'],'-B','-I',
                         str(HERE/'worker228.py'),str(worker_file),'--observe']
                write(out/'metadata/COMMAND.json',dict(argv=command,env=worker_env,start_new_session=True))
                process=subprocess.Popen(command,env=worker_env,stdout=kwargs['stdout'],
                    stderr=kwargs['stderr'],cwd=out,start_new_session=True)
                class ObservedProcess:
                    def wait(self):
                        nonlocal worker_rc
                        while process.poll() is None:
                            if sampler.process.poll() is not None:
                                stop.write_text('nvidia-smi telemetry stopped; no retry\n')
                            time.sleep(1)
                        worker_rc=process.returncode
                        return worker_rc
                return ObservedProcess()
            with control_environment():
                result=runner.run(chosen,cards,deadline,prefix=prefix,launcher=launch)
            if sampler.process.poll() is not None:
                result['failure']='nvidia-smi telemetry failed; run is diagnostic-only'
                write(Path(chosen['output'])/'SUMMARY.json',result)
            return result
        try:
            with Sampler(card,out/'telemetry/nvidia-smi.csv') as sampler:
                summary=operator.run(run_cfg,end,[card],runner=execute)
            failure=summary.get('failure')
            if (out/'telemetry/OOM.json').exists():failure='First CUDA OOM; stopped without retry'
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
