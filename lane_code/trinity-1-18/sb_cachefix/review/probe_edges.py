"""Refute probes: full StageOne.features chain (lift, link, scene_candidates, accept_features, candidate_vectors)
on unpatched A4 bytes against the patched copy, for edge inputs the shipped tests do not cover."""
import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np

A4 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4/src')
PATCHED = Path('/scratch/jjyeung/orch_n30/sb_cachefix/work/patched/src/tree/student_pilot')
sys.path.insert(0, str(A4/'b/heads/selector/sl118'))
import selector_inputs as SI  # noqa: E402


def package(name, folder):
    pkg = types.ModuleType(name)
    pkg.__path__ = [str(folder)]
    sys.modules[name] = pkg
    mods = {}
    for module in ('routed_candidates', 'routed_features'):
        spec = importlib.util.spec_from_file_location(f'{name}.{module}', folder/f'{module}.py')
        mods[module] = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mods[module]
        spec.loader.exec_module(mods[module])
    return mods['routed_features']


ORIG, NEW = package('rv_orig', A4/'tree/student_pilot'), package('rv_new', PATCHED)


class PlaneGeometry:
    def has(self, frame):
        return 1 <= frame <= 32

    def cam(self, frame):
        return np.eye(3), np.zeros(3)

    def fov_of(self, frame):
        return np.pi/2, np.pi/2

    def _depth(self, slot, u, v):
        return np.full(np.asarray(u).shape, 2.)

    def lift(self, frame, uv, mode="center"):
        uv = np.asarray(uv)
        points = np.column_stack(((uv[:, 0]/500-1)*2, (uv[:, 1]/500-1)*2, np.full(len(uv), 2.)))
        return points, points.copy(), np.zeros(len(uv))


def rect(y0, y1, x0, x1):
    m = np.zeros((480, 640), bool)
    m[y0:y1, x0:x1] = True
    return m


def frames(rng, kind):
    out = []
    for k in range(32):
        pres = rng.uniform(.05, 1.)
        frame = []
        # Two persistent objects (cross-frame links) plus clutter; ties in score on purpose.
        for j, (y, x) in enumerate([(100, 120), (260, 380)] + [tuple(rng.integers(20, 380, 2))
                                                                for _ in range(int(rng.integers(0, 4)))]):
            score = [.9, .9, .6, .45, .3][j % 5] if kind == 'ties' else float(rng.uniform(.3, 1.))
            p = pres if kind != 'mixed' else rng.uniform(.05, 1.)
            if kind == 'float32':
                p = np.float32(pres)
            if kind == 'torch':
                import torch
                p = torch.tensor(pres, dtype=torch.float32)
            dy, dx = rng.integers(-4, 5, 2)
            frame.append(dict(mask=rect(int(y+dy), int(y+dy+70), int(x+dx), int(x+dx+90)), score=score, presence=p))
        frame.sort(key=lambda v: -float(v['score']))  # sam3_detect / cache_detect emit score-sorted lists
        out.append(frame)
    return out


def chain(F, raw):
    geo = PlaneGeometry()
    grids = F.candidates.lift_grid(geo)
    props, _ = F.candidates.lift(F.cache_for('obj', raw), 'obj', geo, floor=.3, grids=grids, phrase='obj')
    pools = {'obj': F.candidates.link(props, 'obj')}
    F.candidates.scene_candidates(pools, geo)
    exact = F.Geometry(geo)
    acc = F.accept_features(pools['obj'], raw, exact)
    x = SI.candidate_vectors(pools['obj'], raw, exact, acc) if acc else []
    return props, pools['obj'], acc, x


def same(a, b):
    pa, ta, aa, xa = a
    pb, tb, ab, xb = b
    return (len(pa) > 0 and [(p.frame, p.index, p.score, p.presence) for p in pa] == [(p.frame, p.index, p.score, p.presence) for p in pb]
            and [[(p.frame, p.index) for p in t.proposals] for t in ta] == [[(p.frame, p.index) for p in t.proposals] for t in tb]
            and [v['candidate_id'] for v in aa] == [v['candidate_id'] for v in ab]
            and json.dumps([v['features'] for v in aa]) == json.dumps([v['features'] for v in ab])
            and np.array_equal(np.asarray(xa), np.asarray(xb)))


result = {}
for kind in ('single', 'float32', 'torch', 'ties'):
    ok, n_cands, multi = True, 0, 0
    for seed in range(6):
        raw = frames(np.random.default_rng(100+seed), kind)
        a, b = chain(ORIG, raw), chain(NEW, raw)
        ok &= same(a, b)
        n_cands += len(a[2]); multi += sum(len(t.proposals) > 1 for t in a[1])
    result[kind] = dict(identical=bool(ok), candidates=n_cands, multi_member_tracks=multi)

# Mixed frames: patched proposals carry the raw entry's own presence; raw-side member mean lies in [min, max].
fi = SI.FIELDS
ip, lo, hi = fi.index('sam_presence_members'), fi.index('presence_min'), fi.index('presence_max')
mixed = dict(orig_outside=0, new_outside=0, new_index_mismatch=0, candidates=0)
for seed in range(6):
    raw = frames(np.random.default_rng(200+seed), 'mixed')
    for tag, F in (('orig', ORIG), ('new', NEW)):
        props, tracks, acc, x = chain(F, raw)
        for v in x:
            mixed[f'{tag}_outside'] += not (v[lo]-1e-12 <= v[ip] <= v[hi]+1e-12)
        if tag == 'new':
            mixed['candidates'] += len(x)
            mixed['new_index_mismatch'] += sum(p.presence != float(raw[p.frame-1][p.index]['presence']) for p in props)
result['mixed'] = mixed

# NaN presence on a single-presence frame: both versions propagate the same NaN.
raw = frames(np.random.default_rng(7), 'single')
for v in raw[3]:
    v['presence'] = float('nan')
pa = ORIG.candidates.lift(ORIG.cache_for('obj', raw), 'obj', PlaneGeometry(), floor=.3, phrase='obj')[0]
pb = NEW.candidates.lift(NEW.cache_for('obj', raw), 'obj', PlaneGeometry(), floor=.3, phrase='obj')[0]
result['nan'] = dict(same_nan_positions=[np.isnan(p.presence) for p in pa] == [np.isnan(p.presence) for p in pb],
                     n_nan=int(sum(np.isnan(p.presence) for p in pa)))

# A non-first entry without 'presence': unpatched tolerates it, patched raises KeyError in cache_for.
raw = frames(np.random.default_rng(8), 'single')
del raw[0][1]['presence']
out = {}
for tag, F in (('orig', ORIG), ('new', NEW)):
    try:
        F.cache_for('obj', raw)
        out[tag] = 'ok'
    except KeyError as e:
        out[tag] = f'KeyError {e}'
result['missing_presence_non_first'] = out
print(json.dumps(result, indent=1))
