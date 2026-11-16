"""One artifact: a manifest that pins every data file the model reads by sha256, and a loader
that reads nothing else.

Manifest (JSON, schema e2e-artifact-v1), paths relative to the artifact root:
  components: {name: {role, files: [{rel, sha256, bytes}]}}   # LM, ViT, heads, connector,
                                                             # G3T, SAM 3, scale/selector heads, tokenizer
  code:       [{rel, sha256, bytes}]                         # reader/tree sources (EAT-1 A3 scans them)
The caller pins the manifest itself by sha256. During generate() an audit hook records every
open; a data file outside the manifest raises PermissionError (EAT-1 A1).
"""
import hashlib
import json
import os
import sys
import threading
from pathlib import Path

SCHEMA = 'e2e-artifact-v1'
CODE_SUFFIXES = ('.py', '.pyc', '.so')
SYSTEM_PREFIXES = ('/proc/', '/sys/', '/dev/null', '/dev/urandom', '/dev/random')
WRITE_FLAGS = frozenset('wax+')
REQUIRED_ROLES = ('checkpoint', 'tokenizer', 'g3t', 'scale_head')  # sam3 + selector_head for stage-1 ground


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def build_manifest(root, components, code_roots=None):
    """components: {name: (role, [relative paths])}; code_roots: {root name: directory} whose
    .py files are pinned (code may live outside the data root; it is identified by sha256)."""
    root = Path(root)
    entry = lambda base, rel: dict(rel=str(rel), sha256=sha256(Path(base) / rel), bytes=(Path(base) / rel).stat().st_size)
    code = []
    for name, base in sorted((code_roots or {}).items()):
        base = Path(base)
        for p in sorted(base.rglob('*.py')):
            code.append(dict(entry(base, p.relative_to(base)), root=name))
    manifest = dict(schema=SCHEMA,
                    components={n: dict(role=role, files=[entry(root, r) for r in rels]) for n, (role, rels) in components.items()},
                    code=code)
    return manifest


def write_manifest(root, manifest, name='E2E_MANIFEST.json'):
    path = Path(root) / name
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
    return path, sha256(path)


class ArtifactError(ValueError):
    pass


class Artifact:
    def __init__(self, root, manifest_name, manifest_sha256, *, code_roots=None, required_roles=REQUIRED_ROLES,
                 env_roots=()):
        """env_roots: extra installed-library directories of the runtime environment (e.g. a site-packages overlay),
        trusted like the interpreter's own site-packages and listed in every audit report."""
        self.root = Path(root).resolve()
        self.env_roots = tuple(os.path.realpath(r) + '/' for r in env_roots)
        self.code_roots = {k: Path(v).resolve() for k, v in (code_roots or {}).items()}
        path = self.root / manifest_name
        if sha256(path) != manifest_sha256:
            raise ArtifactError('manifest_sha256_differs')
        self.manifest = json.loads(path.read_text())
        if self.manifest.get('schema') != SCHEMA:
            raise ArtifactError('manifest_schema')
        roles = {c['role'] for c in self.manifest['components'].values()}
        missing = [r for r in required_roles if r not in roles]
        if missing:
            raise ArtifactError('manifest_missing_roles:' + ','.join(missing))
        self.allowed, self.code = {str(path)}, set()
        for comp in self.manifest['components'].values():
            for f in comp['files']:
                self.allowed.add(str(self._resolve(f['rel'])))
        for f in self.manifest.get('code', []):
            self.code.add(str(self._code_path(f)))
        self.verified = False

    def _code_path(self, f):
        base = self.code_roots.get(f.get('root'))
        if base is None:
            raise ArtifactError('code_root_not_bound:' + str(f.get('root')))
        p = (base / f['rel']).resolve()
        if base not in p.parents:
            raise ArtifactError('code_path_outside_root:' + f['rel'])
        return p

    def _resolve(self, rel):
        p = (self.root / rel).resolve()
        if self.root not in p.parents:
            raise ArtifactError('path_outside_artifact:' + rel)
        return p

    def verify(self):
        """Hash every pinned file; refuse any difference (size first, then sha256)."""
        for name, comp in self.manifest['components'].items():
            for f in comp['files']:
                p = self._resolve(f['rel'])
                if not p.is_file() or p.stat().st_size != f['bytes'] or sha256(p) != f['sha256']:
                    raise ArtifactError(f'component_file_differs:{name}:{f["rel"]}')
        for f in self.manifest.get('code', []):
            p = self._code_path(f)
            if not p.is_file() or sha256(p) != f['sha256']:
                raise ArtifactError('code_file_differs:' + f['rel'])
        self.verified = True
        return self

    def path(self, component, rel=None):
        """Absolute path of a pinned file (the only way reader code names a data file)."""
        files = self.manifest['components'][component]['files']
        if rel is None:
            if len(files) != 1:
                raise ArtifactError('component_has_several_files:' + component)
            rel = files[0]['rel']
        if not any(f['rel'] == rel for f in files):
            raise ArtifactError('file_not_in_component:' + rel)
        return self._resolve(rel)

    def files(self, component):
        return [self._resolve(f['rel']) for f in self.manifest['components'][component]['files']]


# ------------------------------------------------------------------ audit (EAT-1 A1)
def _roots():
    import sysconfig
    return tuple(sorted({os.path.realpath(sysconfig.get_paths()[k]) + '/' for k in ('stdlib', 'platstdlib', 'purelib', 'platlib')}))


_STDLIB_ROOTS = _roots()


def _stdlib(path):
    """Interpreter and installed-library code (python, torch, numpy, transformers): pinned by the
    runtime environment's own identity, not by this manifest."""
    return path.startswith(_STDLIB_ROOTS)


_state = threading.local()
_installed = False


def _hook(event, args):
    audit = getattr(_state, 'audit', None)
    if audit is None or event != 'open' or not args:
        return
    target = args[0]
    if not isinstance(target, (str, bytes, os.PathLike)):
        return
    try:
        path = os.path.realpath(os.fsdecode(target))
    except Exception:
        return
    mode = args[1] if len(args) > 1 and isinstance(args[1], str) else 'r'
    if len(args) > 2 and isinstance(args[2], int) and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC):
        mode = 'w'
    audit.record(path, mode)


# Native readers open files below the audit layer (safetensors and tokenizers in Rust). The audit
# wraps them so the path is checked before the native open; every module attribute bound to an
# original is rebound while an audit is active.
_NATIVE = {}


def _native_targets():
    targets = []
    try:
        import safetensors
        import safetensors.torch as st
        targets += [(safetensors, 'safe_open'), (st, 'safe_open'), (st, 'load_file')]
    except ImportError:
        pass
    try:
        import tokenizers
        targets.append((tokenizers.Tokenizer, 'from_file'))
    except ImportError:
        pass
    return targets


def _native_path(args, kwargs):
    for value in list(args[:1]) + [kwargs.get(k) for k in ('filename', 'path', 'file', 'name')]:
        if isinstance(value, (str, bytes, os.PathLike)):
            return os.path.realpath(os.fsdecode(value))
    return None


def _audited(original):
    def wrapper(*a, **k):
        audit = getattr(_state, 'audit', None)
        if audit is not None:
            path = _native_path(a, k)
            if path is None:
                audit._refuse('native_open_without_path', repr(original))
            else:
                audit.record(path, 'rb')
        return original(*a, **k)
    wrapper.__wrapped_native__ = original
    return wrapper


def _same(value, original):
    try:
        return value is original or (type(value) is type(original) and bool(value == original))
    except Exception:
        return False


def _patch_native():
    """Wrap every native opener and rebind every module global that holds one, whatever its name."""
    swaps, pairs = [], []
    for owner, name in _native_targets():
        current = getattr(owner, name)
        original = getattr(current, '__wrapped_native__', current)
        wrapper = next((w for o, w in _NATIVE.values() if _same(original, o)), None)
        if wrapper is None:
            wrapper = _audited(original)
            _NATIVE[len(_NATIVE)] = (original, wrapper)
        swaps.append((owner, name, current))
        setattr(owner, name, wrapper)
        pairs.append((original, wrapper))
    kinds = {type(o) for o, _ in pairs}
    for mod in list(sys.modules.values()):
        d = getattr(mod, '__dict__', None)
        if not isinstance(d, dict):
            continue
        for name, value in list(d.items()):
            if type(value) not in kinds:
                continue
            for original, wrapper in pairs:
                if _same(value, original):
                    swaps.append((mod, name, value))
                    setattr(mod, name, wrapper)
                    break
    return swaps


def install_audit():
    global _installed
    if not _installed:
        sys.addaudithook(_hook)
        _installed = True


class Audit:
    """Context active for the duration of one generate(): records opens (Python and the wrapped
    native readers), refuses data and code outside the artifact, and refuses every write mode
    (a read has no outputs on disk)."""

    def __init__(self, artifact, *, enforce=True):
        self.artifact, self.enforce = artifact, enforce
        self.opens, self.violations, self.entries = [], [], 0
        self._swaps = []

    def _refuse(self, kind, path):
        self.violations.append((kind, path))
        if self.enforce:
            raise PermissionError(f'e2e_artifact_refuses:{kind}:{path}')

    def record(self, path, mode):
        self.opens.append((path, mode))
        if path.startswith(SYSTEM_PREFIXES):
            return
        if WRITE_FLAGS & set(mode):
            return self._refuse('write', path)
        if path in self.artifact.allowed:
            return
        if path.endswith(CODE_SUFFIXES) or (path.endswith('.pth') and _stdlib(path)):
            source = path
            if path.endswith('.pyc') and '/__pycache__/' in path:
                head, tail = path.rsplit('/__pycache__/', 1)
                source = head + '/' + tail.split('.', 1)[0] + '.py'
            if source not in self.artifact.code and not (_stdlib(path) or path.startswith(self.artifact.env_roots)):
                self._refuse('code_outside_manifest', path)
            return
        if os.path.isdir(path):
            return
        self._refuse('data_outside_manifest', path)

    def __enter__(self):
        install_audit()
        if getattr(_state, 'audit', None) is not None:
            raise RuntimeError('nested_generate_audit')
        self._swaps = _patch_native()
        _state.audit = self
        return self

    def __exit__(self, *exc):
        _state.audit = None
        for owner, name, value in reversed(self._swaps):
            setattr(owner, name, value)
        self._swaps = []
        return False

    def report(self):
        return dict(opens=len(self.opens), model_entries=self.entries, env_roots=list(self.artifact.env_roots),
                    violations=[list(v) for v in self.violations],
                    data_files=sorted({p for p, _ in self.opens if p in self.artifact.allowed}))


def load_tensors(path):
    """Read a safetensors file through Python's open() so the audit hook sees it (safetensors'
    own loader opens files in Rust, below the audit layer)."""
    from safetensors.torch import load
    with open(path, 'rb') as f:
        return load(f.read())
