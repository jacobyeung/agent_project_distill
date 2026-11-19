"""cache_for/lift per-instance presence: unpatched A4 bytes against the patched copy.

Run: ./run.sh -m pytest -q -p no:cacheprovider work/test_cachefix.py
"""
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
A4 = HERE/'orig/src/tree/student_pilot'
K1 = Path('/scratch/jjyeung/k1/run_convert_2')
SHA = {'routed_features.py': '736c5a642fe28656c5508022210b050a87e49821381980a9c6f79007ef1fda13',
       'routed_candidates.py': '9a2004108d85f3c2a70ca5e4d66240748807d4f0c3ced8a2e0842fea4d78482f'}


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
    return types.SimpleNamespace(F=mods['routed_features'], C=mods['routed_candidates'])


ORIG = package('sp_orig', A4)
NEW = package('sp_patched', HERE/'patched/src/tree/student_pilot')


class Geo:
    """Deterministic stand-in for the scaled geometry: every frame valid, depth 2 m."""

    def has(self, frame):
        return 1 <= frame <= 32

    def lift(self, frame, uv, mode='center'):
        uv = np.asarray(uv, float)
        P = np.column_stack((uv[:, 0]/500-1, uv[:, 1]/500-1, np.full(len(uv), 2.)+.01*frame))
        return P, P.copy(), np.full(len(uv), .05)


def rect(y0, y1, x0, x1):
    mask = np.zeros((480, 640), bool)
    mask[y0:y1, x0:x1] = True
    return mask


def proposals(out):
    keep, rejected = out
    return [(p.frame, p.index, p.score, p.presence, p.joint, p.prior, p.mask.tobytes(), p.points.tobytes(),
             p.center.tobytes(), p.extent, p.depth, sorted(p.voxels)) for p in keep], rejected


def strip(cache):
    return json.dumps({k: {f: {'phrases': {n: dict(r, instances=[{a: b for a, b in i.items() if a != 'presence'}
                                                                  for i in r['instances']])
                                            for n, r in v['phrases'].items()}} for f, v in cache['frames'].items()}
                           if k == 'frames' else cache[k] for k in cache}, sort_keys=True)


def test_baseline_bytes_are_the_a4_bundle():
    for name, digest in SHA.items():
        assert hashlib.sha256((A4/name).read_bytes()).hexdigest() == digest


def mixed_frames():
    frames = [[] for _ in range(32)]
    frames[0] = [dict(mask=rect(40, 200, 40, 260), score=.9, presence=.1),
                 dict(mask=rect(260, 440, 340, 600), score=.8, presence=.9)]
    return frames


def test_unpatched_collapses_mixed_frame_to_first_presence():
    cache = ORIG.F.cache_for('chair', mixed_frames())
    assert cache['frames']['0']['phrases']['chair']['presence'] == .1
    got, _ = ORIG.C.lift(cache, 'chair', Geo(), floor=.3, phrase='chair')
    assert [p.presence for p in got] == [.1, .1]


def test_mixed_frame_keeps_each_instance_presence():
    cache = NEW.F.cache_for('chair', mixed_frames())
    assert [i['presence'] for i in cache['frames']['0']['phrases']['chair']['instances']] == [.1, .9]
    got, rejected = NEW.C.lift(cache, 'chair', Geo(), floor=.3, phrase='chair')
    assert not rejected
    assert [(p.score, p.presence) for p in got] == [(.9, .1), (.8, .9)]
    assert [p.joint for p in got] == pytest.approx([.09, .72])
    # link peels the highest-joint member, which is now the high-presence instance.
    linked = NEW.C.link(got, 'chair')
    assert sorted(len(c.proposals) for c in linked) == [1, 1]


def random_frames(rng, mixed=False):
    frames = []
    for _ in range(32):
        presence = float(rng.uniform(.05, 1.))
        frame = []
        for _ in range(int(rng.integers(0, 6))):
            y, x = int(rng.integers(0, 400)), int(rng.integers(0, 560))
            frame.append(dict(mask=rect(y, y+int(rng.integers(8, 80)), x, x+int(rng.integers(8, 80))),
                              score=float(rng.uniform(0, 1)),
                              presence=float(rng.uniform(.05, 1.)) if mixed else presence))
        frames.append(frame)
    return frames


@pytest.mark.parametrize('seed', range(20))
def test_single_presence_frames_are_identical(seed):
    frames = random_frames(np.random.default_rng(20261119+seed))
    old, new = ORIG.F.cache_for('obj', frames), NEW.F.cache_for('obj', frames)
    assert strip(new) == json.dumps(old, sort_keys=True)
    grids = ORIG.C.lift_grid(Geo())
    a = proposals(ORIG.C.lift(old, 'obj', Geo(), floor=.3, grids=grids, phrase='obj'))
    b = proposals(NEW.C.lift(new, 'obj', Geo(), floor=.3, grids=grids, phrase='obj'))
    assert a[0] and a == b


@pytest.mark.parametrize('seed', range(5))
def test_mixed_random_frames_carry_every_presence(seed):
    frames = random_frames(np.random.default_rng(7+seed), mixed=True)
    got, _ = NEW.C.lift(NEW.F.cache_for('obj', frames), 'obj', Geo(), floor=.3, phrase='obj')
    assert len({p.presence for p in got}) > 1
    for p in got:
        ordered = sorted(frames[p.frame-1], key=lambda v: -v['score'])
        assert p.presence == ordered[p.index]['presence']


def k1_caches(n=3):
    folders = sorted(p for p in K1.iterdir() if (p/'candidates.json').is_file())[:n] if K1.is_dir() else []
    return [json.loads((p/'candidates.json').read_text()) for p in folders]


@pytest.mark.skipif(not K1.is_dir(), reason='K1 stage-1 caches absent on this node')
def test_stage1_caches_lifted_directly_are_unchanged():
    """live_parity_adapter, ground_sources and price_masks lift stage-1 caches whose instances lack 'presence'."""
    caches = k1_caches()
    assert caches
    grids = ORIG.C.lift_grid(Geo())
    lifted = 0
    for cache in caches:
        assert not any('presence' in i for f in cache['frames'].values()
                       for r in f['phrases'].values() for i in r['instances'])
        for name in cache['phrases']:
            a = proposals(ORIG.C.lift(cache, name, Geo(), floor=.3, grids=grids, phrase=name))
            b = proposals(NEW.C.lift(cache, name, Geo(), floor=.3, grids=grids, phrase=name))
            assert a == b
            lifted += len(a[0])
    assert lifted
