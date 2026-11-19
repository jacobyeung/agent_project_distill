"""Strict serialization and fail-closed errors shared by the CLI and replay."""
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path


class ProvenanceError(RuntimeError):
    """A build-level mismatch: abort, retaining partial output."""


class Refusal(ValueError):
    def __init__(self, reason, detail="", disposition="rejected"):
        super().__init__(detail or reason)
        self.reason, self.detail, self.disposition = reason, detail, disposition


def defer(reason, detail=""):
    raise Refusal(reason, detail, "deferred")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ProvenanceError("duplicate JSON key: " + k)
        d[k] = v
    return d


def loads(s):
    return json.loads(s, object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ProvenanceError(s)))


def read_json(path):
    p = Path(path)
    if not p.is_absolute() or not str(p.resolve()).startswith("/scratch/"):
        raise ProvenanceError("JSON inputs must use exact local scratch paths")
    return loads(p.read_text())


def pinned(pin, missing_row=False):
    p = Path(pin["path"])
    if not p.is_absolute() or not str(p.resolve()).startswith("/scratch/"):
        raise ProvenanceError("inputs must use exact /scratch paths: " + str(p))
    if not p.is_file():
        if missing_row:
            defer("missing_asset", str(p))
        raise ProvenanceError("missing pinned input: " + str(p))
    if sha256(p) != pin["sha256"]:
        raise ProvenanceError("SHA mismatch: " + str(p))
    return p


def source_module(name, pin):
    """Execute the hashed source bytes, never an unpinned cached .pyc."""
    path = pinned(pin)
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != pin["sha256"]:
        raise ProvenanceError("dependency changed while loading: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as f:
        for n, line in enumerate(f, 1):
            try:
                yield n, loads(line)
            except (ValueError, TypeError) as e:
                raise ProvenanceError(f"invalid JSONL {path}:{n}: {e}") from e


def write_json(path, value):
    with Path(path).open("x") as f:
        f.write(encoded(value) + "\n")


def rounded(v, places=8):
    if hasattr(v, "tolist"):
        v = v.tolist()
    if isinstance(v, (list, tuple)):
        return [rounded(x, places) for x in v]
    x = float(v)
    if not math.isfinite(x):
        raise Refusal("nonfinite_evidence")
    return round(x, places)


CONVENTION = "Printed f1: x right, y up, z floor heading; camera: OpenCV y down; move: L_k y down; metres; cross>0/yaw>0 left"
SIGN = "dot=u_x*v_x+u_z*v_z; cross=u_x*v_z-u_z*v_x; theta=atan2(cross,dot); positive means left"
