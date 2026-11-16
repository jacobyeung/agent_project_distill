import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import select
import shutil
import signal
import subprocess
import tarfile
import time

import chain_save as A


MIN_FREE = 200*1024**3
CHUNK = 1024**2
RUNTIME_ABSOLUTE_LINKS = {
    'sj/envs/p1cpu/bin/python3.12':
        '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',
    'm/ap/19252904/e/bin/python':
        '/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12',
}


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            value.update(chunk)
    return value.hexdigest()


def room(path, extra=0):
    if shutil.disk_usage(path).free < MIN_FREE+extra:
        raise ValueError('Staging would breach the 200 GiB node-local free-space floor')


def relative(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\x00' in name:
        raise ValueError('Unsafe archive member')
    return path


def extract_stream(stream, destination, step, limit, links=False, strip=0, overlay=False):
    destination = Path(destination).resolve()
    seen, inventory, total = set(), {}, 0
    with tarfile.open(fileobj=stream, mode='r|*') as archive:
        for item in archive:
            path = relative(item.name)
            if len(path.parts) <= strip:
                if not item.isdir():
                    raise ValueError('Archive strip would discard a file')
                continue
            path = PurePosixPath(*path.parts[strip:])
            if step is not None and path.parts[0] != 'm'+str(step):
                raise ValueError('Export contains a foreign milestone')
            if str(path) in seen:
                raise ValueError('Duplicate archive member')
            seen.add(str(path))
            if len(seen) > 200000 or item.size < 0:
                raise ValueError('Invalid archive inventory')
            total += item.size
            if total > limit:
                raise ValueError('Archive exceeds its expanded byte allowance')
            target = destination/str(path)
            parent = target.parent.resolve()
            if not parent.is_relative_to(destination) or target.is_symlink():
                raise ValueError(f'Archive member escapes its local destination: {path} -> {item.linkname}')
            if item.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.issym() and links:
                link = PurePosixPath(item.linkname)
                if link.is_absolute():
                    if RUNTIME_ABSOLUTE_LINKS.get(str(path)) != item.linkname:
                        raise ValueError(f'Runtime symlink has an unregistered absolute target: {path} -> {item.linkname}')
                else:
                    first_name = next((i for i, part in enumerate(link.parts) if part != '..'), len(link.parts))
                    if '..' in link.parts[first_name:]:
                        raise ValueError(f'Runtime symlink has ambiguous parent traversal: {path} -> {item.linkname}')
                    if not Path(os.path.normpath(str(parent/str(link)))).is_relative_to(destination):
                        raise ValueError(f'Runtime symlink escapes its archive: {path} -> {item.linkname}')
                target.symlink_to(item.linkname)
                continue
            if item.islnk() and links:
                source = destination/str(relative(item.linkname))
                if not source.resolve().is_relative_to(destination) or source.is_symlink() or not source.is_file():
                    raise ValueError(f'Unsafe runtime hard link: {path} -> {item.linkname}')
                os.link(source, target)
                continue
            if not item.isfile():
                raise ValueError('Archive links and special files are not admitted')
            if overlay and target.exists():
                if not target.is_file():
                    raise ValueError('A code overlay may only replace a local regular file')
                target.chmod(item.mode | 0o200)
            hashed = hashlib.sha256()
            with archive.extractfile(item) as source, target.open('wb' if overlay else 'xb') as output:
                copied = 0
                for chunk in iter(lambda: source.read(CHUNK), b''):
                    copied += len(chunk)
                    hashed.update(chunk)
                    if output.write(chunk) != len(chunk):
                        raise OSError('Short staging write')
            if copied != item.size:
                raise ValueError('Truncated archive member')
            target.chmod(item.mode & 0o777)
            inventory[str(path)] = dict(bytes=copied, sha256=hashed.hexdigest())
    return inventory


def copy_parts(parts, destination, opener, expected_sha=None, rate=0, check_space=True):
    destination = Path(destination)
    partial = destination.with_name(destination.name+'.partial')
    size = sum(part['bytes'] for part in parts)
    if destination.exists() or partial.exists():
        raise FileExistsError('A staging destination already exists')
    if check_space:
        room(destination.parent, size)
    whole = hashlib.sha256()
    started, count = time.monotonic(), 0
    with partial.open('xb') as output:
        for part in parts:
            hashed, md5, copied = hashlib.sha256(), hashlib.md5(), 0
            with opener(part) as source:
                for chunk in iter(lambda: source.read(CHUNK), b''):
                    copied += len(chunk)
                    count += len(chunk)
                    if copied > part['bytes']:
                        raise ValueError('Part exceeds its authenticated size')
                    hashed.update(chunk)
                    md5.update(chunk)
                    whole.update(chunk)
                    if output.write(chunk) != len(chunk):
                        raise OSError('Short staging write')
                    if rate:
                        time.sleep(max(0, count/rate-(time.monotonic()-started)))
            if copied != part['bytes'] or hashed.hexdigest() != part['sha256']:
                raise ValueError('Part size or SHA256 differs')
            if part.get('md5') and base64.b64encode(md5.digest()).decode() != part['md5']:
                raise ValueError('Part MD5 differs')
        output.flush()
        os.fsync(output.fileno())
    if expected_sha is not None and whole.hexdigest() != expected_sha:
        raise ValueError('The complete archive SHA256 differs')
    os.replace(partial, destination)
    return dict(bytes=count, sha256=whole.hexdigest(), seconds=time.monotonic()-started)


class ProcessStream:
    def __init__(self, process):
        self.process = process

    def read(self, size):
        if not select.select([self.process.stdout], [], [], 300)[0]:
            raise RuntimeError('Staging stream made no progress for 300 seconds')
        return os.read(self.process.stdout.fileno(), size)


@contextmanager
def process_stream(argv, environment, log):
    with Path(log).open('ab') as output:
        process = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE, stderr=output,
                                   start_new_session=True)
        try:
            yield ProcessStream(process)
            if process.wait(timeout=60):
                raise RuntimeError('Staging command failed; no automatic retry')
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=20)
            process.stdout.close()


def unpack(path, root, **kwargs):
    with Path(path).open('rb') as stream:
        return extract_stream(stream, root, None, Path(path).stat().st_size, **kwargs)


def cloud_environment(path):
    return dict(os.environ, CLOUDSDK_CONFIG=path,
                CLOUDSDK_CORE_DISABLE_FILE_LOGGING='1', CLOUDSDK_CORE_DISABLE_PROMPTS='1',
                CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK='1',
                CLOUDSDK_CORE_DISABLE_USAGE_REPORTING='1')


def config_metadata(path):
    result = {}
    with os.scandir(path) as entries:
        for entry in entries:
            if len(result) >= 256:
                raise ValueError('Cloud config metadata inventory exceeds its bound')
            value = entry.stat(follow_symlinks=False)
            result[entry.name] = dict(bytes=value.st_size, mtime_ns=value.st_mtime_ns,
                                      directory=entry.is_dir(follow_symlinks=False))
    return result


def stage(root, config, physical):
    root = Path(root)
    assets = config['assets']
    receipts = {}
    last_phase = time.monotonic()

    def phase(name):
        nonlocal last_phase
        now = time.monotonic()
        receipts.setdefault('phases', {})[name] = dict(
            completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            seconds=now-last_phase, local_free_bytes=shutil.disk_usage(root).free)
        last_phase = now
        A.atomic_json(root/'STAGING.json', receipts)

    phase('start')
    archives = root/'archives'
    archives.mkdir()
    for index, group in enumerate(assets['groups']):
        parts = [dict(path=p, bytes=n, sha256=h) for p, n, h in group]
        archive = archives/f'runtime_{index}.tar'
        receipts['runtime_'+str(index)] = copy_parts(
            parts, archive, lambda part: Path(part['path']).open('rb'),
            rate=0)
        unpack(archive, root, links=True)
        phase('runtime_'+str(index))
    camera = assets['camera_archive']
    archive = archives/'a0.tar'
    receipts['camera'] = copy_parts([camera], archive, lambda part: Path(part['path']).open('rb'))
    unpack(archive, root)
    phase('a0')
    payload = root/'bootstrap/payload.tar.gz'
    if sha(payload) != config['payload_sha256']:
        raise ValueError('Reader payload differs from the submitted package')
    with payload.open('rb') as stream:
        extract_stream(stream, root, None, 32*1024**2, overlay=True)
    phase('reader_payload')
    bwrap = assets['bwrap_pin']
    target = root/'bwrap'
    receipts['bwrap'] = copy_parts([bwrap], target, lambda part: Path(part['path']).open('rb'))
    target.chmod(0o700)
    phase('bwrap')
    base = root/'m/ap/85fc3486'
    base.mkdir(parents=True)
    source = Path(assets['base_archive'])
    if source.stat().st_size != assets['base_archive_bytes']:
        raise ValueError('Base archive size differs')
    room(root, source.stat().st_size)
    inventory = unpack(source, base, strip=3)
    manifest = physical(root, assets['base_manifest']['path'])
    if sha(manifest) != assets['base_manifest']['sha256']:
        raise ValueError('Base snapshot manifest differs')
    for row in json.loads(manifest.read_text())['files']:
        if inventory.get(row['path']) != {key: row[key] for key in ('bytes', 'sha256')}:
            raise ValueError('Base snapshot payload differs from its frozen manifest')
    receipts['base'] = dict(manifest_sha256=sha(manifest), files=len(inventory))
    phase('base_snapshot')
    transport = json.loads(physical(root, config['release']['transport']['path']).read_text())
    receipts['export_transport'] = transport
    environment = cloud_environment(assets['gcloud_config'])

    def cloud(part):
        uri = 'gs://cmu-gpucloud-jjyeung/'+part['name']+'#'+str(part['generation'])
        return process_stream(['gcloud', 'storage', 'cat', uri], environment, root/'staging.log')

    archive = archives/'export.tar'
    before = config_metadata(assets['gcloud_config'])
    try:
        receipts['export'] = copy_parts(transport['parts'], archive, cloud,
                                        expected_sha=transport['archive_sha256'])
    finally:
        after = config_metadata(assets['gcloud_config'])
        receipts['gcloud_config_observation'] = dict(
            before=before, after=after, shared_config=True, attribution_exclusive=False,
            changed=[name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)])
        phase('export_fetch')
    if receipts['export']['bytes'] != transport['archive_bytes']:
        raise ValueError('Export byte count differs')
    destination = physical(root, config['spec']['artifact']['path']).parent.parent
    destination.mkdir(parents=True)
    room(root, archive.stat().st_size)
    with archive.open('rb') as stream:
        extract_stream(stream, destination, config['spec']['step'], archive.stat().st_size)
    if sha(physical(root, config['spec']['artifact']['path'])) != config['spec']['artifact']['sha256']:
        raise ValueError('Downloaded production artifact differs')
    phase('export_extract')
    receipts['videos'] = stage_videos(root, config, physical)
    phase('videos')
    room(root)
    return receipts


def stage_videos(root, config, physical):
    root=Path(root)
    package=physical(root,config['spec']['package'])
    rows=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
    destination=root/'v'
    destination.mkdir()
    verified=[]
    for row in rows:
        source=Path(row['alias_path'])
        if not any(source.is_relative_to(Path('/project/community/jjyeung')/a) for a in ('3e0e8a36','8b677689')):
            raise ValueError('Unregistered video alias')
        source=video_source(row)
        target=destination/(row['sha256']+'.mp4')
        copied=copy_parts([dict(path=str(source),bytes=source.stat().st_size,sha256=row['sha256'])],target,
                   lambda part:Path(part['path']).open('rb'))
        verified.append(dict(relative_path=row['relative_path'],alias_path=str(source),**copied))
    question=question_source()
    target=physical(root,config['spec']['inputs']['rows']);target.parent.mkdir(parents=True,exist_ok=True)
    copy_parts([dict(bytes=question.stat().st_size,sha256='d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc')],
               target,lambda part:question.open('rb'))
    return dict(videos=len(rows),verified=True,files=verified)


def video_source(row):
    return Path(row["alias_path"])


def question_source():
    return Path("/project/community/jjyeung/cp4tk_eval/official/meta_5130.jsonl")
