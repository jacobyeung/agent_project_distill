"""Small package contracts; transport lives in the pinned template."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ORDER = ('camera_displacement', 'camera_rotation', 'camera_movement_direction',
         'object_abs_distance', 'room_size_estimation')
FORBIDDEN = ('split', 'revsi', 'vsibench', 'scannet', 'arkit', 'distill', 'qgen',
             'sam', 'qwen', 'h1', 'h10', 'head', 'routing', 'faithful', 'devs1',
             'g3t', 'camera', 'displacement', 'rotation', 'movement', 'distance',
             'r0', 'scannetpp', 'direction', 'own', 'room', 'selector', 'parity', 'benchmark', 'dataset', 'model')
POOL = '/project/community/jjyeung/okh7/ae71c903'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def opaque(values):
    for value in values:
        if value == '--gres=gpu:h100:1':continue  # Exact hardware request, not an experiment name.
        if any(word in str(value).lower() for word in FORBIDDEN):
            raise ValueError('Non-opaque Slurm surface: '+str(value))


def valid_token(value):
    if not re.fullmatch('[a-f][0-9a-f]{10,15}', value):
        raise ValueError('Require 11–16 hex characters, starting a–f for template compatibility')
    return value


def template(path=None):
    path = Path(path) if path else Path(__file__).parent/'vendor'
    sys.path.insert(0, str(path.resolve()))
    import orchard_stage, orchard_job, orchard_results, return_io, chain_save
    return orchard_stage, orchard_job, orchard_results, return_io, chain_save


def seconds(value):
    if not re.fullmatch(r'\d{2}:\d{2}:\d{2}', value):
        raise ValueError('Time must be HH:MM:SS')
    h, m, s = map(int, value.split(':'))
    if m >= 60 or s >= 60:raise ValueError('Invalid time')
    return h*3600+m*60+s


def submit_argv(token, gpus, walltime):
    valid_token(token)
    limit=seconds(walltime)
    if not 1 <= gpus <= 4 or not 2400 <= limit or limit*gpus > 5*3600:
        raise ValueError('Require 1–4 GPUs, at least 40 minutes, and at most 5 allocated GPU-hours')
    values=['sbatch', '--parsable', '--account=mt01', '--partition=general', '--nodes=1',
            '--ntasks=1', '--gres=gpu:h100:'+str(gpus), '--cpus-per-task=8', '--mem=200G',
            '--time='+walltime, '--signal=B:USR1@1800', '--no-requeue', '--export=NONE',
            '--output=/dev/null', '--error=/dev/null', '--chdir=/tmp',
            '--job-name=a15_cot_ap'+token]
    opaque(values)
    return values


def read_config(package):
    """Public descriptor authenticates the tar; descriptive pins live only inside it."""
    import tarfile
    package=Path(package)
    public=json.loads((package/'0.json').read_text())
    if sha(package/'0.tgz')!=public['payload_sha256']:raise ValueError('Code archive differs')
    with tarfile.open(package/'0.tgz') as archive:
        cfg=json.load(archive.extractfile('9.json'))
    if canonical(cfg)!=public['plan_sha256']:raise ValueError('Plan digest differs')
    return {**cfg,**public}


def checked_run(argv, **kwargs):
    import subprocess
    opaque(argv)
    return subprocess.run(argv,**kwargs)


def install_process_guard(root):
    """Scan every descendant launched by Python, including template helpers."""
    import subprocess
    root=Path(root)
    original=subprocess.Popen
    def spawn(argv,*args,**kwargs):
        argv=list(argv)
        for i,arg in enumerate(argv):
            if str(arg).endswith('/orchard_h10/vendor/return_io.py'):
                dest=root/'6.py'
                dest.write_bytes(Path(arg).read_bytes());argv[i]=str(dest)
        opaque(argv)
        env=kwargs.get('env')
        if env is None:
            env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','CUDA_VISIBLE_DEVICES','TMPDIR') or k.startswith('SLURM_')}
            kwargs['env']=env
        opaque([f'{k}={v}' for k,v in env.items()])
        if kwargs.get('cwd') is not None:opaque([kwargs['cwd']])
        return original(argv,*args,**kwargs)
    subprocess.Popen=spawn
