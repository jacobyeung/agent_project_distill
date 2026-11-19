"""Package-interpreter operator and import probe; execute only with an explicit switch."""
import argparse
import importlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *
from gpu228 import Sampler

PROBE_MODULES=('e2e_reader.perception_memo','h1eval.h10.launch','h1eval.items','h1eval.modes','h1eval.cli')

def probe(package):
    install_imports(package)
    # Match Orchard's entry/dispatch argv branch while importing h1eval.
    sys.argv=[str(Path(package)/'orchard_h10/entry.py'),'1.json']
    for name in PROBE_MODULES:importlib.import_module(name)
    return dict(passed=True,modules=list(PROBE_MODULES),python=sys.executable)

def worker_command(python,prefix,worker_file):
    # The operator is already in the package namespace. vnice owns only the worker group.
    return ['nice','-n','10']+list(prefix)+[python,'-B','-I',str(HERE/'worker228.py'),str(worker_file),'--observe']

def execute(dispatch):
    target_host()
    out=local(dispatch['out']);cfg=dispatch['config'];card=dispatch['card'];end=dispatch['end']
    install_imports(cfg['package'])
    from orchard_h10.common import install_process_guard
    install_process_guard(out)
    sys.argv=[str(Path(cfg['package'])/'orchard_h10/entry.py'),'1.json']
    operator=load_module(dispatch['operator'],'read228_sealed_operator')
    from orchard_h10 import runner
    # These logical d/q paths resolve to the authenticated private root inside bwrap.
    policy_check(paths=dict(vnice=cfg['prefix'][1],terminator=str(Path(cfg['prefix'][1]).with_name('terminator.sh'))))
    if dispatch['on']:
        chosen=read(cfg['settings'])
        chosen.update(read_processor_only='off',read_processor_cache='on',read_vision_cache='on',
                      read_sam_cache='on',read_cache_bytes=12*1024**3)
        path=out/'metadata/settings_on.json';write(path,chosen);cfg['settings']=str(path)
    stop=Path(cfg['output'])/'metadata/STOP'
    def stop_requested(number,frame):stop.write_text('Signal '+str(number)+'; finish current item\n')
    old={n:signal.signal(n,stop_requested) for n in (signal.SIGINT,signal.SIGTERM,signal.SIGUSR1)}
    failure=None;summary=None
    def run(chosen,cards,deadline,*,prefix):
        def launch(argv,**kwargs):
            config=read(Path(kwargs['cwd'])/argv[-1])
            write(out/'metadata/WORKER_ARGS.json',runner.worker_args(config))
            worker_file=out/'metadata/worker.json'
            write(worker_file,dict(worker=config,adapter=dict(out=str(out),on=dispatch['on'],
                items=dispatch['items'],extensions=dispatch['extensions'])))
            worker_env=clean_environment(out,card)
            command=worker_command(cfg['python'],prefix,worker_file)
            write(out/'metadata/COMMAND.json',dict(argv=command,env=worker_env,start_new_session=True,
                                                  inherited_namespace=True))
            process=subprocess.Popen(command,env=worker_env,stdout=kwargs['stdout'],
                stderr=kwargs['stderr'],cwd=out,start_new_session=True)
            class ObservedProcess:
                def wait(self):
                    while process.poll() is None:
                        if sampler.process.poll() is not None:
                            stop.write_text('nvidia-smi telemetry stopped; no retry\n')
                        time.sleep(1)
                    return process.returncode
            return ObservedProcess()
        with control_environment():
            result=runner.run(chosen,cards,deadline,prefix=prefix,launcher=launch)
        if sampler.process.poll() is not None:
            result['failure']='nvidia-smi telemetry failed; run is diagnostic-only'
            write(Path(chosen['output'])/'SUMMARY.json',result)
        return result
    try:
        with Sampler(card,out/'telemetry/nvidia-smi.csv') as sampler:
            summary=operator.run(cfg,end,[card],runner=run)
        failure=summary.get('failure')
        if (out/'telemetry/OOM.json').exists():failure='First CUDA OOM; stopped without retry'
    except BaseException as error:
        failure=str(error);traceback.print_exc()
    finally:
        for n,handler in old.items():signal.signal(n,handler)
    write(out/'metadata/OPERATOR_RESULT.json',dict(summary=summary,failure=failure))
    return 1 if failure or summary is None else 0

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--probe',metavar='PACKAGE');mode.add_argument('--execute',metavar='DISPATCH')
    args=parser.parse_args(argv)
    if args.probe:
        print(json.dumps(probe(args.probe),sort_keys=True));return 0
    return execute(read(args.execute))

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print('REFUSED: '+type(error).__name__+': '+str(error),file=sys.stderr);raise SystemExit(2)
