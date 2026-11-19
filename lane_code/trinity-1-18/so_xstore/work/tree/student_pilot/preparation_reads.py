"""Experimental dependency recorder; not wired into native preparation.

Callers must use these views for every semantic input. The Python I/O guard is
a development tripwire, not a sandbox for C extensions or captured references.
No production planner or admission authority is implemented by this module.
"""
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


EXCLUDED = frozenset(("output", "run_key", "preparation_output"))
_guard = ContextVar("preparation_read_guard", default=None)
_internal = ContextVar("preparation_read_internal", default=False)
_installed = False


class UnkeyedRead(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _audit(event, args):
    if _guard.get() is None or _internal.get():
        return
    if event in ("open", "sqlite3.connect", "os.listdir", "os.scandir",
                 "subprocess.Popen", "os.system", "ctypes.dlopen") or event.startswith("socket."):
        raise UnkeyedRead("Raw I/O outside the recorded interface: " + event)


class Recorder:
    """Record actual accesses, then reject any new or changed replay access.

    File names are logical roles. Paths stay outside the key; complete file
    bytes enter it. Config file pins must therefore be supplied as file roles,
    not raw absolute path strings in the content configuration.
    """
    def __init__(self, config, *, files=None, environment=None, expected=None):
        if os.environ.get("TK_XSTORE_EXPERIMENT") != "1":
            raise ValueError("TK_XSTORE_EXPERIMENT=1 is required")
        self._config = json.loads(canonical(config))
        self._files = {k: Path(v) for k, v in (files or {}).items()}
        self._environment = dict(environment or {})
        self._expected = None if expected is None else json.loads(canonical(expected))
        self._reads = {}
        self.config = ConfigView(self, self._config, ())

    def _record(self, kind, path, value):
        if kind == "config" and path and path[0] in EXCLUDED:
            raise UnkeyedRead("Run-specific content read: " + str(path[0]))
        tag = canonical([kind, list(path)]).decode("ascii")
        item = json.loads(canonical(value))
        if self._expected is not None and (tag not in self._expected or self._expected[tag] != item):
            raise UnkeyedRead("Unkeyed or changed read: " + tag)
        if tag in self._reads and self._reads[tag] != item:
            raise UnkeyedRead("Input changed during execution: " + tag)
        self._reads[tag] = item

    def _wrap(self, value, path):
        if isinstance(value, dict):
            return ConfigView(self, value, path)
        if isinstance(value, list):
            return ListView(self, value, path)
        self._record("config", path, {"value": value})
        return value

    def environment(self, name):
        if name not in self._environment:
            raise UnkeyedRead("Undeclared environment input: " + name)
        value = self._environment[name]
        if value is not None and not isinstance(value, str):
            raise TypeError("Environment values must be strings or explicit absence")
        self._record("environment", (name,), value)
        return value

    def read_file(self, role):
        if role not in self._files:
            raise UnkeyedRead("Undeclared file role: " + role)
        token = _internal.set(True)
        try:
            # O_NOFOLLOW prevents silently changing the declared input into a link.
            fd = os.open(self._files[role], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as handle:
                before = os.fstat(handle.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise UnkeyedRead("File role is not regular: " + role)
                if before.st_size > 64 << 20:
                    raise UnkeyedRead("Prototype file reader is bounded to 64 MiB: " + role)
                raw = handle.read()
                after = os.fstat(handle.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                        after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise UnkeyedRead("File changed while reading: " + role)
        finally:
            _internal.reset(token)
        self._record("file", (role,), {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return raw

    def finish(self):
        if self._expected is not None and self._reads != self._expected:
            raise UnkeyedRead("Execution did not consume the exact planned read set")
        return json.loads(canonical(self._reads))

    @property
    def key(self):
        return digest({"schema": "preparation-read-set-v1", "reads": self.finish()})

    @contextmanager
    def python_io_guard(self):
        global _installed
        if not _installed:
            sys.addaudithook(_audit)
            _installed = True
        token = _guard.set(self)
        try:
            yield self
        finally:
            _guard.reset(token)


class ConfigView(Mapping):
    def __init__(self, recorder, value, path):
        self._recorder, self._value, self._path = recorder, value, path

    def __getitem__(self, key):
        path = (*self._path, key)
        if key not in self._value:
            self._recorder._record("config", path, {"present": False})
            raise KeyError(key)
        value = self._value[key]
        if isinstance(value, (dict, list)):
            self._recorder._record("config", path, {"type": type(value).__name__})
        return self._recorder._wrap(value, path)

    def __contains__(self, key):
        present = key in self._value
        self._recorder._record("config", (*self._path, key, "@present"), present)
        return present

    def __iter__(self):
        # Enumeration itself consumes the key set. Refuse excluded names before
        # yielding even one key, including dict(view) and {**view} callers.
        keys = list(self._value)
        if not self._path and EXCLUDED.intersection(keys):
            raise UnkeyedRead("Run-specific content read through config iteration")
        self._recorder._record("config", (*self._path, "@keys"), keys)
        return iter(keys)

    def __len__(self):
        if not self._path and EXCLUDED.intersection(self._value):
            raise UnkeyedRead("Run-specific content read through config length")
        self._recorder._record("config", (*self._path, "@length"), len(self._value))
        return len(self._value)


class ListView(Sequence):
    def __init__(self, recorder, value, path):
        self._recorder, self._value, self._path = recorder, value, path

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        # Bind length for negative indexing and exhausted iteration alike.
        length = len(self)
        if index < 0:
            index += length
        if not 0 <= index < length:
            raise IndexError(index)
        return self._recorder._wrap(self._value[index], (*self._path, index))

    def __len__(self):
        self._recorder._record("config", (*self._path, "@length"), len(self._value))
        return len(self._value)
