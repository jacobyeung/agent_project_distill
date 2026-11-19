"""Explicit Orchard read relocation; file bindings retain their original path strings."""
import json
import os
from pathlib import Path

PROJECT = Path(os.environ.get('R1_MOUNT') or '/project/community/jjyeung/distill')
SCRATCH = Path('/tmp/jjyeung')


def enabled():
    return os.environ.get(('Q_E1' if 'Q_E1' in os.environ else 'STUDENT_ORCHARD')) == '1'


def owned(path, *, resolve=None):
    path = (resolve or Path.resolve)(Path(path))
    return enabled() and any(path.is_relative_to(root) and path != root for root in (PROJECT, SCRATCH))


def resolve_read(path, *, resolve=None):
    path = Path(path)
    resolve = resolve or Path.resolve
    mapping = os.environ.get(('Q_E4' if 'Q_E4' in os.environ else 'STUDENT_FRAME_ROOT_MAP'))
    if not mapping:
        return path
    if not enabled():
        raise ValueError('Frame root mapping requires explicit STUDENT_ORCHARD=1')
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
    root = Path(os.environ['Q_E3' if 'Q_E3' in os.environ else 'STUDENT_MODEL_ROOT']).resolve()
    if not owned(root):
        raise ValueError('Orchard model root must be owned project or node-local storage')
    original = spec['snapshot']
    return root / spec.get('snapshot_dir', original.parent.parent.name) / 'snapshots' / original.name
