"""One allocation: admission, staging, namespace, phase, return. Never submits."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_support as H
import stage_job as S

def main():
    root = Path(sys.argv[1])
    config = json.loads((root / 'a.json').read_text())
    try:
        return allocation(root, config)
    except Exception as error:
        source = root / 'a06'
        (source / 'metadata').mkdir(parents=True, exist_ok=True)
        H.dump(source / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        for name in ('a01.json', 'a04.json', 'a05.json'):
            if (root / name).is_file():
                (source / 'metadata' / name).write_bytes((root / name).read_bytes())
        H.snapshot_manifest(source)
        try:
            H.publish(source, config['pool'], config['cloud'], 'e' + os.urandom(8).hex(),
                      config['manifest_binding_digest'], 1)
        except Exception as returned_error:
            print(json.dumps(dict(event='a2', code=1, error_type=type(returned_error).__name__)), flush=True)
        return 1

def allocation(root, config):
    config['started_unix'] = time.time()
    config['pool'] = str(Path(config['pool']) / os.environ['SLURM_JOB_ID'])
    # The stable parent holds the lock and pointer; each allocation has a bounded
    # native return pool, so retained snapshots do not hit a shared 1-GiB cap.
    evidence = H.probe(config['pool'], root)
    print(json.dumps(dict(event='a0', **evidence)), flush=True)
    if evidence['pool']['free'] < 600_000_000 + 1024**2:
        raise ValueError('Pool lacks room for two bounded returns')
    lock = open(Path(config['pointer']).parent / 'a.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if evidence['local']['free'] < 200 * 1024**3:
        raise ValueError('Node-local staging reserve is unavailable')
    _, _, _, J = H.native()
    H.dump(root / 'a05.json', J.storage_proof(root, job=os.environ['SLURM_JOB_ID']))
    runtime = S.stage(root, config)
    _, _, NS, _ = H.native()
    source = NS.physical(root, config['logical_run'])
    source.mkdir(parents=True, exist_ok=True)
    (source / 'logs').mkdir(exist_ok=True)
    config['source'] = config['logical_run']
    H.dump(root / 'a03.json', config)
    command = S.namespace(root, config) + [runtime['python']['path'], '-I', '-s', '-B',
        str(root / 'reference/sj/orch_cd/evalx/work/milestone/native_bootstrap.py'),
        '--spec', str(root / 'a02.json'), '--', str(root / 'phase_worker.py'), str(root / 'a03.json')]
    # Every stream is retained for return; the scheduler sees only the opaque code.
    with (source / 'logs/a.log').open('xb') as log:
        process = subprocess.run(command, cwd=root, env=S.environment(root), stdout=log, stderr=subprocess.STDOUT)
    H.dump(root / 'a04.json', dict(code=process.returncode))
    if process.returncode:
        # Admission errors precede the worker's finally block; return them too.
        H.dump(source / 'FAILED.json', dict(returncode=process.returncode))
        H.snapshot_manifest(source)
        H.publish(source, config['pool'], config['cloud'], 'e' + os.urandom(8).hex(),
                  config['manifest_binding_digest'], process.returncode)
    print(json.dumps(dict(event='a1', code=process.returncode)), flush=True)
    return process.returncode

if __name__ == '__main__':
    raise SystemExit(main())
