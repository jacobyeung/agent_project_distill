"""Convert supplied hrp_rows witnesses; never regenerate target pairs."""
import argparse
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path
import numpy as np
from .ground_v312 import load_backend, wrap, RowRefusal
from .ground_v313 import point_line, pair_distance, surface_support
from .calculator import PrintedPointRegistry
from .ground_v312_tokens import tokenizer_for_rows


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_pin(pin):
    path = Path(pin['path'])
    if not path.resolve().is_relative_to('/scratch'):
        raise ValueError('Only named scratch assets are supported')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('source_pin_mismatch')
    return data


def visible(geometry, world, frame, mask, *, z_tolerance_m=.01):
    """Project into the native first-hit raster, with instance and z-buffer gates."""
    point = np.asarray(world, float)
    R, t = geometry.cam(frame)
    pc = (point-t) @ R
    if not np.isfinite(pc).all() or pc[2] <= 0:
        return dict(visible=False, reason='invalid_or_behind_camera')
    p = pc @ geometry.K[frame-1].T
    xy = p[:2]/p[2]
    h, w = geometry.depth.shape[1:]
    if not (0 <= xy[0] < w and 0 <= xy[1] < h):
        return dict(visible=False, reason='outside_image')
    x, y = np.floor(xy).astype(int)
    d = float(geometry.depth[frame-1, y, x])
    if not bool(mask[frame-1, y, x]):
        return dict(visible=False, reason='wrong_instance_or_silhouette')
    if not np.isfinite(d) or d <= 0 or abs(d-pc[2]) > z_tolerance_m:
        return dict(visible=False, reason='occluded_or_invalid_depth')
    uv = [(x+.5)*1000/w, (y+.5)*1000/h]
    lifted = geometry.lift(frame, [uv], patch=False)[0][0]
    return dict(visible=True, pixel=[int(x), int(y)], projected_pixel=xy.tolist(),
                uv=uv, depth_residual_m=float(abs(d-pc[2])),
                roundtrip_error_m=float(np.linalg.norm(lifted-point)),
                pixel_region_0_1000=[[x*1000/w,y*1000/h],[(x+1)*1000/w,(y+1)*1000/h]])


def pair_allowed(points, reference_m, *, tolerance_m=1e-6):
    return bool(abs(float(np.linalg.norm(np.asarray(points[0])-points[1]))-reference_m) <= tolerance_m)


def convert(pairs_path, review_path, summary_path, *, hrp_root, backend_path, tokenizer_path):
    # Import the target owner's adapters, not another implementation of them.
    sys.path.insert(0, str(Path(hrp_root)/'work'))
    import hrp
    import keypoints
    pairs = [json.loads(l) for l in Path(pairs_path).read_text().splitlines()]
    review = [json.loads(l) for l in Path(review_path).read_text().splitlines()]
    summary = json.loads(Path(summary_path).read_text())
    backend = load_backend(backend_path)
    tokenizer = tokenizer_for_rows(tokenizer_path)
    from tokenizers import AddedToken
    for opener in ('<surface_pair', '<extent_ends'):
        tokenizer.add_tokens([AddedToken(opener, normalized=False, special=False)])
    # local_sources carries exact 32-frame source indices and the mask encoding.
    entries = {e['scene']:e for e in json.loads((Path(hrp_root)/'out/local_sources.json').read_text())}
    outputs, refusals, cache = [], [], {}
    for pair in pairs:
        scene = pair['scene']
        source_rows = []
        for iid, witness in zip(pair['instances'], pair['witnesses']):
            matches = [r for r in review if r['dataset']+'/'+r['scene']==scene
                and r['keypoint']['family']=='nearest_surface'
                and r['keypoint']['instance_id']==iid
                and r['keypoint']['detail']['pair']==pair['instances']
                and r['keypoint']['witness']==witness]
            if len(matches) != 1:
                raise RowRefusal('missing_or_duplicate_hrp_witness_join')
            source_rows.append(matches[0])
        pins = source_rows[0]['provenance']['inputs']
        if any(r['provenance']['inputs'] != pins for r in source_rows):
            raise RowRefusal('pair_geometry_pin_mismatch')
        if scene not in cache:
            with np.load(io.BytesIO(read_pin(pins['depth'])), allow_pickle=False) as z:
                depth = z['depth']
            with np.load(io.BytesIO(read_pin(pins['calibration'])), allow_pickle=False) as z:
                K, poses, indices, hw = z['intrinsics'], z['camera_poses'], z['indices'], z['raster_hw']
            entry = entries[scene]
            if indices.tolist() != entry['frame_indices'] or len(indices) != 32:
                raise RowRefusal('source_frame_mismatch')
            if entry['mask'] != pins['mask']:
                raise RowRefusal('mask_pin_mismatch')
            K = np.diag([depth.shape[2]/hw[1], depth.shape[1]/hw[0], 1]) @ K
            geo = keypoints.Geometry(depth, K, poses)
            masks, labels, used, frames, _ = hrp.decode_source(entry, hrp.Reader(rate=8_000_000))
            cache[scene] = (geo, masks, labels, used, frames, indices)
        geo, masks, labels, used, frames, indices = cache[scene]
        checks = []
        for iid, label, witness, source in zip(pair['instances'],pair['labels'],pair['witnesses'],source_rows):
            slot = witness['slot']
            if (not used[slot] or labels[iid] != label or source['student_input']['frame_indices'] != [int(indices[slot])]
                    or frames[slot]['sha256'] != witness['frame_sha256']):
                raise RowRefusal('instance_or_frame_binding_mismatch')
            check = visible(geo, witness['world'], slot+1, masks[iid])
            if not check['visible'] or check['roundtrip_error_m'] > 1e-6:
                refusals.append(dict(scene=scene, instances=pair['instances'], reason=check))
                break
            # The integer 0..1000 target must address the same native raster cell.
            x, y = geo.px([witness['uv']])
            if [int(x[0]), int(y[0])] != check['pixel']:
                raise RowRefusal('source_uv_pixel_mismatch')
            checks.append(check)
        if len(checks) != 2:
            continue
        positions = [w['world'] for w in pair['witnesses']]
        if not pair_allowed(positions, pair['observed_gt_surface_gap_m']):
            raise RowRefusal('source_pair_distance_mismatch')
        registry = PrintedPointRegistry()
        a,b = pair['labels']
        # This target is a call-response fragment. Prerequisite grounding is context,
        # and P1/P2 are reserved by those calls in a full trace.
        for label, witness in zip(pair['labels'], pair['witnesses']):
            camera, f1 = backend.public_centres(geo, witness['slot']+1, np.asarray(witness['world']))
            registry.register(camera=[float(backend.number(x)) for x in camera],
                              f1=[float(backend.number(x)) for x in f1], spread=0., requested_frame=witness['slot']+1)
        support = []
        for iid, w in zip(pair['instances'], pair['witnesses']):
            # Reuse the target owner's native surface lift for this exact frame.
            points, refs = keypoints.cloud(masks[iid], geo, frames)
            support.append(points[refs[:, 0] == w['slot']])
        lines = surface_support(backend, geo, registry, pair['labels'],
                                [w['slot']+1 for w in pair['witnesses']], positions, support)
        if lines is None:
            refusals.append(dict(scene=scene, instances=pair['instances'], reason='surface_facing_or_membership'))
            continue
        body = '\n'.join(lines)
        body += '\nvisible pair distance '+pair_distance(registry, lines[-2:])+'\nfull surface gap unavailable'
        call = f'<surface_pair a="{a}" b="{b}" mode="closest_visible">'
        target = call+'\n'+wrap(body)
        token_count = len(tokenizer.encode(target, add_special_tokens=False).ids)
        if token_count > 5000:
            raise RowRefusal('suffix_cap')
        qid = 'surface313_'+hashlib.sha256(json.dumps([scene,pair['instances']],sort_keys=True).encode()).hexdigest()[:24]
        outputs.append(dict(qid=qid, scene=scene, instances=pair['instances'], labels=pair['labels'],
            target=target, target_kind='call_response_fragment', requires_singular_ground_context=True,
            registry_prefix_labels=['P1','P2'], suffix_tokens=token_count, spec_version='3.13',
            training_admitted=False, reference='observed_gt_depth_surface_union',
            full_surface_target=None, full_surface_status='unavailable_missing_mesh',
            source_qids=[r['qid'] for r in source_rows], source_frame_indices=indices.tolist(),
            witnesses=pair['witnesses'], zbuffer_checks=checks, never_co_visible=pair['never_co_visible'],
            acceptable_pairs=dict(representation='implicit_joint_set', surfaces=pins,
                instances=pair['instances'], frames='all_32_exact_source_frames',
                reference_distance_m=pair['observed_gt_surface_gap_m'], pair_tolerance_m=1e-6,
                z_tolerance_m=.01, membership='observed native instance raster centre-depth samples',
                predicate='both_on_own_surface AND both_visible AND abs(norm(a-b)-reference_distance_m)<=pair_tolerance_m',
                canonical_pair_world=positions),
            provenance=dict(pairs_sha256=sha(pairs_path),review_sha256=sha(review_path),summary_sha256=sha(summary_path),
                keypoints_sha256=sha(Path(hrp_root)/'work/keypoints.py'),hrp_sha256=sha(Path(hrp_root)/'work/hrp.py'),
                backend_sha256=sha(backend_path),tokenizer_sha256=sha(tokenizer_path),inputs=pins),
            loss_spans=[dict(start=0,end=len(call),loss_weight=1),dict(start=len(call)+1,end=len(target),loss_weight=0)]))
    return outputs, dict(converted=len(outputs),refusals=refusals,source_pairs=len(pairs),
        source_reference=summary.get('reference'),training_admitted=False,
        full_surface_targets=0, distinct_scenes=len(cache),max_fragment_tokens=max((r['suffix_tokens'] for r in outputs),default=0))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--hrp-root',required=True);ap.add_argument('--backend',required=True);ap.add_argument('--tokenizer',required=True)
    a=ap.parse_args();src=Path(a.source);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    rows,report=convert(src/'pairs.jsonl',src/'review_rows.jsonl',src/'summary.json',hrp_root=a.hrp_root,
                        backend_path=a.backend,tokenizer_path=a.tokenizer)
    (out/'surface_pair_rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (out/'CONVERSION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
