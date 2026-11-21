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
