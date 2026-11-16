"""Parent-only AWS extraction; preserve stale kit files outside b/ and k/."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import time


def stream_sha(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1 << 20), b''):
        digest.update(block)
    return digest.hexdigest()


def deploy(archive, expected_sha256, root):
    archive, root = Path(archive), Path(root).resolve()
    with archive.open('rb') as stream:
        if stream_sha(stream) != expected_sha256:
            raise ValueError('Archive digest differs')
    with tarfile.open(archive) as tf:
        members = tf.getmembers()
        names = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != member.name or member.name in names
                    or (path.parts[0] not in ('b', 'k', 'f')
                        and member.name not in ('ANON_OK.json', 'SHA256SUMS.txt'))):
                raise ValueError('Unexpected deployment member')
            dest = root/member.name
            if not dest.resolve().is_relative_to(root) or dest.is_symlink():
                raise ValueError('Unsafe deployment destination')
            names.add(member.name)
        cert = json.load(tf.extractfile('ANON_OK.json'))
        sums = tf.extractfile('SHA256SUMS.txt').read()
        if cert.get('status') != 'CLEAN' or cert.get('hits') != 0 or hashlib.sha256(sums).hexdigest() != cert['manifest_sha256']:
            raise ValueError('Invalid content seal')
        expected = {}
        for line in sums.decode().splitlines():
            digest, name = line.split('  ', 1)
            if name in expected:
                raise ValueError('Repeated manifest member')
            expected[name] = digest
        if names != set(expected) | {'ANON_OK.json', 'SHA256SUMS.txt'}:
            raise ValueError('Archive inventory differs')
        for name, digest in expected.items():
            if stream_sha(tf.extractfile(name)) != digest:
                raise ValueError('Archive member digest differs')
        current = json.load(tf.extractfile('k/0.json'))
        active = 'k/'+Path(current['trainer']['file']).name
        trainers = {n for n in names if n.startswith('k/t_') and n.endswith('.tar')}
        if trainers != {active} or 'k/t.tar' in names:
            raise ValueError('Expected only the current trainer archive')
        retained = root/'.retained'/str(time.time_ns())
        stale = [p for directory in ('b', 'k') for p in (root/directory).rglob('*')
                 if p.is_file() and str(p.relative_to(root)) not in names]
        for path in stale:
            dest = retained/path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            path.rename(dest)
        for member in members:
            dest = root/member.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tf.extractfile(member) as src, dest.open('wb') as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            dest.chmod(member.mode & 0o777)
    (root/'o').mkdir(exist_ok=True)
    return {'files': len(names), 'retained_files': len(stale)}


if __name__ == '__main__':
    print(json.dumps(deploy(*sys.argv[1:])))
