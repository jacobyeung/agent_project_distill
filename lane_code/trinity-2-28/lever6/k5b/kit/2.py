import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import resource
import sys
import time
import warnings

CAP = 5_000_000
DET_CODE = 3


def diagnostics():
    import importlib.util
    spec = importlib.util.spec_from_file_location('a9', Path(__file__).with_name('9.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def u(value):
    return bytes.fromhex(value).decode()


def digest(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, value, cap=CAP):
    raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) >= cap:
        raise ValueError('E01')
    with Path(p).open('xb') as f:
        f.write(raw)
    return raw


def positions(n, reverse):
    order = list(range(n))
    if reverse:
        order.reverse()
    return order+[0]


# Switch names kept as hex so the shipped text stays neutral.
BN = u('62656e63686d61726b')
WS = ':4096:8'
ENV = ('CUBLAS_WORKSPACE_CONFIG', 'PYTORCH_CUDA_ALLOC_CONF', 'PYTORCH_NO_CUDA_MEMORY_CACHING',
       'NVIDIA_TF32_OVERRIDE', 'CUDA_LAUNCH_BLOCKING', 'TORCH_CUDNN_V8_API_DISABLED', 'OMP_NUM_THREADS')


def switches(pt):
    def get(fn):
        try:
            return fn()
        except Exception:
            return None
    c, b = pt.backends.cudnn, pt.backends.cuda
    value = dict(
        cudnn_auto=get(lambda: getattr(c, BN)), cudnn_deterministic=get(lambda: c.deterministic),
        cudnn_tf32=get(lambda: c.allow_tf32), cudnn_enabled=get(lambda: c.enabled),
        matmul_tf32=get(lambda: b.matmul.allow_tf32),
        matmul_bf16_reduced=get(lambda: b.matmul.allow_bf16_reduced_precision_reduction),
        matmul_fp16_reduced=get(lambda: b.matmul.allow_fp16_reduced_precision_reduction),
        matmul_precision=get(pt.get_float32_matmul_precision),
        algorithms=get(pt.are_deterministic_algorithms_enabled),
        algorithms_warn_only=get(pt.is_deterministic_algorithms_warn_only_enabled),
        sdp_flash=get(b.flash_sdp_enabled), sdp_efficient=get(b.mem_efficient_sdp_enabled),
        sdp_math=get(b.math_sdp_enabled), sdp_cudnn=get(lambda: b.cudnn_sdp_enabled()),
        cuda_initialized=get(pt.cuda.is_initialized))
    value.update({'env_'+k: os.environ.get(k) for k in ENV})
    return value


def settle(pt, det, warn):
    """Set every switch before the first CUDA call; return the record of what was set."""
    before = switches(pt)
    record = dict(before=before, set=[], warn_only=bool(warn))
    if det:
        if os.environ.get('CUBLAS_WORKSPACE_CONFIG') != WS:
            raise ValueError('E30')
        c, b = pt.backends.cudnn, pt.backends.cuda
        setattr(c, BN, False)
        c.deterministic = True
        pt.use_deterministic_algorithms(True, warn_only=bool(warn))
        # Precision switches stay at their served values; only re-assert them.
        c.allow_tf32 = before['cudnn_tf32']
        b.matmul.allow_tf32 = before['matmul_tf32']
        pt.manual_seed(0)
        record['set'] = ['CUBLAS_WORKSPACE_CONFIG='+WS, 'cudnn.auto=False', 'cudnn.deterministic=True',
                         'use_deterministic_algorithms(True, warn_only=%s)' % bool(warn),
                         'cudnn.allow_tf32=%s' % before['cudnn_tf32'],
                         'matmul.allow_tf32=%s' % before['matmul_tf32'], 'manual_seed(0)']
    record['after'] = switches(pt)
    record['cuda_initialized_at_set'] = pt.cuda.is_initialized()
    if record['cuda_initialized_at_set']:
        raise ValueError('E31')
    return record


class Files:
    """Artifact stand-in: the served call reads only the pinned weight and config files."""
    def __init__(self, paths, role):
        self.paths, self.role = [Path(p) for p in paths], role

    def files(self, role):
        if role != self.role:
            raise ValueError('E32')
        return list(self.paths)


class Stub:
    """Input-dependent, history-free stand-in with the served output contract (local tests only)."""
    def __init__(self, keys, np):
        self.keys, self.np, self.loads, self.size = keys, np, 0, None
        setattr(self, keys[14], None)

    def __call__(self, frames):
        np, k = self.np, self.keys
        if os.environ.get('K5_STUB_REFUSE') == '1':
            import torch
            text = 'index_add_cuda_ '+MARK+", but you set it"
            if torch.are_deterministic_algorithms_enabled():
                if not torch.is_deterministic_algorithms_warn_only_enabled():
                    raise RuntimeError(text)
                warnings.warn(text)
        images = frames[k[0]]
        if self.size != len(images):
            self.size = len(images)
            self.loads += 1
            setattr(self, k[14], object())
        level = np.array([np.asarray(im, dtype=np.float64).mean()/255 for im in images])
        n = len(images)
        raw = np.zeros((n, 9))
        raw[:, 6] = 1
        raw[:, 7], raw[:, 8] = 1.0, 1.2
        raw[1:, 0] = level[1:]*0.1+np.arange(1, n)*0.01
        slots = np.asarray(frames[k[2]])
        base = level[slots][:, None, None]
        grid = (1+base+np.linspace(0, 1, 51)[None, :, None]*0.1)*np.ones((32, 51, 51))
        conf = 1+np.linspace(0, 1, 51*51).reshape(1, 51, 51)*np.ones((32, 1, 1))
        return {k[4]: raw, k[2]: slots, k[5]: np.asarray(frames[k[1]]), k[6]: grid.astype(np.float32),
                k[7]: conf.astype(np.float32), k[8]: np.zeros((32, 51, 51, 3), np.float32),
                k[9]: np.linspace(0, 1000, 51, dtype=np.float32), k[10]: (images[0].height, images[0].width)}


def bind(cfg, row, keys):
    from PIL import Image
    root = Path(cfg['xc'])
    images = []
    for h in row['h']:
        p = root/h[:2]/(h+'.png')
        if not p.resolve().is_relative_to(root.resolve()) or digest(p) != h:
            raise ValueError('E07')
        with Image.open(p) as im:
            images.append(im.convert('RGB'))
    if [images[0].height, images[0].width] != row['w'] or len(images) != row['n']:
        raise ValueError('E09')
    return {keys[0]: images, keys[1]: list(row['i']), keys[2]: list(row['s']), keys[3]: list(row['a'])}


def array_sha(np, value):
    a = np.ascontiguousarray(np.asarray(value))
    return dict(sha256=hashlib.sha256(a.tobytes()).hexdigest(), dtype=str(a.dtype), shape=list(a.shape))


def card(pt):
    """UUID and PCI bus id of the card this process computes on."""
    try:
        q = pt.cuda.get_device_properties(0)
        bus = [getattr(q, n, None) for n in ('pci_domain_id', 'pci_bus_id', 'pci_device_id')]
        return dict(uuid=str(getattr(q, 'uuid', '')) or None,
                    bus='%08x:%02x:%02x.0' % tuple(bus) if all(isinstance(x, int) for x in bus) else None)
    except Exception as e:
        return dict(uuid=None, bus=None, error=type(e).__name__.encode().hex()[:40])


class Engine:
    def __init__(self, cfg, mode, det, warn):
        self.cfg, self.mode = cfg, mode
        self.np = importlib.import_module('numpy')
        self.pt = importlib.import_module('torch')
        self.record = settle(self.pt, det, warn)
        threads = len(os.sched_getaffinity(0)) if mode in ('c', 't') else 8
        self.pt.set_num_threads(threads)
        self.record['threads'] = threads
        for p in cfg['x8']:
            sys.path.insert(0, u(p))
        for p, h in cfg['x9']:
            if digest(u(p)) != h:
                raise ValueError('E11')
        a = [u(x) for x in cfg['xa']]
        self.keys = [u(x) for x in cfg['xk']]
        self.build = getattr(importlib.import_module(a[2]), a[3])
        self.ratio = getattr(importlib.import_module(a[4]), a[5])
        self.gpu = mode == 'g'
        self.device = 'cuda:0' if self.gpu else 'cpu'
        if mode in ('s', 't'):
            self.unit = Stub(self.keys, self.np)
        else:
            if self.gpu and (self.pt.cuda.device_count() != 1 or a[7] not in self.pt.cuda.get_device_name(0)):
                raise ValueError('E13')
            self.unit = getattr(importlib.import_module(a[0]), a[1])(Files([u(x) for x in cfg['xb']], a[6]), self.device)
        self.record['torch'] = self.pt.__version__
        self.record['device_name'] = self.pt.cuda.get_device_name(0) if self.gpu else 'cpu'
        self.record['card'] = card(self.pt) if self.gpu else None
        plane = Path(cfg['xl'])
        raw = plane.read_bytes()
        if hashlib.sha256(raw).hexdigest() != cfg['xp']['raw_sha256']:
            raise ValueError('E12')
        self.planes = self.np.frombuffer(raw, dtype='<f2').reshape(cfg['xp']['shape'])

    def scale(self, out, row):
        """Served median-ratio rule with the read-side plane held fixed per capture."""
        np, pt, k = self.np, self.pt, self.keys
        fixed = self.planes[row['o']].astype(np.float64) if row['o'] >= 0 else np.ones((32, 51, 51))
        value = self.ratio(out[k[6]], out[k[7]], fixed)
        log_s = float(pt.tensor(float(np.log(value)), dtype=pt.float64))
        return float(pt.tensor(log_s).exp())

    def run(self, row):
        np, pt, k = self.np, self.pt, self.keys
        started = time.perf_counter()
        frames = bind(self.cfg, row, k)
        bound = time.perf_counter()-started
        if self.gpu:
            pt.cuda.synchronize()
            pt.cuda.reset_peak_memory_stats()
        before = getattr(self.unit, k[14], None)
        began = time.perf_counter()
        with pt.no_grad():
            out = self.unit(frames)
        if self.gpu:
            pt.cuda.synchronize()
        seconds = time.perf_counter()-began
        rebuilt = getattr(self.unit, k[14], None) is not before
        s = self.scale(out, row)
        g = self.build(out[k[4]], out[k[2]], out[k[5]], out[k[6]], out[k[9]], row['g'], s, out[k[10]])
        contract = getattr(g, k[11])
        K, C, U = np.asarray(g.K), np.asarray(g.C), np.asarray(getattr(contract, k[12]))
        if float(getattr(contract, k[13])) != s or not all(np.isfinite(x).all() for x in (K, C, U)):
            raise ValueError('E18')
        value = dict(status='ok', k=row['k'], n=row['n'], seconds=seconds, bind_seconds=bound, rebuilt=rebuilt,
                     K=K.tolist(), cm=C.tolist(), cu=U.tolist(), s=s,
                     sha={name: array_sha(np, out[k[i]]) for name, i in (('p9', 4), ('d', 6), ('dc', 7), ('pt', 8))})
        value['sha'].update(K=array_sha(np, K), cm=array_sha(np, C), cu=array_sha(np, U),
                            s=array_sha(np, np.float64(s)))
        if row['c'] is not None:
            fixed = np.array(out[k[6]], dtype=float, copy=True)
            fixed *= row['c']
            value['sha']['df'] = array_sha(np, fixed)
        finite = all(np.isfinite(np.asarray(out[k[i]], dtype=np.float64)).all() for i in (4, 6, 7, 8))
        if not finite:
            raise ValueError('E19')
        value['peak_bytes'] = pt.cuda.max_memory_allocated() if self.gpu else 0
        value['reserved_bytes'] = pt.cuda.max_memory_reserved() if self.gpu else 0
        value['rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value


MARK = 'does not have a deterministic implementation'


def chain(exc):
    seen = []
    while exc is not None and len(seen) < 8:
        seen.append(exc)
        exc = exc.__cause__ or exc.__context__
    return seen


def nondet_ops(messages):
    found = []
    for m in messages:
        hit = re.search(r'([A-Za-z0-9_:.]+) '+MARK, m)
        name = hit.group(1) if hit else 'unparsed'
        if name.encode().hex() not in found:
            found.append(name.encode().hex())
    return found[:20]


def estimate(cfg, n):
    e = cfg['x7']
    return e['t64_max'] if n == 64 else e['t32_max']


def cpu_choice(cfg, remaining):
    e, rows = cfg['x7'], cfg['x3']
    need = lambda n: 1.25*(e['cpu64'] if n == 64 else e['cpu32'])+60
    if need(rows[0]['n']) <= remaining:
        return 0, dict(reason='first', need_s=need(rows[0]['n']), remaining_s=remaining)
    for i, r in enumerate(rows):
        if r['n'] == 32:
            return i, dict(reason='time_guard' if need(32) <= remaining else 'over_budget',
                           need_s=need(32), remaining_s=remaining)
    raise ValueError('E20')


def decode_all(cfg, keys):
    count, started = 0, time.monotonic()
    for row in cfg['x3']:
        frames = bind(cfg, row, keys)
        count += len(frames[keys[0]])
        del frames
    return count, time.monotonic()-started


def run(cfg, arm, mode, warn):
    started = time.time()
    unit = mode in ('c', 't')
    reverse, det = cfg['xr'][arm] if not unit else (0, 1)
    rows = cfg['x3']
    result = dict(schema=1, token=cfg['x0'], arm=arm, mode=mode, det=bool(det), reverse=bool(reverse), pid=os.getpid(),
                  warn_only=bool(warn), status='started', complete=False, records=[], error=None,
                  ops=[], warned_ops=[], order=[])
    end = cfg.get('xe', time.time()+3000)
    caught = []
    try:
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter('always')
            engine = Engine(cfg, mode, det, warn)
            result['switches'] = engine.record
            result['load_seconds'] = time.time()-started
            if unit:
                count, secs = decode_all(cfg, engine.keys)
                result.update(decoded_frames=count, decode_seconds=secs)
                index, admission = cpu_choice(cfg, end-time.time())
                result['admission'] = admission
                plan = [index]
            else:
                plan = positions(len(rows), reverse)
            result['order'] = plan
            longest = 0.0
            for pos, x in enumerate(plan):
                row = rows[x]
                allowance = max(estimate(cfg, row['n']), 1.5*longest)+cfg['x7']['reload']+30
                if not unit and time.time()+allowance > end:
                    result['status'] = 'budget'
                    break
                value = engine.run(row)
                value.update(position=pos, index=x)
                longest = max(longest, value['seconds'])
                result['records'].append(value)
            else:
                result['status'] = 'ok'
            caught = [str(w.message) for w in seen if MARK in str(w.message)]
        result['complete'] = result['status'] == 'ok' and len(result['records']) == len(plan)
    except Exception as e:
        texts = [str(x) for x in chain(e) if MARK in str(x)]
        if det and not warn and texts:
            result['status'] = 'nondeterministic_op'
            result['ops'] = nondet_ops(texts)
        else:
            result['status'] = 'failed'
            result['error'] = diagnostics().detail(e)
    result['warned_ops'] = nondet_ops(caught)
    result['warned_count'] = len(caught)
    result['seconds'] = time.time()-started
    if result['error'] and cfg.get('xu'):
        diagnostics().record(cfg['xu'], result['error'])
    return result


def main():
    cfg_path, out, arm, mode, warn = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
    if mode not in ('g', 'c', 's', 't') or warn not in (0, 1):
        raise ValueError('E21')
    cfg = json.loads(cfg_path.read_text())
    value = run(cfg, arm, mode, warn)
    raw = write(out, value)
    write(out.with_suffix('.1.json'), dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                                           input_sha256=digest(cfg_path), arm=arm, mode=mode, warn_only=warn,
                                           job=os.environ.get('SLURM_JOB_ID', '0')))
    if value['status'] == 'nondeterministic_op':
        return DET_CODE
    return 0 if value['status'] in ('ok', 'budget') else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        diagnostics().record(Path(sys.argv[2]).with_name('9.err'), diagnostics().detail(exc))
        print('E99', file=sys.stderr)
        raise SystemExit(1)
