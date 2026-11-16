import argparse
import csv
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orchard_stage as S
import orchard_results as R
import chain_save as A


SJ = Path('/scratch/jjyeung')
FSW = Path('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung')
AP = Path('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap')
UV = '/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'


def physical(root, path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Require a canonical registered path')
    for logical, local in ((SJ, 'sj'), (FSW, 'fsw'), (AP, 'm/ap')):
        if path.is_relative_to(logical):
            return Path(root)/local/path.relative_to(logical)
    raise ValueError('Path has no job-local mapping: '+str(path))


class StorageRefusal(ValueError):
    def __init__(self, message, evidence):
        super().__init__(message)
        self.evidence = evidence


def active_mount(path):
    anchor = Path(path)
    while not anchor.exists():
        anchor = anchor.parent
    fd = os.open(anchor, os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for line in Path(f'/proc/self/fdinfo/{fd}').read_text().splitlines():
            if line.startswith('mnt_id:'):
                return dict(mount_id=int(line.split()[1]), probe_path=str(anchor))
        raise ValueError('The directory handle has no kernel mount id')
    finally:
        os.close(fd)


def storage_proof(path, mountinfo=None, job=None):
    path = Path(path).resolve()
    text = Path('/proc/self/mountinfo').read_text() if mountinfo is None else mountinfo
    entries, tmp_entries = [], []
    for line in text.splitlines():
        before, after = line.split(' - ', 1)
        fields, fs = before.split(), after.split()
        decode = lambda value: re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), value)
        mount = Path(decode(fields[4]))
        if mount == Path('/tmp'):
            tmp_entries.append(line)
        if path.is_relative_to(mount):
            entries.append(dict(path=str(path), mount=str(mount), mount_id=int(fields[0]),
                mount_root=decode(fields[3]), filesystem=fs[0], source=decode(fs[1]),
                selected_mount_entry=line))
    observed = dict(path=str(path), tmp_mount_entries=tmp_entries, selected_mount_entry=None)
    try:
        observed.update(active_mount(path))
    except (OSError, ValueError) as error:
        raise StorageRefusal('Cannot identify the work directory mount: '+str(error), observed) from error
    matches = [entry for entry in entries if entry['mount_id'] == observed['mount_id']]
    if len(matches) != 1:
        raise StorageRefusal('No unique physical local storage evidence for the kernel mount id', observed)
    value = dict(observed, **matches[0])
    if (value['filesystem'] not in ('ext4', 'xfs', 'btrfs', 'tmpfs')
            or (value['filesystem'] != 'tmpfs' and not value['source'].startswith('/dev/'))):
        raise StorageRefusal('Storage is not a proven local filesystem', value)
    if job is not None:
        parts = Path(value['mount_root']).parts
        if (not str(job).isdigit() or value['mount'] != '/tmp' or 'job_tmp' not in parts
                or str(job) not in parts):
            raise StorageRefusal('Storage is not the assigned job-private /tmp mount', value)
        value['job'] = str(job)
    return value


def card(require_empty=False):
    query = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,name,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'],
                           check=True, capture_output=True, text=True, timeout=30)
    processes = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory',
                                '--format=csv,noheader,nounits'],
                               check=True, capture_output=True, text=True, timeout=30)
    own = subprocess.run(['pgrep', '-fu', os.environ['USER'],
                          '[/]a[a-z][0-9a-f]+/p/reader/chain.py'],
                         capture_output=True, text=True, timeout=30)
    visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    rows = [[item.strip() for item in row] for row in csv.reader(query.stdout.splitlines()) if row]
    assigned = rows if len(rows) == 1 else [row for row in rows if visible in row[:2]]
    if len(assigned) != 1 or assigned[0][2] != 'NVIDIA H100 80GB HBM3':
        raise ValueError('The assigned card is not one authenticated H100 80GB HBM3')
    selected = assigned[0]
    if not visible or ',' in visible or (visible.startswith('GPU-') and visible != selected[1]):
        raise ValueError('CUDA visibility differs from the single assigned GPU')
    if require_empty and (float(selected[3]) > 32 or float(selected[4]) != 0
                          or selected[1] in processes.stdout):
        raise ValueError('The assigned GPU is not empty at the fresh check')
    return dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), job=os.environ['SLURM_JOB_ID'],
                hostname=os.uname().nodename, gpu_type=selected[2], gpu_uuid=selected[1],
                slurm_job_gpus=os.environ.get('SLURM_JOB_GPUS'), cuda_visible_devices=visible,
                nvidia_smi=query.stdout, compute_processes=processes.stdout,
                pgrep=own.stdout, pgrep_returncode=own.returncode)


def namespace(root, config=None):
    root = Path(root)
    argv = [str(root/'bwrap')]
    for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc', 'opt', 'run', 'sys'):
        path = Path('/')/name
        if path.is_symlink():
            argv += ['--symlink', os.readlink(path), str(path)]
        elif path.exists():
            argv += ['--ro-bind', str(path), str(path)]
    argv += ['--dev-bind', '/dev', '/dev', '--proc', '/proc', '--bind', '/tmp', '/tmp',
             '--dir', '/scratch', '--bind', str(root/'sj'), str(SJ),
             '--bind', str(root/'fsw'), str(FSW), '--dir', '/lustre',
             '--bind', str(root/'m/ap'), str(AP),
             '--ro-bind', str(root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'), UV,
             '--dir', '/home/jjyeung', '--die-with-parent', '--chdir', str(root)]
    if config is not None:
        package=physical(root,config['spec']['package'])
        for row in json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text()):
            argv += ['--ro-bind',str(root/'v'/(row['sha256']+'.mp4')),
                     config['spec']['inputs']['video_root']+'/'+row['relative_path']]
    return argv


def environment(root):
    root = Path(root)
    for name in ('cache', 'temp', 'home'):
        (root/name).mkdir(exist_ok=True)
    return dict(PATH='/usr/local/bin:/usr/bin:/bin', USER=os.environ['USER'],
                SLURM_JOB_ID=os.environ['SLURM_JOB_ID'],
                CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES', ''),
                HOME=str(root/'home'), TMPDIR=str(root/'temp'), XDG_CACHE_HOME=str(root/'cache'),
                HF_HOME=str(root/'cache/hf'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false',
                VLLM_NO_USAGE_STATS='1', DO_NOT_TRACK='1', VLLM_USE_FLASHINFER_SAMPLER='0',
                PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='1')


def stop(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=20)


def run(root, config):
    root = Path(root)
    source = physical(root, config['spec']['run'])
    output = physical(root, config['output'])
    process, code, failure = None, 1, None
    evidence = {}
    proof = config.get('mode') == 'proof'
    if proof:
        from proof_card import card as selected_card
    else:
        selected_card = card

    def interrupted(number, frame):
        raise RuntimeError('Orchard allocation signal '+str(number))

    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(number, interrupted)
    try:
        evidence['storage'] = storage_proof(root, job=os.environ['SLURM_JOB_ID'])
        local_environment = environment(root)
        os.environ.update({key: local_environment[key] for key in ('HOME', 'TMPDIR', 'XDG_CACHE_HOME')})
        evidence['initial_card'] = selected_card(require_empty=True)
        evidence['staging'] = S.stage(root, config, physical)
        output.mkdir(parents=True)
        for path in (source.parent, output):
            proof = storage_proof(path, job=os.environ['SLURM_JOB_ID'])
            if proof['source'] != evidence['storage']['source']:
                raise ValueError('Runtime output does not use the proven job-local disk')
        evidence['launch_card'] = selected_card(require_empty=True)
        command = namespace(root,config)+[config['spec']['interpreters']['vllm'], '-s', '-B',
            str(root/'bootstrap/trace_runtime.py'), '--script',
            str(Path(config['spec']['package'])/'reader/chain.py'), '--root', str(root),
            '--config', str(root/'bootstrap/CONFIG.json')]
        with (root/'chain.log').open('xb') as log:
            process = subprocess.Popen(command, env=environment(root), cwd=root,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            code = process.wait()
        if code:
            raise RuntimeError('Accepted chain exited with code '+str(code))
        if not (source/'COMPLETE.json').is_file() or (source/'FAILED.json').exists():
            raise ValueError('Chain completion is missing or conflicts with a failure')
    except BaseException as error:
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
            signal.signal(number, signal.SIG_IGN)
        failure, code = str(error), code or 1
        if isinstance(error, StorageRefusal):
            evidence['storage_refusal'] = error.evidence
        stop(process)
    finally:
        source.mkdir(parents=True, exist_ok=True)
        (source/'metadata').mkdir(exist_ok=True)
        (source/'logs').mkdir(exist_ok=True)
        try:
            evidence['final_card'] = selected_card()
        except Exception as error:
            evidence['final_card_error'] = str(error)
            failure, code = failure or 'Final GPU evidence unavailable', code or 1
        if failure:
            A.atomic_json(source/'FAILED.json', dict(error=failure, returncode=code))
        A.atomic_json(source/'metadata/ORCHARD_LAUNCHER.json', evidence)
        if (root/'STAGING.json').is_file():
            (source/'metadata/STAGING.json').write_bytes((root/'STAGING.json').read_bytes())
        for name in ('launch_card', 'final_card'):
            if name in evidence:
                (source/'metadata'/(name+'.txt')).write_text(evidence[name].get('nvidia_smi', ''))
        artifact = physical(root, config['spec']['artifact']['path'])
        if artifact.is_file():
            if artifact.stat().st_size > 4*1024**2:
                failure, code = 'Export metadata exceeds its allowance', code or 1
                A.atomic_json(source/'FAILED.json', dict(error=failure, returncode=code))
            else:
                (source/'metadata/EXPORT_ARTIFACT.json').write_bytes(artifact.read_bytes())
        for name in ('chain.log', 'staging.log'):
            path = root/name
            if path.is_file():
                with path.open('rb') as stream:
                    stream.seek(max(0, path.stat().st_size-2*1024**2))
                    (source/'logs'/('launcher_'+name)).write_bytes(stream.read(2*1024**2))
        try:
            import trace_runtime
            trace_runtime.snapshot()
            trace_runtime.collect(root, source/'TRACE.json.gz')
            A.ARCHIVE_LIMIT = (19000000 if proof else 200000000) - 1
            result = R.publish(source, R.AUTHORIZED_POOL, config['token'], config['plan_sha256'], code)
            code = code if result['status'] == 'COMPLETE' else code or 1
        except Exception as error:
            A.atomic_json(root/'RETURN_INCOMPLETE.json', dict(error=str(error), returncode=code or 1))
            code = code or 1
        return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if config.get('schema') != 'evalx-orchard-batch-v1':
        raise ValueError('Unrecognized Orchard batch contract')
    review = json.loads((Path(args.config).parent/'REVIEW.json').read_text())
    digest = S.hashlib.sha256(json.dumps(config['launcher_pins'], sort_keys=True).encode()).hexdigest()
    if (S.sha(Path(args.config).parent/'REVIEW.json') != config['launcher_review_pin']['sha256']
            or review.get('schema') != 'new-build-integrity-v1' or review.get('code_pins_sha256') != digest):
        raise ValueError('Build integrity record differs')
    for path, expected in config['launcher_pins'].items():
        if S.sha(Path(args.config).parent/Path(path).name) != expected:
            raise ValueError('A packaged dependency differs')
    import orchard_launcher as L
    payload = Path(args.config).parent/'payload.tar.gz'
    if S.sha(payload) != config['payload_sha256']:
        raise ValueError('The reader payload differs')
    L.validate_payload(payload.read_bytes(), config)
    raise SystemExit(run(args.root, config))


if __name__ == '__main__':
    main()
