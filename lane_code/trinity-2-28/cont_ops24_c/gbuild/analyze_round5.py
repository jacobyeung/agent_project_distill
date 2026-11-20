"""CPU camera audit. Only small NPZ members are loaded; no raster or RGB reads."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import resource
resource.setrlimit(resource.RLIMIT_AS, (15 * 1024**3, 15 * 1024**3))
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from gpkg.capture_io import Records
from gt.v2 import alignment

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'cap/score_t2'
PAY = ROOT / 'work/payload'
FRAMES = PAY / 'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
DENSE = PAY / 'b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
FLIP = np.diag([1., -1., -1., 1.])
WORLD = np.array([[1.,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]])
HYPOTHESES = {
    'c2w_cv': dict(invert=False, flip=False, evidence='c2w field; native.prepare_native requires opencv_c2w_raw_z_up_m; exact builder lineage unavailable'),
    'c2w_gl': dict(invert=False, flip=True, evidence='requested ARKit/OpenGL ambiguity; no exact-builder evidence; diagnostic only'),
    'w2c_cv': dict(invert=True, flip=False, evidence='requested direction ambiguity; contrary to c2w field and available builder; negative control'),
    'w2c_gl': dict(invert=True, flip=True, evidence='combined requested ambiguities; contrary to available builder; negative control'),
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def converted(poses, name):
    h = HYPOTHESES[name]
    result = np.linalg.inv(poses) if h['invert'] else np.array(poses, float, copy=True)
    return result @ FLIP if h['flip'] else result


def angles(rotations):
    return np.degrees(np.arccos(np.clip((np.trace(rotations, axis1=-2, axis2=-1)-1)/2, -1, 1)))


def residuals(a, b, R, scale=1.):
    x, y = a[:, :3, 3], b[:, :3, 3]
    t = y.mean(0) - scale * R @ x.mean(0)
    e = np.linalg.norm(scale * x @ R.T + t - y, axis=1)
    q = angles((R @ a[:, :3, :3]) @ b[:, :3, :3].transpose(0,2,1))
    return dict(scale=float(scale), translation_rms_m=float(np.sqrt(np.mean(e**2))),
                translation_residual_m=e.tolist(), rotation_rms_deg=float(np.sqrt(np.mean(q**2))),
                rotation_max_deg=float(q.max()), rotation_residual_deg=q.tolist(),
                rotation=R.tolist(), translation=t.tolist())


def diagnostics(a, b):
    rigid = alignment(a, b)
    R = np.asarray(rigid['reader_world_to_gt_world'])[:3, :3]
    x, y = a[:, :3, 3], b[:, :3, 3]
    xc, yc = x-x.mean(0), y-y.mean(0)
    # Umeyama scale with a proper rotation; diagnostic only, never an S4 transform.
    scale = np.sum((xc @ R.T) * yc) / np.sum(xc**2)
    sim = residuals(a, b, R, scale)
    sim['would_meet_numeric_ruling'] = bool(sim['translation_rms_m'] <= .10 and sim['rotation_max_deg'] <= 5)
    # Independent rotation-consistency fit: chordal SO(3) mean of B_i A_i^T.
    # This has no arbitrary metre/radian weight and is never used for stage acceptance.
    u, _, vt = np.linalg.svd(np.sum(b[:,:3,:3] @ a[:,:3,:3].transpose(0,2,1), axis=0))
    Q = u @ np.diag([1.,1.,np.linalg.det(u @ vt)]) @ vt
    rot = residuals(a, b, Q)
    rot['center_fit_rotation_difference_deg'] = float(angles(Q @ R.T))
    aa = a[:,:3,:3]; bb = b[:,:3,:3]
    ra = angles(aa[:,None].transpose(0,1,3,2) @ aa[None,:])
    rb = angles(bb[:,None].transpose(0,1,3,2) @ bb[None,:])
    delta = np.abs(ra-rb)
    pair = np.unravel_index(delta.argmax(), delta.shape)
    # Each accepted anchor has <=5 deg error, so every pair differs by <=10 deg.
    pairwise = dict(max_relative_angle_disagreement_deg=float(delta.max()),
                    anchor_slots_zero_based=list(map(int,pair)),
                    excludes_any_fixed_world_and_camera_axis_rotation=bool(delta.max()>10.001))
    return dict(rigid=rigid, similarity_diagnostic=sim, rotation_only_diagnostic=rot,
                pairwise_rotation_invariant=pairwise,
                center_singular_values=np.linalg.svd(xc,compute_uv=False).tolist())


def extract():
    refs = {r['item_id']:r for r in read(ROOT/'kit2/kit/rerun2/items544.json')['items']}
    groups = defaultdict(list)
    records = Records(ROOT.parent/'cap/t2.gz', ROOT.parent/'cap/t2ret/CAPTURE.json')
    counts = Counter()
    for row in records:
        counts[row['arm']] += 1
        ref = refs[row['item_id']]
        assert row['capture'] == ref['capture']
        assert row['source_indices'] == ref['source_indices']
        if row['arm'] not in ('points', 'restricted_selector'):
            continue
        g = row['geometry']
        if g:
            assert g['source_indices'] == row['source_indices']
            a, u = np.asarray(g['camera_to_world_metric']), np.asarray(g['camera_to_world_unscaled'])
            assert np.allclose(a[:,:3,3], u[:,:3,3] * g['scale'], atol=1e-10, rtol=1e-10)
            assert np.array_equal(a[:,:3,:3], u[:,:3,:3])
            assert g['pose_scale_count'] == g['depth_scale_count'] == 1
        groups[row['capture']].append(dict(item_id=row['item_id'], arm=row['arm'],
            source_indices=row['source_indices'], dense_indices=row['dense_indices'], geometry=g))
    assert counts == dict(points=150, restricted_selector=150, text_noise=10)
    assert not records.report['salvaged']
    parity = read(ROOT.parent/'cap/t2ret/PARITY.json')
    assert records.report['raw_sha256'] == parity['capture_sha256']
    result = dict(schema='t2-camera-audit-input-v1', capture_read=records.report,
                  counts=dict(counts), captures=dict(groups))
    write_new(OUT/'CAMERAS_T2_R5.json', result)
    print(json.dumps(dict(extracted_records=records.report['records'], captures=len(groups))), flush=True)


def analyze():
    start = time.monotonic()
    cache = read(OUT/'CAMERAS_T2_R5.json')
    refs = read(ROOT/'kit2/kit/rerun2/items544.json')['items']
    truth = read(ROOT/'out2/GT.json')
    previous = {v['capture']:v for v in read(OUT/'STAGES_T2.json')['alignments']}
    frames = {c['native']:c for c in read(FRAMES)['captures']}
    dense = read(DENSE)['captures']
    bindings = {b['item_id']:b for b in read(ROOT.parent/'cap/t2ret/PARITY.json')['bindings']}
    files = read(ROOT/'kit2/kit/rerun2/gt_staging.json')['files']
    results, missing = [], []
    members_read = 0
    for entry in files:
        capture = entry['capture']
        path = ROOT.parent/'gt'/entry['relative_path']
        if not path.is_file():
            missing.append(capture)
            continue
        rr = [r for r in refs if r['capture']==capture]
        rows = cache['captures'][capture]
        with np.load(path, allow_pickle=False) as z:
            fields = z.files
            source, b, valid = z['frame_indices'], z['c2w'].astype(float), z['valid']
            members_read += sum(z.zip.getinfo(k+'.npy').compress_size for k in ('frame_indices','c2w','valid'))
        source = source.tolist()
        assert source == truth[capture]['source_indices']
        assert np.array_equal(b, np.asarray(truth[capture]['c2w']))
        native = rr[0]['task']['native']; c, d = frames[native], dense[native]
        assert c['scene'] == capture
        checks = dict(npz_vs_task=all(source==r['task']['source_frame_indices'] for r in rr),
                      npz_vs_reference=all(source==r['source_indices'] for r in rr),
                      npz_vs_capture=all(source==r['source_indices'] for r in rows),
                      npz_vs_rgb_manifest=source==c['anchor_indices']==[f['index'] for f in c['frames']],
                      npz_vs_dense_slots=source==[d['frames'][s]['index'] for s in d['anchor_slots']],
                      dense_hashes_vs_anchors=[d['frames'][s]['sha256'] for s in d['anchor_slots']]==[f['sha256'] for f in c['frames']],
                      captured_dense_indices=all(r['dense_indices']==[f['index'] for f in d['frames']] for r in rows),
                      receipt_rgb_hashes=all(bindings[r['item_id']]['frame_hashes_match'] and
                          bindings[r['item_id']]['bound_anchor_sha256']==bindings[r['item_id']]['expected_anchor_sha256']==[f['sha256'] for f in c['frames']] for r in rr))
        observed = [r for r in rows if r['geometry']]
        checks['npz_vs_geometry'] = all(r['geometry']['source_indices']==source for r in observed)
        assert all(checks.values()), (capture, checks)
        a = np.asarray(observed[0]['geometry']['camera_to_world_metric'])
        identical = all(np.array_equal(a,r['geometry']['camera_to_world_metric']) for r in observed)
        assert identical, 'Do not silently collapse distinct camera arrays'
        fits = {h:diagnostics(a,converted(b,h)) for h in HYPOTHESES}
        base = fits['c2w_cv']['rigid']
        for metric in ('translation_rms_m','rotation_rms_deg','rotation_max_deg'):
            assert abs(base[metric]-previous[capture][metric]) < 1e-5, (capture,metric)
        assert base['accepted'] == previous[capture]['accepted']
        # A common proper world-up change cannot alter either residual.
        world = alignment(a, WORLD @ b)
        invariant = {k:abs(world[k]-base[k]) for k in ('translation_rms_m','rotation_rms_deg','rotation_max_deg')}
        assert max(invariant.values()) < 1e-5
        g = observed[0]['geometry']
        results.append(dict(capture=capture,dataset=capture.split('/')[0],npz_path=str(path),
            npz_fields=fields, pose_array_sha256=hashlib.sha256(b.tobytes()).hexdigest(),
            frame_binding=dict(checks=checks,source_indices=source,source_numbering_verified=False,
                reason='NPZ has no native frame-ID/timestamp/RGB-hash map; exact source calibration/selection sidecar absent',
                fps=c['fps'],timestamps=c['timestamps'],timestamps_are_index_over_fps=bool(np.allclose(c['timestamps'],np.array(source)/c['fps'])),
                total_num_frames=c['total_num_frames'],total_num_frames_lower_bound=c.get('total_num_frames_lower_bound',False),
                original_frame_ids_or_timestamps_available=False,
                offsets_or_permutations_tested=[],same_order=True,valid_frames=int(valid.sum()),
                records_with_geometry=len(observed),records_without_geometry=len(rows)-len(observed),
                unique_camera_arrays=1,reader_rgb_hw=c['hw'],gt_orientation=truth[capture]['orientation'],
                rgb_frames=c['frames'],dense_anchor_slots=d['anchor_slots']),
            reader=dict(scale=g['scale'],camera_axes=g['camera_axes'],world_axes=g['world_axes'],
                        depth_scale_count=g['depth_scale_count'],pose_scale_count=g['pose_scale_count'],
                        single_scale_application_verified=True),
            hypotheses=fits,world_up_control=dict(transform=WORLD.tolist(),residual_absolute_deltas=invariant)))
    summaries = {}
    for dataset in sorted({r['dataset'] for r in results}):
        group = [r for r in results if r['dataset']==dataset]
        summaries[dataset] = dict(captures=len(group), hypotheses={})
        for h in HYPOTHESES:
            fs = [r['hypotheses'][h] for r in group]
            summaries[dataset]['hypotheses'][h] = dict(
                rigid_accepted=sum(f['rigid']['accepted'] for f in fs),
                median_translation_rms_m=float(np.median([f['rigid']['translation_rms_m'] for f in fs])),
                median_rotation_max_deg=float(np.median([f['rigid']['rotation_max_deg'] for f in fs])),
                similarity_scales=[f['similarity_diagnostic']['scale'] for f in fs],
                similarity_numeric_passes=sum(f['similarity_diagnostic']['would_meet_numeric_ruling'] for f in fs),
                rotation_invariant_exclusions=sum(f['pairwise_rotation_invariant']['excludes_any_fixed_world_and_camera_axis_rotation'] for f in fs))
    source_paths = [ROOT/'gt/v2.py',Path(__file__),ROOT/'kit2/kit/rerun2/items544.json',
        FRAMES,DENSE,ROOT.parent/'cap/t2ret/PARITY.json',ROOT/'out2/GT.json',OUT/'STAGES_T2.json',
        PAY/'b/e2e_reader/parity.py',PAY/'b/e2e_reader/geometry.py',PAY/'tree/student_pilot/_tower_native.py',
        PAY/'tree/student_pilot/camera_targets.py',PAY/'tree/student_pilot/geometry_profiles.py',
        PAY/'tree/generator/derivgen_v7/derivgen/native.py',PAY/'tree/student_pilot/g3t_vendor/vggt/utils/pose_enc.py']
    result = dict(schema='t2-camera-conventions-r5',capture_read=cache['capture_read'],
        hypotheses=HYPOTHESES,summary=summaries,captures=results,missing_gt=missing,
        decision=dict(change_gt_v2=False,selected_convention_by_fit=False,
            convention_table={d:dict(current='c2w_cv',change=None,exact_builder_lineage_verified=False) for d in summaries},
            stage_join_rerun=False,reason='No tested alternative establishes a dataset-wide repair; source numbering remains unverified'),
        provenance={str(p):sha(p) for p in source_paths},
        resources=dict(seconds=time.monotonic()-start,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            npz_compressed_member_bytes_read=members_read,threads=1,gpu_used=False,rasters_loaded=False))
    write_new(OUT/'CAMERA_CONVENTIONS_T2.json',result)
    print(json.dumps(dict(summary=summaries,resources=result['resources'])),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('mode',choices=['extract','analyze'])
    args = p.parse_args()
    (extract if args.mode=='extract' else analyze)()
