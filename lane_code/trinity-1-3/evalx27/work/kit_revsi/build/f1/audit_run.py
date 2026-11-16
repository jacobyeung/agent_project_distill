"""Record a local proof without changing packaged executable code."""
import json
import os
from pathlib import Path
import runpy
import selectors
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE / 'empty04'
RECORDS = HERE / 'records04'
RECORDS.mkdir(exist_ok=True)
LOG = RECORDS / (str(os.getpid()) + '.jsonl')
ACTIVE = False
SEEN = set()


def record(kind, **values):
    global ACTIVE
    if ACTIVE:
        return
    ACTIVE = True
    try:
        line = json.dumps(dict(kind=kind, **values), default=str, sort_keys=True)
        if line not in SEEN:
            SEEN.add(line)
            with LOG.open('a') as stream:
                stream.write(line + '\n')
    finally:
        ACTIVE = False


def audit(event, args):
    if ACTIVE:
        return
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR):
            path = os.fsdecode(path)
            if str(WORK) in str(Path(path).absolute()):
                record('write', path=str(Path(path).absolute()))
    elif event in ('os.mkdir', 'os.symlink', 'os.link', 'os.rename'):
        path = args[1] if event != 'os.mkdir' else args[0]
        if isinstance(path, (str, bytes)) and str(WORK) in str(Path(os.fsdecode(path)).absolute()):
            record('create', path=str(Path(os.fsdecode(path)).absolute()))


OriginalPopen = subprocess.Popen


class RecordedPopen(OriginalPopen):
    def __init__(self, args, *extra, **kwargs):
        argv = list(map(str, args)) if isinstance(args, (tuple, list)) else args
        record('subprocess', argv=argv)
        if isinstance(argv, list) and Path(argv[0]).name.startswith('python'):
            index = next((i for i in range(1, len(argv)) if not argv[i].startswith('-')), None)
            if index is not None and argv[index].endswith('.py'):
                args = argv[:index] + [str(Path(__file__).resolve()), '--child'] + argv[index:]
        super().__init__(args, *extra, **kwargs)


def profile(frame, event, value):
    if event != 'call' or ACTIVE:
        return
    filename = frame.f_code.co_filename
    name = frame.f_code.co_name
    loc = frame.f_locals
    if filename.endswith('/proof/run.py'):
        if name in ('command', 'cloud', 'execv'):
            record('proof_boundary', function=name, argv=list(map(str, loc['argv'])))
        elif name == '__init__' and 'cmd' in loc:
            record('proof_boundary', function='chain_child', argv=list(map(str, loc['cmd'])))
        elif name == 'utility':
            spec = loc['spec']
            config = Path(os.environ['A_JOB_CONFIG'])
            root = config.parent.parent
            argv = [loc.get('python') or spec['interpreters']['p1cpu'], '-s', '-B',
                    str(root / 'bootstrap/trace_runtime.py'), '--root', str(root),
                    '--config', str(config), '--script', str(loc['script']),
                    *map(str, loc['args'])]
            record('utility_request', argv=argv,
                   note='Exact argv assembled by unchanged chain.utility; local proof substitutes its body.')


# This sandbox can leave asyncio thread completions waiting in epoll indefinitely.
# Bound idle waits only in this external local harness, including its children.
original_select = selectors.DefaultSelector.select
def bounded_select(self, timeout=None):
    return original_select(self, 0.1 if timeout is None else min(timeout, 0.1))
selectors.DefaultSelector.select = bounded_select
subprocess.Popen = RecordedPopen
if sys.argv[1:2] == ['--child']:
    sys.argv = sys.argv[2:]
    sys.path.insert(0, str(Path(sys.argv[0]).parent))
    runpy.run_path(sys.argv[0], run_name='__main__')
else:
    package = HERE / 'extracted'
    sys.path.insert(0, str(package / 'proof'))
    import run as proof
    patch_object = proof.patch.object
    def recorded_patch(target, attribute, *args, **kwargs):
        if args and callable(args[0]) and attribute in ('utility','run','Popen','execv','process_stream'):
            original = args[0]
            def call(*a, **kw):
                if attribute == 'utility':
                    spec, script, rest = a[:3]
                    config = Path(os.environ['A_JOB_CONFIG'])
                    root = config.parent.parent
                    argv = [kw.get('python') or spec['interpreters']['p1cpu'], '-s', '-B',
                        str(root/'bootstrap/trace_runtime.py'), '--root', str(root),
                        '--config', str(config), '--script', str(script), *map(str, rest)]
                    record('utility_request', argv=argv,
                        note='Exact argv assembled by unchanged chain.utility; local proof substitutes its body.')
                else:
                    argv = a[1] if attribute == 'execv' else a[0]
                    record('proof_boundary', function=attribute, argv=list(map(str,argv)))
                return original(*a, **kw)
            args = (call, *args[1:])
        return patch_object(target,attribute,*args,**kwargs)
    proof.patch.object = recorded_patch
    import faulthandler
    with (HERE/'stacks04.log').open('w') as stacks:
        faulthandler.dump_traceback_later(90, file=stacks)
        result = proof.run(WORK)
        faulthandler.cancel_dump_traceback_later()
    (HERE / 'proof_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
