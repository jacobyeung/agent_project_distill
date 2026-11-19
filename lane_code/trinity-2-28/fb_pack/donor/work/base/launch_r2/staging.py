"""Python 3.6 bootstrap: authenticated node-local staging before trainer imports."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile

AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
AL = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
P = '/project/community/jjyeung/c7d31ddd'


def sha(path):
    h = hashlib.sha256()
    with open(str(path), 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    value = json.loads(Path(path).read_text())
    if isinstance(value, dict) and value.get('encoding') == 'base64-json':
        raw = base64.b64decode(value['payload'], validate=True)
        if hashlib.sha256(raw).hexdigest() != value['sha256']:
            raise ValueError('Capsule digest differs')
        return json.loads(raw)
    return value


def checked(path, expected):
    path = Path(path)
    if sha(path) != expected:
        raise ValueError('Staging digest differs')
    return path


def unpack(path, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(str(path)) as archive:
        for m in archive.getmembers():
            target = destination / m.name
            if Path(m.name).is_absolute() or '..' in Path(m.name).parts or m.isdev() or m.isfifo():
                raise ValueError('Archive escaped node-local root')
            if m.issym() or m.islnk():
                link = (target.parent / m.linkname).resolve() if m.issym() else (destination / m.linkname).resolve()
                if destination not in link.parents:
                    raise ValueError('Archive link escaped node-local root')
        archive.extractall(str(destination))


def assemble(entry, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if 'payload' in entry:
        raw = base64.b64decode(entry['payload'], validate=True)
        with destination.open('xb') as f:
            f.write(raw)
    else:
        with destination.open('xb') as out:
            for part in entry['parts']:
                with open(part, 'rb') as source:
                    shutil.copyfileobj(source, out, 1024 * 1024)
    if entry.get('sha256'):
        return checked(destination, entry['sha256'])
    if not entry.get('inventory'):
        raise ValueError('Archive has no authenticated inventory')
    return destination


def relative_paths(value):
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.update(relative_paths(key))
            found.update(relative_paths(item))
    elif isinstance(value, list):
        for item in value:
            found.update(relative_paths(item))
    elif isinstance(value, str) and value.startswith('u/'):
        found.add(value)
    return found


def validate_plan(cfg, entries):
    missing = relative_paths(cfg) - set(entries)
    if missing:
        raise ValueError('Relative pins absent from staging plan: '+','.join(sorted(missing)))
    for name in relative_paths(cfg):
        e = entries[name]
        if not e.get('sha256') or not any(k in e for k in ('payload', 'parts', 'archive', 'directory', 'required_parameter')):
            raise ValueError('Unresolved staging input: '+name)
    return sorted(relative_paths(cfg))


def stage_inputs(entries, local):
    local = Path(local).resolve()
    archives = {}
    for name, entry in sorted(entries.items()):
        target = local / name
        if not name.startswith('u/') or '..' in Path(name).parts or local not in target.resolve().parents:
            raise ValueError('Staging target escaped the input root')
        if 'archive' in entry or 'directory' in entry:
            source = entry.get('archive', entry.get('directory'))
            key = source.get('sha256') or source['inventory_sha256']
            if not isinstance(key, str) or len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
                raise ValueError('Invalid archive identity')
            if key not in archives:
                path = assemble(source, local/'a'/key)
                archives[key] = local/'x'/key
                unpack(path, archives[key])
                for member, expected in source.get('inventory', {}).items():
                    if Path(member).is_absolute() or '..' in Path(member).parts:
                        raise ValueError('Staging inventory escaped its archive')
                    checked(archives[key]/member, expected)
            member = Path(entry.get('member', ''))
            if member.is_absolute() or '..' in member.parts:
                raise ValueError('Staging member escaped its archive')
            origin = archives[key]/entry.get('member', '')
            if entry.get('directory'):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(origin, target_is_directory=True)
            else:
                checked(origin, entry['sha256'])
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(str(origin), str(target))
        else:
            assemble(entry, target)


def command(root, mode, local, plan):
    bw = checked(plan['bwrap']['file'], plan['bwrap']['sha256'])
    union = local/'root/aws/u'
    union.mkdir(parents=True, exist_ok=True)
    cmd = [str(bw)]
    for name in ('/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc', '/opt', '/run', '/sys', '/project'):
        if Path(name).exists():
            cmd += ['--ro-bind', name, name]
    cmd += ['--dev-bind', '/dev', '/dev', '--proc', '/proc', '--tmpfs', '/home',
            '--dir', '/home/jjyeung', '--ro-bind', str(union), AS, '--ro-bind', str(union), AL,
            '--bind', str(local/'kit'), AS+'/ap/8865619b',
            '--ro-bind', str(local/'root/c7d31ddd'), P,
            '--bind', str(local), str(local), '--remount-ro', '/home',
            '--unshare-user', '--uid', str(os.getuid()), '--gid', str(os.getgid()),
            '--chdir', AS+'/ap/8865619b',
            P+'/venvs/rwtrain_torch211_cu129/bin/python', '-I', '-s', '-B',
            str(local/'kit/b/l.py'), str(local/'kit'), mode, str(local/'source')]
    return cmd


def main(root, mode):
    root = Path(root).resolve()
    sys.path.insert(0, str(root/'b'))
    import a
    a.main(root, build_only=False)
    zero = read(root/'k/0.json')
    plan = read(checked(root/zero['staging']['path'], zero['staging']['sha256']))
    launch = read(root/'k/launch.json')
    cfg = read(checked(root/launch['config']['file'], launch['config']['sha256']))
    validate_plan(cfg, plan['entries'])
    local = Path('/tmp/jjyeung/okit_'+zero['commit'][-16:])
    local.mkdir(parents=True, exist_ok=False)
    signal.signal(signal.SIGUSR1, lambda *_: (local/'stop').write_text('USR1\n'))
    # All writable state, including controls and upload receipts, stays local.
    for name in ('b', 'k'):
        shutil.copytree(str(root/name), str(local/'kit'/name))
    for name in ('ANON_OK.json', 'SHA256SUMS.txt', 'job.sh'):
        shutil.copyfile(str(root/name), str(local/'kit'/name))
    (local/'kit/o').mkdir()
    (local/'kit/runs').mkdir()
    (local/'tmp').mkdir()
    archive = checked(plan['venv']['file'], plan['venv']['sha256'])
    unpack(archive, local/'root/c7d31ddd/venvs')
    if mode == 'h':
        proof = subprocess.run(['/usr/bin/python3', '-I', '-s', '-B', str(root/'b/q.py'), str(root)],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        value = json.loads(proof.stdout)
        value.update(venv_sha256=plan['venv']['sha256'], bwrap_sha256=plan['bwrap']['sha256'])
        raw = json.dumps(value, sort_keys=True).encode()
        (local/'kit/o/01.json').write_text(json.dumps(dict(encoding='base64-json',
            sha256=hashlib.sha256(raw).hexdigest(), payload=base64.b64encode(raw).decode())))
    env = {k:v for k,v in os.environ.items() if k.startswith('SLURM_') or k in (
        'PATH', 'CUDA_VISIBLE_DEVICES', 'TK_JOB_START', 'LANG')}
    env.update(TMPDIR=str(local/'tmp'), XDG_CACHE_HOME=str(local/'tmp/c'),
               HF_HOME=str(local/'tmp/h'), OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
               PYTHONDONTWRITEBYTECODE='1', K2=str(local/'source'), K3=str(local/'stop'))
    process = subprocess.Popen(command(root, mode, local, plan), env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b''):
        print(json.dumps(dict(code='L01',sha256=hashlib.sha256(line).hexdigest())),flush=True)
    return process.wait()


if __name__ == '__main__':
    try:
        sys.exit(main(*sys.argv[1:]))
    except Exception as error:
        # The plaintext mapping is retained by the builder's test/report harness.
        print(json.dumps(dict(code='E01', sha256=hashlib.sha256(str(error).encode()).hexdigest())))
        sys.exit(2)
