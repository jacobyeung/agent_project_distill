#!/usr/bin/env python3
"""Stage every pinned input of a job, each checked by sha256, under one collision policy per destination.

    python3 -m <package>.stage rehearse --kit KIT [--root ROOT]
    python3 -m <package>.stage run      --kit KIT --root ROOT

KIT holds PINS.json and CONFIG.json. CONFIG.stage is a list of items, applied in order:

    {"logical_path": "<pin entry>",                 one entry, or
     "parts": ["<pin entry>", ...],                 entries whose bytes are joined in this order
     "unpack": "file|tar",                          place the bytes as one file, or extract them as a tar
     "dest": "<path under ROOT>",
     "policy": "new|disjoint|same",
     "members": ["<optional member names, used by the rehearsal when no local bytes exist>"]}

Bytes come from the entry's source: kind file reads KIT/<logical_path>; kind orchard reads the absolute
pool path in uri; kind gcs fetches uri at its generation. Every entry is checked against its bytes
and sha256 before any byte of it is placed.

Policies: new (the destination must not exist and no other item may place anything in it); disjoint
(the destination may exist; no member may collide with an existing path or another item's member);
same (like disjoint, except that a collision with identical bytes is allowed).

The rehearsal lays out the complete logical tree in memory from local bytes, stand-ins or member
lists, and reports every collision before a byte moves; run refuses to start when it finds one.
Python 3.6-safe, standard library only. Nothing here removes a file.
"""
import argparse
import hashlib
import io
import json
import os
import posixpath
import shutil
import stat
import subprocess
import sys
import tarfile
import time

if __package__ in (None, ''):
    import importlib
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))  # noqa: A001
    importlib.import_module(__package__)
from . import util  # noqa: E402

POLICIES = ('new', 'disjoint', 'same')
UNPACK = ('file', 'tar')
FETCH_DIR = '.fetch'
COPY_CHUNK = 1 << 20


class StageError(ValueError):
    pass


# ---------------------------------------------------------------- names

def member_name(name):
    """Normalized relative member name, or StageError for an absolute name or one that climbs out."""
    if not isinstance(name, str) or '\x00' in name:
        raise StageError('unsafe member name %r' % (name,))
    if name.startswith('/'):
        raise StageError('absolute member %r' % name)
    parts = [part for part in name.split('/') if part not in ('', '.')]
    if not parts or '..' in parts:
        raise StageError('unsafe member %r' % name)
    return '/'.join(parts)


def relative_dest(dest):
    try:
        return member_name(dest)
    except StageError:
        raise StageError('dest must be a relative path inside the root: %r' % (dest,))


def link_inside(member, target):
    """True when a symbolic link at member pointing to target stays inside the destination."""
    if not target or target.startswith('/'):
        return False
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(member), target))
    return joined != '..' and not joined.startswith('../') and not joined.startswith('/')


def check_members(items):
    """Validate a tar's TarInfo list: no absolute or climbing name, no escaping link, no duplicate,
    no device or fifo. Returns the normalized names in order."""
    seen = set()
    names = []
    for item in items:
        name = member_name(item.name)
        if name in seen:
            raise StageError('duplicate member %r' % name)
        seen.add(name)
        if item.issym():
            if not link_inside(name, item.linkname):
                raise StageError('link %r leaves the destination (%r)' % (name, item.linkname))
        elif item.islnk():
            if member_name(item.linkname) not in seen:
                raise StageError('hard link %r names no earlier member' % name)
        elif not (item.isfile() or item.isdir()):
            raise StageError('special member %r' % name)
        names.append(name)
    return names


# ---------------------------------------------------------------- sources

class Joined(io.RawIOBase):
    """A read-only stream over several files in order (the parts of one split object)."""

    def __init__(self, paths):
        self.paths = list(paths)
        self.handle = None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.handle is None:
                if not self.paths:
                    return 0
                self.handle = open(self.paths.pop(0), 'rb')
            data = self.handle.read(len(buffer))
            if data:
                buffer[:len(data)] = data
                return len(data)
            self.handle.close()
            self.handle = None


def default_gcs_fetch(uri, generation, target, env=None):
    """Fetch one GCS object at its generation: an https URI by GET, a gs:// URI through gcloud."""
    if uri.startswith(('https://', 'http://')):
        from urllib.request import urlopen
        with urlopen(uri, timeout=600) as reply, open(target, 'xb') as out:
            shutil.copyfileobj(reply, out, COPY_CHUNK)
        return
    if not uri.startswith('gs://'):
        raise StageError('unsupported gcs uri %r' % uri)
    full = dict(os.environ)
    full.update(env or {})
    code = subprocess.call(['gcloud', 'storage', 'cp', '%s#%s' % (uri, generation), target],
                           env=full)
    if code:
        raise StageError('gcs fetch of %s failed with %d' % (uri, code))


class Sources(object):
    """Resolve pin entries to local paths and check each one's bytes and sha256 once."""

    def __init__(self, kit, manifest, root=None, gcs_fetch=None, gcs_env=None):
        self.kit = str(kit)
        self.entries = dict((entry['logical_path'], entry) for entry in manifest['entries'])
        self.root = root
        self.gcs_fetch = gcs_fetch or default_gcs_fetch
        self.gcs_env = gcs_env
        self.checked = {}

    def entry(self, logical):
        if logical not in self.entries:
            raise StageError('%s is not a pin entry' % logical)
        return self.entries[logical]

    def local(self, logical):
        """Local path holding the entry's bytes now, or None (rehearsal never fetches)."""
        entry = self.entry(logical)
        kind = entry['source']['kind']
        if kind == 'file':
            path = os.path.join(self.kit, logical)
        elif kind == 'orchard':
            path = entry['source']['uri']
        else:
            path = os.path.join(self.root, FETCH_DIR, logical) if self.root else None
        return path if path and os.path.isfile(path) else None

    def standin(self, logical):
        entry = self.entry(logical)
        if entry.get('standin'):
            path = os.path.join(self.kit, entry['standin'])
            if os.path.isfile(path):
                return path
        return None

    def fetch(self, logical):
        """Local path of the entry's verified bytes; fetches a gcs entry into ROOT/.fetch first."""
        if logical in self.checked:
            return self.checked[logical]
        entry = self.entry(logical)
        path = self.local(logical)
        if path is None and entry['source']['kind'] == 'gcs':
            path = os.path.join(self.root, FETCH_DIR, logical)
            parent = os.path.dirname(path)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            self.gcs_fetch(entry['source']['uri'], entry['source']['generation'], path,
                           self.gcs_env)
        if path is None or not os.path.isfile(path):
            raise StageError('%s: source bytes are missing (%s %s)' % (
                logical, entry['source']['kind'], entry['source']['uri']))
        digest, count = util.sha256_file(path)
        if count != entry['bytes'] or digest != entry['sha256']:
            raise StageError('%s: sha256 or size differs from its pin (%d bytes found, %d pinned)'
                             % (logical, count, entry['bytes']))
        self.checked[logical] = path
        return path


# ---------------------------------------------------------------- plan

def load_plan(config):
    plan = []
    for index, item in enumerate(config.get('stage') or []):
        if not isinstance(item, dict):
            raise StageError('stage item %d is not an object' % index)
        names = item.get('parts') or ([item['logical_path']] if item.get('logical_path') else [])
        if not names or (item.get('parts') and item.get('logical_path')):
            raise StageError('stage item %d needs logical_path or parts, not both' % index)
        if item.get('unpack') not in UNPACK:
            raise StageError('stage item %d: unpack must be one of %s' % (index, UNPACK))
        if item.get('policy') not in POLICIES:
            raise StageError('stage item %d: policy must be one of %s' % (index, POLICIES))
        plan.append({'index': index, 'label': item.get('logical_path') or names[0] + '+parts',
                     'names': list(names), 'unpack': item['unpack'],
                     'dest': relative_dest(item.get('dest')), 'policy': item['policy'],
                     'members': item.get('members')})
    return plan


def _member_digests(handle_or_path):
    """{name: (kind, sha256 or link target)} of a local tar, after the safety check."""
    if isinstance(handle_or_path, str):
        archive = tarfile.open(handle_or_path, mode='r:*')
    else:
        archive = tarfile.open(fileobj=handle_or_path, mode='r|*')
    out = {}
    with archive:
        infos = []
        for item in archive:
            infos.append(item)
            name = member_name(item.name)
            if item.isfile():
                out[name] = ('file', hashlib.sha256(archive.extractfile(item).read()).hexdigest())
            elif item.isdir():
                out[name] = ('dir', None)
            elif item.issym() or item.islnk():
                out[name] = ('link', item.linkname)
            else:
                out[name] = ('special', None)
        check_members(infos)
    return out


def layout(item, sources):
    """{relative path under ROOT: (kind, digest or None)} that the item will place, or None when the
    rehearsal has no bytes, stand-in or member list for it."""
    paths = [sources.local(name) or sources.standin(name) for name in item['names']]
    if item['unpack'] == 'file':
        digest = None
        if len(item['names']) == 1 and sources.local(item['names'][0]):
            digest = sources.entry(item['names'][0])['sha256']
        return {item['dest']: ('file', digest)}
    if all(paths):
        handle = paths[0] if len(paths) == 1 else io.BufferedReader(Joined(paths))
        members = _member_digests(handle)
        if not all(sources.local(name) for name in item['names']):
            members = dict((name, (kind, None if kind == 'file' else value))
                           for name, (kind, value) in members.items())
    elif item['members'] is not None:
        members = dict((member_name(name), ('file', None)) for name in item['members'])
    else:
        return None
    return dict((posixpath.join(item['dest'], name), value) for name, value in members.items())


def _parents(path):
    parts = path.split('/')
    return ['/'.join(parts[:index]) for index in range(1, len(parts))]


def rehearse(kit, root=None, config=None, manifest=None, gcs_fetch=None):
    """Report every collision of the stage plan without moving a byte.

    Returns {ok, items, paths, collisions: [{path, items, reason}], unknown: [label], problems}.
    """
    kit = str(kit)
    config = config if config is not None else util.read_json(os.path.join(kit, 'CONFIG.json'))
    manifest = manifest if manifest is not None else util.read_json(os.path.join(kit, 'PINS.json'))
    sources = Sources(kit, manifest, root, gcs_fetch)
    plan = load_plan(config)
    claims = {}
    owners = {}
    collisions = []
    unknown = []
    problems = []

    def collide(path, first, second, reason):
        collisions.append({'path': path, 'items': [first['label'], second['label']],
                           'reason': reason})

    for item in plan:
        for name in item['names']:
            try:
                sources.entry(name)
            except StageError as err:
                problems.append(str(err))
        dest = item['dest']
        for path, owner in sorted(owners.items()):
            if owner is item:
                continue
            if path == dest or dest.startswith(path + '/') or path.startswith(dest + '/'):
                collide(dest, owner, item, 'destination of a "new" item is shared')
        if item['policy'] == 'new':
            if root and os.path.lexists(os.path.join(str(root), dest)):
                collisions.append({'path': dest, 'items': [item['label']],
                                   'reason': 'destination exists on disk (policy new)'})
            for path, (first, _) in sorted(claims.items()):
                if path == dest or path.startswith(dest + '/'):
                    if claims[path][1][0] != 'dir' or path != dest:
                        collide(dest, first, item, 'destination of a "new" item is shared')
            owners[dest] = item
        try:
            placed = layout(item, sources)
        except (StageError, tarfile.TarError, OSError) as err:
            problems.append('%s: %s' % (item['label'], err))
            continue
        if placed is None:
            unknown.append(item['label'])
            placed = {dest: ('dir' if item['unpack'] == 'tar' else 'file', None)}
        for path, value in sorted(placed.items()):
            for parent in _parents(path):
                held = claims.get(parent)
                if held and held[1][0] not in ('dir',):
                    collide(parent, held[0], item, 'a file and a directory share a path')
                claims.setdefault(parent, (item, ('dir', None)))
            held = claims.get(path)
            if held is not None:
                first, old = held
                if old[0] == 'dir' and value[0] == 'dir':
                    continue
                if first is item:
                    continue
                if item['policy'] == 'same' and old == value and old[1] is not None:
                    continue
                reason = ('identical bytes unproven (no local bytes)' if item['policy'] == 'same'
                          and (old[1] is None or value[1] is None) else 'member collides')
                collide(path, first, item, reason)
                continue
            if root and value[0] != 'dir' and os.path.lexists(os.path.join(str(root), path)):
                existing = os.path.join(str(root), path)
                same = (item['policy'] == 'same' and value[0] == 'file' and value[1] is not None
                        and os.path.isfile(existing) and util.sha256_file(existing)[0] == value[1])
                if not same:
                    collisions.append({'path': path, 'items': [item['label']],
                                       'reason': 'member exists on disk (policy %s)' % item['policy']})
            claims[path] = (item, value)
    return {'ok': not collisions and not problems, 'items': len(plan), 'paths': len(claims),
            'collisions': collisions, 'unknown': unknown, 'problems': problems}


# ---------------------------------------------------------------- placement

def _inside(root, path):
    real_root = os.path.realpath(root)
    real = os.path.realpath(path)
    return real == real_root or real.startswith(real_root + os.sep)


def _write_file(source, target, policy, mode=0o644, digest=None):
    """Write the bytes of an open stream to target under the policy. Returns 'written' or 'same'."""
    if os.path.lexists(target):
        if policy != 'same' or os.path.islink(target) or not os.path.isfile(target):
            raise StageError('%s exists (policy %s)' % (target, policy))
        data = source.read()
        if util.sha256_file(target)[0] != hashlib.sha256(data).hexdigest():
            raise StageError('%s exists with different bytes (policy same)' % target)
        return 'same'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode & 0o755 | 0o600)
    with os.fdopen(fd, 'wb') as out:
        shutil.copyfileobj(source, out, COPY_CHUNK)
        out.flush()
        os.fsync(out.fileno())
    return 'written'


def _makedirs(root, path):
    if os.path.lexists(path) and not (os.path.isdir(path) and not os.path.islink(path)):
        raise StageError('%s exists and is not a directory' % path)
    if not os.path.isdir(path):
        os.makedirs(path)
    if not _inside(root, path):
        raise StageError('%s resolves outside the root' % path)


def safe_extract(opener, dest, policy, root=None):
    """Extract a tar into dest under the policy. opener() returns a fresh binary stream; it is read
    twice: once to check every member, once to extract. Returns the member count."""
    root = root or dest
    with opener() as handle, tarfile.open(fileobj=handle, mode='r|*') as archive:
        check_members(list(archive))
    if policy == 'new' and os.path.lexists(dest):
        raise StageError('%s exists (policy new)' % dest)
    _makedirs(root, dest)
    count = 0
    with opener() as handle, tarfile.open(fileobj=handle, mode='r|*') as archive:
        for item in archive:
            name = member_name(item.name)
            target = os.path.join(dest, name)
            _makedirs(root, os.path.dirname(target))
            if item.isdir():
                _makedirs(root, target)
            elif item.issym():
                if os.path.lexists(target):
                    if policy != 'same' or not os.path.islink(target) or \
                            os.readlink(target) != item.linkname:
                        raise StageError('%s exists (policy %s)' % (target, policy))
                else:
                    os.symlink(item.linkname, target)
            elif item.islnk():
                source_path = os.path.join(dest, member_name(item.linkname))
                with open(source_path, 'rb') as source:
                    _write_file(source, target, policy, item.mode)
            else:
                _write_file(archive.extractfile(item), target, policy, item.mode)
            count += 1
    return count


def place(item, sources, root):
    """Verify every entry of one item, then place its bytes under root."""
    paths = [sources.fetch(name) for name in item['names']]
    dest = os.path.join(root, item['dest'])

    def opener():
        if len(paths) == 1:
            return open(paths[0], 'rb')
        return io.BufferedReader(Joined(paths))

    if item['unpack'] == 'file':
        _makedirs(root, os.path.dirname(dest))
        if item['policy'] == 'new' and os.path.lexists(dest):
            raise StageError('%s exists (policy new)' % dest)
        with opener() as source:
            mode = os.stat(paths[0]).st_mode
            _write_file(source, dest, item['policy'], stat.S_IMODE(mode))
        return 1
    return safe_extract(opener, dest, item['policy'], root)


def run(kit, root, config=None, manifest=None, gcs_fetch=None, gcs_env=None, log=None):
    """Rehearse, then stage every item. Returns the stage receipt; raises StageError on any fault."""
    kit, root = str(kit), str(root)
    config = config if config is not None else util.read_json(os.path.join(kit, 'CONFIG.json'))
    manifest = manifest if manifest is not None else util.read_json(os.path.join(kit, 'PINS.json'))
    report = rehearse(kit, root, config, manifest)
    if not report['ok']:
        raise StageError('rehearsal found %d collisions and %d problems: %s' % (
            len(report['collisions']), len(report['problems']),
            json.dumps(report['collisions'] + report['problems'], sort_keys=True)[:4000]))
    if not os.path.isdir(root):
        os.makedirs(root)
    sources = Sources(kit, manifest, root, gcs_fetch, gcs_env)
    rows = []
    for item in load_plan(config):
        started = time.time()
        count = place(item, sources, root)
        rows.append({'item': item['label'], 'dest': item['dest'], 'policy': item['policy'],
                     'members': count, 'seconds': round(time.time() - started, 3)})
        if log is not None:
            log.write((json.dumps(rows[-1], sort_keys=True) + '\n').encode('utf-8'))
            log.flush()
    return {'schema': 'stage-receipt-v1', 'utc': util.utc_iso(), 'ok': True, 'items': rows,
            'unknown_in_rehearsal': report['unknown']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p_rehearse = sub.add_parser('rehearse')
    p_rehearse.add_argument('--kit', required=True)
    p_rehearse.add_argument('--root')
    p_run = sub.add_parser('run')
    p_run.add_argument('--kit', required=True)
    p_run.add_argument('--root', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'rehearse':
            report = rehearse(args.kit, args.root)
            print(json.dumps(report, sort_keys=True, indent=1))
            return 0 if report['ok'] else 1
        if args.command == 'run':
            print(json.dumps(run(args.kit, args.root), sort_keys=True, indent=1))
            return 0
    except (StageError, OSError, ValueError, tarfile.TarError) as err:
        sys.stderr.write('stage: %s\n' % err)
        return 2
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
