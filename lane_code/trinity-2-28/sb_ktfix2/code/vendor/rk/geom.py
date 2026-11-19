"""Build G3T x s heads with own depth, FoV and gravity by default.

With own FoV, G3T supplies raw_pose slots 0:7 (rotation and translation).
G3T and own FoV are mixed only in the intrinsics, slots 7:9.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = 'rk'

from .g3t import save_json, sha256

GEO = Path('/scratch/jjyeung/orch_cd/ttower/work/geo')


def references():
    """Import the frozen estimator and C1's exact camera_targets import path."""
    search, environment = sys.path[:], dict(os.environ)
    try:
        sys.path.insert(0, str(GEO))
        import geo_common
        spec = importlib.util.spec_from_file_location('_rk_ttower_scale', GEO / 'scale.py')
        scale = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scale)
        expected = json.loads((GEO / 'scales64.json').read_text())['rule_sha256']
        actual = geo_common.rule_hash()
        if actual != expected:
            raise ValueError('Frozen scale rule sha256 differs from ttower scales64.json')
        return geo_common, scale, actual
    finally:
        sys.path[:] = search
        # geo_common sets CPU environment variables at import time.
        for key in set(os.environ) - set(environment):
            os.environ.pop(key)
        os.environ.update(environment)


def convert(g3t, own, out, fov='g3t', gravity='own', refs=None):
    common, scale, rule = references() if refs is None else refs
    if fov not in ('own', 'g3t') or gravity not in ('own', 'g3t'):
        raise ValueError('FoV/gravity must be own or g3t')
    g3t, own, out = Path(g3t), Path(own), Path(out)
    inputs = dict(g3t_sha256=sha256(g3t), own_sha256=sha256(own))
    with np.load(g3t, allow_pickle=False) as g, np.load(own, allow_pickle=False) as v:
        raw = g['raw_pose32'].astype(float).copy()
        if raw.shape != (32, 9):
            raise ValueError('Expected 32 G3T poses')
        common.assert_identity(raw)
        indices, slots = g['frame_indices'], g['anchor_slots']
        if (slots.shape != (32,) or slots.dtype.kind not in 'iu' or slots[0] != 0
                or np.any(np.diff(slots) <= 0) or slots[-1] >= len(indices)):
            raise ValueError('Invalid G3T anchor slots')
        anchors = indices[slots]
        if 'frame_indices' in v.files and not np.array_equal(anchors, v['frame_indices']):
            raise ValueError('Own and G3T frame indices differ')
        depth = v['depth_grid']
        if depth.shape != (32, 51, 51):
            raise ValueError('Expected own depth [32,51,51]')
        uv = g['grid_uv']
        if not np.array_equal(uv, np.linspace(0, 1000, 51, dtype=np.float32)):
            raise ValueError('Unexpected G3T depth grid coordinates')
        if 'grid_uv' in v.files and not np.array_equal(v['grid_uv'], uv):
            raise ValueError('Own and G3T grid coordinates differ')
        s, selected, threshold = scale.estimate(g['depth_grid'], g['depth_conf_grid'], depth)
        if not np.isfinite(s) or s <= 0:
            raise ValueError('Invalid metric scale')
        raw[:, :3] *= s
        if fov == 'own':
            if v['raw_pose'].shape != (32, 9):
                raise ValueError('Expected 32 own poses for FoV')
            raw[:, 7:9] = v['raw_pose'][:, 7:9]
        common.assert_identity(raw)
        up = (v if gravity == 'own' else g)['gravity_up'].astype(float)
        if up.shape != (3,) or not np.isfinite(up).all() or np.linalg.norm(up) < 1e-6:
            raise ValueError('Invalid gravity up vector')
        if gravity == 'g3t':
            up /= np.linalg.norm(up)
        extra = dict(depth_grid=depth.astype(np.float32), grid_uv=uv.copy(), scale=np.array(s),
                     anchor_frame_indices=anchors, source_hw=g['source_hw'],
                     pose_source=np.array('g3t_x_s'), depth_source=np.array('own'), fov_source=np.array(fov))
        out.mkdir(parents=True, exist_ok=True)
        # The imported writer supplies layout, gravity_source and float64 transforms.
        temporary_key = g3t.stem + '.part'
        common.C1.write(str(out), temporary_key, raw, up, gravity, extra)
        dest = out / g3t.name
        os.replace(out / (temporary_key + '.npz'), dest)
    return dict(s=s, selected_points=int(selected.sum()), confidence_p50=threshold,
                rule_sha256=rule, inputs=inputs, npz_sha256=sha256(dest))


def heads(g3t, own, out, fov='g3t', gravity='own'):
    g3t, own, out = (Path(p).resolve() for p in (g3t, own, out))
    if out in (g3t, own):
        raise ValueError('Output must differ from input directories')
    refs = references()
    out.mkdir(parents=True, exist_ok=True)
    result = dict(g3t=str(g3t), own=str(own), fov_source=fov, gravity_source=gravity,
                  rule_sha256=refs[2], scenes={}, failures={}, missing_own=[], missing_g3t=[])
    sources = {p.name: p for p in g3t.glob('*__*.npz')}
    targets = {p.name: p for p in own.glob('*__*.npz')}
    result['missing_own'] = sorted(set(sources) - set(targets))
    result['missing_g3t'] = sorted(set(targets) - set(sources))
    with (out / 'HEADS.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in sorted(set(sources) & set(targets)):
            try:
                result['scenes'][Path(name).stem] = convert(sources[name], targets[name], out, fov, gravity, refs)
            except (ValueError, KeyError, OSError) as error:
                result['failures'][Path(name).stem] = f'{type(error).__name__}: {error}'
        save_json(out / 'HEADS.json', result)
    return result


def own_heads(own, out):
    """Fallback when G3T is unavailable: the base's own pose, FoV, gravity and depth (pose_source 'own')."""
    own, out = Path(own).resolve(), Path(out).resolve()
    if out == own:
        raise ValueError('Output must differ from the input directory')
    common = references()[0]
    out.mkdir(parents=True, exist_ok=True)
    result = dict(own=str(own), pose_source='own', scenes={}, failures={})
    for path in sorted(own.glob('*__*.npz')):
        try:
            with np.load(path, allow_pickle=False) as v:
                raw = v['raw_pose'].astype(float)
                if raw.shape != (32, 9) or v['depth_grid'].shape != (32, 51, 51):
                    raise ValueError('Expected own poses [32,9] and depth [32,51,51]')
                extra = dict(depth_grid=v['depth_grid'].astype(np.float32), grid_uv=v['grid_uv'].copy(),
                             pose_source=np.array('own'),
                             depth_source=np.array('own'), fov_source=np.array('own'))
                if 'frame_indices' in v.files:
                    extra['anchor_frame_indices'] = v['frame_indices']
                common.C1.write(str(out), path.stem, raw, v['gravity_up'].astype(float), 'own', extra)
            result['scenes'][path.stem] = dict(npz_sha256=sha256(out / path.name), input_sha256=sha256(path))
        except (ValueError, KeyError, OSError) as error:
            result['failures'][path.stem] = f'{type(error).__name__}: {error}'
    save_json(out / 'HEADS.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('heads')
    for name in ('g3t', 'own', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--fov', choices=('own', 'g3t'), default='g3t')
    p.add_argument('--gravity', choices=('own', 'g3t'), default='own')
    o = sub.add_parser('own-heads')
    o.add_argument('--own', required=True, type=Path)
    o.add_argument('--out', required=True, type=Path)
    a = parser.parse_args(argv)
    if a.command == 'own-heads':
        result = own_heads(a.own, a.out)
        print(json.dumps(dict(converted=len(result['scenes']), failures=result['failures'])))
        return int(bool(result['failures']))
    result = heads(a.g3t, a.own, a.out, a.fov, a.gravity)
    print(json.dumps(dict(converted=len(result['scenes']), failures=result['failures'])))
    return int(bool(result['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
