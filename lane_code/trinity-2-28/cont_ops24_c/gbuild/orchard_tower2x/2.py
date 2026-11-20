import contextlib
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time


def digest(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, value):
    raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) >= 5_000_000:
        raise ValueError('E01')
    with Path(p).open('xb') as f:
        f.write(raw)
    return raw


def binding(row, arm):
    a = row['x4'][arm]
    if a is None:
        return None
    ids, hashes, slots = a['x0'], a['x1'], a['x2']
    if (len(ids) != (32, 64, 96)[arm] or len(set(ids)) != len(ids)
            or ids != sorted(ids) or len(hashes) != len(ids)
            or len(slots) != 32 or slots != sorted(set(slots))
            or slots[0] != 0 or slots[-1] >= len(ids)
            or [ids[s] for s in slots] != row['x4'][0]['x0']
            or [hashes[s] for s in slots] != row['x4'][0]['x1']):
        raise ValueError('E02')
    if arm and not set(row['x4'][arm-1]['x0']).issubset(ids):
        raise ValueError('E03')
    return ids, hashes, slots


def forecast(cfg):
    costs = cfg['x7']
    return costs[0] + costs[1] + costs[2] * sum(
        costs[3+i] for r in cfg['x3'] for i, a in enumerate(r['x4']) if a is not None) + costs[6]


class Engine:
    def __init__(self, cfg, stub):
        self.cfg, self.stub = cfg, stub
        self.unit = None
        if not stub:
            for p in cfg['x8']:
                sys.path.insert(0, p)
            self.np = importlib.import_module('numpy')
            self.pt = importlib.import_module('torch')
            if self.pt.cuda.device_count() != 1 or 'H100' not in self.pt.cuda.get_device_name(0):
                raise ValueError('E04')
            for p, h in cfg['x9']:
                if digest(p) != h:
                    raise ValueError('E05')
            z = cfg['xa']
            self.mod = importlib.import_module(z[0])
            if getattr(self.mod, z[1]) != z[2]:
                raise ValueError('E06')
            self.unit = getattr(self.mod, z[3])(cfg['xb'])
            self.unit._load()
            self.convert = getattr(importlib.import_module(z[4]), z[5])

    def run(self, row, arm):
        ids, hashes, slots = binding(row, arm)
        start = time.monotonic()
        if self.stub:
            h, w = row['x5']
            frames = [dict(shape=(h, w, 3), dtype='uint8') for _ in ids]
            if len(frames) != len(ids) or any(f['shape'] != (h, w, 3) for f in frames):
                raise ValueError('E07')
            c = [[[1., 0., 0., math.cos(i/10)], [0., 1., 0., math.sin(i/10)],
                  [0., 0., 1., i/100], [0., 0., 0., 1.]] for i in range(len(ids))]
            peak = reserved = 0
        else:
            from PIL import Image
            frames = []
            for h in hashes:
                p = Path(self.cfg['xc']) / h[:2] / (h + '.png')
                if digest(p) != h:
                    raise ValueError('E08')
                with Image.open(p) as im:
                    im.load()
                    if [im.height, im.width] != row['x5']:
                        raise ValueError('E09')
                    frames.append(im.convert('RGB'))
            self.pt.cuda.reset_peak_memory_stats()
            z = self.cfg['xd']
            setattr(self.unit, z[0], len(ids))
            batch = {z[1]: frames, z[2]: self.np.array(ids), z[3]: self.np.array(slots),
                     z[4]: self.np.array(row['x4'][0]['x0'])}
            value = self.unit.run(batch)
            if getattr(value, z[5]).shape != (len(ids), 9):
                raise ValueError('E10')
            r, t, _ = self.convert(getattr(value, z[5]), self.np.asarray(row['x2']))
            c = self.np.tile(self.np.eye(4), (len(ids), 1, 1))
            c[:, :3, :3], c[:, :3, 3] = r, t * row['x1']
            c = c.tolist()
            self.pt.cuda.synchronize()
            peak = self.pt.cuda.max_memory_allocated()
            reserved = self.pt.cuda.max_memory_reserved()
            del value, frames
        return dict(status='ok', ids=ids, sha256=hashes, slots=slots, c2w=c,
                    scale=row['x1'], gravity=row['x2'], seconds=time.monotonic()-start,
                    peak_bytes=peak, reserved_bytes=reserved,
                    rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def run(cfg, stub=False, only=None):
    started = time.monotonic()
    if forecast(cfg) > 1500:
        raise ValueError('E11')
    result = dict(schema=1, token=cfg['x0'], stub=stub, rows=[], complete=False,
                  estimate_seconds=forecast(cfg), error=None)
    try:
        load = time.monotonic()
        engine = Engine(cfg, stub)
        result['load_seconds'] = time.monotonic()-load
        result['load_peak_bytes'] = 0 if stub else engine.pt.cuda.max_memory_allocated()
        result['load_reserved_bytes'] = 0 if stub else engine.pt.cuda.max_memory_reserved()
        for row in cfg['x3'][:only]:
            out = dict(key=row['x0'], arms=[])
            result['rows'].append(out)
            for a in range(3):
                if row['x4'][a] is None:
                    out['arms'].append(dict(status='unavailable', reason='E12'))
                    continue
                if time.time() > cfg.get('xe', float('inf')) - 90:
                    raise TimeoutError('E13')
                out['arms'].append(engine.run(row, a))
        result['complete'] = True
    except Exception as e:
        result['error'] = type(e).__name__
    result['seconds'] = time.monotonic()-started
    return result


def main():
    p, out = map(Path, sys.argv[1:3])
    cfg = json.loads(p.read_text())
    stub = len(sys.argv) == 4 and sys.argv[3] == '0'
    with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        value = run(cfg, stub=stub, only=1 if stub else None)
    raw = write(out, value)
    write(out.with_suffix('.1.json'), dict(schema=1, token=cfg['x0'],
          input_sha256=digest(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
          complete=value['complete'], stub=stub, job=os.environ.get('SLURM_JOB_ID', '0')))
    return 0 if value['complete'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('E99', file=sys.stderr)
        raise SystemExit(1)
