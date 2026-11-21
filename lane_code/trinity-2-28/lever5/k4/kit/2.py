import hashlib
import importlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

# Per arm: frame count, nested gap points (sixths), source code (0 none, 1 extras, 2 all).
SPEC = ((32, (), 0), (32, (), 0), (32, (), 2), (63, (3,), 2), (94, (2, 4), 2), (63, (3,), 1), (94, (2, 4), 1))


def diagnostics():
    import importlib.util
    spec = importlib.util.spec_from_file_location('a9', Path(__file__).with_name('9.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def digest(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, value):
    raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) >= 3_200_000:
        raise ValueError('E01')
    with Path(p).open('xb') as f:
        f.write(raw)
    return raw


def binding(row, arm):
    a = row['x4'][arm]
    if a is None:
        return None
    count, parts, low = SPEC[arm]
    ids, hashes, slots = a['x0'], a['x1'], a['x2']
    base = row['x4'][0]
    if (len(ids) != count or ids != sorted(set(ids))
            or len(hashes) != len(ids) or len(slots) != 32 or slots != sorted(set(slots))
            or slots[0] != 0 or slots[-1] >= len(ids)
            or [ids[s] for s in slots] != base['x0']
            or any(len(a[k]) != len(ids) for k in ('x5', 'x6'))):
        raise ValueError('E02')
    anchors = base['x0']
    expected = anchors if not parts else sorted(anchors+[
        round(x+j*(y-x)/6) for x, y in zip(anchors, anchors[1:]) for j in parts])
    if ids != expected:
        raise ValueError('E03')
    held = set(slots)
    flags = [low == 2 or (low == 1 and i not in held) for i in range(len(ids))]
    if a['x5'] != flags:
        raise ValueError('E19')
    for i, (h, flag) in enumerate(zip(hashes, flags)):
        if len(h) != 64 or set(h) - set('0123456789abcdef'):
            raise ValueError('E19')
        if not flag and (i not in held or h != base['x1'][slots.index(i)] or a['x6'][i] != base['x6'][slots.index(i)]):
            raise ValueError('E19')
    if arm == 1 and a != base:
        raise ValueError('E19')
    return ids, hashes, slots


def tasks(cfg):
    return [(r, a) for a in cfg['xr'] for r in range(len(cfg['x3'])) if cfg['x3'][r]['x4'][a] is not None]


def cost(cfg, a):
    return cfg['x7'][2]*cfg['x7'][3+(32, 63, 94).index(SPEC[a][0])]+cfg['xs']


def forecast(cfg):
    return cfg['x7'][0]+cfg['x7'][1]+sum(cost(cfg, a) for _, a in tasks(cfg)[:cfg['xq']])+cfg['x7'][6]


def adapt(cfg):
    names = (cfg['xa'][0], cfg['xm'][5], cfg['xa'][4])
    mods = {}
    for i in (2, 1, 0):
        name = names[i]
        old, new, count = cfg['xp'][i]
        mod = importlib.import_module(name)
        p = Path(mod.__file__)
        if digest(p) != cfg['x9'][i][1]:
            raise ValueError('E04')
        raw = p.read_text()
        if raw.count(old) != count:
            raise ValueError('E05')
        exec(compile(raw.replace(old, new), str(p), 'exec'), mod.__dict__)
        mods[i] = mod
    return mods[0]


def images(cfg, row, arm, keep=True):
    import numpy as np
    from PIL import Image
    import PIL
    cv = importlib.import_module(cfg['xk'][2])
    versions = dict(cv2=cv.__version__, PIL=PIL.__version__, numpy=np.__version__)
    a = row['x4'][arm]
    frames, raw_hashes, matches = [], [], []
    started = time.monotonic()
    for h, low, expected in zip(a['x1'], a['x5'], a['x6']):
        root = Path(cfg['xl'] if low else cfg['xc'])
        p = root/(h+'.png') if low else root/h[:2]/(h+'.png')
        if not p.is_relative_to(root):
            raise ValueError('E06')
        if digest(p) != h:
            raise ValueError('E07')
        with Image.open(p) as im:
            im.load()
            im = im.convert('RGB')
            if low:
                if im.size != (256, 192):
                    raise ValueError('E08')
                im = Image.fromarray(np.ascontiguousarray(np.rot90(np.asarray(im), row['x6'])))
                if cfg['xk'][0] == 0:
                    im = im.resize(tuple(reversed(row['x5'])), cfg['xk'][1])
                else:
                    cv.setNumThreads(1)
                    im = Image.fromarray(cv.resize(np.asarray(im), tuple(reversed(row['x5'])), interpolation=cfg['xk'][1]))
            if [im.height, im.width] != row['x5']:
                raise ValueError('E09')
            raw_hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
            matches.append(raw_hashes[-1] == expected)
            if keep:
                frames.append(im.copy())
    return frames, raw_hashes, time.monotonic()-started, matches, versions


class Engine:
    def __init__(self, cfg, mode):
        self.cfg, self.mode = cfg, mode
        self.gpu = mode == 'gpu'
        for p in cfg['x8']:
            sys.path.insert(0, p)
        self.np = importlib.import_module('numpy')
        self.pt = importlib.import_module('torch')
        self.pt.set_num_threads(8)
        for p, h in cfg['x9']:
            if digest(p) != h:
                raise ValueError('E11')
        self.mod = adapt(cfg)
        z = cfg['xa']
        if getattr(self.mod, z[1]) != z[2]:
            raise ValueError('E12')
        self.convert = getattr(importlib.import_module(z[4]), z[5])
        if mode == 'stub':
            self.unit = self.fake()
        elif mode == 'cpu':
            self.unit = getattr(self.mod, z[3])(dict(cfg['xb'], device='cpu'))
            self.unit._load()
        else:
            if self.pt.cuda.device_count() != 1 or 'H100' not in self.pt.cuda.get_device_name(0):
                raise ValueError('E13')
            self.unit = getattr(self.mod, z[3])(cfg['xb'])
            self.unit._load()

    def fake(self):
        pt, z = self.pt, self.cfg['xm']
        class F(pt.nn.Module):
            def __init__(self, local):
                super().__init__()
                self.local = local
            def forward(self, value):
                n = value[0].shape[1]
                vals = [0., 0., 0., 1., 1., 1.2] if self.local else [0., 0., 0., 0., 1.]
                out = pt.tensor(vals).repeat(1, n, 1)
                if not self.local:
                    out[0, :, 0] = pt.arange(n)/100
                    out[0, :, 1] = pt.sin(pt.arange(n)/10)/10
                return [out]
        class D(pt.nn.Module):
            def forward(self, small, images, **kw):
                shape = (1, images.shape[1], 518, 518)
                return pt.ones(*shape, 1), pt.ones(shape)
        unit = pt.nn.Module()
        for key, value in zip(z[:5], [pt.nn.Identity(), F(True), F(False), D(), None]):
            setattr(unit, key, value)
        def aggregate(_, inputs):
            n = inputs.shape[1]
            if tuple(inputs.shape) != (1, n, 3, 518, 518) or not pt.isfinite(inputs).all():
                raise ValueError('E14')
            blocks = [None]*24
            for k in (4, 11, 17, 23):
                blocks[k] = pt.zeros(1, n, 1, 1)
            return blocks, 0
        setattr(importlib.import_module(z[5]), z[6], aggregate)
        settings = dict(self.cfg['xb'], device='cpu')
        return getattr(self.mod, self.cfg['xa'][3])(settings, module=unit)

    def run(self, row, arm):
        ids, hashes, slots = binding(row, arm)
        start = time.monotonic()
        frames, raw_hashes, decode_seconds, matches, versions = images(self.cfg, row, arm)
        z = self.cfg['xd']
        setattr(self.unit, z[0], len(ids))
        if self.gpu:
            self.pt.cuda.reset_peak_memory_stats()
        batch = {z[1]: frames, z[2]: self.np.array(ids), z[3]: self.np.array(slots),
                 z[4]: self.np.array(row['x4'][0]['x0'])}
        before = time.monotonic()
        value = self.unit.run(batch)
        if getattr(value, z[5]).shape != (len(ids), 9):
            raise ValueError('E15')
        r, t, _ = self.convert(getattr(value, z[5]), self.np.asarray(row['x2']))
        c = self.np.tile(self.np.eye(4), (len(ids), 1, 1))
        c[:, :3, :3], c[:, :3, 3] = r, t*row['x1']
        if not self.np.isfinite(c).all():
            raise ValueError('E18')
        if self.gpu:
            self.pt.cuda.synchronize()
        return dict(status='ok', ids=ids, sha256=hashes, raw_sha256=raw_hashes, slots=slots, c2w=c.tolist(),
                    raw_matches=matches, raw_match_count=sum(matches), decode_versions=versions,
                    scale=row['x1'], gravity=row['x2'], seconds=time.monotonic()-start,
                    decode_seconds=decode_seconds, inference_seconds=time.monotonic()-before,
                    shape=[len(ids), row['x5'][0], row['x5'][1], 3],
                    peak_bytes=self.pt.cuda.max_memory_allocated() if self.gpu else 0,
                    reserved_bytes=self.pt.cuda.max_memory_reserved() if self.gpu else 0,
                    rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def decode_all(cfg):
    out = []
    for row in cfg['x3']:
        arms = []
        for a in range(len(row['x4'])):
            if binding(row, a) is None:
                arms.append(None)
                continue
            _, raw_hashes, seconds, matches, versions = images(cfg, row, a, keep=False)
            arms.append(dict(raw_sha256=raw_hashes, raw_match_count=sum(matches), frames=len(raw_hashes),
                             seconds=seconds, decode_versions=versions))
        out.append(dict(key=row['x0'], arms=arms))
    return out


def run(cfg, mode='stub', only=None):
    started = time.monotonic()
    if forecast(cfg) > cfg['xv'][1] or cfg['xq'] < 1 or not cfg['xt']:
        raise ValueError('E16')
    rows = cfg['x3'][:1 if mode == 'cpu' else only]
    order = [0] if mode == 'cpu' else cfg['xr']
    result = dict(schema=3, token=cfg['x0'], stub=mode == 'stub', mode=mode, rows=[dict(key=r['x0'], arms=[
        dict(status='unavailable' if a is None else 'budget') for a in r['x4']]) for r in rows],
        complete=False, finished=False, estimate_seconds=forecast(cfg), error=None, ran=[])
    try:
        before = time.monotonic()
        engine = Engine(cfg, mode)
        result['load_seconds'] = time.monotonic()-before
        result['load_peak_bytes'] = engine.pt.cuda.max_memory_allocated() if engine.gpu else 0
        result['load_reserved_bytes'] = engine.pt.cuda.max_memory_reserved() if engine.gpu else 0
        end = cfg.get('xe', time.time()+cfg['xv'][0])
        stop = False
        for a in order:
            for i, row in enumerate(rows):
                if row['x4'][a] is None:
                    continue
                allowance = cost(cfg, a)
                actual = [v['seconds'] for rr in result['rows'] for v in rr['arms'] if v['status'] == 'ok']
                if actual:
                    allowance = max(allowance, max(actual)*1.5)
                if engine.gpu and time.time()+allowance+cfg['x7'][6] > end:
                    stop = True
                    break
                result['rows'][i]['arms'][a] = engine.run(row, a)
                result['ran'].append([i, a])
            if stop:
                break
        if mode == 'cpu':
            before = time.monotonic()
            result['decoded'] = decode_all(cfg)
            result['decode_all_seconds'] = time.monotonic()-before
            result['complete'] = result['rows'][0]['arms'][0]['status'] == 'ok'
        else:
            result['complete'] = all(v['status'] in ('ok', 'unavailable') for r in result['rows'] for v in r['arms'])
        result['finished'] = True
    except Exception as e:
        result['error'] = type(e).__name__
        result['error_detail'] = diagnostics().detail(e)
        if cfg.get('xu'):
            diagnostics().record(cfg['xu'], result['error_detail'])
        if isinstance(e, TimeoutError):
            result['finished'] = True
    result['raw_match_count'] = sum(a.get('raw_match_count', 0) for r in result['rows'] for a in r['arms'])
    result['raw_frame_count'] = sum(len(a.get('raw_sha256', [])) for r in result['rows'] for a in r['arms'])
    result['seconds'] = time.monotonic()-started
    return result


def main():
    p, out = map(Path, sys.argv[1:3])
    cfg = json.loads(p.read_text())
    mode = {'0': 'stub', '1': 'cpu'}.get(sys.argv[3]) if len(sys.argv) == 4 else 'gpu'
    if mode is None:
        raise ValueError('E31')
    def alarm(*args):
        raise TimeoutError('E17')
    if mode != 'stub' and 'xe' in cfg:
        signal.signal(signal.SIGALRM, alarm)
        signal.alarm(max(1, int(cfg['xe']-time.time()-60)))
    value = run(cfg, mode=mode, only=1 if mode == 'stub' else None)
    signal.alarm(0)
    raw = write(out, value)
    write(out.with_suffix('.1.json'), dict(schema=3, token=cfg['x0'], input_sha256=digest(p),
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=value['complete'], stub=mode == 'stub',
        mode=mode, job=os.environ.get('SLURM_JOB_ID', '0')))
    return 0 if value['finished'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        diagnostics().record(Path(sys.argv[2]).with_name('9.err'), diagnostics().detail(exc))
        print('E99', file=sys.stderr)
        raise SystemExit(1)
