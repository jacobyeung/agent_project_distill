"""Inside sbx.sh lcopy: strace the payload imports (launcher environment), a no-OPENSSL_CONF control, and the real
launch_gpu.sh chain with the fake nvidia-smi. Audit every file syscall for /home and /data* paths and writes."""
import json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path('/scratch/jjyeung/orch_n30/sb_ph2fix'); KIT = ROOT/'sb_mask_phrase'
W = Path('/scratch/jjyeung/orch_n30/sb_ph2chk/work'); LOGS = W/'logs'
sys.path.insert(0, str(KIT/'part2'))
import launch_gpu as L  # noqa: E402

PY = str(ROOT/'payload/environment/bin/python')
CODE = ('import ssl, hashlib, torch; torch.set_num_threads(8); '
        'print(ssl.OPENSSL_VERSION, hashlib.sha256(b"probe").hexdigest(), torch.__version__)')
STRACE = ['strace', '-f', '-v', '-yy', '-s', '4096', '-e', 'trace=%file,%process']
LINE = re.compile(r'^(\d+)\s+(\w+)\((.*)$')
NFS = re.compile(r'^/(?:home|data[^/]*)(?:/|$)')
WRITE_FLAGS = ('O_WRONLY', 'O_RDWR', 'O_CREAT', 'O_TRUNC', 'O_APPEND')
MUTATE = {'mkdir', 'mkdirat', 'rename', 'renameat', 'renameat2', 'unlink', 'unlinkat', 'rmdir', 'link', 'linkat', 'symlink',
          'symlinkat', 'chmod', 'fchmodat', 'truncate', 'utimensat', 'creat', 'mknod', 'mknodat'}


def launcher_shell_env():
    """The environment launch_gpu.sh hands to launch_gpu.py (its exports over the caller's environment)."""
    env = dict(os.environ)
    env.update(OPENSSL_CONF=str(KIT)+'/../payload/environment/ssl/openssl.cnf', PATH='/usr/bin:/bin',
               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
    return env


def audit(log, allowed):
    nfs, writes, opens_nfs, cnf, execs = {}, {}, 0, [], []
    for line in open(log, errors='replace'):
        m = LINE.match(line)
        if not m:
            continue
        pid, call, rest = m.groups()
        if call in ('execve', 'execveat'):
            first = re.findall(r'"((?:[^"\\]|\\.)*)"', rest)[:1]
            envs = dict(x.split('=', 1) for x in re.findall(r'"([A-Z_][A-Z0-9_]*=[^"]*)"', rest) if '=' in x)
            execs.append(dict(pid=pid, file=first[0] if first else None, OPENSSL_CONF=envs.get('OPENSSL_CONF'), PATH=envs.get('PATH')))
            paths = first
        else:
            paths = re.findall(r'"((?:[^"\\]|\\.)*)"', rest) + re.findall(r'<(/[^>]*)>', rest)
        for p in paths:
            if NFS.match(p):
                key = f'{call} {p}'
                nfs[key] = nfs.get(key, 0) + 1
                if call in ('open', 'openat', 'openat2', 'creat'):
                    opens_nfs += 1
            if p.endswith('openssl.cnf'):
                cnf.append(f'{call} {p} {line.rsplit("=", 1)[-1].strip()[:40]}')
        is_write = (call in ('open', 'openat', 'openat2') and any(f in rest for f in WRITE_FLAGS)) or call in MUTATE
        q = re.findall(r'"((?:[^"\\]|\\.)*)"', rest)
        if is_write and q and ' = -1 ' not in line:
            p = q[-1] if call.startswith(('rename', 'link', 'symlink')) else q[0]
            if p.startswith('/') and not p.startswith(('/dev/', '/proc/')) and not any(p.startswith(a) for a in allowed):
                writes[f'{call} {p}'] = writes.get(f'{call} {p}', 0) + 1
            elif not p.startswith('/'):
                fd = re.findall(r'<(/[^>]*)>', rest)
                full = (fd[0]+'/'+p) if fd else 'RELATIVE:'+p
                if not any(full.startswith(a) for a in allowed):
                    writes[f'{call} {full}'] = writes.get(f'{call} {full}', 0) + 1
    payload_execs = [e for e in execs if e['file'] and e['file'].startswith(str(ROOT/'payload'))]
    return dict(log=str(log), nfs_touches=sum(nfs.values()), nfs_opens=opens_nfs, nfs_detail=dict(sorted(nfs.items())[:40]),
                writes_outside=dict(sorted(writes.items())[:40]), n_writes_outside=sum(writes.values()), openssl_cnf=cnf[:10],
                payload_execs=payload_execs[:10], execs=len(execs))


def traced(name, cmd, env, allowed, cwd):
    log = LOGS/f'strace_{name}.txt'
    t = time.time()
    r = subprocess.run(STRACE+['-o', str(log)]+cmd, env=env, cwd=cwd, capture_output=True, text=True)
    rec = dict(command=cmd, rc=r.returncode, seconds=round(time.time()-t, 1), stdout=r.stdout[-600:], stderr=r.stderr[-1500:])
    rec.update(audit(log, allowed))
    print(name, json.dumps({k: rec[k] for k in ('rc', 'seconds', 'nfs_touches', 'nfs_opens', 'n_writes_outside', 'openssl_cnf')}), flush=True)
    return rec


def main():
    out = KIT/'out/pool_part2'
    probe = W/'strace_probe_out'
    orig = dict(os.environ)
    base = launcher_shell_env()
    os.environ.clear(); os.environ.update(base)
    env = L.environment(KIT, probe, '', 4320, 'pass', False)
    for key in ('HOME', 'TMPDIR'):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    allowed = [str(probe), '/tmp/terminator/', str(LOGS)]
    res = dict(environment={k: env[k] for k in ('OPENSSL_CONF', 'PATH', 'HOME', 'CUDA_VISIBLE_DEVICES')})
    res['imports'] = traced('imports', [PY, '-B', '-c', CODE], env, allowed, str(KIT))
    control = {k: v for k, v in env.items() if k != 'OPENSSL_CONF'}
    res['control_no_openssl_conf'] = traced('control', [PY, '-B', '-c', CODE], control, allowed, str(KIT))
    allowed = [str(out), '/tmp/terminator/', str(LOGS)]
    # As the documented launch: `env PATH=/usr/bin:/bin bash launch_gpu.sh` from the caller's shell environment.
    res['launcher_chain'] = traced('launcher', ['bash', str(KIT/'part2/launch_gpu.sh'), '--node-local', '0'],
                                   dict(orig, PATH='/usr/bin:/bin'), allowed, str(KIT))
    res['caller_env_nfs_vars'] = {k: v for k, v in orig.items() if re.search(r'(^|:)/(home|data)', v)}
    res['pool_after'] = sorted(str(p.relative_to(out)) for p in out.rglob('*')) if out.exists() else None
    for name in ('step5.log', 'KILLED.json'):
        p = out/name
        res[name] = p.read_text()[-1500:] if p.exists() else None
    (W/'STRACE_CHECK.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
