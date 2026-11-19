"""Portable tower/SAM and own-head artifacts; CPU conversion preserves K1 cache files."""
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import bindings as B
import pipeline as P

PHASES = ('tower_sam', 'own', 'convert')


def images_for(c, anchors=False):
    from PIL import Image
    pins = [c['dense_frames'][i] for i in c['anchor_slots']] if anchors else c['dense_frames']
    images = []
    for pin in pins:
        with Image.open(B.checked(pin)) as im:
            images.append(im.convert('RGB'))
    return images


def receipt(c, boundary, dest, phase, names, **extra):
    record = dict(capture_sha256=B.digest(c), phase=phase, checkpoint=boundary.checkpoint,
                  synthetic=boundary.synthetic, sources=B.source_identity(),
                  producer_sha256=B.sha(__file__),
                  files={n: B.sha(dest / n) for n in names}, **extra)
    B.write(dest / 'PHASE_COMPLETE.json', record)
    return record


def checked_phase(c, root, phase):
    dest = Path(root) / B.digest(c['canonical'])[:16]
    r = B.load(dest / 'PHASE_COMPLETE.json')
    if (r['capture_sha256'] != B.digest(c) or r['phase'] != phase
            or r['sources'] != B.source_identity() or r.get('producer_sha256') != B.sha(__file__)):
        raise ValueError('Phase capture/source binding differs')
    expected = {'tower_sam': {'tower.npz', 'candidates.json', 'parity_raw.jsonl'}, 'own': {'own.npz'}}
    if set(r['files']) != expected[phase]:
        raise ValueError('Phase file set differs')
    for name, sha in r['files'].items():
        if Path(name).name != name or B.sha(dest / name) != sha:
            raise ValueError('Phase file hash differs')
    return dest, r


def tower_sam(c, boundary, dest, progress):
    images = images_for(c)
    state = boundary.tower(c, images)
    if state.frame_indices[state.anchor_slots].tolist() != c['anchor_indices']:
        raise ValueError('Tower anchor order differs')
    arrays = dict(raw_pose=state.raw_pose9, depth_grid=state.depth_grid,
                  depth_conf_grid=state.depth_conf_grid, frame_indices=state.frame_indices,
                  anchor_slots=state.anchor_slots, grid_uv=state.grid_uv)
    if state.points_grid is not None:
        arrays['points_grid'] = state.points_grid
    np.savez(dest / 'tower.npz', **arrays)
    progress('tower_saved')
    # Use the same raw prompt recorder as the single-process producer.
    from k1_pipeline import raw_proposals
    raw_proposals(c, [images[i] for i in c['anchor_slots']], boundary, dest)
    progress('sam_saved')
    return receipt(c, boundary, dest, 'tower_sam',
                   ['tower.npz', 'candidates.json', 'parity_raw.jsonl'],
                   source_hw=list(images[0].size[::-1]))


def own(c, boundary, dest, progress):
    from student_pilot.tower_read import GRID_UV
    images = images_for(c, anchors=True)
    depth, gravity = boundary.own(c, images, SimpleNamespace(grid_uv=GRID_UV))
    depth, gravity = np.asarray(depth), np.asarray(gravity)
    if depth.shape != (32, 51, 51) or not np.isfinite(depth).all() or np.any(depth <= 0):
        raise ValueError('Own depth must be finite positive 32x51x51')
    if gravity.shape not in ((3,), (32, 3)) or not np.isfinite(gravity).all():
        raise ValueError('Own gravity differs')
    np.savez(dest / 'own.npz', depth=depth, gravity=gravity)
    progress('heads_saved')
    return receipt(c, boundary, dest, 'own', ['own.npz'])


def convert(c, boundary, dest, tower_root, own_root, progress):
    from student_pilot.tower_read import TowerState
    a, ar = checked_phase(c, tower_root, 'tower_sam')
    b, br = checked_phase(c, own_root, 'own')
    if ar['synthetic'] != br['synthetic'] or ar['checkpoint'] != br['checkpoint']:
        raise ValueError('Phase checkpoint/synthetic identity differs')
    if ar['synthetic'] != boundary.synthetic or ar['checkpoint'] != boundary.checkpoint:
        raise ValueError('Conversion identity differs')
    state = TowerState.from_npz(a / 'tower.npz')
    if (state.frame_indices.tolist() != [f['index'] for f in c['dense_frames']]
            or state.anchor_slots.tolist() != c['anchor_slots']):
        raise ValueError('Saved tower frame identity differs')
    with np.load(b / 'own.npz', allow_pickle=False) as z:
        geometry = B.geometry.convert(state, z['depth'], z['gravity'], ar['source_hw'], dest / 'geometry.npz')
    for name in ('candidates.json', 'parity_raw.jsonl'):
        shutil.copyfile(a / name, dest / name)
    result = dict(capture_sha256=B.digest(c), checkpoint=boundary.checkpoint,
                  synthetic=boundary.synthetic, geometry=geometry, sources=B.source_identity(),
                  files={n: B.pin(dest / n) for n in ('geometry.npz', 'candidates.json', 'parity_raw.jsonl')},
                  phase='unselected_cache_no_responses')
    B.write(dest / 'CACHE_COMPLETE.json', result)
    progress('converted')
    return result


def journal(out, phase, event, canonical=None, **extra):
    row = dict(phase=phase, event=event, canonical=canonical, unix=time.time(), **extra)
    with (out / 'PROGRESS.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')


def run(m, out, boundary, phase, max_seconds, tower_root=None, own_root=None, max_bytes=1_500_000_000):
    if phase not in PHASES:
        raise ValueError('Unknown phase')
    if phase == 'convert' and (not tower_root or not own_root):
        raise ValueError('Conversion requires both phase roots')
    out = Path(out).resolve()
    if Path('/scratch') not in out.parents:
        raise ValueError('Phase output must be under scratch')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'HALTED.json').exists():
        raise ValueError('HALTED: operator review and fresh root required')
    identity = dict(manifest_sha256=B.digest(m), phase=phase, sources=B.source_identity(),
                    producer_sha256=B.sha(__file__), tower_root=str(tower_root), own_root=str(own_root))
    if (out / 'BINDING.json').exists():
        if B.load(out / 'BINDING.json') != identity:
            raise ValueError('Resume binding differs')
    else:
        B.write(out / 'BINDING.json', identity)
    start = time.monotonic()
    journal(out, phase, 'start')
    try:
        for c in m['captures']:
            if time.monotonic() - start >= max_seconds or ((out / 'STOP').exists() and (out / 'STOP').read_text().strip() != 'RESUME'):
                journal(out, phase, 'stopped')
                return 4
            if not boundary.synthetic and shutil.disk_usage(out).free < 100 * 1024**3 + max_bytes:
                raise ValueError('Disk reserve')
            dest = out / B.digest(c['canonical'])[:16]
            complete = 'CACHE_COMPLETE.json' if phase == 'convert' else 'PHASE_COMPLETE.json'
            if (dest / complete).exists():
                if phase == 'convert':
                    from k1_pipeline import cached
                    cached(c, dest)
                else:
                    checked_phase(c, out, phase)
            elif dest.exists():
                raise ValueError('Incomplete capture preserved; use a fresh root after review')
            else:
                dest.mkdir()
                journal(out, phase, 'capture_start', c['canonical'])
                progress = lambda event: journal(out, phase, event, c['canonical'])
                if phase == 'tower_sam':
                    tower_sam(c, boundary, dest, progress)
                elif phase == 'own':
                    own(c, boundary, dest, progress)
                else:
                    convert(c, boundary, dest, tower_root, own_root, progress)
            journal(out, phase, 'capture_commit', c['canonical'], receipt_sha256=B.sha(dest / complete))
            if sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) > max_bytes:
                raise ValueError('Output cap')
        journal(out, phase, 'complete')
        return 0
    except Exception as e:
        B.write(out / 'HALTED.json', dict(error=repr(e), automatic_retry=False))
        journal(out, phase, 'failed')
        raise
