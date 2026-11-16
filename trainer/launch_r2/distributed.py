"""Use the parent's worker launcher only after explicit, bound GPU authorization."""
import datetime
import importlib
import os
from pathlib import Path
import subprocess
import sys
from student_pilot.p3_provenance import file_pin, load, pinned, write


def parent_launcher():
    previous = {name: sys.modules.get(name) for name in ('v', 'q0')}
    try:
        for name in previous:
            sys.modules[name] = importlib.import_module('launch_s1.b.'+name)
        return importlib.import_module('launch_s1.b.i')
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def authorized(root, launch, cfg, mode, environment=None):
    from student_pilot.carrier_c1_run import identity
    environment = os.environ if environment is None else environment
    auth = load(Path(root)/'k/4.json')
    end = datetime.datetime.fromisoformat(auth['allow_until_utc'].replace('Z','+00:00'))
    if (mode not in ('t','u') or mode not in auth['modes']
            or not launch.get('production_authorized') or auth.get('production_go_granted') is not True
            or auth.get('source_revision') != launch['source_revision']
            or auth.get('config_sha256') != identity(cfg)
            or end.tzinfo is None or end <= datetime.datetime.now(datetime.timezone.utc)):
        raise ValueError('Missing or expired production GO for this source and mode')
    review = load(pinned(cfg['admission'])) if cfg.get('admission') else {}
    if (review.get('verdict') != 'PASS' or not review.get('reviewer')
            or review.get('config_sha256') != identity(cfg) or review.get('preparation') != cfg['preparation']):
        raise ValueError('Independent review is not bound to the derived configuration')
    native = parent_launcher()
    world = native.allocation_gpus(mode,cfg)
    if (environment.get('S1_CPU_REHEARSAL','0') != '0'
            or environment.get('SLURM_JOB_NUM_NODES') != '1'
            or environment.get('SLURM_GPUS_ON_NODE') != str(world)
            or not environment.get('SLURM_JOB_ID','').isdecimal()
            or native.granted(auth,mode,'0') != world
            or auth['other_running_and_pending_gpus']+world > auth['gpu_cap']):
        raise ValueError('Production allocation differs from the parent authorization')
    allocation = load(pinned(cfg['authorization'])) if cfg.get('authorization') else {}
    if allocation != dict(config_sha256=identity(cfg),new_gpus=world,
                          job_id=environment['SLURM_JOB_ID'],verdict='GO'):
        raise ValueError('Missing job-bound allocation receipt')
    if mode=='u' and not cfg.get('resume'):
        raise ValueError('Resume requires a pinned continuation')
    return native.launcher(Path(root),mode,'0',cfg)


def launch(root, cfg, mode, launch_record):
    command = authorized(root,launch_record,cfg,mode)
    path = Path(root)/'o/ee000006.json'
    write(path,cfg)
    return subprocess.run(command,env={**os.environ,'K1':file_pin(path)['sha256']},check=True)


def worker(root, mode, arm):
    root = Path(root).resolve()
    if arm != '0':
        raise ValueError('Unknown worker arm')
    from student_pilot.source_seal import inventory
    from student_pilot.carrier_c1_run import train
    source = root/'o/ee000001'
    if inventory(source) != load(root/'k/7.json')['files']:
        raise ValueError('Worker source differs from the sealed archive')
    cfg = load(pinned(dict(path=str(root/'o/ee000006.json'),sha256=os.environ['K1'])))
    authorized(root,load(root/'k/launch.json'),cfg,mode)
    return train(cfg,resume_pin=cfg.get('resume') if mode=='u' else None)
