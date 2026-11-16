"""Shared helpers for every kit: hashing, canonical JSON, atomic writes, process identity, locked appends.

Standard library only and Python 3.6-safe, because job-side code runs under the batch host's system
Python. Kits import these helpers instead of defining their own. One owner (the core package build)
changes this file; every other build uses it unchanged.

Nothing here removes a file. A write that fails leaves its temporary file beside the target, named
<target>.tmp.<pid>.<microseconds>, as evidence for whoever inspects the failure.
"""
import errno
import fcntl
import hashlib
import json
import os
import time

CHUNK = 1 << 20


def sha256_bytes(data):
    """Hex sha256 of a bytes object."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path, chunk=CHUNK):
    """Return (hex sha256, byte count) of a file, read in bounded chunks."""
    digest = hashlib.sha256()
    count = 0
    with open(str(path), 'rb') as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
            count += len(block)
    return digest.hexdigest(), count


def canonical_json(obj):
    """Canonical UTF-8 bytes of a JSON value: sorted keys, no spaces, no trailing newline.

    NaN and infinity are refused, so two hosts cannot serialize one value two ways.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def canonical_sha256(obj):
    """Identity of a JSON value: sha256 of its canonical bytes."""
    return sha256_bytes(canonical_json(obj))


def atomic_write(path, data):
    """Write bytes to path through a same-directory temporary file, fsync, then rename.

    The rename replaces the target in one step, so a reader sees the old bytes or the new bytes and
    never a partial file.
    """
    path = str(path)
    tmp = '%s.tmp.%d.%d' % (path, os.getpid(), int(time.time() * 1e6))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.rename(tmp, path)


def write_json(path, obj):
    """Atomically write a JSON value in canonical form plus one trailing newline."""
    atomic_write(path, canonical_json(obj) + b'\n')


def read_json(path):
    with open(str(path), 'rb') as handle:
        return json.loads(handle.read().decode('utf-8'))


def utc_stamp(now=None):
    """Compact UTC stamp, for example 20261116T112200Z."""
    return time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))


def utc_iso(now=None):
    """ISO UTC stamp, for example 2026-11-16T11:22:00Z."""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))


def proc_identity(pid):
    """Identity of a live process from /proc/<pid>/stat, or None when it has gone.

    Returns {'pid', 'comm', 'state', 'starttime'}. comm may hold spaces or parentheses, so the
    fields are split at the last ')'.
    """
    try:
        with open('/proc/%d/stat' % int(pid), 'rb') as handle:
            raw = handle.read().decode('utf-8', 'replace')
    except (IOError, OSError) as err:
        if err.errno in (errno.ENOENT, errno.ESRCH):
            return None
        raise
    head, _, tail = raw.rpartition(')')
    fields = tail.split()
    return {'pid': int(pid), 'comm': head.split('(', 1)[1], 'state': fields[0],
            'starttime': int(fields[19])}


def append_jsonl_locked(path, row, max_bytes=1024):
    """Append one canonical JSON line under an exclusive flock; refuse a line above max_bytes.

    The lock is taken on the target itself, so every writer on every host that mounts it serializes.
    """
    line = canonical_json(row) + b'\n'
    if len(line) > max_bytes:
        raise ValueError('row is %d bytes; limit %d' % (len(line), max_bytes))
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, line)
        os.fsync(fd)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    return len(line)
