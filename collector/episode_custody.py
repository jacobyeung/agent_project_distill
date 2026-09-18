"""Parent-controlled custody for provider children; no filesystem deletion."""
from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import stat
import threading
import time
from typing import Callable

ENV_KEY = "SPLIT_EPISODE_CUSTODY_V1"


class CustodyLost(RuntimeError):
    pass


def process_start(pid: int) -> int:
    value = Path(f"/proc/{pid}/stat").read_text()
    return int(value[value.rfind(")") + 2:].split()[19])


class FailureEvent(threading.Event):
    """A one-way event that revokes subscribed channels synchronously."""

    def __init__(self):
        super().__init__()
        self._listener_lock = threading.RLock()
        self._listeners: dict[object, tuple[Callable[[], None], Callable[[], None] | None]] = {}
        self.callback_errors: list[str] = []

    def subscribe(self, callback: Callable[[], None], *,
                  after_set: Callable[[], None] | None = None) -> Callable[[], None]:
        token = object()
        already_failed = False
        with self._listener_lock:
            if self.is_set():
                callback()
                already_failed = True
            else:
                self._listeners[token] = (callback, after_set)
        if already_failed and after_set is not None:
            self._start_diagnostics((after_set,))

        def unsubscribe() -> None:
            with self._listener_lock:
                self._listeners.pop(token, None)
        return unsubscribe

    def _start_diagnostics(self, callbacks) -> None:
        if not callbacks:
            return

        def record() -> None:
            for callback in callbacks:
                try:
                    callback()
                except BaseException as exc:
                    self.callback_errors.append(type(exc).__name__)
        try:
            threading.Thread(target=record, name="episode-custody-diagnostic",
                             daemon=True).start()
        except BaseException as exc:
            self.callback_errors.append(type(exc).__name__)

    def set(self) -> None:
        diagnostics = []
        with self._listener_lock:
            if self.is_set():
                return
            try:
                for callback, after_set in tuple(self._listeners.values()):
                    try:
                        callback()
                    except BaseException as exc:
                        self.callback_errors.append(type(exc).__name__)
                    if after_set is not None:
                        diagnostics.append(after_set)
            finally:
                super().set()
        # Every pipe is revoked and waiters can abort before optional storage work.
        self._start_diagnostics(tuple(diagnostics))

    def clear(self) -> None:
        raise CustodyLost("failed episode custody cannot be restored")


def _publish_abort(path: Path, envelope: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"schema": "split-episode-custody-abort-v1", "reason": "episode_failure",
             "round": envelope["round"], "qid": envelope["qid"],
             "owner_pid": envelope["owner_pid"], "owner_start": envelope["owner_start"],
             "wall_time_ns": time.time_ns()}
    try:
        with path.open("x") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        return
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class CustodyChannel:
    """Give a child only the read end of a parent-owned revocable pipe."""

    def __init__(self, *, round_id: int, contract_sha256: str, qid: str,
                 worker_id: str, failed_event: FailureEvent, abort_path: Path):
        if not isinstance(failed_event, FailureEvent):
            raise CustodyLost("the real episode pump must use FailureEvent")
        if type(round_id) is not int or round_id <= 0:
            raise CustodyLost("invalid round identity")
        if (len(contract_sha256) != 64 or any(c not in "0123456789abcdef" for c in contract_sha256)
                or not isinstance(qid, str) or not qid
                or not isinstance(worker_id, str) or not worker_id):
            raise CustodyLost("incomplete custody scope")
        self.abort_path = Path(abort_path)
        if not self.abort_path.is_absolute():
            raise CustodyLost("abort path must be absolute")
        self.failed_event = failed_event
        self._lock = threading.Lock()
        self._read_fd: int | None = None
        self._write_fd: int | None = None
        self._unsubscribe: Callable[[], None] | None = None
        self._entered = False
        self.marker_error: str | None = None
        self.marker_done = threading.Event()
        self.envelope = {"schema": "split-episode-custody-v1", "round": round_id,
                         "contract_sha256": contract_sha256, "qid": qid,
                         "worker_id": worker_id, "owner_pid": os.getpid(),
                         "owner_start": process_start(os.getpid())}

    def __enter__(self):
        if self._entered or self.failed_event.is_set() or self.abort_path.exists():
            raise CustodyLost("child channel cannot start after failure or reuse")
        self._entered = True
        self._read_fd, self._write_fd = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        identity = os.fstat(self._read_fd)
        self.envelope.update(read_fd=self._read_fd, pipe_device=identity.st_dev,
                             pipe_inode=identity.st_ino)
        try:
            self._unsubscribe = self.failed_event.subscribe(
                self.invalidate, after_set=self._record_abort)
            if self.failed_event.is_set():
                raise CustodyLost("episode failed while creating child custody")
            return self
        except BaseException:
            self.close()
            raise

    def invalidate(self) -> None:
        with self._lock:
            writer, self._write_fd = self._write_fd, None
            if writer is None:
                return
            os.close(writer)

    def _record_abort(self) -> None:
        try:
            _publish_abort(self.abort_path, self.envelope)
        except BaseException as exc:
            self.marker_error = type(exc).__name__
        finally:
            self.marker_done.set()

    @property
    def pass_fds(self) -> tuple[int]:
        if self._read_fd is None or self._write_fd is None or self.failed_event.is_set():
            raise CustodyLost("child channel is not live")
        return (self._read_fd,)

    def child_env(self) -> dict[str, str]:
        self.pass_fds
        return {ENV_KEY: json.dumps(self.envelope, sort_keys=True, separators=(",", ":"))}

    def close(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        with self._lock:
            descriptors = (self._write_fd, self._read_fd)
            self._write_fd = self._read_fd = None
            for descriptor in descriptors:
                if descriptor is not None:
                    os.close(descriptor)

    def __exit__(self, *_args):
        self.close()


def assert_child_custody(*, round_id: int, contract_sha256: str,
                         qid: str, worker_id: str) -> None:
    """Refuse before an effect when this child has lost its parent's permit."""
    try:
        envelope = json.loads(os.environ[ENV_KEY])
        expected = {"schema": "split-episode-custody-v1", "round": round_id,
                    "contract_sha256": contract_sha256, "qid": qid, "worker_id": worker_id}
        if any(envelope.get(key) != value for key, value in expected.items()):
            raise CustodyLost("child custody scope mismatch")
        owner = envelope["owner_pid"]
        if (type(owner) is not int or owner <= 0 or os.getppid() != owner
                or process_start(owner) != envelope["owner_start"]):
            raise CustodyLost("child custody owner has died or changed")
        descriptor = envelope["read_fd"]
        if type(descriptor) is not int or descriptor < 0:
            raise CustodyLost("invalid custody descriptor")
        identity = os.fstat(descriptor)
        if (not stat.S_ISFIFO(identity.st_mode) or os.get_blocking(descriptor)
                or identity.st_dev != envelope["pipe_device"]
                or identity.st_ino != envelope["pipe_inode"]):
            raise CustodyLost("custody descriptor identity mismatch")
        try:
            content = os.read(descriptor, 1)
        except BlockingIOError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                raise
            return
        raise CustodyLost("parent revoked child custody" if content == b"" else
                          "unexpected data in custody permit")
    except CustodyLost:
        raise
    except (KeyError, ValueError, TypeError, OSError) as exc:
        raise CustodyLost("child lacks authenticated parent custody") from exc


class JoinedAbort:
    """Event-compatible wait for any of the supplied independent abort events."""

    def __init__(self, *events: threading.Event):
        if not events:
            raise ValueError("at least one abort event is required")
        self.events = events

    def is_set(self) -> bool:
        return any(event.is_set() for event in self.events)

    def wait(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
        while not self.is_set():
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                return False
            self.events[0].wait(0.01 if remaining is None else min(0.01, remaining))
        return True
