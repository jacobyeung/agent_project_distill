"""Hash public CPU tool outputs against a pinned receipt; no inference or network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import uuid


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--labels', nargs='+')
    parser.add_argument('--overlap-audit', type=Path)
    parser.add_argument('--overlap-ids', nargs=2, type=int)
    args = parser.parse_args()
    sys.path.insert(0, str(args.package.resolve()))
    def refuse_network(*_args, **_kwargs):
        raise AssertionError('CPU fixture forbids network access')
    socket.socket.connect = refuse_network
    socket.create_connection = refuse_network
    import numpy as np
    import gt_tool_bindings as tools
    from gt_training_r1313 import grounding_provider, load_selected_dense
    from gt_scene_assets import DATA_ROOT, read_json, sha, validate_scene, load_arrays
    root = DATA_ROOT/'runtime_control/gt_teacher_r1313/sparse_collector_fixtures'/str(uuid.uuid4())
    root.mkdir(parents=True)
    os.environ.update(R1313_SCENE_RECEIPT=str(args.receipt.resolve()),
        R1313_SCENE_RECEIPT_SHA256=sha(args.receipt), REQ73_RUN_OUTPUT_ROOT=str(root))
    receipt = validate_scene(read_json(args.receipt), load_dense=True)
    provider = grounding_provider()
    scene = receipt['runtime_scene_id']
    labels = args.labels or sorted({p['label'] for p in receipt['rendering_proof']})
    def normalize(value):
        if isinstance(value, dict):
            return {k: sha(v) if k in ('mask_handle', 'mask_dense_handle') else normalize(v)
                    for k, v in value.items()}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        return value
    snapshot = {'masks': {}, 'boxes': {}, 'points': {}, 'frame_search': {}, 'video': {}}
    for label in labels:
        print('public tools', scene, label, flush=True)
        found = tools.find_frames_with_object.invoke(dict(scene_id=scene, object_label=label, num_frames='all'))
        expected_frames = [i for i in range(1, 33) if provider.visible_instances(scene, i, label)]
        assert found == expected_frames
        endpoints = tools.find_frames_with_object.invoke(dict(scene_id=scene, object_label=label, num_frames='1'))
        assert endpoints == (sorted({found[0], found[-1]}) if found else [])
        snapshot['frame_search'][label] = {'all': found, '1': endpoints,
            '5': tools.find_frames_with_object.invoke(dict(scene_id=scene, object_label=label, num_frames='5'))}
        dense = load_selected_dense(scene)
        for frame in (1, 17, 32):
            key = f'{label}/{frame}'
            request = dict(scene_id=scene, frame_index=frame, object_label=label)
            masks = tools.predict_2d_segmentation_masks.invoke(request)
            boxes = tools.predict_2d_bounding_box.invoke(request)
            points = tools.predict_2d_points.invoke(dict(scene_id=scene, frame_index=frame, query=label))
            assert [m['instance_id'] for m in masks] == [p['instance_id'] for p in points]
            assert len(boxes) == len(masks)
            for mask_row, box, point in zip(masks, boxes, points):
                mask = np.load(mask_row['mask_handle'], allow_pickle=False)
                ys, xs = np.where(mask)
                h, w = mask.shape
                pixel_box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                assert mask_row['bbox_pixels'] == pixel_box
                assert mask_row['mask_pixel_count'] == len(xs)
                assert box == [round(v/d, 3) for v, d in zip(pixel_box, (w, h, w, h))]
                x0, y0, x1, y1 = pixel_box
                center = [round((x0+x1)/(2.0*w), 4), round((y0+y1)/(2.0*h), 4)]
                assert point['pixel_norm'] == center
                px, py = min(w-1, max(0, int(center[0]*w))), min(h-1, max(0, int(center[1]*h)))
                support = dense['mask'][frame-1]
                if not support[py, px]:
                    yy, xx = np.where(support)
                    nearest = np.argmin((yy-py)**2+(xx-px)**2)
                    py, px = int(yy[nearest]), int(xx[nearest])
                assert point['world'] == [round(float(v), 4) for v in dense['pts3d_world'][frame-1, py, px]]
            snapshot['masks'][key] = normalize(masks)
            snapshot['boxes'][key] = boxes
            snapshot['points'][key] = points
        video = tools.predict_2d_segmentation_masks_video.invoke(dict(
            scene_id=scene, object_label=label, frame_indices=[1, 17, 32]))
        for frame in (1, 17, 32):
            assert normalize(video['frames'][frame]) == snapshot['masks'][f'{label}/{frame}']
        snapshot['video'][label] = normalize(video)
    proofs = []
    for proof in receipt['rendering_proof']:
        rendered = provider._render_instance(scene, proof['slot_1based'], proof['instance_id'])
        np.testing.assert_array_equal(rendered['mask'], load_arrays(proof['arrays'])['mask'])
        assert rendered['mask_pixel_count'] == proof['visible_mask_pixels']
        proofs.append({k: proof[k] for k in ('instance_id', 'slot_1based', 'visible_mask_pixels')})
    result = {'receipt_sha256': sha(args.receipt), 'scene': scene, 'labels': labels,
              'frames': [1, 17, 32], 'snapshot': snapshot, 'proofs': proofs,
              'hashes': {k: digest(v) for k, v in snapshot.items()}, 'combined_sha256': digest(snapshot)}
    if args.overlap_audit:
        result['overlap'] = check_overlap(args, provider, receipt, root)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print('PASS', result['combined_sha256'], flush=True)


def check_overlap(args, provider, receipt, root):
    import numpy as np
    from gt_scene_assets import read_json, sha, save_arrays, verify
    from gt_training_r1313 import TrainingGrounding
    from mesh_membership import instance_faces
    scene = receipt['runtime_scene_id']
    mesh = provider._instance_mesh(scene)
    audit = read_json(args.overlap_audit)
    assert set(mesh['membership_instance_ids'].tolist()) == {r['instance_id'] for r in audit['instances']}
    for row in audit['instances']:
        selected = instance_faces(mesh, row['instance_id'])
        assert len(selected) == row['faces']
        assert hashlib.sha256(selected.astype(np.int64).tobytes()).hexdigest() == row['face_set_sha256']
    counts = np.bincount(mesh['membership_face_indices'].astype(np.int64), minlength=len(mesh['faces']))
    assert int((counts > 1).sum()) == audit['shared_faces']
    assert int(counts.sum()) == audit['face_memberships']
    provenance = read_json(receipt['source_provenance']['path'])
    raw = provenance['raw_sources']
    # Read the official source annotations and segments without using a CSR builder.
    source_annotation = verify(audit['source_annotation'], prepared=False)
    groups = read_json(source_annotation)['segGroups']
    segments_path = source_annotation.with_name('segments.json')
    segment_spec = next(v for v in raw.values() if Path(v['path']) == segments_path)
    verify(segment_spec, prepared=False)
    segments = np.asarray(read_json(segments_path)['segIndices'], np.int64)
    ids = args.overlap_ids
    expected = {}
    oracles = {}
    for iid in ids:
        group = next(g for g in groups if int(g.get('objectId', g['id'])) == iid)
        member = np.isin(segments, group['segments'])
        selected = np.flatnonzero(member if len(segments) == len(mesh['faces']) else member[mesh['faces']].all(axis=1))
        np.testing.assert_array_equal(selected, instance_faces(mesh, iid))
        expected[iid] = selected
        face_ids = np.full(len(mesh['faces']), -1, np.int32)
        face_ids[selected] = iid
        asset = save_arrays(root/f'oracle_{iid}.npz', vertices_world=mesh['vertices'],
                            faces=mesh['faces'], face_instance_ids=face_ids)
        oracles[iid] = TrainingGrounding(dict(receipt, instance_mesh=asset))
    shared = np.intersect1d(*expected.values(), assume_unique=True)
    assert len(shared)
    # A shared-only dense oracle attributes common visible pixels to shared source faces.
    shared_ids = np.full(len(mesh['faces']), -1, np.int32)
    shared_ids[shared] = ids[0]
    asset = save_arrays(root/'shared_oracle.npz', vertices_world=mesh['vertices'],
                       faces=mesh['faces'], face_instance_ids=shared_ids)
    shared_provider = TrainingGrounding(dict(receipt, instance_mesh=asset))
    witness = None
    for frame in range(1, 33):
        actual = [provider._render_instance(scene, frame, iid) for iid in ids]
        for iid, rendered in zip(ids, actual):
            oracle = oracles[iid]._render_instance(scene, frame, iid)
            assert (rendered is None) == (oracle is None)
            if rendered:
                np.testing.assert_array_equal(rendered['mask'], oracle['mask'])
                assert rendered['bbox_pixels'] == oracle['bbox_pixels']
        shared_render = shared_provider._render_instance(scene, frame, ids[0])
        if shared_render and all(r is not None for r in actual):
            visible_shared = shared_render['mask'] & actual[0]['mask'] & actual[1]['mask']
            if visible_shared.any() and witness is None:
                y, x = np.argwhere(visible_shared)[0]
                witness = {'frame': frame, 'pixel_xy': [int(x), int(y)],
                           'common_visible_pixels': int(visible_shared.sum())}
    assert witness is not None, 'no shared face contributes visible pixels to both instances'
    # Isolate one shared source face to identify an explicit common-pixel witness.
    frame = witness['frame']
    actual = [provider._render_instance(scene, frame, iid) for iid in ids]
    single_mesh = shared_provider._instance_mesh(scene)
    single_mesh['instance_ids'].fill(-1)
    for face in shared:
        single_mesh['instance_ids'][face] = ids[0]
        shared_provider._masks.clear()
        single = shared_provider._render_instance(scene, frame, ids[0])
        single_mesh['instance_ids'][face] = -1
        common = None if single is None else single['mask'] & actual[0]['mask'] & actual[1]['mask']
        if common is not None and common.any():
            y, x = np.argwhere(common)[0]
            witness.update(source_face_index=int(face), pixel_xy=[int(x), int(y)])
            break
    assert 'source_face_index' in witness
    import gt_tool_bindings as tools
    for iid, rendered in zip(ids, actual):
        label = provider._inventory(scene)['labels'][iid]
        masks = tools.predict_2d_segmentation_masks.invoke(dict(scene_id=scene, frame_index=frame, object_label=label))
        target = next(m for m in masks if m['instance_id'] == iid)
        np.testing.assert_array_equal(np.load(target['mask_handle'], allow_pickle=False), rendered['mask'])
        boxes = tools.predict_2d_bounding_box.invoke(dict(scene_id=scene, frame_index=frame, object_label=label))
        points = tools.predict_2d_points.invoke(dict(scene_id=scene, frame_index=frame, query=label))
        slot = next(n for n, p in enumerate(points) if p['instance_id'] == iid)
        x0, y0, x1, y1 = rendered['bbox_pixels']
        w, h = rendered['frame_size']
        assert boxes[slot] == [round(x0/w, 3), round(y0/h, 3), round(x1/w, 3), round(y1/h, 3)]
        assert points[slot]['pixel_norm'] == [round((x0+x1)/(2*w), 4), round((y0+y1)/(2*h), 4)]
    return {'audit_sha256': sha(args.overlap_audit), 'official_instances': len(audit['instances']),
            'shared_faces': audit['shared_faces'], 'face_memberships': audit['face_memberships'],
            'all_face_set_hashes_match_audit': True, 'oracle_frames': 32,
            'instance_ids': ids, 'pair_shared_faces': len(shared), 'witness': witness}


if __name__ == '__main__':
    main()
