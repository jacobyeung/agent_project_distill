"""Replay G3T tower gravity (not student-head gravity) through native sessions."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

L = Path('/scratch/jjyeung/orch_n30/contracts_rebuild')
parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=('base', 'off', 'on'))
parser.add_argument('--only')
parser.add_argument('--tag', default='full')
args = parser.parse_args()
tree = L/'work/base/work/base/tree_b01ce449' if args.mode == 'base' else L/'work/trees/r3_proof/base'
sys.path[:0] = [str(tree), str(L / 'work/tests_r3')]
from fixtures_contracts import response, masks, head_state
from student_pilot.camera_targets import to_gravity_reference_frame, gravity_reference_rotation
from student_pilot.geometry_profiles import GeometryContract, ProfileGeometry, GeometryError
from student_pilot.scene_state import FrameMap, SceneState
from student_pilot.ground_sources import MaskProvider, MaskBatch
from student_pilot.ground_v3 import GroundV3
from student_pilot.live_trace313 import LiveSession
if args.mode != 'base':
    from trace_format.contracts import contract_epoch, heading_available

SOURCE = 'G3T tower gravity, not student-head gravity'
ROOT = L / 'work/real/x_geo'
OUT = L / 'out/real_replay_r3'
CALLS = dict(room='<ground mode="room">', chair_box='<ground obj="chair" mode="box">',
    table_box='<ground obj="table" mode="box">',
    distance='<gap a="chair" b="table" rule="box_grid_5cm">',
    camera_gap='<gap camera="2" b="chair" rule="box_grid_5cm">',
    centre='<ground obj="chair">',count='<ground obj="chair" mode="instances">')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def adapter(path):
    with np.load(path, allow_pickle=False) as z:
        schema = {k: dict(shape=list(z[k].shape), dtype=str(z[k].dtype)) for k in z.files}
        raw, g = z['raw_pose'], z['gravity_up']
        slots, indices = z['anchor_slots'], z['frame_indices']
        selected = raw[slots]
        assert np.allclose(selected, z['raw_pose32'], atol=1e-6, rtol=0)
        assert np.allclose(selected[0, :6], 0, atol=2e-5)
        assert np.isclose(abs(selected[0, 6]), 1, atol=2e-5)
        R, t, fov = to_gravity_reference_frame(selected, g)
        assert np.allclose(R[0], gravity_reference_rotation(g), atol=2e-5)
        h, w = map(int, z['source_hw'])
        # K is encoded by the stored per-frame FoV, not stored as a matrix.
        K = np.zeros((len(slots), 3, 3))
        K[:, 0, 0] = w / (2 * np.tan(fov[:, 1] / 2))
        K[:, 1, 1] = h / (2 * np.tan(fov[:, 0] / 2))
        K[:, 0, 2], K[:, 1, 2], K[:, 2, 2] = w / 2, h / 2, 1
        A = np.repeat(np.diag([w / 1000, h / 1000, 1.])[None], len(slots), axis=0)
        C = np.repeat(np.eye(4)[None], len(slots), axis=0)
        C[:, :3, :3], C[:, :3, 3] = R, t
        frames = FrameMap(tuple(map(int, indices[slots])))
        # The archive lacks the student metric-scale head: retain raw units at s=1.
        contract = GeometryContract('scaled_g3t_depth', frames, frames.source_indices[0],
            K, A, C, 1., 'g3t', 'unscaled', 'unscaled', 0, 0)
        depth, uv = z['depth_grid'], z['grid_uv']
        details = dict(schema=schema, gravity_up=g.tolist(), source_hw=[h, w],
            frame_indices=list(frames.source_indices), scale=1.,
            scale_status='Raw tower units; no metric calibration supplied. Native formatter retains its m labels.',
            anchor_pose=selected[0].tolist(),
            depth_valid_fraction=float(np.mean(np.isfinite(depth) & (depth > 0))),
            converted_array_sha256={k: hashlib.sha256(np.asarray(v).tobytes()).hexdigest()
                for k, v in dict(K=K, A=A, C=C, depth=depth).items()})
    return contract, depth, uv, details

def mask_setup(geo):
    templates = {name: masks(name).masks[1].copy() for name in ('chair', 'table')}
    yy, xx = np.indices(next(iter(templates.values())).shape)
    coords = np.column_stack(((xx.ravel() + .5) / xx.shape[1] * 1000,
                              (yy.ravel() + .5) / yy.shape[0] * 1000))
    allowed = templates['chair'] | templates['table']
    candidates = []
    for slot in range(1, 32):
        d = geo.depth(slot + 1, coords).reshape(yy.shape)[allowed]
        if np.isfinite(d).all() and (d > 0).all():
            candidates.append(slot)
    assert candidates, 'no_depth_valid_synthetic_mask_frame'
    chosen = candidates[0]
    arrays = {}
    for name, template in templates.items():
        a = np.zeros((32, *template.shape), dtype=bool)
        a[chosen] = template
        arrays[name] = a
    spec = dict(synthetic=True, fixture_source=str(L/'work/tests_r3/fixtures_contracts.py'),
        selection='First nonreference frame with positive finite depths in both fixed rectangles',
        slot_zero_based=chosen, display_frame=chosen+1,
        source_frame=geo.frame_map.source_indices[chosen], mask_shape=list(arrays['chair'].shape),
        rectangles=dict(chair=[7,18,4,12], table=[7,18,20,28]),
        mask_sha256={k: hashlib.sha256(v.tobytes()).hexdigest() for k,v in arrays.items()})
    return arrays, spec

def run(path):
    c, depth, uv, details = adapter(path)
    R = c.camera_to_world[:, :3, :3]
    planes, margins = np.linalg.norm(R[:, 2, :2], axis=1), -R[:, 2, 1]
    pitches = np.degrees(np.arcsin(np.clip(R[:, 2, 2], -1, 1)))
    rolls = np.degrees(np.arctan2(-R[:, 2, 0], -R[:, 2, 1]))
    usable = planes >= .3
    metadata = path.with_suffix('.json')
    metadata_value = json.loads(metadata.read_text())
    assert sha(path) == metadata_value['npz_sha256']
    row = dict(capture=path.stem, dataset=path.stem.split('__')[0],
        source=str(path), metadata_source=str(metadata), gravity_source=SOURCE,
        mode=args.mode, tree_source=str(tree), adapter=details,
        plane=float(planes[0]), margin=float(margins[0]), pitch_deg=float(pitches[0]),
        roll_deg=float(rolls[0]), per_frame=dict(plane=planes.tolist(), margin=margins.tolist(),
        pitch_deg=pitches.tolist(), roll_deg=rolls.tolist()),
        median_plane=float(np.median(planes)), median_margin=float(np.median(margins)),
        median_pitch_deg=float(np.median(pitches)), median_roll_deg=float(np.median(rolls)),
        median_usable_normalized_margin=float(np.median(margins[usable]/planes[usable])) if usable.any() else None,
        median_roll_pitch_above_minus60=float(np.median(rolls[pitches > -60])) if (pitches > -60).any() else None,
        heading_geometrically_defined=bool(planes[0] >= .3), guard='pass', responses={})
    try:
        c.validate()
    except GeometryError as e:
        row.update(guard=str(e), session_status='not_constructed_guard_refusal',
                   heading_exposed=False, synthetic_masks='not_reached')
        return row
    geo = ProfileGeometry(c, depth, uv)
    row['heading_exposed'] = True if args.mode == 'base' else heading_available(geo)
    arrays, spec = mask_setup(geo)
    row['synthetic_masks'] = spec
    mask_calls = []
    def provider(name):
        mask_calls.append(name)
        return MaskBatch(arrays[name], np.ones(32), geo.frame_map.source_indices)
    source = MaskProvider(provider, 'synthetic-fixed-rectangles-real-depth', ('chair', 'table'))
    owner = GroundV3(SceneState('a'*64, geo.frame_map, geo.identity), geo, source,
        mask_source='mdg', geometry_profile=c.profile,
        audit_dir=L/'work/real_replay_r3/audit'/args.tag/args.mode/path.stem)
    assert owner.geometry_error is None, owner.geometry_error
    session = LiveSession(owner, program_version='3.14')
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    session.registry = PrintedPointRegistry()
    session.bind_state(head_state(geo, owner))
    for label, call in CALLS.items():
        row['responses'][label] = response(session, call)
        if label == 'room':
            row['room_mask_calls'] = len(mask_calls)
            assert not mask_calls
    own_frames = [int(k)+1 for k in np.flatnonzero(planes >= .3) if k > 0]
    assert len(own_frames) >= 2, 'two_defined_nonreference_headings_required'
    i, j = own_frames[:2]
    row['relative_frames'] = [i, j]
    k = spec['display_frame']
    calls = dict(move=f'<move from={i} to={j}>', turn=f'<turn from={i} to={j}>',
                 pose=f'<pose frame={j}>', depth=f'<depth_at frame={k} pts=[[180,350],[330,450],[210,620]]>')
    for label, call in calls.items():
        row['responses'][label] = response(session, call)
    labels = list(session.registry._points)[-3:]
    call = f'<angle S={labels[0]} F={labels[1]} Q={labels[2]} rule=hard>'
    row['responses']['angle'] = response(session, call)
    row['head_calls'] = dict(calls, angle=call)
    if args.mode == 'on':
        from student_pilot.carrier_c1_decode import respond
        # Force only the availability policy OFF on the same readout, after the ON guard admitted it.
        with contract_epoch(False):
            row['heading_defined_computation'] = {name: respond(text, session.registry, session.state.geometry)[0]
                for name, text in calls.items() if name != 'depth'}
        from copy import deepcopy
        defined_registry = deepcopy(session.registry)
        for point in defined_registry._points.values():
            point['heading_defined'] = True
        row['heading_defined_computation']['angle'] = respond(call, defined_registry, session.state.geometry)[0]
        row['heading_plane_min'] = session.heading_plane_min
    row['size_lines'] = {k: [s for s in row['responses'][k].splitlines() if s.startswith('size ')]
                         for k in ('chair_box', 'table_box')}
    row['session_status'] = 'completed'
    row['session_query_kinds'] = [q.get('kind', 'object') for q in session.queries]
    row['mask_provider_calls'] = mask_calls
    return row

paths = sorted(ROOT.glob('*/g3t/*.npz'), key=lambda p:p.stem)
assert len({p.stem for p in paths}) == len(paths), 'duplicate capture geometry'
if args.only:
    paths = [p for p in paths if p.stem == args.only]
assert paths
result_path = OUT / (args.tag+'_'+args.mode+'.jsonl')
context = contextlib.nullcontext() if args.mode == 'base' else contract_epoch(args.mode == 'on')
with result_path.open('x') as f, context:
    for path in paths:
        row = run(path)
        f.write(json.dumps(row, sort_keys=True)+'\n')
        f.flush()
        print(SOURCE+' | '+args.mode+' '+path.stem+' '+row['guard'], flush=True)
