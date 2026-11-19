"""Host-only containment and source-bound statement receipts."""
from contextlib import contextmanager
import inspect
import os
from pathlib import Path
import resource
import sys
from urllib.parse import parse_qs, unquote, urlsplit
from student_pilot.p3_provenance import file_pin

_active = []


def audit(event, args):
    if not _active:
        return
    root = _active[-1]
    paths = []
    if event == 'open' and isinstance(args[0], (str, bytes)):
        mode, flags = args[1:3]
        if any(c in (mode or '') for c in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            paths = [args[0]]
    elif event == 'sqlite3.connect':
        value = str(args[0])
        if value.startswith('file:'):
            uri = urlsplit(value)
            if parse_qs(uri.query).get('mode') == ['ro']:
                return
            value = unquote(uri.path)
        paths = [value]
    elif event == 'os.mkdir':
        paths = [args[0]]
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        paths = [args[1]]
    elif event in ('socket.connect', 'subprocess.Popen'):
        raise ValueError('Host job cannot open a network connection or child process')
    for value in paths:
        if not Path(os.fsdecode(value)).resolve().is_relative_to(root):
            raise ValueError('Write outside the one job folder')


audit.__cantrace__ = True
sys.addaudithook(audit)


@contextmanager
def bounded_writes(root, max_file_bytes):
    root = Path(root).resolve()
    old = resource.getrlimit(resource.RLIMIT_FSIZE)
    ceiling = max_file_bytes if old[1] == resource.RLIM_INFINITY else min(max_file_bytes, old[1])
    resource.setrlimit(resource.RLIMIT_FSIZE, (ceiling, old[1]))
    _active.append(root)
    try:
        yield
    finally:
        _active.pop()
        resource.setrlimit(resource.RLIMIT_FSIZE, old)


def obligations():
    from student_pilot import r2_materialize as materializer, carrier_c1_run as run
    specs = [(materializer.materialize, "if os.environ.get('STUDENT_R2_FRAME_HOST')", 'frame-host'),
             (materializer.materialize, "raise ValueError('Full materialization requires an explicit frame-host admission')", 'frame-host'),
             (materializer.materialize, 'limit = None', 'frame-host'),
             (run.dryrun, 'plan = next(data.mixed_indices(', 'model-loader'),
             (run.first_batch_check, 'plans = list(data.mixed_indices(', 'model-loader')]
    records = []
    for fn, needle, category in specs:
        lines, start = inspect.getsourcelines(fn)
        matches = [start+i for i,line in enumerate(lines) if needle in line]
        if len(matches) != 1:
            raise ValueError('Statement obligation is ambiguous or absent')
        records.append(dict(source=file_pin(inspect.getsourcefile(fn)), line=matches[0], category=category))
    return records


@contextmanager
def statement_hits(records):
    selected = {r['source']['path'] for r in records}
    previous = sys.gettrace()
    hits = set()
    def trace(frame, event, arg):
        parent = previous(frame, event, arg) if previous is not None else None
        if frame.f_code.co_filename in selected:
            if event == 'line':
                hits.add((frame.f_code.co_filename, frame.f_lineno))
            return trace
        return parent
    sys.settrace(trace)
    try:
        yield hits
    finally:
        sys.settrace(previous)


def checked_hits(records, hits):
    result = [{**r, 'reached':(r['source']['path'],r['line']) in hits} for r in records]
    if any(not row['reached'] for row in result):
        raise ValueError('Host launch statement was not reached')
    return result


def init_layout(archive_pin, root, members, max_member_bytes):
    from .host import stage_init
    from student_pilot.p3_provenance import write
    root = Path(root).resolve()
    mapped = stage_init(archive_pin, root, members, max_member_bytes=max_member_bytes)
    artifact = root/mapped['m544/artifact.json']
    mirror_root = root/'ee544001'
    mirror = mirror_root/file_pin(artifact)['sha256'][:16]
    mirror.mkdir(parents=True)
    (mirror/'artifact.json').symlink_to(artifact)
    for name in ('heads.pt', 'full_weights'):
        target = root/'ap/8865619b/runs/469ddece/m544'/name
        if not target.exists():
            raise ValueError('Init export lacks required member: '+name)
        (mirror/name).symlink_to(target)
    write(mirror/'.verified', dict(archive=archive_pin, members=members))
    return dict(artifact=file_pin(artifact), mirror_root=str(mirror_root), mapped=mapped)
