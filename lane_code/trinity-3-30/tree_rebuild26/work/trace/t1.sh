set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B=$W/w26trace; K=$W/w24/work/build24k
hostname -s
[ -e $B ] && { echo "w26trace exists; stop"; exit 1; }
mkdir -p $B/src $B/s
cat > $B/src/cudatrace.py <<'PYEOF'
"""Record every CUDA-driver query; stacks kept when CUDA_VISIBLE_DEVICES == ''."""
import os, sys, json, threading, traceback, time, functools
OUT = os.environ['CT_OUT']
STATE = dict(stage='init', empty_calls={}, set_calls={}, libcuda=None, nvml=None, events=[])
def _key(stack):
    return '\n'.join(stack[-14:])
def flush():
    with open(OUT, 'w') as f:
        json.dump(STATE, f, indent=1, default=str)
def record(name):
    v = os.environ.get('CUDA_VISIBLE_DEVICES')
    if v == '':
        st = [l.rstrip() for l in traceback.format_stack()[:-2]]
        k = name + '|' + _key(st)
        e = STATE['empty_calls'].setdefault(k, dict(name=name, stage=STATE['stage'], count=0, stack=st[-14:]))
        e['count'] += 1
    else:
        STATE['set_calls'][name+'|'+str(v)] = STATE['set_calls'].get(name+'|'+str(v), 0) + 1
    flush()
def wrap(owner, attr, label):
    f = getattr(owner, attr, None)
    if f is None or getattr(f, '_ct', False):
        return False
    @functools.wraps(f)
    def g(*a, **k):
        record(label)
        return f(*a, **k)
    g._ct = True
    try:
        setattr(owner, attr, g); return True
    except Exception:
        return False
import torch
STATE['libcuda_after_torch_import'] = any('libcuda.so' in l for l in open('/proc/self/maps'))
STATE['torch'] = torch.__version__; STATE['torch_cuda'] = torch.version.cuda
wrapped = []
for a in ('_cuda_getDeviceCount', '_cuda_init', '_cuda_getDevice', '_cuda_setDevice', '_cuda_getDeviceProperties' ):
    if wrap(torch._C, a, 'torch._C.'+a): wrapped.append('torch._C.'+a)
for a in ('is_available', 'device_count', '_lazy_init', 'init', 'current_device', 'set_device',
          'get_device_properties', 'get_device_name', 'get_device_capability', 'is_bf16_supported',
          'synchronize', 'mem_get_info', 'memory_allocated', 'get_rng_state', 'get_rng_state_all',
          '_device_count_nvml', '_raw_device_count_nvml', '_device_count_amdsmi', 'is_initialized',
          'get_arch_list', 'current_stream'):
    if wrap(torch.cuda, a, 'torch.cuda.'+a): wrapped.append('torch.cuda.'+a)
try:
    import torch.backends.cudnn as cudnn
    for a in ('is_available', 'version'):
        if wrap(cudnn, a, 'cudnn.'+a): wrapped.append('cudnn.'+a)
except Exception as e:
    STATE['events'].append('cudnn wrap failed %r' % e)
try:
    import triton, triton.runtime
    STATE['triton'] = triton.__version__
    d = triton.runtime.driver; cls = type(d)
    for a in ('active', 'default'):
        p = cls.__dict__.get(a)
        if isinstance(p, property):
            def mk(p, a):
                def fget(self):
                    record('triton.runtime.driver.'+a); return p.fget(self)
                return property(fget, p.fset)
            setattr(cls, a, mk(p, a)); wrapped.append('triton.runtime.driver.'+a)
    for a in ('set_active', 'reset_active'):
        if wrap(d, a, 'triton.runtime.driver.'+a): wrapped.append('triton.runtime.driver.'+a)
except Exception as e:
    STATE['events'].append('triton wrap: %r' % e)
STATE['wrapped'] = wrapped
MAIN = threading.main_thread().ident
def poll():
    while True:
        try:
            m = open('/proc/self/maps').read()
        except Exception:
            m = ''
        for lib, slot in (('libcuda.so', 'libcuda'), ('libnvidia-ml', 'nvml')):
            if STATE[slot] is None and lib in m:
                fr = sys._current_frames().get(MAIN)
                STATE[slot] = dict(stage=STATE['stage'], env=os.environ.get('CUDA_VISIBLE_DEVICES'),
                                   approx_stack=[l.rstrip() for l in traceback.format_stack(fr)][-14:] if fr else None)
                flush()
        time.sleep(0.02)
threading.Thread(target=poll, daemon=True).start()
def stage(name):
    STATE['stage'] = name; STATE['events'].append('%s stage %s' % (time.strftime('%H:%M:%S'), name)); flush()
flush()
PYEOF
cat > $B/src/slice.py <<'PYEOF'
import os, sys, json, traceback, importlib, ast, time
from pathlib import Path
base = Path(os.environ['CT_BASE']); S = base/'s'; KIT = Path(os.environ['CT_KIT'])
sys.path.insert(0, str(base/'src'))
import cudatrace as ct
ST = ct.STATE; ST['results'] = {}
def mods_before(): return set(sys.modules)
def imp(names, label):
    before = mods_before(); res = {}
    for n in names:
        try:
            importlib.import_module(n); res[n] = 'ok'
        except BaseException as e:
            res[n] = '%s: %s' % (type(e).__name__, str(e)[:200])
    new = sorted({m.split('.')[0] for m in set(sys.modules) - before})
    ST['results'][label] = dict(imports=res, new_top_packages=new); ct.flush()
sys.path.insert(0, str(S))
# a.py top: kit/b modules and launch_r1 / p3_provenance / r1_persisted
sys.path.insert(1, str(KIT/'b'))
ct.stage('A_apy_imports')
imp(['z', 'pl', 'rb', 'launch_r1.build', 'launch_r1.entry', 'student_pilot.p3_provenance',
     'student_pilot.r1_persisted', 'student_pilot.s1_admission', 'launch_r1.production_proof'], 'A_apy_imports')
# _run's lazy imports before admit, with the variable as the job would have it (here '' by rule)
ct.stage('B_run_pre_admit_imports')
imp(['student_pilot.r1_coverage', 'student_pilot.r1_rooms', 'student_pilot.r1_direction_twins',
     'student_pilot.r1_training', 'launch_r1.p_opener_witness', 'student_pilot.r1_handover',
     'student_pilot.r1_population', 'student_pilot.r1_loader', 'student_pilot.source_seal',
     'student_pilot.carrier_c1_run'], 'B_run_pre_admit_imports')
# Mirror production_proof.py:438-447 around the real admit()
import student_pilot.s1_admission as adm
from student_pilot.p3_provenance import file_pin
out = base/'admit_out'; out.mkdir(exist_ok=True)
cfgfile = None
for c in os.environ.get('CT_FIXTURES', '').split(':'):
    if c and Path(c).is_file(): cfgfile = Path(c); break
if cfgfile is None:
    cfgfile = base/'empty_cfg.json'; cfgfile.write_text('{}')
ST['admit_config'] = str(cfgfile)
frames = base/'frames'; frames.mkdir(exist_ok=True)
ct.stage('C_admit_real_call')
visible = os.environ.get('CUDA_VISIBLE_DEVICES'); os.environ['CUDA_VISIBLE_DEVICES'] = ''
try:
    r = adm.admit(file_pin(cfgfile), out, [str(frames)], threads=8, memory_gib=15, prepare_only=True)
    ST['results']['C_admit_real_call'] = dict(status='returned', keys=sorted(r)[:20])
except BaseException as e:
    tb = traceback.format_exc().splitlines()
    ST['results']['C_admit_real_call'] = dict(status='raised', error='%s: %s' % (type(e).__name__, str(e)[:300]), tb=tb[-12:])
finally:
    if visible is None: os.environ.pop('CUDA_VISIBLE_DEVICES', None)
    else: os.environ['CUDA_VISIBLE_DEVICES'] = visible
ct.flush()
# Every module named by a function-level import in modules on admit's path (over-approximation)
ct.stage('D_admit_function_level_imports')
roots = ['s1_admission', 'carrier_c1_data', 'carrier_c1_run', 'rehearsal', 'first_batch_progress', 's1_exclusions',
         'r1_coverage', 'mdg_parent', 's1_routing', 'r1_routing', 'r1_handover', 'row_removals', 'orchard_paths',
         'grounding_train', 'p3_provenance', 'job_env']
targets = set()
for r in roots:
    p = S/'student_pilot'/(r+'.py')
    if not p.is_file(): continue
    for node in ast.walk(ast.parse(p.read_text())):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.col_offset > 0:
            if isinstance(node, ast.Import):
                targets.update(a.name for a in node.names)
            elif node.level:
                if node.module: targets.add('student_pilot.'+node.module)
                else: targets.update('student_pilot.'+a.name for a in node.names)
            else:
                targets.add(node.module)
ST['D_targets'] = sorted(targets)
os.environ['CUDA_VISIBLE_DEVICES'] = ''
imp(sorted(targets), 'D_admit_function_level_imports')
# Third-party probes named in the brief
ct.stage('E_third_party_probes')
imp(['transformers', 'transformers.models.qwen3_5', 'transformers.models.qwen3_5.modeling_qwen3_5',
     'fla', 'fla.ops', 'triton', 'torch.utils.data'], 'E_third_party_probes')
try:
    from transformers import AutoProcessor  # noqa
    ST['results']['E_autoprocessor_symbol'] = 'ok'
except BaseException as e:
    ST['results']['E_autoprocessor_symbol'] = repr(e)[:200]
ct.stage('F_end')
import torch
ST['final'] = dict(cuda_initialized=torch.cuda.is_initialized.__wrapped__() if hasattr(torch.cuda.is_initialized, '__wrapped__') else None,
                   cached_device_count=getattr(torch.cuda, '_cached_device_count', 'n/a'),
                   libcuda_mapped=any('libcuda.so' in l for l in open('/proc/self/maps')),
                   fla_loaded='fla' in sys.modules, triton_loaded='triton' in sys.modules,
                   transformers_loaded='transformers' in sys.modules)
ct.flush()
print('DONE')
PYEOF
echo "== tar size"; ls -la $W/w26fix/n_go/k/t_e047002134f979bd.tar
tar tf $W/w26fix/n_go/k/t_e047002134f979bd.tar | grep -c . ; tar tf $W/w26fix/n_go/k/t_e047002134f979bd.tar | grep '^launch_s1/b/q0' 
nice -n 10 tar xf $W/w26fix/n_go/k/t_e047002134f979bd.tar -C $B/s && echo extracted
echo "== fixture candidates"; ls $K/rehearsal_k6/p $K/rehearsal_k6/p2 2>&1 | head -20
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR=$B/tmp XDG_CACHE_HOME=$B/tmp/cache HF_HOME=$B/tmp/hf TORCH_HOME=$B/tmp/torch TRITON_CACHE_DIR=$B/tmp/triton
mkdir -p $TMPDIR
export CT_OUT=$B/trace.json CT_BASE=$B CT_KIT=$W/w26fix/n_go CT_FIXTURES=$K/rehearsal_k6/p/c.json:$K/rehearsal_k6/p2/c.json
cd $B
( ulimit -v 16000000; timeout 600 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B -s $B/src/slice.py > $B/slice.log 2>&1; echo "exit $?" >> $B/slice.log )
echo "== slice.log"; tail -c 4000 $B/slice.log
echo "== trace.json"; head -c 300000 $B/trace.json
