"""Audit the two guard refusals against existing poses, labels, and CPU reader replay."""
import ast
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(8)
ROOT = Path(__file__).resolve().parent
KBOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
OUT = KBOX / 'out/box_ladder'
K1 = Path('/scratch/jjyeung/k1')
TREE = Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
READER = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4/src/b')
SEL = Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector')
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
LABELS = Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')
NAMES = ['scannetpp/0f69aefe3d', 'scannetpp/2c7c10379b']
PINS = {}


def read(path):
    path = Path(path)
    b = path.read_bytes()
    PINS[str(path)] = hashlib.sha256(b).hexdigest()
    return b


def js(path):
    return json.loads(read(path))


def npz(path):
    with np.load(io.BytesIO(read(path)), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def unit(x):
    return np.asarray(x, float) / np.linalg.norm(x)


def angle(a, b):
    return float(np.degrees(np.arccos(np.clip(unit(a) @ unit(b), -1, 1))))


def declaration(path, name, bindings):
    tree = ast.parse(read(path))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module([node], []), str(path), 'exec'), bindings)
    return bindings[name]


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    return x


def main():
    sys.path[:0] = list(map(str, [READER, TREE, SEL, SEL / 'sl118']))
    from e2e_reader.geometry import from_npz, from_tower
    from e2e_reader.stage1 import StageOne, median_ratio
    from e2e_reader.grounding import StageOneSocket, ground_session
    from student_pilot import camera_targets as CT, geometry_profiles as GP
    from selector_head import load_head
    cache_detect = declaration(KBOX / 'predicted.py', 'cache_detect', dict(np=np))
    mra = declaration(KBOX / 'box_math.py', 'mra', dict(np=np))
    reviewed = declaration(KBOX / 'vendor/gravity_guard.py', 'validate_up_convention',
                           dict(np=np, UP_PLANE_MIN=.3, GeometryError=GP.GeometryError))
    manifest = js(MANIFEST)
    caps = {c['canonical']: c for c in manifest['captures'] if c['canonical'] in NAMES}
    labels = {r['id']: r for r in map(json.loads, read(LABELS).splitlines())}
    parity = js(OUT / 'RESTORED_CAPTURE_PARITY.json')
    parity_by_id = {r['row_id']: r for r in parity['checks']}
    read(KBOX / 'verify_restored.py')
    read(KBOX / 'out/restored_parity.log')
    read(KBOX / 'serving_reference.py')
    read(KBOX / 'train_pricing.py')
    for ext in ['json', 'safetensors']: read(SEL / f'work/run_iso/selector_head.{ext}')
    head, _ = load_head(SEL / 'work/run_iso')
    images = {
        NAMES[0]: 'Upside-down bathroom: floor mat and toilet base appear at the top; window extends toward the bottom; radiator and tiled walls corroborate inversion.',
        NAMES[1]: 'Nearly sideways living room: rug/floor at image right, sofa across the lower half, door and wall toward image left; image-up is not physical up.'
    }
    captures = []
    for name in NAMES:
        c = caps[name]
        key = hashlib.sha256(json.dumps(name, sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
        folder = K1 / 'run_convert_2' / key
        receipt = js(folder / 'CACHE_COMPLETE.json')
        z = npz(folder / 'REFUSED_GEOMETRY.npz')
        assert PINS[str(folder / 'REFUSED_GEOMETRY.npz')] == receipt['files']['REFUSED_GEOMETRY.npz']['sha256']
        ownpath = K1 / 'own_170235/native/probe' / key
        own, ownrec = npz(ownpath / 'own.npz'), js(ownpath / 'PHASE_COMPLETE.json')
        assert PINS[str(ownpath / 'own.npz')] == ownrec['files']['own.npz']
        towerpath = K1 / 'run_tower_sam_2' / key
        tower, towerrec = npz(towerpath / 'tower.npz'), js(towerpath / 'PHASE_COMPLETE.json')
        assert ownrec['capture_sha256'] == towerrec['capture_sha256'] == receipt['capture_sha256']
        gt = npz(c['gt']['path'])
        assert PINS[c['gt']['path']] == c['gt']['sha256']
        assert np.array_equal(gt['frame_indices'], c['anchor_indices'])
        assert np.array_equal(z['anchor_frame_indices'], c['anchor_indices'])
        frame = c['dense_frames'][c['anchor_slots'][0]]
        assert frame['index'] == int(z['reference_source_frame']) == 0
        read(frame['path'])
        assert PINS[frame['path']] == frame['sha256']
        C = z['camera_to_world']
        R = C[:, :3, :3]
        predicted_g = own['gravity']
        gt_g, valid = CT.encode_gravity(gt['c2w'])
        assert valid and gt['valid'][0]
        scale = median_ratio(tower['depth_grid'], tower['depth_conf_grid'], own['depth'])
        served_scale = float(torch.tensor(float(np.log(scale)), dtype=torch.float32).exp())
        stored = from_npz(folder / 'REFUSED_GEOMETRY.npz')
        geo = from_tower(tower['raw_pose'], tower['anchor_slots'], tower['frame_indices'],
                         tower['depth_grid'], tower['grid_uv'], predicted_g, served_scale, towerrec['source_hw'])
        assert np.array_equal(geo.contract.camera_to_world, z['camera_to_world'])
        # Recreate the sealed contract directly from the accepted reader contract.
        contract = stored.contract if hasattr(stored, 'contract') else stored.c
        try:
            GP.GeometryContract.validate(contract)
            sealed = 'ACCEPTED'
        except ValueError as e:
            sealed = str(e)
        try:
            reviewed(R)
            review = 'ACCEPTED'
        except ValueError as e:
            review = str(e)
        try:
            reviewed(gt['c2w'][:, :3, :3])
            gt_review = 'ACCEPTED'
        except ValueError as e:
            gt_review = str(e)
        cache = js(folder / 'candidates.json')
        stage = StageOne(cache_detect(cache), head, geo, rule='candidates_argmax')
        session = ground_session(geo, StageOneSocket(stage.propose, stage.select, (240, 320), 32))
        base = js(OUT / 'base' / (name.replace('/', '__') + '.json'))
        base_rows = {r['row_id']: r for r in base['items'] if r['arm'] == 'A0_deployed'}
        rows = []
        for row in c['rows']:
            if row['id'] not in parity_by_id: continue
            for operand in row['operands']:
                session.execute(f'<ground obj="{operand}" mode="box">')
            a, b = row['operands']
            response = session.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
            match = re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m', response)
            pred = float(match[1]) if match else None
            target = labels[row['id']]['corrected']
            assert target == base_rows[row['id']]['label']
            assert response == parity_by_id[row['id']]['response']
            assert pred == base_rows[row['id']]['prediction']
            rows.append(dict(row_id=row['id'], operands=row['operands'], response=response, prediction_m=pred,
                             corrected_label_m=target, stored_label_m=labels[row['id']]['stored'],
                             relative_error=None if pred is None else abs(pred-target)/target,
                             mra=mra(pred, target), replay_matches=True))
        captures.append(dict(capture=name, key=key, checkpoint=ownrec['checkpoint'],
            reference_source_frame=int(z['reference_source_frame']), first_image=frame, image_description=images[name],
            image_up_camera=[0., -1., 0.], gravity_head_raw=predicted_g, gravity_head_unit=unit(predicted_g),
            image_up_served_world=-R[0, :, 1], image_up_gt_world=-gt['c2w'][0, :3, 1],
            gt_world_up=[0., 0., 1.], gt_physical_gravity_direction_world=[0., 0., -1.],
            gt_up_in_reference_camera=gt_g, gt_physical_gravity_direction_camera=-gt_g,
            gt_gravity_provenance='Derived via camera_targets.encode_gravity(c2w), using dataset z-up convention; NPZ has no separate gravity measurement.',
            gt_floor_ceiling_boxes=[dict(id=int(i),label=str(label),centroid=centre) for i,label,centre in zip(gt['ids'],gt['labels'],gt['obb_centroid']) if str(label) in ('floor','ceiling')],
            predicted_image_up_vs_world_up_deg=angle([0, -1, 0], predicted_g),
            gt_image_up_vs_world_up_deg=angle([0, -1, 0], gt_g),
            gravity_head_error_vs_gt_deg=angle(predicted_g, gt_g),
            guard_margin=float(-R[0, 2, 1]), gt_guard_margin=float(-gt['c2w'][0, 2, 1]),
            reviewed_plane_norm=float(np.linalg.norm(R[0, 2, :2])),
            gt_reviewed_plane_norm=float(np.linalg.norm(gt['c2w'][0, 2, :2])),
            sealed_result=sealed, reviewed_result=review, convert_refusal=receipt['geometry_refusal'],
            gt_sealed_up_axis_result='reference_camera_up_opposes_gravity' if -gt['c2w'][0,2,1]<=0 else 'ACCEPTED',
            gt_reviewed_up_axis_result=gt_review,
            convert_geometry_export_exists=(folder / 'geometry.npz').exists(),
            reader_from_npz='ACCEPTED', reader_from_tower='ACCEPTED',
            reader_reconstruction_exact_unscaled_camera_arrays=True,
            max_metric_translation_difference_due_to_scale_rounding=float(np.max(np.abs(geo.C[:, :3, 3]-stored.C[:, :3, 3]))),
            rotations_max_orthogonality_error=float(np.max(np.abs(R @ R.transpose(0,2,1)-np.eye(3)))),
            rotations_determinants=np.linalg.det(R),
            raw_reference_pose=tower['raw_pose'][tower['anchor_slots'][0]],
            stored_reference_c2w=C[0], gt_reference_c2w=gt['c2w'][0],
            all_gt_c2w=gt['c2w'], all_gt_valid=gt['valid'], all_anchor_indices=gt['frame_indices'],
            all_exported_unscaled_c2w=C, all_served_metric_c2w=geo.C,
            stored_scale=float(z['scale']), median_scale=scale, served_scale=served_scale,
            rows=rows))
        print(json.dumps(clean({k:v for k,v in captures[-1].items() if k in ['capture','gravity_head_raw','gt_up_in_reference_camera','predicted_image_up_vs_world_up_deg','gt_image_up_vs_world_up_deg','gravity_head_error_vs_gt_deg','guard_margin','gt_guard_margin','rows']})), flush=True)
    (ROOT / 'STATUS.md').write_text('Stage 2: Dataset poses and images confirm inverted or sideways reference frames in both captures. The audit reconstructed serving geometry and replayed each requested row on CPU; it is scoring the corrected labels and the remaining training rows.\n')
    # Stream the existing pricing artifact once, retaining only deployed training results.
    items = []
    path = OUT / 'PER_ITEM.jsonl'
    h = hashlib.sha256()
    with path.open('rb') as f:
        for line in f:
            h.update(line)
            if not line.startswith(b'{"arm": "A0_deployed"'): continue
            r = json.loads(line)
            assert r['split'] == 'train' and r['label'] == labels[r['row_id']]['corrected']
            items.append(dict(row_id=r['row_id'],capture=r['capture'],room=r['room'],dataset=r['dataset'],
                              prediction=r['prediction'],label=r['label'],mra=mra(r['prediction'],r['label'])))
    PINS[str(path)] = h.hexdigest()
    assert len(items) == len({r['row_id'] for r in items}) == 1037
    def stats(rows):
        answered = [r for r in rows if r['prediction'] is not None]
        return dict(rows=len(rows), captures=len({r['capture'] for r in rows}), rooms=len({r['room'] for r in rows}),
                    answered=len(answered), refusals=len(rows)-len(answered),
                    mra_percent=100*float(np.mean([r['mra'] for r in rows])),
                    answered_mra_percent=100*float(np.mean([r['mra'] for r in answered])),
                    within_25_percent=sum(abs(r['prediction']-r['label'])/r['label']<.25 for r in answered),
                    within_50_percent=sum(abs(r['prediction']-r['label'])/r['label']<.5 for r in answered))
    groups = {'two_refused': [r for r in items if r['capture'] in NAMES],
              'other_K1_train': [r for r in items if r['capture'] not in NAMES],
              'other_scannetpp_train': [r for r in items if r['capture'] not in NAMES and r['dataset']=='scannetpp'],
              'all_K1_train': items}
    groups.update({name: [r for r in items if r['capture']==name] for name in NAMES})
    summary = {k:stats(v) for k,v in groups.items()}
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and path.endswith('.py') and path.startswith(tuple(map(str,[TREE,READER,SEL]))): read(path)
    read(__file__); read(ROOT / 'run.sh')
    result = dict(command='bash run.sh audit.py > out/audit.log 2>&1',
                  scope='CPU replay of stored step-544 outputs through A4; no fresh checkpoint prefill or step-200 equivalence claim; comparison is registered K1 training rows only.',
                  conventions='OpenCV image-up = (0,-1,0); the gravity head predicts gravity-UP, not physical downward acceleration. All angles compare vectors in the same frame.',
                  captures=captures, summary=summary,
                  metric='MRA = mean of relative-error passes at strict thresholds 0.50,0.45,...,0.05; refusals score zero.',
                  comparison_rows=items,
                  verdict='Reader right about admitting these camera orientations; both partly on quality: the guard detects a real sign but wrongly treats it as invalid geometry, while the reader serves inaccurate distances.',
                  fix='Share one converter/reader geometry contract that accepts arbitrary camera roll and keeps finite/proper-rotation/intrinsic checks; diagnose gravity error separately and evaluate distance accuracy against corrected labels.',
                  limitations=['No independent gravity/IMU field in either manifest GT NPZ; gravity direction is derived from z-up GT poses.', 'The 32.73 and 10.08 degree gravity errors are real, but these observations do not isolate their contribution to distance error.'],
                  input_sha256=PINS)
    (ROOT / 'out/GUARD.json').write_text(json.dumps(clean(result), indent=2, allow_nan=False)+'\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
