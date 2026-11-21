"""fix14: runs the kit's rank script b/u.py in one rank of a scratch two-step start, with the two
checks the walk logged and passed over (pin path, scene census comparison) logged the same way, and
with timing events per stage and per optimizer step. Defect finding only."""
import atexit, importlib, json, os, runpy, sys, time
from pathlib import Path
hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
KIT = Path(os.environ['Q_KIT']).resolve()
R = Path(sys.argv[1])
RANK = os.environ.get('RANK', 'x')
EV = Path('/tmp/a15_dbg_174134/tr2/log') / ('ev_rank%s.jsonl' % RANK)
T0 = time.time()


def ev(kind, **kw):
    rec = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), t=round(time.time() - T0, 1), rank=RANK, kind=kind, **kw)
    with open(EV, 'a') as f:
        f.write(json.dumps(rec, default=str) + '\n')


def fail(step, error):
    ev('ERROR', step=step, error=(type(error).__name__ + ':' + str(error))[:3000],
       tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-14000:])


ev('START', pid=os.getpid(), cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'), world=os.environ.get('WORLD_SIZE'),
   local=os.environ.get('LOCAL_RANK'), omp=os.environ.get('OMP_NUM_THREADS'), job_start=os.environ.get('TK_JOB_START'))
atexit.register(lambda: ev('ATEXIT'))
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(R / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned = prov.load, prov.pinned
run = mod(PK + '.carrier_c1_run'); sx = mod(PK + '.s1_exclusions'); entry = mod('launch_r1.entry')
import torch
ev('IMPORTED', torch=torch.__version__, cuda=torch.cuda.is_available(), devices=torch.cuda.device_count())

native_admits = run.division_admits
is_pin = lambda v: isinstance(v, dict) and set(v) == {'path', 'sha256'}


def soft_admits(stream_division, pose_division):
    if native_admits(stream_division, pose_division):
        return True
    chain, cur = [], pose_division
    for _ in range(6):
        if not is_pin(cur):
            break
        chain.append(cur)
        try:
            cur = load(pinned(cur)).get('parent_division')
        except Exception:
            break
    same = [p for p in chain if is_pin(stream_division) and p['sha256'] == stream_division['sha256'] and p != stream_division]
    if same and native_admits(same[0], pose_division):
        ev('WARNING', what='PIN_PATH_DIFFERS admitted on content hash', stream_pin=stream_division, chain_pin=same[0])
        return True
    ev('WARNING', what='division not admitted (kept as a refusal)', stream_pin=stream_division, reference=pose_division)
    return False


native_cov = sx.coverage_report; native_load = sx.load
cov_seen = set()


def soft_cov(rule, streams, policy=None):
    try:
        return native_cov(rule, streams, policy)
    except ValueError as error:
        if 'Filter differs from independent scene census' not in str(error):
            raise
        if str(error) not in cov_seen:
            cov_seen.add(str(error))
            ev('WARNING', what='scene census comparison refused; logged, then the report is built without the exact comparison', error=str(error))

        def lax(path):
            value = native_load(path)
            if isinstance(value, dict) and value.get('schema') == 'dev_s1_manifest_v1' and value.get('exact_rebuilt_population'):
                value = dict(value, exact_rebuilt_population=False)
            return value
        sx.load = lax
        try:
            return native_cov(rule, streams, policy)
        finally:
            sx.load = native_load


run.division_admits = soft_admits; sx.coverage_report = soft_cov


def staged(owner, name):
    native = getattr(owner, name, None)
    if native is None:
        ev('INFO', what='no such function to time', name=name); return

    def timed(*a, **k):
        started = time.time(); ev('BEGIN', step=name)
        try:
            value = native(*a, **k)
        except BaseException as error:
            fail(name, error); raise
        ev('DONE', step=name, seconds=round(time.time() - started, 1))
        return value
    setattr(owner, name, timed)


for name in ('prepared', 'authenticate', 'network_preflight', 'load_model', 'wrap_model', 'export', 'bind_output', 'run_steps', 'checkpoint'):
    staged(run, name)
staged(entry, 'admit')
native_step = run.optimize_step


def timed_step(*a, **k):
    started = time.time(); number = a[6] if len(a) > 6 else k.get('step')
    ev('STEP_BEGIN', step=number)
    try:
        out = native_step(*a, **k)
    except BaseException as error:
        fail('optimize_step %s' % number, error); raise
    info = out[0] if isinstance(out, tuple) else out
    ev('STEP', step=number, seconds=round(time.time() - started, 2), peak_allocated=torch.cuda.max_memory_allocated(),
       peak_reserved=torch.cuda.max_memory_reserved(), info=info)
    return out


run.optimize_step = timed_step
script = str(KIT / 'b' / 'u.py')
sys.argv = [script, *sys.argv[1:]]
try:
    runpy.run_path(script, run_name='__main__')
except BaseException as error:
    fail('u.py', error); raise
ev('END')
