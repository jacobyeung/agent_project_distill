"""K1 candidate tables + selector-head inputs on frozen G3T geometry at E3's S4 scale (trinity-1-18, CPU).

Table rows come from the kit's unchanged build_tables.build_capture (extract + label). The only difference from
k1_pipeline.tables is the geometry: K1's convert phase has not run, so each capture's geometry.npz is written
here from tower.npz exactly as E3's harness geometry_npz does (profile scaled_g3t_depth, gravity G1 from the
tower's own anchor poses, per-capture scale S4 from E3's train-fit FITS.json). Captures whose G1 geometry the
deployed loader refuses are excluded (listed in the receipt).

A wrapper around routed_features.accept_features records each name's inputs and computes the head's
per-candidate vectors (selector_inputs.candidate_vectors); it returns the original output unchanged.
"""
import os
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys
sys.dont_write_bytecode = True
import argparse, gzip, hashlib, json, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json')
GTSET = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json')
TOWERS = Path('/scratch/jjyeung/k1/run_tower_sam_2')
sys.path[:0] = [str(KIT / 'work'), str(KIT / 'work/refit')]
import gate
import gt_set as G
sys.path.insert(0, str(KIT / 'native_kit'))
import bindings as B
import build_tables
import numpy as np
from student_pilot import camera_targets
from student_pilot import routed_features as F
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
sys.path.insert(0, str(HERE))
import selector_inputs as SI


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def tower_index():
    index = {}
    for p in sorted(TOWERS.glob('*/PHASE_COMPLETE.json')):
        r = json.loads(p.read_text())
        index[r['capture_sha256']] = (p.parent, r)
    return index


def g1(tower):
    raw = tower['raw_pose'][tower['anchor_slots']]
    R = np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw])
    v = np.mean(-R[:, :, 1], axis=0)
    n = np.linalg.norm(v)
    if not np.isfinite(n) or n < 1e-6:
        raise ValueError('degenerate_gravity')
    return v / n


def geometry_npz(c, tower, hw, gravity, scale, dest):
    # Byte-for-byte the arithmetic of E3 harness.geometry_npz.
    R, t, fov = camera_targets.to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']], gravity)
    H, W = map(int, hw)
    C = np.repeat(np.eye(4)[None], 32, axis=0)
    C[:, :3, :3], C[:, :3, 3] = R, t
    K = np.zeros((32, 3, 3))
    K[:, 0, 0], K[:, 1, 1] = W / (2 * np.tan(fov[:, 1] / 2)), H / (2 * np.tan(fov[:, 0] / 2))
    K[:, 0, 2], K[:, 1, 2], K[:, 2, 2] = W / 2, H / 2, 1
    A = np.repeat(np.diag([W / 1000, H / 1000, 1.])[None], 32, axis=0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.savez(dest, profile='scaled_g3t_depth', depth_unit='unscaled', pose_unit='unscaled',
             reference_source_frame=c['anchor_indices'][0], K=K, canvas_to_source=A, camera_to_world=C,
             scale=scale, depth_scale_count=0, pose_scale_count=0,
             anchor_frame_indices=c['anchor_indices'], depth_grid=tower['depth_grid'], grid_uv=tower['grid_uv'])
    result = load_geometry(dest, FrameMap(tuple(c['anchor_indices'])), 'tower_scaled')
    assert result.depth_scale_count == 1 and result.pose_scale_count == 1
    return result


def gt_arrays(c, selection):
    with np.load(B.checked(selection['entries'][c['canonical']]), allow_pickle=False) as z:
        inst = z['instances'] if 'instances' in z else z['inst']
        frames = z['frame_indices']
    shape = (F.OUTPUT_SHAPE[0], F.OUTPUT_SHAPE[1])
    resized = tuple(inst.shape[1:]) != shape
    if resized:
        # Portrait captures: the runtime stretches every SAM 3 mask to 480x640 (routed_features.resize) and
        # keeps [::2, ::2]; apply the same nearest stretch to the GT ids so both live on the same 240x320 grid.
        from scipy import ndimage
        h, w = inst.shape[1:]
        inst = np.stack([ndimage.zoom(f, (shape[0] / h, shape[1] / w), order=0, prefilter=False) for f in inst])
        assert inst.shape[1:] == shape
    return dict(instances=inst, frame_indices=frames), resized


RAW_ONLY = False


def raw_prompts_only(raw):
    """Drop instances SAM 3 found under an alias prompt (dense_aliases contract: 'source_prompt' differs from the
    phrase); the phrase's presence becomes the raw prompt's own presence ('source_presence' of its instances)."""
    out = dict(raw, frames={})
    dropped = kept = 0
    for k, f in raw['frames'].items():
        phrases = {}
        for ph, r in f['phrases'].items():
            inst = [i for i in r.get('instances') or [] if i.get('source_prompt', ph) == ph]
            dropped += len(r.get('instances') or []) - len(inst); kept += len(inst)
            pres = float(inst[0]['source_presence']) if inst and 'source_presence' in inst[0] else float(r['presence'])
            if inst and len({i.get('source_presence') for i in inst}) != 1:
                raise ValueError('raw prompt presence differs inside one frame')
            phrases[ph] = dict(r, instances=inst, presence=pres)
        out['frames'][k] = dict(f, phrases=phrases)
    out['raw_prompts_only'] = dict(kept=kept, dropped=dropped)
    return out


def one(c, entry, scale, selection, out):
    t0 = time.monotonic()
    folder, receipt = entry
    key = c['canonical'].replace('/', '__')
    with np.load(folder / 'tower.npz', allow_pickle=False) as z:
        tower = {k: z[k] for k in ('raw_pose', 'depth_grid', 'depth_conf_grid', 'frame_indices', 'anchor_slots', 'grid_uv')}
    assert np.array_equal(tower['frame_indices'][tower['anchor_slots']], c['anchor_indices'])
    try:
        geo = geometry_npz(c, tower, receipt['source_hw'], g1(tower), scale, out / 'geo' / (key + '.npz'))
    except ValueError as exc:
        return dict(capture=c['canonical'], excluded=type(exc).__name__ + ':' + str(exc))
    raw = B.load(folder / 'candidates.json')
    if RAW_ONLY:
        raw = raw_prompts_only(raw)
    gt, gt_resized = gt_arrays(c, selection)
    head = {}
    original = F.accept_features

    def recorded(tracks, raw_frames, geometry):
        accepted = original(tracks, raw_frames, geometry)
        if accepted:
            name = tracks[0].name
            vecs = SI.candidate_vectors(tracks, raw_frames, geometry, accepted)
            head[name] = {a['candidate_id']: v for a, v in zip(accepted, vecs)}
        return accepted
    F.accept_features = recorded
    try:
        rows, pairs = build_tables.build_capture(c, raw, geo, gt)
    finally:
        F.accept_features = original
    inputs = []
    for r in rows:
        inputs.append(dict(object_id=r['object_id'], candidate_id=r['candidate_id'], name=r['name'],
                           x=head[r['name']][r['candidate_id']]))
    rec = dict(capture=c['canonical'], raw_prompts_only=raw.get('raw_prompts_only'), gt_resized=gt_resized, rows=rows, pairs=pairs, inputs=inputs, scale=scale,
               geometry_sha256=sha(out / 'geo' / (key + '.npz')), candidates_sha256=sha(folder / 'candidates.json'),
               tower_sha256=sha(folder / 'tower.npz'), seconds=time.monotonic() - t0)
    with gzip.open(out / 'caps' / (key + '.json.gz'), 'wt') as f:
        json.dump(rec, f)
    return dict(capture=c['canonical'], gt_resized=gt_resized, rows=len(rows), pairs=len(pairs), seconds=rec['seconds'])


def work(args):
    c, entry, scale, selection, out = args
    try:
        return one(c, entry, scale, selection, Path(out))
    except Exception as exc:
        return dict(capture=c['canonical'], error=type(exc).__name__ + ':' + str(exc), tb=traceback.format_exc()[-3000:])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--scales', required=True)
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--only', default='')
    p.add_argument('--procs', type=int, default=8)
    p.add_argument('--raw-prompts-only', action='store_true')
    a = p.parse_args()
    global RAW_ONLY
    RAW_ONLY = a.raw_prompts_only
    out = Path(a.out)
    (out / 'caps').mkdir(parents=True, exist_ok=True)
    from verify_sources import verify
    n_verified = verify()
    m = json.loads(MANIFEST.read_text())
    selection = G.load(GTSET)
    captures, meta = G.select(m, selection)
    scales = json.loads(Path(a.scales).read_text())['captures']
    index = tower_index()
    if a.only:
        captures = [c for c in captures if c['canonical'] in a.only.split(',')]
    if a.limit:
        captures = captures[:a.limit]
    jobs = []
    for c in captures:
        s = scales[c['canonical']]
        if s['split'] != c['k1_split'] or s['room'] != c['room']:
            raise ValueError('E3 split/room differs: ' + c['canonical'])
        done = out / 'caps' / (c['canonical'].replace('/', '__') + '.json.gz')
        if done.exists():
            continue
        if s['S4'] is None:
            jobs.append(None)
            (out / 'excluded').mkdir(exist_ok=True)
            (out / 'excluded' / (c['canonical'].replace('/', '__') + '.txt')).write_text('E3 G1 refused: ' + str(s['refused']) + '\n')
            continue
        jobs.append((c, index[digest(c)], float(s['S4']), selection, str(out)))
    jobs = [j for j in jobs if j is not None]
    print(json.dumps(dict(verified=n_verified, captures=len(captures), jobs=len(jobs))), flush=True)
    import multiprocessing as mp
    with mp.get_context('fork').Pool(a.procs) as pool, open(out / 'progress.jsonl', 'a') as log:
        for r in pool.imap_unordered(work, jobs):
            log.write(json.dumps(r) + '\n')
            log.flush()
            print(json.dumps({k: v for k, v in r.items() if k != 'tb'}), flush=True)


if __name__ == '__main__':
    main()
