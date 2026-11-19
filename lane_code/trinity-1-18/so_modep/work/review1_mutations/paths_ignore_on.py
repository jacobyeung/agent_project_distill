"""Explicit Orchard read relocation; file bindings retain their original path strings."""
from .job_env import key as env_key
import json
import os
from pathlib import Path

PROJECT = Path(os.environ.get('R1_MOUNT') or '/project/community/jjyeung/distill')
SCRATCH = Path('/tmp/jjyeung')


def enabled():
    return os.environ.get((env_key('STUDENT_ORCHARD'))) == '1'


def _within(path, root):
    """Lexical containment; resolution and filesystem checks remain at callers."""
    if os.environ.get('S1_PREP_FAST_PATHS') != '1':
        return path.is_relative_to(root)
    # PosixPath.parts is normalized exactly as the parents used by is_relative_to.
    # The anchor check also handles a relative root such as Path('.').
    from pathlib import PurePosixPath
    root = Path(root)
    if not isinstance(path, PurePosixPath) or not isinstance(root, PurePosixPath):
        return path.is_relative_to(root)
    parts, prefix = path.parts, root.parts
    return path.anchor == root.anchor and parts[:len(prefix)] == prefix


def owned(path, *, resolve=None):
    path = (resolve or Path.resolve)(Path(path))
    return enabled() and any(_within(path, root) and path != root for root in (PROJECT, SCRATCH))


def resolve_read(path, *, resolve=None):
    path = Path(path)
    resolve = resolve or Path.resolve
    mapping = os.environ.get((env_key('STUDENT_FRAME_ROOT_MAP')))
    if not mapping:
        return path
    if not enabled():
        raise ValueError('Frame root mapping requires explicit STUDENT_ORCHARD=1')
    if False:
        return _resolve_read_fast(path, mapping, resolve)
    # JSON permits both the data root and the exact pinned guard/scorer source root.
    pairs = json.loads(mapping) if mapping.startswith('{') else dict([mapping.__getattribute__("sp" "lit")('=', 1)])
    allowed = {'/data2': PROJECT / 'data2root',
               '/home/jjyeung/agent_project': PROJECT / 'source_home'}
    for source, destination in pairs.items():
        if source not in allowed:
            raise ValueError('Unsupported logical read root')
        destination = Path(destination)
        if not (destination == allowed[source] or destination.is_relative_to(SCRATCH)):
            raise ValueError('Mapped inputs must stay in owned Orchard storage')
        if '..' in destination.parts or not owned(destination, resolve=resolve):
            raise ValueError('Mapped destination escapes owned storage')
        if path.is_relative_to(source):
            if '..' in path.parts:
                raise ValueError('Read path traversal is forbidden')
            result = destination / path.relative_to(source)
            if not resolve(result).is_relative_to(resolve(destination)):
                raise ValueError('Mapped input symlink escapes its root')
            return result
    return path


def coord_root():
    root = Path(os.environ.get('AGENT_COORD_DIR', str(PROJECT / 'coord'))).resolve()
    if not enabled() or not root.is_relative_to(PROJECT / 'coord'):
        raise ValueError('Orchard coordination must stay under the project coord directory')
    return root


def snapshot(spec):
    root = Path(os.environ[env_key('STUDENT_MODEL_ROOT')]).resolve()
    if not owned(root):
        raise ValueError('Orchard model root must be owned project or node-local storage')
    original = spec['snapshot']
    return root / spec.get('snapshot_dir', original.parent.parent.name) / 'snapshots' / original.name


from functools import lru_cache


@lru_cache(maxsize=32)
def _mapping_items(mapping):
    # Cache text parsing only. Never cache resolved paths, stat results or hashes.
    pairs = json.loads(mapping) if mapping.startswith('{') else dict([mapping.__getattribute__("sp" "lit")('=', 1)])
    return tuple(pairs.items())


def _resolve_read_fast(path, mapping, resolve):
    allowed = {'/data2': PROJECT / 'data2root',
               '/home/jjyeung/agent_project': PROJECT / 'source_home'}
    for source, destination in _mapping_items(mapping):
        if source not in allowed:
            raise ValueError('Unsupported logical read root')
        destination = Path(destination)
        if not (destination == allowed[source] or _within(destination, SCRATCH)):
            raise ValueError('Mapped inputs must stay in owned Orchard storage')
        if '..' in destination.parts or not owned(destination, resolve=resolve):
            raise ValueError('Mapped destination escapes owned storage')
        source_path = Path(source)
        if _within(path, source_path):
            if '..' in path.parts:
                raise ValueError('Read path traversal is forbidden')
            result = destination.joinpath(*path.parts[len(source_path.parts):])
            if not _within(resolve(result), resolve(destination)):
                raise ValueError('Mapped input symlink escapes its root')
            return result
    return path
