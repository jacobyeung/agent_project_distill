import os, json, hashlib, resource, struct, subprocess, time
from pathlib import Path

T = Path(__file__).resolve().parent
KIT = T.parent / 'kit'
TREE = T.parent.parent / 'rt24h/tree'
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
NROOT = '/project/community/jjyeung/okh7/x_22c714e1'
STREAMS = ('pose', 'vqa', 'routing', 'pointing')

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (7*1024**3, 7*1024**3))
    assert resource.getrlimit(resource.RLIMIT_FSIZE) == (64*1024**2, 64*1024**2)
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    os.umask(0o077)
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def raw(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return {'path': str(p), 'sha256': sha(p)}

def put(p, value):
    return raw(p, json.dumps(value, sort_keys=True, indent=2)+'\n')

def load(p):
    return json.loads(Path(p).read_text())

def manifest(k):
    expected = dict(line.split('  ', 1)[::-1] for line in (k/'SHA256SUMS.txt').read_text().splitlines())
    actual = {str(p.relative_to(k)): sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt', 'BUILD.json')}
    return dict(path=str(k), seal=sha(k/'SHA256SUMS.txt'), expected=expected, actual=actual, ok=actual == expected)

def prepare_sandbox():
    for name in ('bin', 'tmp', 'shm', 'traces', 'cases'):
        (T/name).mkdir(exist_ok=True)
    raw(T/'bin/python3', '#!/bin/bash\nexec '+PY+' -I -s -B "$@"\n')
    (T/'bin/python3').chmod(0o755)
    # Refuse sockets; read-only mounts deny deletion outside R-backed writable mounts.
    instructions = [(0x20, 0, 0, 0)]
    for nr in (41, 42):
        instructions += [(0x15, 0, 1, nr), (0x06, 0, 0, 0x00050000 | 1)]
    instructions.append((0x06, 0, 0, 0x7fff0000))
    raw(T/'seccomp.bpf', b''.join(struct.pack('HBBI', *i) for i in instructions))

def command(label, root, project, job, args, extra=None):
    project.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    env = {'PATH': str(T/'bin')+':/usr/bin:/bin', 'SLURM_JOB_ID': job,
           'TEST_KIT': str(KIT), 'TEST_ROOT': str(root), 'TMPDIR': str(T/'tmp'),
           'XDG_CACHE_HOME': str(T/'tmp/cache'), 'PYTHONDONTWRITEBYTECODE': '1',
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
           'NUMEXPR_NUM_THREADS': '1', 'CUDA_VISIBLE_DEVICES': ''}
    env.update(extra or {})
    with (T/'seccomp.bpf').open('rb') as sec:
        cmd = ['/usr/bin/bwrap', '--ro-bind', '/usr', '/usr', '--ro-bind', '/bin', '/bin',
               '--ro-bind', '/lib', '/lib', '--ro-bind', '/lib64', '/lib64',
               '--ro-bind', '/etc', '/etc', '--ro-bind', '/scratch', '/scratch',
               '--dev', '/dev', '--remount-ro', '/dev', '--bind', str(T), str(T),
               '--ro-bind', str(KIT), str(KIT), '--ro-bind', str(TREE), str(TREE),
               '--dir', '/project/community/jjyeung/okh7', '--bind', str(project), NROOT,
               '--bind', str(T/'tmp'), '/tmp', '--bind', str(T/'shm'), '/dev/shm',
               '--unshare-user', '--unshare-pid', '--proc', '/proc', '--remount-ro', '/proc',
               '--remount-ro', '/', '--die-with-parent',
               '--chdir', str(root), '--seccomp', str(sec.fileno())]
        for k, v in env.items():
            cmd += ['--setenv', k, v]
        cmd += ['--'] + args
        start = time.monotonic()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, pass_fds=(sec.fileno(),), env=env)
    raw(T/'traces'/f'{label}.stdout', result.stdout)
    raw(T/'traces'/f'{label}.stderr', result.stderr)
    record = dict(label=label, argv=cmd, exit_code=result.returncode,
                  seconds=time.monotonic()-start, stdout=result.stdout, stderr=result.stderr,
                  env=env, nice=os.getpriority(os.PRIO_PROCESS, 0),
                  affinity=sorted(os.sched_getaffinity(0)), memory_limit_bytes=7*1024**3)
    path = T/'commands.json'
    records = load(path) if path.exists() else []
    records.append(record)
    put(path, records)
    print(json.dumps({k: record[k] for k in ('label', 'exit_code', 'seconds')}), flush=True)
    return record
