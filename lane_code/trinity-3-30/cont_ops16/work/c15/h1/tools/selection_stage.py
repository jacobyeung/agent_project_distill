"""Authenticate selection inputs and stage only their required pinned packages."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile


def relative(name):
    p = PurePosixPath(name)
    if (not isinstance(name, str) or not p.parts or p.is_absolute()
            or '..' in p.parts or str(p) != name or '\\' in name
            or any(ord(c) < 32 for c in name)):
        raise ValueError('Unsafe input path')
    return p


def pin(value):
    if (type(value['bytes']) is not int or value['bytes'] < 0
            or not re.fullmatch('[0-9a-f]{64}', value['sha256'])):
        raise ValueError('Invalid input pin')


def authenticate(stream, value):
    pin(value)
    h, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1 << 20), b''):
        h.update(block)
        size += len(block)
    if size != value['bytes'] or h.hexdigest() != value['sha256']:
        raise ValueError('Input bytes or digest differ')


def open_regular(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError('Input is not a regular file')
    return os.fdopen(fd, 'rb')


def inventory(entry):
    result, counts = {}, {}
    for value in entry['inventory']:
        name = str(relative(value['name']))
        pin(value)
        if name in result and result[name] != value:
            raise ValueError('Conflicting inventory member')
        result[name] = value
        counts[name] = counts.get(name, 0) + 1
    if not result or entry['members'] != len(result):
        raise ValueError('Inventory count differs')
    return result, counts


def archive(entry, destination):
    """Verify the complete archive first; never delegate extraction to tarfile."""
    expected, _ = inventory(entry)
    destination.mkdir(mode=0o700)  # Fresh owned directory; no existing targets.
    seen, metadata = set(), {}
    with open_regular(entry['source']) as source:
        authenticate(source, entry)
        source.seek(0)
        with tarfile.open(fileobj=source, mode='r:*') as tf:
            for member in tf:
                # Match Stage.archive's POSIX normalization; retain '..' so the
                # path check refuses traversal before skipping any directory.
                name = str(PurePosixPath(member.name))
                if member.isdir():
                    if name == '.':
                        continue
                    relative(name)
                    continue
                path = relative(name)
                if not member.isfile() or member.issparse():
                    raise ValueError('Nonregular archive member')
                prefix = entry.get('member_prefix')
                if prefix and not path.is_relative_to(prefix):
                    raise ValueError('Archive member has the wrong prefix')
                if name == 'SHA256SUMS' and name not in expected:
                    # Production Stage.archive skips this tar metadata. Check it
                    # against the pinned inventory and never extract it.
                    if member.size > 65536:
                        raise ValueError('Archive metadata differs')
                    with tf.extractfile(member) as payload:
                        data = payload.read()
                    digest = hashlib.sha256(data).hexdigest()
                    if name in metadata and metadata[name] != digest:
                        raise ValueError('Conflicting archive metadata')
                    rows = {}
                    for line in data.decode('ascii').splitlines():
                        match = re.fullmatch(r'([0-9a-f]{64}) [ *](.+)', line)
                        if not match or (match[2] in rows and rows[match[2]] != match[1]):
                            raise ValueError('Archive metadata differs')
                        rows[match[2]] = match[1]
                    if rows != {n: v['sha256'] for n, v in expected.items()}:
                        raise ValueError('Archive metadata differs')
                    metadata[name] = digest
                    continue
                if name not in expected or member.size != expected[name]['bytes']:
                    raise ValueError('Archive member differs from inventory')
                with tf.extractfile(member) as payload:
                    # Inventory occurrence counts do not limit tar repeats.
                    # Authenticate every repeat, but publish each name only once.
                    if name in seen:
                        authenticate(payload, expected[name])
                        continue
                    target = destination / name
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    h, size = hashlib.sha256(), 0
                    with target.open('xb') as output:
                        for block in iter(lambda: payload.read(1 << 20), b''):
                            output.write(block)
                            h.update(block)
                            size += len(block)
                    if size != expected[name]['bytes'] or h.hexdigest() != expected[name]['sha256']:
                        raise ValueError('Member digest differs')
                target.chmod(0o400)
                seen.add(name)
        if set(seen) != set(expected):
            raise ValueError('Archive inventory differs')
        # Detect changes during extraction on the same open descriptor.
        source.seek(0)
        authenticate(source, entry)


def resolve(plan, inputs):
    """Match every input to its production destination, never by hash alone."""
    selected, rows = {}, []
    for item in inputs:
        rel = str(relative(item['relative']))
        candidates = []
        for kind in ('packages', 'archives', 'files'):
            for i, entry in enumerate(plan.get(kind, [])):
                dest = str(relative(entry['destination']))
                if kind == 'files':
                    value = entry if rel == dest else None
                elif rel.startswith(dest + '/'):
                    values, _ = inventory(entry)
                    value = values.get(rel[len(dest) + 1:])
                    if value is None:
                        raise ValueError('Input missing from package inventory')
                else:
                    continue
                if value is not None:
                    if any(value[k] != item[k] for k in ('bytes', 'sha256')):
                        raise ValueError('Input and staging pins disagree')
                    candidates.append((kind, i, entry))
        if len(candidates) > 1:
            raise ValueError('Ambiguous staging source')
        if candidates:
            kind, i, entry = candidates[0]
            selected[(kind, i)] = entry
            rows.append(dict(item, source=entry['source'], staging=kind, entry=i))
        elif rel.startswith('k/'):
            rows.append(dict(item, source='kit/' + rel, staging='kit'))
        else:
            raise ValueError('Input has no authenticated staging source')
    return selected, rows


def metadata(kit, authority):
    # Only the sealed production manifest authorizes metadata bytes. Local
    # reconstructions have their own manifests and cannot supply this authority.
    with open_regular(kit / 'SHA256SUMS.txt') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != authority['manifest_sha256']:
        raise ValueError('Kit manifest digest differs')
    sums = {}
    for line in data.decode('ascii').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64}) [ *](.+)', line)
        if not match or match[2] in sums:
            raise ValueError('Invalid kit manifest')
        name = str(relative(match[2]))
        sums[name] = match[1]
    if 'k/0.json' not in sums:
        raise ValueError('Metadata absent from kit manifest')
    with open_regular(kit / 'k/0.json') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != sums['k/0.json']:
        raise ValueError('Metadata digest differs from kit manifest')
    return json.loads(data)


def stage(kit, work, authority):
    config = metadata(kit, authority)
    plan = config['staged_inputs']
    if plan['schema'] != 's1-staged-inputs-v1':
        raise ValueError('Unknown staging contract')
    selected, rows = resolve(plan, authority['inputs'])
    packages = [entry for (kind, _), entry in selected.items() if kind == 'packages']
    # Canonical JSON preserves array order and JSON types (including bool/int).
    canonical = lambda v: json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if canonical(packages) != canonical(authority['packages']):
        raise ValueError('Staged package entry differs from expected contract')
    root = work / 'p'
    root.mkdir(mode=0o700)
    mounts = []
    for (kind, i), entry in selected.items():
        dest = str(relative(entry['destination']))
        target = root / dest
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if kind == 'files':
            with open_regular(entry['source']) as source:
                authenticate(source, entry)
                source.seek(0)
                with target.open('xb') as output:
                    for block in iter(lambda: source.read(1 << 20), b''):
                        output.write(block)
            with target.open('rb') as f:
                authenticate(f, entry)
            target.chmod(0o400)
        else:
            archive(entry, target)
        mounts.append((str(target), dest))
    for row in rows:
        base = kit if row['staging'] == 'kit' else root
        path = base / row['relative']
        if not path.resolve().is_relative_to(base.resolve()):
            raise ValueError('Input escapes its root')
        with open_regular(path) as f:
            authenticate(f, row)
    with (work / 'm').open('xb') as f:
        for source, dest in mounts:
            f.write(source.encode() + b'\0' + dest.encode() + b'\0')
    (work / 's.json').write_text(json.dumps(rows, sort_keys=True, indent=2) + '\n')
