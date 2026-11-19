"""Opt-in content-store primitives. These objects do not authorize training.

There is deliberately no native prepare/adopt adapter: current native receipts
contain run paths and their native key consumes excluded fields. A matching key
and self-consistent hashes do not prove that an arbitrary producer ran the code.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
import uuid

from .preparation_reads import canonical


SCHEMA = "preparation-object-graph-v1"
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_ROOT = 16 << 20
MAX_OBJECTS = 100_000
BLOCK = 1 << 20


class StoreRefused(ValueError):
    pass


def _hex(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise StoreRefused("invalid_digest")
    return value


def _name(value):
    if (not isinstance(value, str) or not value or "\\" in value or "\x00" in value
            or str(PurePosixPath(value)) != value or PurePosixPath(value).is_absolute()
            or any(p in (".", "..") for p in value.split("/"))):
        raise StoreRefused("invalid_object_name")
    if PurePosixPath(value).name in ("request.json", "data_receipt.json") or PurePosixPath(value).name.startswith("phase_"):
        raise StoreRefused("native_admission_name_refused")
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StoreRefused("duplicate_json_key")
        result[key] = value
    return result


def _json(raw):
    try:
        value = json.loads(raw, object_pairs_hook=_unique,
                           parse_constant=lambda x: (_ for _ in ()).throw(StoreRefused("nonfinite_json")))
        if canonical(value) != raw:
            raise StoreRefused("noncanonical_json")
        return value
    except (TypeError, UnicodeError, json.JSONDecodeError) as error:
        raise StoreRefused("invalid_json") from error


def receipt(value):
    """Accept explicitly portable receipt values; do not rewrite native receipts.

    References are {"object": SHA256}. Logical names must be relative. This
    format has no execution telemetry. Native SQLite/path migration is absent.
    """
    forbidden = {"path", "resolved", "roots", "hostname", "host", "timestamp",
                 "uuid", "resources", "seconds", "run_key", "output", "preparation_output"}

    def check(item):
        if isinstance(item, dict):
            if any(k in forbidden for k in item):
                raise StoreRefused("nonportable_receipt_field")
            if "object" in item:
                if set(item) != {"object"}:
                    raise StoreRefused("malformed_object_reference")
                _hex(item["object"])
            for part in item.values():
                check(part)
        elif isinstance(item, list):
            for part in item:
                check(part)
        elif isinstance(item, str):
            if item.startswith("/") or "\\" in item or "\x00" in item or ".." in item.split("/"):
                raise StoreRefused("nonportable_receipt_value")
        elif item is not None and type(item) not in (int, bool):
            raise StoreRefused("unsupported_receipt_value")

    check(value)
    return canonical(value)


def _references(value):
    if isinstance(value, dict):
        if set(value) == {"object"}:
            yield value["object"]
        for part in value.values():
            yield from _references(part)
    elif isinstance(value, list):
        for part in value:
            yield from _references(part)


@contextmanager
def _regular(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        raise StoreRefused("missing_or_linked_object") from error
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise StoreRefused("nonregular_object")
        yield handle


def _fsync(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _safe_directory(path):
    path = Path(path).absolute()
    # Reject linked ancestors too. Same-user concurrent malicious mutation is
    # outside this primitive's trust model; native adoption is not exposed.
    for part in reversed((path, *path.parents)):
        if part.is_symlink():
            raise StoreRefused("linked_directory")
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise StoreRefused("untrusted_store_directory")
    return path


class Store:
    def __init__(self, path, *, create=False):
        if os.environ.get("TK_XSTORE_EXPERIMENT") != "1":
            raise StoreRefused("switch_off")
        path = Path(path).absolute()
        if create:
            path.mkdir(mode=0o700, exist_ok=False)
            (path / "objects").mkdir(mode=0o700)
            (path / "roots").mkdir(mode=0o700)
            (path / "temporary").mkdir(mode=0o700)
        self.path = _safe_directory(path)
        for name in ("objects", "roots", "temporary"):
            _safe_directory(path / name)

    @contextmanager
    def _locked(self):
        fd = os.open(self.path / "publish.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            # A duplicate publisher fails promptly; it does not idle an allocation.
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def put_bytes(self, raw, *, kind="bytes"):
        if not isinstance(raw, bytes):
            raise TypeError("Object payload must be bytes")
        if kind not in ("bytes", "receipt"):
            raise StoreRefused("unknown_object_kind")
        if kind == "receipt":
            receipt(_json(raw))
        digest = hashlib.sha256(raw).hexdigest()
        temporary = self.path / "temporary" / uuid.uuid4().hex
        with temporary.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        with self._locked():
            target = self.path / "objects" / digest
            if target.exists() or target.is_symlink():
                self._verify_object({"sha256": digest, "bytes": len(raw), "kind": kind})
            else:
                os.rename(temporary, target)
                _fsync(target.parent)
        # Duplicate and failed temporaries remain for operator inspection.
        return {"sha256": digest, "bytes": len(raw), "kind": kind}

    def _verify_object(self, entry, *, copy_to=None):
        digest = hashlib.sha256()
        total = 0
        chunks = [] if entry["kind"] == "receipt" else None
        with _regular(self.path / "objects" / entry["sha256"]) as handle:
            if os.fstat(handle.fileno()).st_size != entry["bytes"]:
                raise StoreRefused("object_size_mismatch")
            while block := handle.read(BLOCK):
                total += len(block)
                if total > entry["bytes"]:
                    raise StoreRefused("object_size_mismatch")
                digest.update(block)
                if chunks is not None:
                    if total > MAX_ROOT:
                        raise StoreRefused("receipt_too_large")
                    chunks.append(block)
                if copy_to is not None:
                    copy_to.write(block)
        if total != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
            raise StoreRefused("object_hash_mismatch")
        if chunks is not None:
            value = _json(b"".join(chunks))
            receipt(value)
            return set(_references(value))
        return set()

    @staticmethod
    def _validate_root(root):
        if not isinstance(root, dict) or set(root) != {"schema", "key", "objects"} or root["schema"] != SCHEMA:
            raise StoreRefused("invalid_root_schema")
        _hex(root["key"])
        entries = root["objects"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_OBJECTS:
            raise StoreRefused("invalid_object_count")
        names = []
        digests = {}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"name", "sha256", "bytes", "kind"}:
                raise StoreRefused("invalid_object_entry")
            names.append(_name(entry["name"]))
            _hex(entry["sha256"])
            if type(entry["bytes"]) is not int or entry["bytes"] < 0 or entry["kind"] not in ("bytes", "receipt"):
                raise StoreRefused("invalid_object_entry")
            if entry["sha256"] in digests and digests[entry["sha256"]] != (entry["bytes"], entry["kind"]):
                raise StoreRefused("inconsistent_object_entry")
            digests[entry["sha256"]] = (entry["bytes"], entry["kind"])
        if names != sorted(set(names)):
            raise StoreRefused("duplicate_or_unsorted_names")
        name_set = set(names)
        if any(str(parent) in name_set for name in names for parent in PurePosixPath(name).parents):
            raise StoreRefused("object_name_prefix_collision")

    def _graph(self, root):
        self._validate_root(root)
        present = {entry["sha256"] for entry in root["objects"]}
        references = set()
        for entry in root["objects"]:
            references.update(self._verify_object(entry))
        if not references <= present:
            raise StoreRefused("incomplete_object_graph")

    def publish(self, key, objects):
        root = {"schema": SCHEMA, "key": _hex(key),
                "objects": sorted(objects, key=lambda entry: entry["name"])}
        raw = canonical(root)
        if len(raw) > MAX_ROOT:
            raise StoreRefused("root_too_large")
        digest = hashlib.sha256(raw).hexdigest()
        with self._locked():
            # The root is never published before the complete graph verifies.
            self._graph(root)
            temporary = self.path / "temporary" / (uuid.uuid4().hex + ".root")
            with temporary.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            target = self.path / "roots" / (digest + ".json")
            if target.exists() or target.is_symlink():
                self.verify(digest, expected_key=key)
            else:
                os.rename(temporary, target)
                _fsync(target.parent)
        return digest

    def verify(self, root_digest, *, expected_key):
        started = time.monotonic()
        _hex(root_digest)
        _hex(expected_key)
        with _regular(self.path / "roots" / (root_digest + ".json")) as handle:
            raw = handle.read(MAX_ROOT + 1)
        if len(raw) > MAX_ROOT:
            raise StoreRefused("root_too_large")
        if hashlib.sha256(raw).hexdigest() != root_digest:
            raise StoreRefused("root_hash_mismatch")
        root = _json(raw)
        self._validate_root(root)
        if root["key"] != expected_key:
            raise StoreRefused("foreign_key")
        self._graph(root)
        return root, {"root_digest": root_digest, "key": expected_key,
                      "object_count": len(root["objects"]),
                      "verify_seconds": time.monotonic() - started, "reason": "verified_objects_only"}

    def materialize_private(self, root_digest, *, expected_key, directory):
        """Write a new private artifact directory, never a training destination."""
        root, telemetry = self.verify(root_digest, expected_key=expected_key)
        directory = Path(directory).absolute()
        _safe_directory(directory.parent)
        directory.mkdir(mode=0o700, exist_ok=False)
        for entry in root["objects"]:
            target = directory / entry["name"]
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as handle:
                self._verify_object(entry, copy_to=handle)
                handle.flush()
                os.fsync(handle.fileno())
        # No admission or completion marker is synthesized here.
        return telemetry


def compare(left, left_digest, right, right_digest, *, key):
    """Compare independently supplied roots without normalizing any difference."""
    a, _ = left.verify(left_digest, expected_key=key)
    b, _ = right.verify(right_digest, expected_key=key)
    if a != b or left_digest != right_digest:
        aa = {e["name"]: e for e in a["objects"]}
        bb = {e["name"]: e for e in b["objects"]}
        changed = sorted(k for k in aa.keys() | bb.keys() if aa.get(k) != bb.get(k))
        raise StoreRefused("determinism_difference:" + ",".join(changed))
    return {"status": "IDENTICAL", "root_digest": left_digest, "key": key,
            "object_count": len(a["objects"])}
