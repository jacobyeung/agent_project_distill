"""Small NFS-safe persistence primitives used by the pool harness."""

from __future__ import annotations

import sys as _lifecycle_sys
from pathlib import Path as _LifecyclePath
_lifecycle_sys.path.insert(0, str(_LifecyclePath(__file__).resolve().parents[1]))
from nondeleting_lifecycle import retire_path, fsync_dir as lifecycle_fsync_dir, publish_immutable

import json
import os
import re
import secrets
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class StateError(RuntimeError):
    """Persistent state is invalid or an atomic state operation failed."""


class AlreadyExists(StateError):
    """An immutable path was already published by another process."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_component(value: str, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise StateError(f"unsafe {label}: {value!r}")
    return value


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_private(directory: Path, stem: str, payload: bytes, mode: int) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    private = directory / (
        f".{stem}.{os.getpid()}.{secrets.token_hex(12)}.private"
    )
    fd = os.open(private, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        view = memoryview(payload)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    return private


def publish_exclusive(path: Path, payload: bytes, mode: int = 0o444) -> Path:
    """Durably create an immutable file with hard-link no-replace semantics."""
    private = _write_private(path.parent, path.name, payload, mode)
    try:
        try:
            os.link(private, path)
            fsync_dir(path.parent)
        except FileExistsError as exc:
            raise AlreadyExists(f"immutable path already exists: {path}") from exc
    finally:
        retire_path(private, missing_ok=True)
    return path


def publish_json_exclusive(path: Path, value: Any, mode: int = 0o444) -> Path:
    return publish_exclusive(path, canonical_bytes(value), mode)


def replace_bytes(path: Path, payload: bytes, mode: int = 0o644) -> Path:
    """Durably replace mutable state; caller supplies any required shared lock."""
    private = _write_private(path.parent, path.name, payload, mode)
    try:
        os.replace(private, path)
        fsync_dir(path.parent)
    finally:
        retire_path(private, missing_ok=True)
    return path


def replace_json(path: Path, value: Any, mode: int = 0o644) -> Path:
    return replace_bytes(path, canonical_bytes(value), mode)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f"cannot read JSON state {path}: {exc}") from exc


@contextmanager
def link_lock(
    lock_dir: Path,
    name: str,
    *,
    timeout_seconds: float = 15.0,
    poll_seconds: float = 0.01,
) -> Iterator[None]:
    """Acquire the same hard-link lock primitive used by the reference run."""
    safe_component(name, "lock name")
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{name}.lock"
    private = _write_private(
        lock_dir,
        name,
        canonical_bytes({
            "host": os.uname().nodename,
            "name": name,
            "pid": os.getpid(),
            "schema": "resizable-pool-link-lock-v1",
        }),
        0o444,
    )
    deadline = time.monotonic() + timeout_seconds
    acquired = False
    try:
        while True:
            try:
                os.link(private, lock_path)
                fsync_dir(lock_dir)
                acquired = True
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise StateError(f"timed out acquiring link lock: {lock_path}")
                time.sleep(poll_seconds)
        yield
    finally:
        if acquired:
            try:
                if not os.path.samestat(private.stat(), lock_path.stat()):
                    raise StateError(f"link-lock inode changed: {lock_path}")
                retire_path(lock_path)
                fsync_dir(lock_dir)
            finally:
                retire_path(private, missing_ok=True)
        else:
            retire_path(private, missing_ok=True)


def durable_unlink(path: Path) -> None:
    retire_path(path)
    fsync_dir(path.parent)
