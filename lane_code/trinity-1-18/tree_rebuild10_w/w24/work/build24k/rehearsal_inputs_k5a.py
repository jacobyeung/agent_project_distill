"""Bound the fixture input set without copying or modifying its databases."""
import json
import os
from pathlib import Path

PLAN_LIMIT = 900_000_000
DISK_LIMIT = 2_850_000_000


def prepare(root, capacity, cfg, write, sha):
    inputs = root / 'inputs'
    frames = inputs / 'frames'
    stores = inputs / 'stores'
    frames.mkdir(parents=True)
    stores.mkdir()
    frame = capacity / 'data2root/f.png'
    os.link(frame, frames / 'f.png')
    seen, databases = set(), {}

    def visit(pin):
        h = pin['sha256']
        if h in seen:
            return
        seen.add(h)
        source = Path(pin['path'])
        if source.stat().st_size > 1_000_000:
            raise ValueError('Fixture stream receipt is unexpectedly large')
        value = json.loads(source.read_text())
        if 'database' in value:
            db = value['database']
            path = Path(db['path'])
            if not (path.is_relative_to(capacity) or path.is_relative_to(root/'fixture')) or path.suffix != '.sqlite':
                raise ValueError('Only the existing capacity fixture stores may be linked')
            if db['sha256'] not in databases:
                os.link(path, stores / db['sha256'])
                st = path.stat()
                databases[db['sha256']] = dict(path=str(path), bytes=st.st_size,
                    device=st.st_dev, inode=st.st_ino, borrowed=not path.is_relative_to(root))
        for child in value.get('sources', []):
            visit(child['receipt'])

    for pin in cfg['streams'].values():
        visit(pin)
    layout = dict(frame_roots=[str(frames)], frame_sha256=sha(frame), stores=databases,
                  linked_store_bytes=sum(x['bytes'] for x in databases.values()),
                  plan_limit=PLAN_LIMIT, disk_limit=DISK_LIMIT)
    write(root / 'INPUT_LAYOUT.json', layout)
    return layout


def usage(root):
    """Count new inodes once; exclude the explicitly recorded input hard links."""
    layout_path = root / 'INPUT_LAYOUT.json'
    layout = json.loads(layout_path.read_text()) if layout_path.exists() else {}
    borrowed = {(v['device'], v['inode']) for v in layout.get('stores', {}).values() if v.get('borrowed', True)}
    frame = root / 'inputs/frames/f.png'
    if frame.exists():
        st = frame.stat()
        borrowed.add((st.st_dev, st.st_ino))
    seen, logical, allocated, shared, shared_allocated = set(), 0, 0, 0, 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        allocated += Path(directory).stat().st_blocks * 512
        for name in files:
            path = Path(directory) / name
            st = path.lstat()
            if path.is_symlink():
                allocated += st.st_blocks * 512
                continue
            inode = st.st_dev, st.st_ino
            if inode in seen:
                continue
            seen.add(inode)
            if inode in borrowed:
                shared += st.st_size
                shared_allocated += st.st_blocks * 512
            else:
                logical += st.st_size
                allocated += st.st_blocks * 512
    return dict(new_bytes=logical, allocated_bytes=allocated, linked_input_bytes=shared,
                linked_allocated_bytes=shared_allocated,
                retained_allocated_bytes=allocated+shared_allocated)


def plan_bytes(entries):
    # z.copy_resolved_payload streams the export tar directly into its members;
    # it does not retain a concatenated archive. Tar size bounds extracted bytes.
    return sum(v.get('bytes', v.get('archive', {}).get('bytes', 0)) for v in entries.values())


def check_budget(planned, current):
    if planned >= PLAN_LIMIT or current + planned >= DISK_LIMIT:
        raise RuntimeError('REHEARSAL_STAGING_BUDGET: native plan exceeds cap before copying')


def frame_host(frame_root):
    """Map only the synthetic RGB name; retain the native frame audit checks."""
    from student_pilot import orchard_paths
    root=Path(frame_root)
    if not root.is_relative_to('/tmp/q_22c714e1/p2/q'):
        raise ValueError('Fixture RGB must be inside the native canary namespace')
    original=orchard_paths.resolve_read
    def resolve_read(path, *, resolve=None):
        if Path(path)==Path('/data2/f.png'):
            return root/'f.png'
        return original(path,resolve=resolve)
    orchard_paths.resolve_read=resolve_read
