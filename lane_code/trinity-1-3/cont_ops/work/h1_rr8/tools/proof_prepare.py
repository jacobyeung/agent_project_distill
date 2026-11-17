"""Execute certified production preparation in isolated physical run locations."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import stat
import subprocess
import sys
import time

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text())

def private(p):
    p = Path(p)
    if p.is_symlink() or not p.is_dir() or stat.S_IMODE(p.stat().st_mode) != 0o700:
        raise ValueError('Directory must be private: '+str(p))

def program(wrapper, jobscript):
    # Preserve production commands verbatim. End the outer wrapper before restore
    # or mirror workers, and job.sh before its training-mode selection/exec.
    end = 'read -r slot sstep < <(newest || true)'
    assert wrapper.count(end) == 2
    prefix = wrapper[:wrapper.index(end)]
    marker = 'RUN="$(/usr/bin/python3 -I -c '
    assert jobscript.count(marker) == 1
    jobprefix = jobscript[:jobscript.index(marker)]
    root = 'ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"'
    assert jobprefix.count(root) == 1
    # Sourcing from stdin has no BASH_SOURCE path; ROOT remains the exact KH.
    jobprefix = jobprefix.replace(root, 'ROOT="$KH"')
    return ('set -e\nexport CUDA_VISIBLE_DEVICES=""\n' + prefix + '\nset -e\n' + jobprefix
            + '\n/bin/bash "$ROOT/b/r.sh" p 0\n')

def command(bw, kh, work, rs):
    # The whole filesystem is read-only except proof storage and job receipts.
    # Overlay KH mirrors as well: c.sh persists JSON and arm state after mode p.
    args = [bw, '--die-with-parent', '--unshare-pid', '--unshare-net', '--ro-bind', '/', '/',
            '--proc', '/proc', '--dev', '/dev', '--bind', str(work/'tmp'), '/tmp',
            '--tmpfs', str(rs.parent), '--bind', str(work/'slots'), str(rs),
            '--tmpfs', str(kh)]
    for p in sorted(kh.iterdir()):
        if p.name in ('o', 'arm', 'runs'): continue
        if p.is_symlink(): raise ValueError('Linked kit entry')
        args += ['--ro-bind', str(p), str(p)]
    for n in ('arm', 'runs'): args += ['--bind', str(work/n), str(kh/n)]
    args += ['--bind', str(kh/'o'), str(kh/'o'), '--chdir', str(kh),
             '--setenv', 'CUDA_VISIBLE_DEVICES', '', '/bin/bash', '-c',
             'set -e; chmod 700 -- "$1" "$2"; exec /bin/bash -s',
             'a', str(kh), str(rs.parent)]
    return args

def verify_prepared(kh, physical_run):
    sys.path.insert(0, str(kh/'b'))
    from d import effective
    launch = load(kh/'k/launch.json')
    cfg = load(kh/launch['config']['file'])
    derived = effective(kh, cfg, dict(launch, run_directory=str(physical_run)))
    data_path = physical_run/'inputs/data_receipt.json'
    data = load(data_path)
    if data['status'] != 'PREPARED' or data['gpu_first_step_pending'] is not True:
        raise ValueError('Preparation did not reach the first-batch boundary')
    return dict(admission_result=data, data_receipt_sha256=sha(data_path),
                prepared_seals=dict(source=data['source_seal'], preparation=data['preparation'],
                                    config=data['config'], frames=data['frames']),
                effective_config_verified=True, first_batch_executed=False)

def execute(args, script, log, verify, runner=subprocess.run):
    started = time.time()
    result = dict(status='FAIL', rc=1, started_epoch=started, admission_result=None,
                  prepared_seals=None, first_batch_executed=False, training_executed=False)
    try:
        with log.open('x') as f:
            p = runner(args, input=script, text=True, stdout=f, stderr=subprocess.STDOUT)
        result['rc'] = p.returncode if p.returncode >= 0 else 128-p.returncode
        if p.returncode == 0:
            result.update(verify())
            result['status'] = 'PASS'
    except BaseException as exc:
        rc = exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1
        result.update(status='FAIL', rc=rc or 1, error=type(exc).__name__+': '+str(exc))
    result.update(finished_epoch=time.time(), elapsed_seconds=time.time()-started)
    return result

def main(authority):
    os.umask(0o077)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    def stopped(signum, frame): raise SystemExit(128+signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1): signal.signal(sig, stopped)
    job = os.environ.get('SLURM_JOB_ID', '')
    if not re.fullmatch('[1-9][0-9]*', job): raise ValueError('Numeric allocation required')
    if os.environ.get('SLURM_JOB_NAME') != authority['job_name']: raise ValueError('Job name differs')
    kh, bun = Path(authority['kh']), Path(authority['bun'])
    for p in (kh.parent, kh, bun, kh/'o'): private(p)
    destination = kh/'o'/(job+'.proof.json')
    # Reserve the receipt name before expensive work. A failure is never PASS.
    with destination.open('x') as f:
        json.dump(dict(status='RUNNING', job=job, rc=None, production_authorized=False), f)
        f.write('\n')
    result = dict(status='FAIL', rc=1, job=job, production_authorized=False,
                  started_epoch=time.time(), admission_result=None, prepared_seals=None)
    try:
        ids = load(bun/'ids.json')
        assert ids['identity'] == authority['identity'] and ids['contract'] == authority['contract']
        assert sha(bun/'jb.sh') == authority['wrapper_sha256']
        for n, h in authority['runtime'].items():
            if sha(kh/n) != h: raise ValueError('Production runtime differs: '+n)
        launch = load(kh/'k/launch.json')
        cfg = load(kh/launch['config']['file'])
        sys.path.insert(0, str(kh/'b'))
        from i import identity, allocation_gpus
        from d import contract, digest
        import a
        a.main(kh)
        assert launch['status'] == 'READY' and identity(cfg) == authority['identity']
        assert digest(contract(launch, cfg)) == authority['contract']
        assert allocation_gpus('p', cfg) == 0
        assert cfg['s1_routing']['selection']['sha256'] == authority['selection_sha256']
        assert sha(kh/'k/selection_equality.json') == authority['equality_sha256']
        compared = load(bun/'compare.json')
        assert compared['manifest_sha256'] == sha(kh/'SHA256SUMS.txt')
        assert compared['config_key']+'.json' == Path(launch['config']['file']).name
        work = Path('/tmp/jjyeung')/('p_'+authority['tag']+'_'+job)
        private(work.parent)
        work.mkdir(mode=0o700)
        for n in ('tmp', 'tmp/jjyeung', 'tmp/jjyeung/a_17c4ffa4', 'slots', 'arm', 'runs'):
            (work/n).mkdir(mode=0o700)
        rs = Path(launch['persistent_run_root'])
        assert str(rs) == authority['persistent_root']
        physical = work/'tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4'
        script = program((bun/'jb.sh').read_text(), (kh/'job.sh').read_text())
        (work/'entry.sh').write_text(script)
        args = command('/usr/bin/bwrap', kh, work, rs)
        result.update(config_identity=identity(cfg), config=launch['config'],
                      manifest_sha256=sha(kh/'SHA256SUMS.txt'), contract_sha256=digest(contract(launch,cfg)),
                      selection=cfg['s1_routing']['selection'], equality_sha256=authority['equality_sha256'],
                      wrapper_sha256=authority['wrapper_sha256'], runtime_sha256=authority['runtime'],
                      entry_sha256=sha(work/'entry.sh'), physical_run=str(physical),
                      physical_slots=str(work/'slots'), staging_root=str(work/'tmp/jjyeung/a_17c4ffa4/root'),
                      real_job_reuse=False, cuda_visible_devices='',
                      allocation_gpus=os.environ.get('SLURM_GPUS_ON_NODE', '0'))
        result.update(execute(args, script, kh/'o'/(job+'.proof.log'), lambda: verify_prepared(kh, physical)))
    except BaseException as exc:
        rc = exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1
        result.update(status='FAIL', rc=rc or 1, error=type(exc).__name__+': '+str(exc))
    result.setdefault('finished_epoch', time.time())
    result.setdefault('elapsed_seconds', result['finished_epoch']-result['started_epoch'])
    with destination.open('w') as f:
        json.dump(result, f, sort_keys=True, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps(dict(status=result['status'], rc=result['rc'], receipt=str(destination))))
    return result['rc']
