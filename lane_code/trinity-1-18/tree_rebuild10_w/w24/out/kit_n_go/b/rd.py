"""Publish bounded routing evidence from the batch shell after the view exits."""
from pathlib import Path
import json
import os
import stat
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from z import load, screen


def publish(kit, root, job, returncode):
    kit, root = Path(kit).resolve(), Path(root).resolve()
    if not job or any(c not in '0123456789' for c in job):
        raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
    target = Path(load(kit/'k/p.json')['n_root'])/'o'/job
    if not target.is_absolute() or '..' in target.parts:
        raise ValueError('R1_ROUTING_DESTINATION_INVALID')
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError('R1_ROUTING_DESTINATION_INVALID')
    if any(target.resolve() == p or p in target.resolve().parents for p in (kit, root)):
        raise ValueError('R1_ROUTING_DESTINATION_INVALID')
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    records = {}
    for name, source, limit in (
        ('q.log', root/'q.log', 2_000_000),
        ('r0.json', root/'p/r0.json', 500_000),
        ('routing_selection.json', root/'p/routing_selection.json', 2_000_000),
    ):
        if not source.exists():
            continue
        if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
            raise ValueError('R1_ROUTING_EVIDENCE_UNUSABLE')
        with source.open('rb') as f:
            if name == 'q.log':
                f.seek(max(0, source.stat().st_size-limit))
            raw = f.read(limit+1)
        if len(raw) > limit:
            raise ValueError('R1_ROUTING_EVIDENCE_TOO_LARGE')
        if name == 'q.log':
            # The shell has already run l.py; screen the retained tail as well.
            raw = screen(raw.decode('utf-8', errors='replace'), load(kit/'k/g.json'),
                         load(kit/'b/wh.json')).encode()[-limit:]
        else:
            json.loads(raw)
        leaf = target/name
        fd = os.open(leaf, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
        records[name] = len(raw)
    raw = (json.dumps(dict(returncode=int(returncode), files=records), sort_keys=True)+'\n').encode()
    fd = os.open(target/'r1.json', os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    if int(returncode) == 0 and 'routing_selection.json' not in records:
        raise ValueError('R1_ROUTING_SELECTION_MISSING')
    return records


if __name__ == '__main__':
    publish(Path(__file__).resolve().parents[1], *sys.argv[1:])
