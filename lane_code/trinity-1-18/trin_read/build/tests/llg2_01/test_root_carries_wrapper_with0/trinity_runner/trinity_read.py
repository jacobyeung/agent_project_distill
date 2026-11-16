#!/usr/bin/env python3
"""Local-only Trinity staging and launch boundary for the unchanged dev-S1 reader."""
import argparse
import ast
import base64
import contextlib
import csv
import datetime
import fcntl
import glob
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import threading
import time
import uuid

sys.dont_write_bytecode = True
BUILD = Path(__file__).resolve().parent
AREA = Path('/scratch/jjyeung/orch_n30/trin_read')
DEFAULT_ROOT = AREA/'root'
KIT = Path('/trinity-kit') if Path('/trinity-kit').exists() else AREA/'kit_src'
REFERENCE = Path('/scratch/jjyeung/orch_n30/evalx27/work/kit/build/pb59bef09f3')
STORE = '/project/community/jjyeung/cp4tk_fr/k6tk'
VNICE = '/data3/shared/scripts/vnice/vnice.sh'
DEFAULT_BWRAP = '/usr/bin/bwrap'
PINNED_BWRAP_SHA256 = 'e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71'
ACCEPTED_CONFIG_SHA256 = 'a5d934125b00400916e2660c8721beb7d88dcf02f9e6cfeebbb97ae136920dfa'
FAMILIES = ('main', 'away', 'forward')
REQUIRED_PIECES = {'bootstrap', 'runtime_0', 'runtime_1', 'runtime_2', 'a0', 'bwrap', 'reader_payload', 'base', 'export'}
SJ = Path('/scratch/jjyeung')
FSW = Path('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung')
AP = Path('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap')
VLLM_ENV = AP/'19252904/e'
LLG_STUB = AREA/'build/llg_stub/llguidance'
LLG_TARGET = VLLM_ENV/'lib/python3.12/site-packages/llguidance'
LLG_PINS = {
    '__init__.py': '01fc27773baceee9eb87ff76cec70d8ce761a8ddef6c73055224e77a70023572',
    'hf.py': '72b199ae58e47693d9d9eecd1974ce4eba13ded40acab969ecdbdba00201b1f2',
    'torch.py': '72b199ae58e47693d9d9eecd1974ce4eba13ded40acab969ecdbdba00201b1f2',
}
UV = '/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'
LINEAGE = FSW/'ap/8865619b/runs/469ddece'


def inside(path, parent):
    try:
        Path(path).relative_to(parent)
        return True
    except ValueError:
        return False


def writable(path):
    path = Path(path).resolve()
    if not any(inside(path, p) for p in (AREA/'build', DEFAULT_ROOT)):
        raise ValueError('Writes must remain under build/ or root/: '+str(path))
    return path


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def install_runner(root):
    """Carry the three wrapper modules with a root-only copy; never alter kit bytes."""
    destination = root/'trinity_runner'
    rows = {}
    for name in ('trinity_read.py', 'namespace_worker.py', 'compare_tokens.py'):
        source = BUILD/name; target = destination/name
        rows[name] = dict(bytes=source.stat().st_size, sha256=sha(source))
        if target.exists():
            if sha(target) != rows[name]['sha256']:
                raise ValueError('Staged wrapper differs; preserve and review '+str(target))
        else:
            destination.mkdir(exist_ok=True)
            with target.open('xb') as f: f.write(source.read_bytes())
    if (destination/'MANIFEST.json').exists():
        if load(destination/'MANIFEST.json') != rows:
            raise ValueError('Staged wrapper manifest differs')
    else:
        dump(destination/'MANIFEST.json', rows)


def package(root, config):
    return physical(root, config['spec']['package'])


def gz_bytes(raw):
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as f:
        f.write(raw)
    return stream.getvalue()


def dump(path, value):
    path = writable(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name+'.new.'+uuid.uuid4().hex)
    with pending.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(str(pending), str(path))


@contextlib.contextmanager
def lock(path):
    path = writable(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def kit_stage():
    # Trinity's system Python is 3.6; this compatibility method changes no kit file.
    if not hasattr(Path, 'is_relative_to'):
        Path.is_relative_to = lambda self, other: inside(self, other)
    source = KIT/'launcher' if (KIT/'launcher').is_dir() else BUILD.parent/'bootstrap'
    sys.path.insert(0, str(source))
    import orchard_stage
    return orchard_stage


def physical(root, path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Require a canonical logical path')
    for prefix, directory in ((SJ, 'sj'), (FSW, 'fsw'), (AP, 'm/ap')):
        if inside(path, prefix):
            return Path(root)/directory/path.relative_to(prefix)
    raise ValueError('Unregistered logical path: '+str(path))


def reference_bundle(reference=REFERENCE):
    """Decode data from the accepted BATCH.sh; never execute its shell/Python."""
    config = load(reference/'CONFIG.json')
    script = (reference/'BATCH.sh').read_text()
    literal = re.search(r'^raw=base64.b64decode\((.*),validate=True\)$', script, re.M)
    expected = re.search(r"^if hashlib.sha256\(raw\).hexdigest\(\)!='([0-9a-f]{64})'", script, re.M)
    if not literal or not expected:
        raise ValueError('Unrecognized accepted bootstrap')
    raw = base64.b64decode(ast.literal_eval(literal.group(1)), validate=True)
    if hashlib.sha256(raw).hexdigest() != expected.group(1):
        raise ValueError('Bootstrap hash differs')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
        for m in tf:
            if not m.isfile() or m.name in files or not re.fullmatch(r'bootstrap/[A-Za-z0-9_.]+', m.name):
                raise ValueError('Unexpected bootstrap member')
            files[m.name] = tf.extractfile(m).read()
    if json.loads(files['bootstrap/CONFIG.json']) != config:
        raise ValueError('Reference CONFIG differs from bundle')
    for name, digest in config['launcher_pins'].items():
        if hashlib.sha256(files['bootstrap/'+Path(name).name]).hexdigest() != digest:
            raise ValueError('Bootstrap launcher pin differs')
    if hashlib.sha256(files['bootstrap/REVIEW.json']).hexdigest() != config['launcher_review_pin']['sha256']:
        raise ValueError('Bootstrap review pin differs')
    payload = files['bootstrap/payload.tar.gz']
    if hashlib.sha256(payload).hexdigest() != config['payload_sha256']:
        raise ValueError('Bootstrap payload pin differs')
    pins = {}
    with tarfile.open(fileobj=io.BytesIO(payload)) as tf:
        for m in tf:
            kit_stage().relative(m.name)
            if not m.isfile() or m.name in pins:
                raise ValueError('Unexpected payload member')
            pins[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()
    if pins != config['payload_pins']:
        raise ValueError('Payload member pins differ')
    return config, files


def receipt_ready(path):
    receipt = Path(str(path)+'.RECEIPT.json')
    if not path.is_file() or not receipt.is_file():
        return False
    value = load(receipt)
    if not isinstance(value, dict):
        raise ValueError('Invalid completion receipt: '+str(receipt))
    # Receipts admit a completed transfer; authoritative hashes come from the kit.
    for key in ('bytes', 'size'):
        if key in value and isinstance(value[key], int) and value[key] != path.stat().st_size:
            raise ValueError('Receipt size differs: '+str(path))
    if 'sha256' in value and sha(path) != value['sha256']:
        raise ValueError('Receipt SHA256 differs: '+str(path))
    return True


def authenticate_parts(path, group):
    if path.stat().st_size != sum(row[1] for row in group):
        raise ValueError('Runtime archive size differs')
    whole = hashlib.sha256()
    with path.open('rb') as f:
        for _, size, expected in group:
            h = hashlib.sha256(); remaining = size
            while remaining:
                chunk = f.read(min(1024*1024, remaining))
                if not chunk:
                    raise ValueError('Truncated runtime archive')
                h.update(chunk); whole.update(chunk); remaining -= len(chunk)
            if h.hexdigest() != expected:
                raise ValueError('Runtime part SHA256 differs')
    return whole.hexdigest()


def small_archive_inventory(source, pin):
    """Recover an old camera receipt's member pins from its authenticated small tar."""
    if source.stat().st_size != pin['bytes'] or sha(source) != pin['sha256']:
        raise ValueError('Camera archive pin differs')
    inventory = {}
    with tarfile.open(str(source)) as archive:
        for member in archive:
            kit_stage().relative(member.name)
            if member.isdir(): continue
            if not member.isfile() or member.name in inventory:
                raise ValueError('Unexpected camera archive member')
            digest = hashlib.sha256()
            with archive.extractfile(member) as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''): digest.update(chunk)
            inventory[member.name] = dict(bytes=member.size, sha256=digest.hexdigest())
    return inventory


def piece(root, state, name, action):
    previous = state['pieces'].get(name)
    if previous:
        if previous['status'] != 'complete':
            raise ValueError('Partial stage refused: '+name+'; preserve it for operator review')
        return
    state['pieces'][name] = dict(status='partial', started=time.time())
    dump(root/'STAGING.json', state)
    result = action()
    state['pieces'][name] = dict(status='complete', completed=time.time(), evidence=result)
    dump(root/'STAGING.json', state)


def verify_export_local(root, config):
    """Hash the existing export without moving it or resolving its logical links on host."""
    spec = config['spec']; pin = spec['artifact']; artifact = physical(root, pin['path'])
    if sha(artifact) != pin['sha256']:
        raise ValueError('Existing export artifact SHA256 differs')
    a = load(artifact)
    if a['step'] != spec['step'] or a['schema'] != 'carrier-c1-artifact-v1':
        raise ValueError('Existing export identity differs')
    manifest = physical(root, a['full_weights']['path'])
    if manifest != artifact.parent/'full_weights/full_weights.json' or sha(manifest) != a['full_weights']['sha256']:
        raise ValueError('Existing full-weights manifest differs')
    m = load(manifest)
    for row in [m['index']]+m['files']:
        if Path(row['name']).name != row['name']:
            raise ValueError('Unsafe export member')
        p = manifest.parent/row['name']
        if 'bytes' in row and p.stat().st_size != row['bytes']:
            raise ValueError('Existing export shard size differs')
        if sha(p) != row['sha256']:
            raise ValueError('Existing export member SHA256 differs: '+row['name'])
    return dict(artifact_sha256=pin['sha256'], full_weights_sha256=a['full_weights']['sha256'],
                files=len(m['files']), moved=False)


def stage(root, dl):
    root = writable(root); dl = Path(dl).resolve(); root.mkdir(parents=True, exist_ok=True)
    config, bootstrap = reference_bundle(); S = kit_stage()
    with lock(root/'.stage.lock'):
        state = load(root/'STAGING.json') if (root/'STAGING.json').exists() else dict(schema=1, pieces={})
        for name, item in state['pieces'].items():
            if item['status'] != 'complete':
                raise ValueError('Partial stage refused: '+name)
        S.room(root)
        def boot():
            if (root/'bootstrap').exists():
                raise ValueError('Unrecorded bootstrap destination exists')
            for name, raw in bootstrap.items():
                p = root/name; p.parent.mkdir(parents=True, exist_ok=True)
                with p.open('xb') as f: f.write(raw)
            return dict(payload_sha256=config['payload_sha256'])
        piece(root, state, 'bootstrap', boot)
        missing = []
        for index, group in enumerate(config['assets']['groups']):
            name = 'runtime_'+str(index); source = dl/(name+'.tar')
            if name in state['pieces']:
                continue
            if not receipt_ready(source):
                missing.append(source.name+' + receipt'); continue
            def runtime(source=source, group=group):
                digest = authenticate_parts(source, group); S.room(root, source.stat().st_size)
                inventory = S.unpack(source, root, links=True)
                return dict(sha256=digest, files=len(inventory), inventory=inventory)
            piece(root, state, name, runtime)
        for name, filename, pin in [('a0', 'camera.tar', config['assets']['camera_archive']),
                                     ('bwrap', 'bwrap', config['assets']['bwrap_pin'])]:
            source = dl/filename
            if name in state['pieces']:
                if name == 'a0' and 'inventory' not in state['pieces'][name]['evidence'] and receipt_ready(source):
                    state['pieces'][name]['evidence']['inventory'] = small_archive_inventory(source, pin)
                continue
            if not receipt_ready(source):
                missing.append(filename+' + receipt'); continue
            def small(source=source, pin=pin, name=name):
                if source.stat().st_size != pin['bytes'] or sha(source) != pin['sha256']:
                    raise ValueError('Local '+name+' pin differs')
                if name == 'bwrap':
                    with (root/'bwrap').open('xb') as out, source.open('rb') as inp:
                        shutil.copyfileobj(inp, out)
                    (root/'bwrap').chmod(0o700)
                else:
                    inventory = S.unpack(source, root)
                    return dict(sha256=pin['sha256'], inventory=inventory)
                return dict(sha256=pin['sha256'])
            piece(root, state, name, small)
        runtime_done = all('runtime_'+str(i) in state['pieces'] for i in range(3))
        if runtime_done and 'a0' in state['pieces']:
            def payload():
                with (root/'bootstrap/payload.tar.gz').open('rb') as f:
                    inventory = S.extract_stream(f, root, None, 32*1024**2, overlay=True)
                return dict(files=len(inventory), sha256=config['payload_sha256'], inventory=inventory)
            piece(root, state, 'reader_payload', payload)
        source = dl/'base.tar'
        if 'base' not in state['pieces']:
            if 'runtime_2' not in state['pieces'] or not receipt_ready(source):
                missing.append('base.tar + receipt + runtime_2')
            else:
                def base():
                    if source.stat().st_size != config['assets']['base_archive_bytes']:
                        raise ValueError('Base archive size differs')
                    pin = config['assets']['base_manifest']; manifest = physical(root, pin['path'])
                    if sha(manifest) != pin['sha256']:
                        raise ValueError('Base manifest hash differs')
                    dest = root/'m/ap/85fc3486'
                    if dest.exists(): raise ValueError('Unrecorded base destination exists')
                    S.room(root, source.stat().st_size); dest.mkdir(parents=True)
                    inventory = S.unpack(source, dest, strip=3)
                    expected = {r['path']: {k:r[k] for k in ('bytes', 'sha256')} for r in load(manifest)['files']}
                    if inventory != expected:
                        raise ValueError('Base file inventory differs from frozen manifest')
                    return dict(files=len(inventory), manifest_sha256=pin['sha256'])
                piece(root, state, 'base', base)
        # Verification is independent of pending runtime pieces; no export fetch exists.
        piece(root, state, 'export', lambda: verify_export_local(root, config))
        state['complete'] = REQUIRED_PIECES <= set(state['pieces']); state['missing'] = missing
        dump(root/'STAGING.json', state)
        install_runner(root)
        return state


def store_index(root):
    path = Path(root)/'k6tk/MEMBERS.tsv.gz'; result = {}
    if path.exists():
        with gzip.open(str(path), 'rt') as f:
            for line in f:
                digest, shard = line.rstrip('\n').split('\t')
                if not re.fullmatch('[0-9a-f]{64}', digest) or not re.fullmatch('[a-z0-9]+_[0-9]+[.]tar', shard):
                    raise ValueError('Malformed frame store index')
                if digest in result: raise ValueError('Duplicate store SHA')
                part = path.parent/'parts'/shard.split('_')[0]/shard
                if not part.is_file(): raise ValueError('Indexed frame shard is absent')
                result[digest] = shard
    return result


def frame_members(path):
    with tarfile.open(str(path), 'r:*') as tf:
        seen = set()
        for m in tf:
            digest = Path(m.name).stem
            if (not m.isfile() or not re.fullmatch('[0-9a-f]{64}', digest)
                    or m.name != digest[:2]+'/'+digest+'.png' or digest in seen or m.size > 64*1024**2):
                raise ValueError('Unexpected PNG archive member: '+m.name)
            raw = tf.extractfile(m).read()
            if not raw.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('PNG SHA256 or signature differs: '+m.name)
            seen.add(digest)
            yield digest, raw


def frames(root, archives):
    root = writable(root); store = root/'k6tk'; store.mkdir(parents=True, exist_ok=True)
    with lock(store/'.lock'):
        index = store_index(root); added = 0; total_bytes = 0
        for path in archives:
            path = Path(path).resolve()
            # Validate the entire input before publishing anything from this input.
            fresh = {h:len(raw) for h, raw in frame_members(path) if h not in index}
            if not fresh: continue
            kit_stage().room(store, sum(fresh.values())+1024*len(fresh)+10240)
            tag = 't'+uuid.uuid4().hex; partdir = store/'parts'/tag; partdir.mkdir(parents=True)
            shard = tag+'_000.tar'; partial = partdir/(shard+'.partial')
            with tarfile.open(str(partial), 'w', format=tarfile.USTAR_FORMAT) as tf:
                written = set()
                for digest, raw in frame_members(path):
                    if digest not in fresh: continue
                    info = tarfile.TarInfo(digest[:2]+'/'+digest+'.png'); info.size = len(raw); info.mode = 0o444
                    tf.addfile(info, io.BytesIO(raw)); written.add(digest)
                if written != set(fresh): raise ValueError('Frame input changed during build')
            os.replace(str(partial), str(partdir/shard))
            # Append a gzip member: existing index bytes and shards never change.
            rows = ''.join(h+'\t'+shard+'\n' for h in sorted(fresh)).encode()
            with (store/'MEMBERS.tsv.gz').open('ab') as f:
                f.write(gz_bytes(rows)); f.flush(); os.fsync(f.fileno())
            index.update({h:shard for h in fresh}); added += len(fresh); total_bytes += sum(fresh.values())
        if not (store/'MEMBERS.tsv.gz').exists():
            (store/'MEMBERS.tsv.gz').write_bytes(gz_bytes(b''))
        return dict(added=added, added_png_bytes=total_bytes, frames=len(index))


def shm_directory(root, shm=None):
    path = writable(shm or root/'shm')
    path.mkdir(parents=True, exist_ok=True)
    return path


def bwrap_path(root, path=DEFAULT_BWRAP):
    """Reject the staged evidence binary, including links and byte-identical copies."""
    path = Path(path).resolve()
    staged = root/'bwrap'
    if path == staged.resolve() or (staged.exists() and os.path.samefile(str(path), str(staged))):
        raise ValueError('Staged bwrap is authenticated evidence only; choose a host bwrap')
    if sha(path) == PINNED_BWRAP_SHA256:
        raise ValueError('Pinned Orchard bwrap must never execute')
    if not path.is_file() or not os.access(str(path), os.X_OK):
        raise ValueError('bwrap must be an executable file: '+str(path))
    return str(path)


def bwrap_evidence(root, path=DEFAULT_BWRAP):
    path = bwrap_path(root, path)
    digest = sha(path)
    version = subprocess.run([path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True, timeout=30, check=True)
    if sha(path) != digest: raise ValueError('bwrap changed during version check')
    return dict(path=path, sha256=digest, version=version.stdout, version_stderr=version.stderr)


def llguidance_evidence(enabled=True):
    """Authenticate the entire import-only overlay before exposing it to Python."""
    evidence = dict(enabled=bool(enabled), path=str(LLG_STUB), target=str(LLG_TARGET),
                    sha256=dict(LLG_PINS), verified=False, version=2,
                    satisfies=['llguidance', 'LLMatcher', 'LLTokenizer', 'LLInterpreter',
                               'llguidance.hf (raises)', 'llguidance.torch (raises)'])
    if not enabled:
        return evidence
    if not LLG_STUB.is_dir() or LLG_STUB.is_symlink():
        raise ValueError('llguidance stub directory missing or linked: '+str(LLG_STUB))
    if set(p.name for p in LLG_STUB.iterdir()) != set(LLG_PINS):
        raise ValueError('llguidance stub inventory differs: '+str(LLG_STUB))
    for name, digest in LLG_PINS.items():
        path = LLG_STUB/name
        if path.is_symlink() or not path.is_file() or sha(path) != digest:
            raise ValueError('llguidance stub pin mismatch: '+str(path))
    evidence['verified'] = True
    return evidence


def namespace(root, gpu=False, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):
    root = writable(root)
    overlay = llguidance_evidence(llguidance_stub)
    if overlay['enabled']:
        target = physical(root, LLG_TARGET)
        if not target.is_dir() or target.is_symlink() or target.resolve() != target:
            raise ValueError('llguidance overlay requires an existing staged directory: '+str(target))
    argv = [bwrap_path(root, bwrap), '--unshare-net']
    for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc', 'opt', 'run', 'sys'):
        path = Path('/')/name
        if path.is_symlink(): argv += ['--symlink', os.readlink(str(path)), str(path)]
        elif path.exists(): argv += ['--ro-bind', str(path), str(path)]
    argv += (['--dev-bind', '/dev', '/dev'] if gpu else ['--dev', '/dev'])
    argv += ['--bind', str(shm_directory(root, shm)), '/dev/shm',
             '--proc', '/proc', '--bind', str(root/'temp'), '/tmp',
             '--dir', '/scratch', '--bind', str(root/'sj'), str(SJ),
             '--bind', str(root/'fsw'), str(FSW), '--dir', '/lustre',
             '--bind', str(root/'m/ap'), str(AP),
             '--ro-bind', str(root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'), UV,
             '--bind', str(root), str(root), '--ro-bind', str(root/'trinity_runner'), '/trinity-build',
             '--ro-bind', str(root/'k6tk'), STORE,
             '--dir', '/home/jjyeung', '--die-with-parent', '--chdir', str(root)]
    if overlay['enabled']:
        argv += ['--ro-bind', overlay['path'], overlay['target']]
    return argv


def environment(root, gpu='', token='cpu', shm=None):
    shm_directory(root, shm)
    for name in ('cache', 'temp', 'home', 'k6tk', 'cache/hf', 'cache/triton', 'cache/torchinductor', 'cache/vllm'):
        (root/name).mkdir(parents=True, exist_ok=True)
    return dict(PATH='/usr/local/bin:/usr/bin:/bin', USER=os.environ.get('USER', 'jjyeung'),
                SLURM_JOB_ID=token, CUDA_VISIBLE_DEVICES=gpu, HOME=str(root/'home'), TMPDIR=str(root/'temp'),
                XDG_CACHE_HOME=str(root/'cache'), HF_HOME=str(root/'cache/hf'),
                TRITON_CACHE_DIR=str(root/'cache/triton'), TORCHINDUCTOR_CACHE_DIR=str(root/'cache/torchinductor'),
                VLLM_CACHE_ROOT=str(root/'cache/vllm'),
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                TOKENIZERS_PARALLELISM='false', VLLM_NO_USAGE_STATS='1', DO_NOT_TRACK='1',
                VLLM_USE_FLASHINFER_SAMPLER='0', PYTHONDONTWRITEBYTECODE='1',
                OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='1')


def require_stage(root):
    state = load(root/'STAGING.json')
    if not state.get('complete'): raise ValueError('Stage incomplete: '+str(state.get('missing')))
    config = load(root/'bootstrap/CONFIG.json')
    if sha(root/'bootstrap/payload.tar.gz') != config['payload_sha256']:
        raise ValueError('Staged payload changed')
    return config


def ns_command(root, config_path, script, args=(), gpu=False, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):
    config = load(config_path)
    return namespace(root, gpu, shm, bwrap, llguidance_stub)+[config['spec']['interpreters']['vllm'] if gpu else config['spec']['interpreters']['p1cpu'],
        '-s', '-B', str(root/'bootstrap/trace_runtime.py'), '--root', str(root), '--config', str(config_path),
        '--script', str(script)]+list(args)


def selected_tasks(tasks, ids=None, first=None):
    if any(t['benchmark'] != 'devrows' for t in tasks):
        raise ValueError('Only dev-S1 direct items are admitted')
    ordered = sorted(tasks, key=lambda t:(t['benchmark'], t['example_id']))
    if len({t['example_id'] for t in ordered}) != len(ordered):
        raise ValueError('Duplicate dev-S1 task IDs')
    if ids is not None:
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('Require a nonempty unique ID list')
        unknown = set(ids)-{t['example_id'] for t in ordered}
        if unknown: raise ValueError('IDs outside the family dev-S1 direct set: '+', '.join(sorted(unknown)))
        ordered = [t for t in ordered if t['example_id'] in set(ids)]
    elif first is not None:
        if first <= 0 or first > len(ordered): raise ValueError('--first exceeds the nonempty family set')
        ordered = ordered[:first]
    return ordered


def needed(captures, tasks):
    return sorted({f['sha256'] for t in tasks for f in captures[t['native']]['frames']})


def read_ids(path):
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]


def cpu_need(root, family, ids=None, first=None, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):
    config = require_stage(root)
    overlay = llguidance_evidence(llguidance_stub)
    install_runner(root)
    executed = bwrap_evidence(root, bwrap)
    work = root/'needs'/uuid.uuid4().hex; work.mkdir(parents=True)
    request = dict(action='need', family=family, ids=ids, first=first, work=str(work))
    dump(work/'INPUT.json', request)
    env = environment(root, shm=shm)
    cmd = ns_command(root, root/'bootstrap/CONFIG.json', '/trinity-build/namespace_worker.py',
                     ['--input', str(work/'INPUT.json')], shm=shm, bwrap=executed['path'], llguidance_stub=llguidance_stub)
    dump(work/'COMMAND.json', dict(argv=cmd, bwrap=executed, llguidance_stub=overlay))
    started = time.monotonic(); code = None
    try:
        process = subprocess.run(cmd, env=env)
        code = process.returncode
        process.check_returncode()
    finally:
        dump(work/'EXIT.json', dict(returncode=code, wall_seconds=time.monotonic()-started, bwrap=executed, llguidance_stub=overlay))
    result = load(work/'NEED.json')
    result.update(bwrap=executed, llguidance_stub=overlay, evidence_directory=str(work))
    dump(work/'NEED.json', result)
    return result


def need_command(args):
    root = writable(args.root); results = {}
    for family in FAMILIES if args.all else (args.family,):
        results[family] = cpu_need(root, family, read_ids(args.ids) if args.ids else None,
                                   args.first if not args.all else None, None, args.bwrap, getattr(args, 'llguidance_stub', True))
    hashes = sorted({h for result in results.values() for h in result['need']})
    index = store_index(root); missing = sorted(set(hashes)-set(index))
    out = writable(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(''.join(h+'\n' for h in hashes))
    Path(str(out)+'.missing').write_text(''.join(h+'\n' for h in missing))
    report = dict(families=results, frames=len(hashes), missing=missing,
                  estimated_png_bytes=sum(max(r['estimated_frame_bytes'].get(h, 0) for r in results.values()) for h in hashes),
                  estimate_basis='Conservative uncompressed RGB bytes (height * width * 3); PNG and tar sizes vary.')
    dump(str(out)+'.json', report)
    print(json.dumps(dict(out=str(out), frames=len(hashes), absent=len(missing),
                         items={f:r['items'] for f,r in results.items()}, estimated_bytes=report['estimated_png_bytes'])))


def smi(arguments):
    return subprocess.check_output(['nvidia-smi']+arguments, universal_newlines=True, timeout=30)


def check_card(index):
    if not re.fullmatch('[0-9]+', str(index)): raise ValueError('--gpu requires one physical card index')
    raw = smi(['-i', str(index), '--query-gpu=index,uuid,name,memory.total,memory.used', '--format=csv,noheader,nounits'])
    rows = list(csv.reader(raw.strip().splitlines()))
    if len(rows) != 1: raise ValueError('Require exactly one selected visible GPU')
    card_index, card_uuid, name, total, used = [x.strip() for x in rows[0]]
    processes = smi(['-i', str(index), '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'])
    if card_index != str(index) or float(total) < 40*1024 or float(used) >= 100 or card_uuid in processes:
        raise ValueError('Card must have >=40 GiB, <100 MiB used, and no compute process')
    return dict(index=card_index, uuid=card_uuid, name=name, total_mib=float(total), initial_used_mib=float(used))


class Sampler:
    def __init__(self, index, path):
        self.index, self.path = index, path
        self.stop = threading.Event(); self.errors = []
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        with self.path.open('x') as f:
            while not self.stop.is_set():
                start = time.monotonic()
                try:
                    value = float(smi(['-i', self.index, '--query-gpu=memory.used', '--format=csv,noheader,nounits']).strip())
                    f.write(json.dumps(dict(time=time.time(), memory_used_mib=value))+'\n'); f.flush()
                except Exception as error:
                    self.errors.append(str(error)); return
                self.stop.wait(max(0, 1-(time.monotonic()-start)))


def logical_artifact(root, value, step):
    path = Path(value)
    expected = LINEAGE/('m'+str(step))/'artifact.json'
    if path == physical(root, expected): path = expected
    if step <= 0 or path != expected:
        raise ValueError('Export must be the staged artifact.json of this lineage and step')
    return str(path)


def read_space(root, config, plan):
    base_pin = config['spec']['models']['base']['manifest']
    base_path = physical(root, base_pin['path'])
    artifact_pin = config['spec']['artifact']; artifact_path = physical(root, artifact_pin['path'])
    if sha(base_path) != base_pin['sha256'] or sha(artifact_path) != artifact_pin['sha256']:
        raise ValueError('Model metadata pin differs before launch')
    weight_pin = load(artifact_path)['full_weights']; weight_path = physical(root, weight_pin['path'])
    if sha(weight_path) != weight_pin['sha256']:
        raise ValueError('Full-weights manifest differs before launch')
    model_bytes = sum(row['bytes'] for row in load(base_path)['files'])+sum(row['bytes'] for row in load(weight_path)['files'])
    # The unchanged reader copies both models. Pulled PNGs also occupy a tar and an extracted tree.
    reserve = model_bytes+2*sum(plan['estimated_frame_bytes'].values())+2*1024**3
    kit_stage().room(root, reserve)
    return reserve


def host_shm_ours(directory=Path('/dev/shm')):
    """Stat immediate children only, including symlinks without following them."""
    rows = []
    for path in directory.iterdir():
        try: info = path.lstat()
        except FileNotFoundError: continue
        if info.st_uid == os.getuid():
            rows.append(dict(path=str(path), bytes=info.st_size))
    return sorted(rows, key=lambda row: row['path'])


def yield_pattern(value):
    if value is None: return None
    # A single local directory avoids recursive or shared-filesystem polling.
    path = Path(value)
    if '**' in value or glob.has_magic(str(path.parent)):
        raise ValueError('--yield-glob requires a fixed local parent and a nonrecursive filename glob')
    return str(writable(path.parent)/path.name)


def disk_listing(directory):
    """Record metadata only; never follow a directory or file symlink."""
    rows = []
    if not directory.exists(): return rows
    for parent, directories, files in os.walk(str(directory), followlinks=False):
        for name in sorted(directories+files):
            path = Path(parent)/name
            try:
                info = path.lstat()
                row = dict(path=str(path), bytes=info.st_size,
                           kind='symlink' if stat.S_ISLNK(info.st_mode) else 'directory' if stat.S_ISDIR(info.st_mode) else 'file')
                if stat.S_ISLNK(info.st_mode): row['target'] = os.readlink(str(path))
                rows.append(row)
            except FileNotFoundError:
                rows.append(dict(path=str(path), bytes=None, kind='vanished'))
    return sorted(rows, key=lambda row: row['path'])


def stop_group(process, grace=60):
    """Only signal the session/process group created by run_reader."""
    group = process.pid
    if group <= 1 or group == os.getpgrp():
        raise RuntimeError('Refuse to signal the wrapper process group')
    try: os.killpg(group, signal.SIGTERM)
    except ProcessLookupError: return process.wait()
    # Do not reap the leader until escalation ends: its PID cannot be recycled.
    time.sleep(grace)
    try: os.killpg(group, signal.SIGKILL)
    except ProcessLookupError: pass
    return process.wait()


def run_reader(command, env, root, log, pattern=None):
    process = subprocess.Popen(command, env=env, cwd=str(root), stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    try:
        while True:
            if pattern:
                matches = []
                for name in glob.glob(pattern):
                    try:
                        if stat.S_ISREG(Path(name).lstat().st_mode): matches.append(name)
                    except FileNotFoundError: pass
                if matches:
                    event = dict(matched_file=sorted(matches)[0], time=time.time(),
                                 utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), process_group=process.pid)
                    stop_group(process)
                    return 75, event
            try: return process.wait(timeout=30 if pattern else None), None
            except subprocess.TimeoutExpired: pass
    except BaseException:
        stop_group(process)
        raise


SMALL_FILE_BYTES = 1024*1024


def cheap_verify(root, rows):
    result = dict(files=0, hashed=0, size_only=0, errors=[])
    for relative, pin in sorted(rows.items()):
        path = root/relative
        try:
            if Path(relative).is_absolute() or '..' in Path(relative).parts or not inside(path.resolve(), root):
                raise ValueError('Inventory path escapes root')
            info = path.stat()
            if not stat.S_ISREG(info.st_mode): raise ValueError('Not a regular file')
            if 'bytes' in pin and info.st_size != pin['bytes']: raise ValueError('Size differs')
            if info.st_size <= SMALL_FILE_BYTES:
                if sha(path) != pin['sha256']: raise ValueError('SHA256 differs')
                result['hashed'] += 1
            elif 'bytes' not in pin:
                raise ValueError('No recorded size for large file')
            else: result['size_only'] += 1
            result['files'] += 1
        except (OSError, ValueError) as error:
            result['errors'].append(dict(path=str(path), error=str(error)))
    return result


def config_audit(root):
    """Separate authenticated, unused evidence from paths consumed by the runner."""
    rows = []; links = []; accepted = {}
    systems = ('/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc', '/opt', '/run', '/sys', '/dev', '/proc')
    bootstrap = root/'bootstrap/CONFIG.json'
    authenticated = bootstrap.is_file() and sha(bootstrap) == ACCEPTED_CONFIG_SHA256
    def flatten(value, location='$'):
        if isinstance(value, dict):
            for key, item in value.items():
                for entry in flatten(item, location+'.'+str(key)): yield entry
        elif isinstance(value, list):
            for index, item in enumerate(value):
                for entry in flatten(item, location+'['+str(index)+']'): yield entry
        elif isinstance(value, str): yield location, value
    if authenticated: accepted = dict(flatten(load(bootstrap)))

    def mapped_path(value):
        path = Path(os.path.normpath(value))
        if inside(path, root): return path
        for prefix, target in ((Path(UV), root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'),
                               (SJ, root/'sj'), (FSW, root/'fsw'), (AP, root/'m/ap'),
                               (Path(STORE), root/'k6tk'), (Path('/tmp'), root/'temp'),
                               (Path('/dev/shm'), root/'shm')):
            if inside(path, prefix): return target/path.relative_to(prefix)
        return path

    def path_check(value):
        mapped = mapped_path(value)
        resolved = mapped.resolve()
        allowed = any(inside(resolved, Path(p).resolve()) for p in (str(root), '/data3/shared/scripts/vnice')+systems)
        return str(mapped), allowed

    def active(location, filename):
        # Assets/archive transport, phase-A inputs, release records and launcher
        # receipts remain data. These fields alone reach the direct runner.
        return (location == '$.spec.package' or location == '$.assets.base_manifest.path'
                or location.startswith(('$.spec.artifact.', '$.spec.models.', '$.spec.interpreters.'))
                or (location in ('$.output', '$.spec.run') and filename != str(bootstrap)))

    def visit(value, filename):
        for location, item in flatten(value):
            path = item.startswith('/')
            host = bool(re.search(r'\b(?:trinity(?:-\d+-\d+)?|orchard-login-\d+)\b', item))
            pinned = accepted.get(location) == item
            if location == '$.spec.llguidance_stub.path' and item == str(LLG_STUB):
                try:
                    llguidance_evidence(value.get('spec', {}).get('llguidance_stub', {}).get('enabled', False))
                    valid = True
                except (ValueError, OSError):
                    valid = False
                rows.append(dict(file=filename, field=location, value=item, kind='pinned_overlay', fails=not valid))
            elif pinned and (not path or not active(location, filename)):
                rows.append(dict(file=filename, field=location, value=item, kind='pinned_evidence', fails=False))
            elif path:
                mapped, allowed = path_check(item)
                rows.append(dict(file=filename, field=location, value=item, mapped_path=mapped,
                                 kind=('namespace_alias' if mapped != item else 'allowed_path') if allowed else 'external_path',
                                 fails=not allowed))
            elif host:
                rows.append(dict(file=filename, field=location, value=item, kind='metadata', fails=False))
    for parent, directories, files in os.walk(str(root), followlinks=False):
        for name in directories+files:
            if name.startswith('.'): continue
            path = Path(parent)/name
            if path.is_symlink():
                target = os.readlink(str(path))
                logical = target if target.startswith('/') else os.path.normpath(str(path.parent/target))
                mapped, allowed = path_check(logical)
                links.append(dict(path=str(path), target=target, mapped_path=mapped, allowed=allowed))
        directories[:] = [d for d in directories if not d.startswith('.') and not (Path(parent)/d).is_symlink()]
        if 'CONFIG.json' in files:
            path = Path(parent)/'CONFIG.json'
            if path.is_symlink():
                mapped, allowed = path_check(str(path))
                rows.append(dict(file=str(path), kind='config_symlink', value=os.readlink(str(path)), fails=not allowed))
                if allowed and path.is_file() and path.stat().st_size <= 4*1024**2: visit(load(path), str(path))
            elif path.stat().st_size > 4*1024**2:
                rows.append(dict(file=str(path), kind='config_too_large_to_audit', fails=True))
            else: visit(load(path), str(path))
    passed = not any(r['fails'] for r in rows) and not any(not r['allowed'] for r in links)
    return dict(passed=passed, findings=rows, symlinks=links, pinned_template_authenticated=authenticated,
                scope='CONFIG string values and symlink targets; pinned evidence is informational. Active aliases resolve into root; large files receive no content scan.')


def selfcheck(root, bwrap=DEFAULT_BWRAP):
    root = writable(root); state = load(root/'STAGING.json'); config = load(root/'bootstrap/CONFIG.json')
    checks = {}; rows = {}; unverifiable = []
    missing = sorted(REQUIRED_PIECES-set(state['pieces']))
    overlays = state['pieces'].get('reader_payload', {}).get('evidence', {}).get('inventory', {})
    for name, item in sorted(state['pieces'].items()):
        if item['status'] != 'complete':
            unverifiable.append(name+': partial'); continue
        evidence = item['evidence']; current = {}
        if name == 'bootstrap':
            if evidence['payload_sha256'] != config['payload_sha256']:
                unverifiable.append('bootstrap: payload pin differs from STAGING.json')
            # Small bootstrap archive and launcher files have authoritative hashes.
            for filename, digest in config['launcher_pins'].items():
                current['bootstrap/'+Path(filename).name] = dict(sha256=digest)
            current['bootstrap/REVIEW.json'] = dict(sha256=config['launcher_review_pin']['sha256'])
            payload = root/'bootstrap/payload.tar.gz'
            checks['bootstrap_payload'] = dict(passed=sha(payload) == evidence['payload_sha256'])
        elif name == 'bwrap':
            current['bwrap'] = dict(config['assets']['bwrap_pin'])
            # bwrap is small enough to authenticate explicitly despite the metadata threshold.
            checks['bwrap_hash'] = dict(passed=sha(root/'bwrap') == evidence['sha256'])
        elif name == 'export':
            pin = config['spec']['artifact']; artifact = physical(root, pin['path'])
            current[str(artifact.relative_to(root))] = dict(sha256=evidence['artifact_sha256'])
            weight = load(artifact)['full_weights']; manifest = physical(root, weight['path'])
            current[str(manifest.relative_to(root))] = dict(sha256=evidence['full_weights_sha256'])
            for row in [load(manifest)['index']]+load(manifest)['files']:
                current[str((manifest.parent/row['name']).relative_to(root))] = row
        elif name == 'base':
            pin = config['assets']['base_manifest']; manifest = physical(root, pin['path'])
            current[str(manifest.relative_to(root))] = dict(sha256=evidence['manifest_sha256'])
            for row in load(manifest)['files']:
                current['m/ap/85fc3486/'+row['path']] = row
        elif 'inventory' in evidence:
            current = {p:pin for p,pin in evidence['inventory'].items() if name == 'reader_payload' or p not in overlays}
        else:
            unverifiable.append(name+': STAGING.json has no extracted-file inventory')
        rows.update(current)
    checks['pieces'] = cheap_verify(root, rows)
    manifest = root/'trinity_runner/MANIFEST.json'
    if manifest.exists():
        checks['runner'] = cheap_verify(root, {'trinity_runner/'+p:pin for p,pin in load(manifest).items()})
    else: unverifiable.append('trinity_runner: not installed; run stage from build before copying')
    # This probe needs no staged interpreter, model, frame, cache, or GPU device.
    executed = bwrap_evidence(root, bwrap)
    command = [executed['path'], '--unshare-net', '--dev', '/dev', '--dev-bind', '/dev/null', '/dev/null',
               '--tmpfs', '/dev/shm', '--proc', '/proc', '--dir', '/trinity-probe']
    for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc'):
        path = Path('/')/name
        if path.is_symlink(): command += ['--symlink', os.readlink(str(path)), str(path)]
        elif path.exists(): command += ['--ro-bind', str(path), str(path)]
    command += ['--bind', str(root), str(root), '--chdir', str(root), '--die-with-parent', '/bin/true']
    try:
        probe = subprocess.run(command, env=dict(PATH='/usr/bin:/bin'), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
        checks['cpu_namespace'] = dict(returncode=probe.returncode, stderr=probe.stderr, command=command, bwrap=executed)
    except (OSError, subprocess.SubprocessError) as error:
        checks['cpu_namespace'] = dict(returncode=None, error=str(error), command=command, bwrap=executed)
    audit = config_audit(root)
    passed = (state.get('complete', False) and not missing and not unverifiable and not checks['pieces']['errors']
              and not checks.get('runner', {}).get('errors') and checks['cpu_namespace']['returncode'] == 0
              and all(c.get('passed', True) for c in checks.values()) and audit['passed'])
    return dict(passed=bool(passed), stage_complete=state.get('complete', False), checks=checks,
                unverifiable=unverifiable, missing_pieces=missing, portability=audit, small_file_bytes=SMALL_FILE_BYTES,
                bwrap=executed, note='Large file sizes are checked, not large-file content hashes. Pinned evidence does not fail the path audit.')


def stub_usage(path, enabled=True):
    """Count all engine events; unreadable or malformed evidence cannot pass."""
    result = dict(path=str(path), enabled=enabled, import_events_count=0, call_events_count=0,
                  errors=[], calls=[])
    try:
        for line in Path(path).read_text().splitlines():
            row = json.loads(line)
            if row.get('event') == 'import' and isinstance(row.get('pid'), int) and row.get('module'):
                result['import_events_count'] += 1
            elif row.get('event') == 'call' and isinstance(row.get('name'), str):
                result['call_events_count'] += 1
                result['calls'].append(row['name'])
            else:
                result['errors'].append('Invalid stub event: '+repr(row))
    except (OSError, ValueError) as error:
        result['errors'].append(str(error))
    if result['call_events_count']:
        result['errors'].append('llguidance stub called {} time(s): {}'.format(result['call_events_count'], ', '.join(result['calls'])))
    if enabled and not result['import_events_count']:
        result['errors'].append('Enabled llguidance stub has no import evidence')
    result['passed'] = not result['errors']
    return result


def capture_command(argv):
    try:
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=30)
        return dict(argv=argv, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except (OSError, subprocess.SubprocessError) as error:
        return dict(argv=argv, returncode=None, error=str(error))


def sandbox_receipt(command=None, executed=None, overlay=None, probe_report=None):
    """Record actual namespace argv, with explicit unknowns before execution."""
    binds = []; special = []
    argv = command or []
    for i, arg in enumerate(argv):
        if arg in ('--bind', '--ro-bind', '--dev-bind'):
            binds.append(dict(source=argv[i+1], target=argv[i+2], mode='ro' if arg == '--ro-bind' else 'rw', option=arg))
        elif arg in ('--symlink',):
            special.append(dict(option=arg, source=argv[i+1], target=argv[i+2]))
        elif arg in ('--dev', '--proc', '--tmpfs'):
            special.append(dict(option=arg, target=argv[i+1]))
    glibc = capture_command(['ldd', '--version'])
    driver = capture_command(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'])
    libraries = []
    for name in ('libcuda.so.1', 'libnvidia-ml.so.1'):
        path = Path('/usr/lib64')/name
        row = dict(name=name, path=str(path), resolved_path=str(path.resolve()), bytes=None)
        try: row['bytes'] = path.stat().st_size
        except OSError as error: row['error'] = str(error)
        libraries.append(row)
    p = probe_report or {}
    return dict(bwrap=executed, namespace_argv=command, binds=binds, special_mounts=special,
                llguidance_stub=overlay, host_glibc=next(iter(glibc.get('stdout', '').splitlines()), None),
                host_glibc_command=glibc, namespace_glibc=p.get('glibc'),
                host_nvidia_driver=driver, host_driver_libraries=libraries,
                namespace_driver_resolution=p.get('imports', {}).get('driver_resolution'),
                versions=p.get('versions', {}), probe_path=p.get('evidence_directory'),
                probe_passed=p.get('passed'), unavailable_reason=p.get('error'))


PROBE_MARKER = 'TRINITY_PROBE_JSON='
PROBE_CODE = r'''
import ctypes, json, os, sys, traceback
from types import SimpleNamespace
result = dict(versions={'python': sys.version}, glibc=os.confstr('CS_GNU_LIBC_VERSION'), imports_passed=False,
              structured_output=dict(passed=False, status='not_reached'))
try:
    import vllm, torch, transformers
    result['versions'].update(vllm=vllm.__version__, torch=torch.__version__, transformers=transformers.__version__)
    from vllm import LLM
    from vllm.model_executor.models import qwen3_5
    import vllm.v1.engine.core, vllm.v1.worker.gpu_model_runner
    result['imports_passed'] = True
except Exception as error:
    result['error'] = type(error).__name__ + ': ' + str(error)
    traceback.print_exc()
try:
    from vllm.v1.structured_output.backend_guidance import GuidanceBackend, StructuredOutputOptions
    backend = SimpleNamespace(disable_any_whitespace=False, disable_additional_properties=False,
                              ll_tokenizer=None, vocab_size=1)
    # Execute the installed method; no model, tokenizer download, or GPU allocation.
    result['structured_output']['stage'] = 'GuidanceBackend.compile_grammar(REGEX, "a")'
    GuidanceBackend.compile_grammar(backend, StructuredOutputOptions.REGEX, 'a')
    result['structured_output'].update(status='unexpected_success', reason='Guidance compilation did not raise')
except Exception as error:
    result['structured_output'].update(status='raised', exception=type(error).__name__, reason=str(error))
    result['structured_output']['stub_runtime_error'] = isinstance(error, RuntimeError) and str(error).startswith('llguidance stub:')
result['driver_resolution'] = []
for name in ('libcuda.so.1', 'libnvidia-ml.so.1'):
    row = dict(name=name, paths=[])
    try:
        lib = ctypes.CDLL(name)
        with open('/proc/self/maps') as f:
            paths = sorted({line.split()[-1] for line in f if '/libcuda.so' in line or '/libnvidia-ml.so' in line})
        row['paths'] = [dict(path=p, bytes=os.stat(p).st_size) for p in paths if os.path.basename(p).startswith(name.split('.so')[0]+'.so')]
    except Exception as error:
        row['error'] = type(error).__name__ + ': ' + str(error)
    result['driver_resolution'].append(row)
result['cryptography_imported'] = any(n == 'cryptography' or n.startswith('cryptography.') for n in sys.modules)
print('TRINITY_PROBE_JSON=' + json.dumps(result, sort_keys=True), flush=True)
sys.exit(0 if result['imports_passed'] else 1)
'''



def probe(root, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):
    """Check vLLM imports with host libraries and an isolated CPU-only /dev."""
    root = writable(root)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out = root/'runs'/('probe_'+stamp); out.mkdir(parents=True)
    report = dict(passed=False, cpu_only=True, evidence_directory=str(out), returncode=None,
                  versions={}, glibc=None, cryptography_imported=None)
    started = time.monotonic()
    command = None; executed = None
    log = out/'llg_stub_calls.jsonl'; log.touch(exist_ok=False)
    try:
        report['llguidance_stub'] = llguidance_evidence(llguidance_stub)
        state = load(root/'STAGING.json') if (root/'STAGING.json').exists() else {}
        runtime = state.get('pieces', {}).get('runtime_0', {})
        uv_python = root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12'
        if runtime.get('status') != 'complete' or not uv_python.is_file():
            raise ValueError('probe requires runtime_0 staged (uv Python); input archives are not consumed or awaited')
        # The venv's absolute interpreter link resolves only inside the namespace.
        python = physical(root, VLLM_ENV/'bin/python')
        if not os.path.lexists(str(python)):
            raise ValueError('probe requires the staged vLLM interpreter: '+str(python))
        env = environment(root, shm=shm)
        env['LLG_STUB_LOG'] = str(log)
        executed = bwrap_evidence(root, bwrap)
        report.update(bwrap=executed, env=env, shm=str(shm_directory(root, shm)))
        # Match vllm_isolated.sh's -I without requiring the reader payload to be staged.
        command = namespace(root, gpu=False, shm=shm, bwrap=executed['path'], llguidance_stub=llguidance_stub)
        command += [str(VLLM_ENV/'bin/python'), '-I', '-B', '-c', PROBE_CODE]
        report['argv'] = command
        process = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, timeout=120)
        report.update(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)
        records = [line[len(PROBE_MARKER):] for line in process.stdout.splitlines() if line.startswith(PROBE_MARKER)]
        if len(records) == 1:
            imports = json.loads(records[0])
            report.update({k:imports[k] for k in ('versions', 'glibc', 'cryptography_imported')})
            report['imports'] = imports
            usage = stub_usage(log, llguidance_stub)
            structured = imports.get('structured_output', dict(status='not_reported'))
            structured['call_events_count'] = usage['call_events_count']
            structured['calls'] = usage['calls']
            structured['passed'] = bool(structured.get('stub_runtime_error') and usage['call_events_count'] > 0)
            report['structured_output'] = structured
            report['stub_usage'] = usage
            report['passed'] = (process.returncode == 0 and imports['imports_passed']
                                and (not llguidance_stub or structured['passed']))
        if not report['passed']:
            raise RuntimeError('CPU import probe failed; inspect '+str(out/'PROBE.json'))
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        error.probe_report = report
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-started
        report.setdefault('structured_output', dict(passed=False, status='not_executed', reason=report.get('error')))
        report.setdefault('stub_usage', stub_usage(log, llguidance_stub))
        dump(out/'SANDBOX.json', sandbox_receipt(command, executed, report.get('llguidance_stub'), report))
        dump(out/'PROBE.json', report)
    return report


def launch(args):
    root = writable(args.root)
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', args.token):
        raise ValueError('Token must be a letter followed by 8–32 lowercase hex digits')
    repeat = getattr(args, 'repeat', 1)
    if repeat not in (1, 2) or (args.command != 'proof' and repeat != 1):
        raise ValueError('proof --repeat must be 1 or 2')
    parent = root/'runs'/args.token if args.command == 'proof' else writable(args.out)
    if not inside(parent, root): raise ValueError('Runtime output must be under --root')
    if parent.exists(): raise ValueError('Run output exists; no automatic retry')
    outputs = []
    if repeat == 2:
        for i in (1, 2):
            if (root/'runs'/(args.token+'_r'+str(i))).exists():
                raise ValueError('Repeated run output exists; no automatic retry')
        tokens = root/'tokens'; tokens.mkdir(parents=True, exist_ok=True)
        with (tokens/args.token).open('x') as f: f.write(str(parent)+'\n')
        parent.mkdir(parents=True)
    failure = None
    try:
        for i in range(1, repeat+1):
            child = argparse.Namespace(**vars(args))
            child.run_name = args.token if repeat == 1 else args.token+'_r'+str(i)
            out = root/'runs'/child.run_name if args.command == 'proof' else parent
            try:
                _launch_one(child)
                outputs.append(out)
            finally:
                # Preflight refusals still leave a receipt, with no fabricated execution.
                if not (out/'SANDBOX.json').exists():
                    out.mkdir(parents=True, exist_ok=True)
                    receipt = sandbox_receipt(overlay=llguidance_evidence(getattr(args, 'llguidance_stub', True)))
                    receipt['unavailable_reason'] = 'Reader namespace not executed; preflight refused'
                    dump(out/'SANDBOX.json', receipt)
    except Exception as error:
        failure = error
        raise
    finally:
        if repeat == 2:
            import compare_tokens
            comparison = compare_tokens.write_repeated(root, args.token, parent, str(failure) if failure else None)
            dump(parent/'SANDBOX.json', dict(runs=[dict(path=str(root/'runs'/(args.token+'_r'+str(i))/'SANDBOX.json'),
                receipt=load(root/'runs'/(args.token+'_r'+str(i))/'SANDBOX.json')
                if (root/'runs'/(args.token+'_r'+str(i))/'SANDBOX.json').exists() else None) for i in (1, 2)]))
    if args.command == 'proof':
        passed = comparison['passed'] if repeat == 2 else load(outputs[0]/'PROOF.json')['passed']
        if not passed: raise RuntimeError('Token proof differs; inspect '+str(parent/'PROOF.json'))


def _launch_one(args):
    root = writable(args.root); config = require_stage(root)
    pattern = yield_pattern(getattr(args, 'yield_glob', None))
    shm = shm_directory(root, getattr(args, 'shm', None))
    bwrap = getattr(args, 'bwrap', DEFAULT_BWRAP)
    llguidance_stub = getattr(args, 'llguidance_stub', True)
    overlay = llguidance_evidence(llguidance_stub)
    if not re.fullmatch('[a-z][0-9a-f]{8,32}', args.token): raise ValueError('Token must be a letter followed by 8–32 lowercase hex digits')
    # Preflight selection and missing frames before checking or using any GPU.
    result = cpu_need(root, 'main' if args.command == 'proof' else args.family,
                      read_ids(args.ids) if args.command == 'read' and args.ids else None,
                      20 if args.command == 'proof' else args.first, shm, bwrap, llguidance_stub)
    missing = sorted(set(result['need'])-set(store_index(root)))
    if missing:
        print('NEED\n'+'\n'.join(missing))
        raise ValueError('Missing frames; no GPU launched')
    if args.command == 'proof':
        accepted = load(package(root, config)/'parity/DEV20.json')
        if result['ids'] != accepted['ids'] or set(result['need']) != set(accepted['need']):
            raise ValueError('Proof selection differs from accepted DEV20')
        out = root/'runs'/getattr(args, 'run_name', args.token)
    else:
        out = writable(args.out)
        config['spec']['artifact'] = dict(kind='c1_export', path=logical_artifact(root, args.artifact, args.step), sha256=args.sha256)
        if not re.fullmatch('[0-9a-f]{64}', args.sha256): raise ValueError('Require full export SHA256')
        config['spec']['models']['cp1m200'] = config['spec']['artifact'].copy()
        config['spec']['step'] = args.step
    reserve = read_space(root, config, result)
    out = writable(out)
    if not inside(out, root): raise ValueError('Runtime output must be under --root')
    if out.exists(): raise ValueError('Run output exists; no automatic retry')
    tokens = root/'tokens'; tokens.mkdir(exist_ok=True)
    with (tokens/getattr(args, 'run_name', args.token)).open('x') as f: f.write(str(out)+'\n')
    out.mkdir(parents=True)
    dump(out/'SPACE.json', dict(reserved_estimate_bytes=reserve, free_bytes=shutil.disk_usage(root).free,
                              minimum_remaining_bytes=kit_stage().MIN_FREE))
    config['token'] = args.token; config['spec']['run'] = str(out); config['output'] = str(out)
    config['spec']['llguidance_stub'] = overlay
    config['plan_sha256'] = hashlib.sha256(json.dumps(config['spec'], sort_keys=True).encode()).hexdigest()
    dump(out/'CONFIG.json', config)
    dump(out/'SPEC.json', config['spec'])
    if args.command == 'proof':
        script = Path(config['spec']['package'])/'proof/phase_b.py'; extra = []
    else:
        request = dict(action='read', family=args.family, ids=result['ids'], first=None,
                       work=str(out), config=str(out/'CONFIG.json'), attempt=args.token)
        dump(out/'INPUT.json', request)
        script = '/trinity-build/namespace_worker.py'; extra = ['--input', str(out/'INPUT.json')]
    env = environment(root, str(args.gpu), args.token, shm)
    log_path = out/'llg_stub_calls.jsonl'; log_path.touch(exist_ok=False)
    env['LLG_STUB_LOG'] = str(log_path)
    executed = bwrap_evidence(root, bwrap)
    command = ns_command(root, out/'CONFIG.json', script, extra, gpu=True, shm=shm, bwrap=executed['path'], llguidance_stub=llguidance_stub)
    probe_report = None
    try:
        probe_report = probe(root, shm, bwrap, llguidance_stub)
    except Exception as error:
        probe_report = getattr(error, 'probe_report', dict(passed=False, error=str(error)))
        raise
    finally:
        dump(out/'PROBE.json', probe_report)
        dump(out/'SANDBOX.json', sandbox_receipt(command, executed, overlay, probe_report))
    card = check_card(str(args.gpu)); dump(out/'CARD.json', card)
    # vnice expands ${*} through bash: pass one shell-quoted command string.
    command = [VNICE, ' '.join(shlex.quote(s) for s in command)]
    dump(out/'COMMAND.json', dict(argv=command, bwrap=executed, llguidance_stub=overlay))
    dump(out/'ENV.json', env)
    before = host_shm_ours()
    dump(out/'HOST_SHM_BEFORE.json', dict(host_dev_shm_ours=before, time=time.time()))
    sampler = Sampler(str(args.gpu), out/'MEMORY.jsonl'); sampler.thread.start()
    started = time.monotonic(); code = None; yielded = None
    try:
        with (out/'run.log').open('xb') as log:
            code, yielded = run_reader(command, env, root, log, pattern)
    finally:
        sampler.stop.set(); sampler.thread.join(timeout=35)
        usage = stub_usage(log_path, llguidance_stub)
        dump(out/'LLGUIDANCE.json', dict(llguidance_stub=overlay, usage=usage))
        # Phase B's packet is nested; read packets use the run directory itself.
        packet = out/'b0/d0' if args.command == 'proof' else out
        packet.mkdir(parents=True, exist_ok=True)
        for name in ('SANDBOX.json', 'LLGUIDANCE.json'):
            if packet != out: dump(packet/name, load(out/name))
        dump(out/'EXIT.json', dict(returncode=code, wall_seconds=time.monotonic()-started, sampler_errors=sampler.errors, bwrap=executed, llguidance_stub=overlay, stub_usage=usage,
                                  host_dev_shm_ours_before=before, host_dev_shm_ours=host_shm_ours(), yielded=bool(yielded)))
        try:
            if args.command == 'proof':
                sys.path.insert(0, str(BUILD))
                import compare_tokens
                report = compare_tokens.write_report(package(root, config)/'parity/DEV20.json', out/'b0/d0', 'b0', out,
                                                      out/'MEMORY.jsonl', out/'EXIT.json')
            else:
                report = None
        finally:
            if yielded:
                models = out/'b0/d0/models' if args.command == 'proof' else out/'direct'/args.family/'models'
                yielded.update(run_directory=str(out), files=disk_listing(out), model_directory=str(models),
                               model_copies=disk_listing(models), inventory_note='Metadata snapshot before YIELD.json; no cleanup.')
                dump(out/'YIELD.json', yielded)
    if code or sampler.errors: raise RuntimeError('Run or memory sampler failed; inspect '+str(out)+'; do not retry automatically')
    if report is None and not usage['passed']: raise RuntimeError('llguidance audit failed: '+'; '.join(usage['errors']))
    print(json.dumps(dict(output=str(out), returncode=code)))


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command'); sub.required = True
    for name in ('stage', 'frames', 'need', 'proof', 'read', 'selfcheck', 'probe'):
        q = sub.add_parser(name); q.add_argument('--root', default=str(DEFAULT_ROOT))
        if name in ('proof', 'read', 'need', 'selfcheck', 'probe'):
            q.add_argument('--bwrap', default=DEFAULT_BWRAP, help='Host bubblewrap executable (default: /usr/bin/bwrap); never the pinned Orchard binary')
        if name in ('proof', 'read', 'need', 'probe'):
            overlay = q.add_mutually_exclusive_group()
            overlay.add_argument('--llguidance-stub', dest='llguidance_stub', action='store_true', default=True,
                                 help='Bind the pinned import-only llguidance stub (default: on)')
            overlay.add_argument('--no-llguidance-stub', dest='llguidance_stub', action='store_false')
        if name == 'proof': q.add_argument('--repeat', type=int, choices=(1, 2), default=1)
        if name == 'stage': q.add_argument('--dl', default=str(AREA/'dl'))
        if name == 'frames': q.add_argument('--tar', action='append', required=True)
        if name in ('need', 'read'):
            q.add_argument('--family', choices=FAMILIES, required=name == 'read')
            selection = q.add_mutually_exclusive_group(required=True)
            selection.add_argument('--ids'); selection.add_argument('--first', type=int)
            if name == 'need': selection.add_argument('--all', action='store_true')
            q.add_argument('--out', required=True)
        if name in ('proof', 'read'):
            q.add_argument('--gpu', required=True); q.add_argument('--token', required=True)
            q.add_argument('--yield-glob', help='Local nonrecursive file glob; poll every 30 seconds')
        if name in ('proof', 'read', 'probe'):
            q.add_argument('--shm', help='Private /dev/shm backing directory (default: ROOT/shm)')
        if name == 'read':
            q.add_argument('--artifact', required=True); q.add_argument('--sha256', required=True); q.add_argument('--step', type=int, required=True)
    args = p.parse_args()
    if args.command == 'need' and not args.all and not args.family: p.error('need requires --family unless --all')
    if args.command == 'need' and args.all and args.family: p.error('--all spans all three families; omit --family')
    if args.command == 'stage': print(json.dumps(stage(args.root, args.dl), sort_keys=True))
    elif args.command == 'frames': print(json.dumps(frames(args.root, args.tar), sort_keys=True))
    elif args.command == 'need': need_command(args)
    elif args.command == 'probe':
        print(json.dumps(probe(args.root, args.shm, args.bwrap, args.llguidance_stub), sort_keys=True, indent=2))
    elif args.command == 'selfcheck':
        result = selfcheck(args.root, args.bwrap); print(json.dumps(result, sort_keys=True, indent=2))
        if not result['passed']: raise RuntimeError('Selfcheck incomplete or failed; inspect the JSON report')
    else: launch(args)


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print('REFUSED: '+str(error), file=sys.stderr); sys.exit(2)
