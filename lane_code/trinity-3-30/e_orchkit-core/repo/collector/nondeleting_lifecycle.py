"""Archive retired paths while preserving bytes and existing caller authority."""

from __future__ import annotations

import fcntl
import functools
import os
import secrets
import time
from contextlib import contextmanager
from pathlib import Path


def fsync_dir(path: Path | str) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def retire_path(path: Path | str, *, missing_ok: bool = False) -> Path | None:
    """Move a caller-owned path into a unique, durable sibling archive slot.

    The caller must hold its normal ownership/serialization authority. This
    function never decides whether a lock is stale or a claim may be recovered.
    An error after rename means completion is uncertain; inspect retained state.
    """
    path = Path(path)
    if path.name in {"", ".", "..", ".retired"}:
        raise ValueError(f"refusing ambiguous retirement path: {path}")
    try:
        path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    archive = path.parent / ".retired"
    archive.mkdir(mode=0o700, exist_ok=True)
    if archive.is_symlink() or not archive.is_dir():
        raise RuntimeError(f"archive must be a real directory: {archive}")
    fsync_dir(path.parent)
    while True:
        slot = archive / secrets.token_hex(16)
        try:
            slot.mkdir(mode=0o700)
            break
        except FileExistsError:
            continue
    fsync_dir(archive)
    destination = slot / path.name
    # The exclusive directory reservation guarantees an absent destination.
    try:
        os.rename(path, destination)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    fsync_dir(slot)
    fsync_dir(path.parent)
    return destination


def publish_immutable(path: Path | str, payload: bytes) -> None:
    """Publish once; identical bytes are idempotent, differing bytes refuse."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(16)}.private"
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
                raise FileExistsError(f"immutable publication collision: {path}")
        fsync_dir(path.parent)
    finally:
        retire_path(temporary, missing_ok=True)


@contextmanager
def permanent_lock(path: Path | str, *, timeout_seconds: float = 30.0):
    """Lock a permanent inode; only cooperating successor clients participate."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        os.fsync(fd)
        fsync_dir(path.parent)
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"permanent lock busy: {path}")
                time.sleep(0.01)
        if not os.path.samestat(os.fstat(fd), path.stat(follow_symlinks=False)):
            raise RuntimeError(f"permanent lock inode changed: {path}")
        yield
    finally:
        os.close(fd)


def serialized_work(function):
    """Serialize coord claim, heartbeat and terminal transitions per work id."""
    @functools.wraps(function)
    def wrapped(coord, identity, *args, **kwargs):
        work_id = identity if isinstance(identity, str) else identity.work_id
        if not work_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in work_id):
            raise ValueError("unsafe coordination work id")
        with permanent_lock(Path(coord.root) / ".lifecycle-locks" / f"{work_id}.lock"):
            return function(coord, identity, *args, **kwargs)
    return wrapped


def serialized_merge(function):
    @functools.wraps(function)
    def wrapped(coord, *args, **kwargs):
        with permanent_lock(Path(coord.root) / ".lifecycle-locks" / "MAIN_MERGE.guard"):
            return function(coord, *args, **kwargs)
    return wrapped
