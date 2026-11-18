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
    expected, allowed_counts = inventory(entry)
    destination.mkdir(mode=0o700)  # Fresh owned directory; no existing targets.
    seen, metadata = {}, set()
    with open_regular(entry['source']) as source:
        authenticate(source, entry)
        source.seek(0)
        with tarfile.open(fileobj=source, mode='r:*') as tf:
            for member in tf:
                # Tar commonly prefixes names with './'; do not normalize '..'.
                name = member.name
                if name.startswith('./'):
                    name = name[2:]
                if member.isdir():
                    if name in ('', '.'):
                        continue
                    parent = relative(name.rstrip('/'))
                    if not any(parent in PurePosixPath(n).parents for n in expected):
                        raise ValueError('Extra archive directory')
                    continue
                relative(name)
                if not member.isfile() or member.issparse():
                    raise ValueError('Nonregular archive member')
                if name == 'SHA256SUMS' and name not in expected:
                    # Production Stage.archive skips this tar metadata. Check it
                    # against the pinned inventory and never extract it.
                    if name in metadata or member.size > 65536:
                        raise ValueError('Archive metadata differs')
                    rows = {}
                    for line in tf.extractfile(member).read().decode('ascii').splitlines():
                        match = re.fullmatch(r'([0-9a-f]{64}) [ *](.+)', line)
                        if not match or match[2] in rows:
                            raise ValueError('Archive metadata differs')
                        rows[match[2]] = match[1]
                    if rows != {n: v['sha256'] for n, v in expected.items()}:
                        raise ValueError('Archive metadata differs')
                    metadata.add(name)
                    continue
                if name not in expected or member.size != expected[name]['bytes']:
                    raise ValueError('Archive member differs from inventory')
                seen[name] = seen.get(name, 0) + 1
                if seen[name] > allowed_counts[name]:
                    raise ValueError('Duplicate archive member')
                target = destination / name
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with tf.extractfile(member) as payload:
                    if seen[name] > 1:
                        authenticate(payload, expected[name])
                        continue
                    h, size = hashlib.sha256(), 0
                    with target.open('xb') as output:
                        for block in iter(lambda: payload.read(1 << 20), b''):
                            output.write(block)
                            h.update(block)
                            size += len(block)
                    if size != expected[name]['bytes'] or h.hexdigest() != expected[name]['sha256']:
                        raise ValueError('Member digest differs')
                target.chmod(0o400)
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


def stage(kit, work, authority):
    with open_regular(kit / 'k/0.json') as f:
        authenticate(f, authority['metadata'])
        f.seek(0)
        config = json.load(f)
    plan = config['staged_inputs']
    if plan['schema'] != 's1-staged-inputs-v1':
        raise ValueError('Unknown staging contract')
    selected, rows = resolve(plan, authority['inputs'])
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
