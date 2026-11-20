"""Trace exact source bytes; isolate every nested Python through the same launcher."""
import sys, os, json, hashlib, runpy, atexit, threading
from pathlib import Path
T = Path(__file__).resolve().parent
sys.path.insert(0, str(T))
from common import limits, sha
limits()
seen = set()
lines = {}
KIT_PREFIX = str(T.parent/'kit/b')+'/'
def event(kind, **values):
    p = T/'traces'/('python-'+os.environ.get('SLURM_JOB_ID','none')+'-'+str(os.getpid())+'.jsonl')
    with p.open('a') as f:
        f.write(json.dumps(dict(event=kind, pid=os.getpid(), **values), default=str, sort_keys=True)+'\n')

def audit(name, args):
    if name == 'exec':
        path = getattr(args[0], 'co_filename', '')
        if path not in seen and Path(path).is_file():
            seen.add(path)
            event('executable_source', path=path, sha256=sha(path))
    elif name == 'subprocess.Popen':
        event(name, executable=args[0], argv=args[1])
    elif name.startswith('socket.'):
        event(name, args=repr(args), threads=len(list(Path('/proc/self/task').iterdir())))

def trace(frame, kind, arg):
    filename = frame.f_code.co_filename
    if filename.startswith(KIT_PREFIX):
        if kind == 'line':
            lines.setdefault(filename, set()).add(frame.f_lineno)
        elif kind == 'exception':
            event('exception', file=filename, line=frame.f_lineno, type=arg[0].__name__, message=str(arg[1]))
        elif kind == 'call' and filename.endswith('/gc.py'):
            event('gc_call', function=frame.f_code.co_name, line=frame.f_lineno)
        return trace
    return None

def finish():
    event('coverage', files={p: sorted(v) for p, v in lines.items()})
    event('runtime', nice=os.getpriority(os.PRIO_PROCESS, 0), affinity=sorted(os.sched_getaffinity(0)),
          threads=len(list(Path('/proc/self/task').iterdir())))

sys.addaudithook(audit)
sys.settrace(trace)
threading.settrace(trace)
atexit.register(finish)
event('python_start', binary=sys.executable, sha256=sha(sys.executable), launcher_sha256=sha(__file__), flags=str(sys.flags), argv=sys.argv)
# pc.py invokes sys.executable with only -B. This transparent launcher enforces
# the requested -I -s -B on its unmodified gc.py child and records transport.
sys.executable = str(T/'bin/python3')
args = sys.argv[1:]
while args and args[0] in ('-I', '-s', '-B', '-E', '-S'):
    args = args[1:]
if args[0] == '-c':
    sys.argv = ['-c']+args[2:]
    exec(compile(args[1], '<command>', 'exec'), {'__name__': '__main__'})
elif args[0] == '-m':
    sys.argv = args[1:]
    runpy.run_module(args[1], run_name='__main__', alter_sys=True)
else:
    sys.argv = args
    runpy.run_path(args[0], run_name='__main__')
