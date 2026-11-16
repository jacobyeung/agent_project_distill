from __future__ import annotations
import argparse
import contextlib
import copy
import json
import os
import socket
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np


class ARKitAdapterTests(unittest.TestCase):
    output = None

    @classmethod
    def setUpClass(cls):
        import gt_scene_assets
        import training_assets
        from arkit_fixtures import make_fixture
        from prepare_corpus import prepare
        cls.stack = contextlib.ExitStack()
        cls.addClassCleanup(cls.stack.close)
        cls.stack.enter_context(patch.object(gt_scene_assets, 'DATA_ROOT', cls.output))
        cls.stack.enter_context(patch.object(training_assets, 'DATA_ROOT', cls.output))
        cls.stack.enter_context(patch.object(training_assets, '_SCENE', None))
        cls.args = make_fixture(cls.output / 'positive')
        cls.prepared = prepare(cls.args)
        cls.receipt = gt_scene_assets.validate_scene(gt_scene_assets.read_json(cls.prepared['receipt']['path']), load_dense=True)
        cls.scene = cls.receipt['runtime_scene_id']
        cls.stack.enter_context(patch.dict(os.environ, {
            'R1313_SCENE_RECEIPT': cls.prepared['receipt']['path'],
            'R1313_SCENE_RECEIPT_SHA256': cls.prepared['receipt']['sha256'],
            'REQ73_RUN_OUTPUT_ROOT': str(cls.output / 'tool_runtime'), 'CUDA_VISIBLE_DEVICES': ''}))
        import gt_tool_bindings
        from gt_training_r1313 import grounding_provider
        cls.tools = gt_tool_bindings
        cls.provider = grounding_provider()
        cls.source = gt_scene_assets.load_arrays(cls.receipt['dense'])
        with np.load(cls.args.frames_receipt.parent / 'analytic_oracle.npz', allow_pickle=False) as stored:
            cls.oracle = {key: stored[key] for key in stored.files}

    def test_preparer_is_available(self):
        from prepare_corpus import prepare
        from prepare_arkit_scene import prepare as prepare_arkit
        from arkit_source import parse_annotations, parse_trajectory
        self.assertTrue(all(callable(item) for item in (prepare, prepare_arkit, parse_annotations, parse_trajectory)))

    def test_unchanged_scene_and_registry_schemas(self):
        from collect import registry_rows
        from gt_scene_assets import ASSET_KEYS, read_json, verify
        expected = set(ASSET_KEYS) | {'schema', 'round', 'dataset', 'scene_name', 'runtime_scene_id', 'frames', 'image_count',
            'selected_frames', 'geometry_source', 'coordinate_frame', 'gravity_up', 'student_observations',
            'teacher_initial_observations', 'rendering_proof'}
        self.assertEqual(set(self.receipt), expected)
        self.assertEqual(self.receipt['schema'], 'r1313-scene-assets-v1')
        registry = read_json(verify(self.prepared['registry']))
        self.assertEqual(set(registry), {'schema', 'round', 'receipts'})
        self.assertEqual(registry['schema'], 'r1313-assets-registry-v1')
        rows = registry_rows({'assets_registry': self.prepared['registry']['path']})
        self.assertEqual(rows, {('arkitscenes', self.args.scene): self.prepared['receipt']})

    def test_exact_camera_and_rgb_correspondence(self):
        from arkit_fixtures import ORDINALS
        from gt_scene_assets import load_arrays, read_json, verify
        alignment = read_json(verify(self.receipt['alignment']))
        calibration = load_arrays(self.receipt['calibration'])
        self.assertEqual(len(alignment['frames']), 32)
        self.assertEqual(alignment['validated_slots'], 32)
        self.assertEqual(alignment['pose_field'], 'aligned_pose')
        self.assertFalse(alignment['estimated_geometry_used'])
        self.assertEqual(self.source['indices'].tolist(), ORDINALS)
        self.assertTrue(np.allclose(calibration['camera_poses'], self.oracle['camera_poses'], atol=1e-6, rtol=0))
        self.assertTrue(np.allclose(calibration['intrinsics'], [[90, 0, 64], [0, 92, 48], [0, 0, 1]], atol=1e-6))
        self.assertEqual(calibration['raster_hw'].tolist(), [96, 128])
        for row in alignment['frames']:
            self.assertTrue(row['selected_png_matches_vsi_decode'])
            self.assertGreaterEqual(row['raw_to_vsi_correlation'], 0.99)
            self.assertLessEqual(row['raw_to_vsi_mae'], 8)
            self.assertEqual(row['pose_timestamp_delta_sec'], 0)
            self.assertEqual(row['intrinsics_timestamp_delta_sec'], 0)
            self.assertEqual(row['source_ordinal'], row['ordinal'])
            expected = np.asarray(row['source_to_vsi']) @ row['source_intrinsic']
            self.assertTrue(np.allclose(expected, row['target_intrinsic']))

    def test_official_obb_axis_and_half_extent_conversion(self):
        from arkit_fixtures import source_objects
        from gt_scene_assets import read_json, verify
        inventory = self.provider._inventory(self.scene)
        provenance = read_json(verify(self.receipt['source_provenance']))
        identities = {row['source_uid']: row['instance_id'] for row in provenance['instance_uid_mapping']}
        self.assertEqual(identities, {'uid-a-table': 0, 'uid-b-chair': 1})
        signs = np.asarray([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
                            [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]])
        for item in source_objects():
            iid = identities[item['uid']]
            box = item['segments']['obbAligned']
            axes = np.asarray(box['normalizedAxes']).reshape(3, 3)
            expected = (axes.T @ (signs * (np.asarray(box['axesLengths']) / 2)).T).T + box['centroid']
            self.assertTrue(np.allclose(self.provider._obb_corners(self.scene, iid), expected, atol=1e-7))
            self.assertEqual(inventory['labels'][iid], item['label'])
        self.assertFalse(provenance['native_instance_segmentation_available'])
        self.assertEqual(provenance['source_obb_scale_factor'], 0.5)

    def test_teacher_search_box_mask_points_and_video(self):
        from arkit_fixtures import write_json
        trace, results, overlap = [], {}, []
        config = {'configurable': {'trace_list': trace}}
        for label, iid in (('chair', 1), ('table', 0)):
            found = self.tools.find_frames_with_object.invoke({'scene_id': self.scene, 'object_label': label, 'num_frames': 'all'}, config=config)
            self.assertEqual(found, self.provider.find_frames(self.scene, label, 'all'))
            self.assertEqual(found, list(range(1, 33)))
            args = {'scene_id': self.scene, 'frame_index': 1, 'object_label': label}
            boxes = self.tools.predict_2d_bounding_box.invoke(args, config=config)
            self.assertEqual(boxes, self.provider.boxes(self.scene, 1, label))
            self.assertEqual(len(boxes), 1)
            self.assertTrue(all(0 <= value <= 1 for value in boxes[0]))
            points = self.tools.predict_2d_points.invoke({'scene_id': self.scene, 'frame_index': 1, 'query': label}, config=config)
            self.assertEqual([row['instance_id'] for row in points], [iid])
            self.assertTrue(np.isfinite(points[0]['world']).all())
            masks = self.tools.predict_2d_segmentation_masks.invoke(args, config=config)
            self.assertEqual([row['instance_id'] for row in masks], [iid])
            self.assertEqual(masks[0]['mask_dense_shape'], [96, 128])
            self.assertEqual(masks[0]['mask_handle'], masks[0]['mask_dense_handle'])
            video = self.tools.predict_2d_segmentation_masks_video.invoke({'scene_id': self.scene, 'object_label': label, 'frame_indices': [1, 17, 32]}, config=config)
            self.assertEqual(video['n_unique_instances'], 1)
            self.assertEqual(video['instance_persistence'], {iid: 3})
            for frame in (1, 17, 32):
                self.assertEqual(video['frames'][frame][0]['instance_id'], iid)
                mask = np.load(video['frames'][frame][0]['mask_handle'], allow_pickle=False)
                truth = self.oracle['instance_ids'][frame - 1] == iid
                iou = float((mask & truth).sum() / (mask | truth).sum())
                self.assertGreater(iou, 0.65)
                overlap.append({'label': label, 'slot': frame, 'analytic_mask_iou': iou})
            results[label] = {'frames': found, 'boxes': boxes, 'points': points, 'masks': masks, 'video': video}
        self.assertEqual(len(trace), 10)
        self.assertTrue(all(row['event'] == 'gt_perception' and row['status'] == 'ok' for row in trace))
        self.assertTrue(all(row['scene_receipt_sha256'] == self.prepared['receipt']['sha256'] for row in trace))
        write_json(self.output / 'tool_calls.json', {'tools': results, 'telemetry': trace, 'independent_mask_checks': overlap})

    def test_canonical_geometry_preserves_camera_coordinates(self):
        from gt_training_r1313 import load_selected_dense
        dense = load_selected_dense(self.scene)
        self.assertTrue(np.allclose(dense['camera_poses'][0, :3, 3], 0, atol=1e-6))
        self.assertAlmostEqual(float(dense['camera_poses'][0, 0, 2]), 0, places=6)
        self.assertGreater(dense['camera_poses'][0, 1, 2], 0)
        self.assertTrue(np.array_equal(dense['mask'], self.source['mask']))
        self.assertTrue(np.array_equal(dense['conf'], self.source['mask'].astype(np.float32)))
        self.assertFalse(dense['pts3d_world'].flags.writeable)
        for slot in range(32):
            ys, xs = np.where(self.source['mask'][slot])
            ys, xs = ys[::29], xs[::29]
            a, b = self.source['camera_poses'][slot], dense['camera_poses'][slot]
            first = (self.source['pts3d_world'][slot, ys, xs] - a[:3, 3]) @ a[:3, :3]
            second = (dense['pts3d_world'][slot, ys, xs] - b[:3, 3]) @ b[:3, :3]
            self.assertTrue(np.allclose(first, second, atol=2e-5))
            uv = first[:, :2] / first[:, 2:] * [90, 92] + [64, 48]
            self.assertLess(float(np.linalg.norm(uv - np.column_stack([xs, ys]), axis=1).max()), 0.05)

    def test_rendering_proofs_and_source_pins(self):
        from gt_scene_assets import load_arrays, read_json, verify
        from arkit_fixtures import write_json
        provenance = read_json(verify(self.receipt['source_provenance']))
        for item in provenance['raw_sources'].values():
            verify(item, prepared=False)
        for item in provenance['source_closure'].values():
            verify(item, prepared=False)
        for name in ('source_frames_receipt', 'correspondence', 'mapping_authority', 'source_timeline'):
            verify(provenance[name])
        self.assertEqual(len(self.receipt['rendering_proof']), 2)
        for proof in self.receipt['rendering_proof']:
            verify(proof['side_by_side'])
            arrays = load_arrays(proof['arrays'])
            rendered = self.provider._render_instance(self.scene, proof['slot_1based'], proof['instance_id'])
            self.assertTrue(np.array_equal(arrays['mask'], rendered['mask']))
            self.assertGreaterEqual(proof['visible_mask_pixels'], 32)
        write_json(self.output / 'end_to_end_result.json', {'scene_receipt': self.prepared['receipt'],
            'registry': self.prepared['registry'], 'source_frames': 40, 'validated_selected_frames': len(self.receipt['frames']),
            'annotated_instances': len(provenance['instance_uid_mapping']), 'raw_files_reverified': len(provenance['raw_sources']),
            'rendering_proofs': self.receipt['rendering_proof'], 'dense_shape': list(self.source['mask'].shape)})

    def reject_fixture(self, fault, message):
        from arkit_fixtures import make_fixture, write_json
        from prepare_corpus import prepare
        args = make_fixture(self.output / fault, fault=fault)
        with self.assertRaisesRegex(ValueError, message) as caught:
            prepare(args)
        self.assertFalse((args.output / 'scene_receipt.json').exists())
        self.assertFalse((args.output / 'registry.json').exists())
        write_json(args.output.parent / 'refusal.json', {'fault': fault, 'exception': type(caught.exception).__name__, 'reason': str(caught.exception), 'receipt_published': False})

    def test_missing_pose_refuses_before_publication(self):
        self.reject_fixture('missing_pose', 'missing pose')

    def test_misaligned_frame_refuses_before_publication(self):
        self.reject_fixture('misaligned_frame', 'correlation or MAE failed')

    def test_malformed_annotation_refuses_before_publication(self):
        self.reject_fixture('malformed_annotation', 'malformed annotation OBB')

    def test_missing_intrinsics_refuses(self):
        self.reject_fixture('missing_intrinsics', 'missing intrinsics')

    def test_ambiguous_timestamp_refuses(self):
        self.reject_fixture('ambiguous_pose', 'ambiguous pose')

    def test_missing_mesh_refuses(self):
        self.reject_fixture('missing_mesh', 'regular source file missing')

    def test_unsupported_instance_cannot_reach_obb_fallback(self):
        self.reject_fixture('unsupported_instance', 'OBB fallback forbidden')

    def test_timeline_drift_refuses(self):
        self.reject_fixture('timeline_drift', 'timeline census drift')

    def test_uint16_source_rgb_refuses(self):
        self.reject_fixture('uint16_rgb', 'uint8 three-channel')

    def test_spatially_constant_rgb_refuses(self):
        self.reject_fixture('constant_rgb', 'spatially constant')

    def test_vsi_boolean_ordinal_refuses(self):
        from arkit_fixtures import make_fixture, write_json
        from gt_scene_assets import read_json
        from arkit_alignment import selected_camera_alignment
        args = make_fixture(self.output / 'boolean_ordinal')
        mapping = read_json(args.correspondence)
        mapping['frames'][0]['vsi_ordinal'] = False
        path = args.correspondence.with_name('bad_correspondence.json')
        write_json(path, mapping)
        with self.assertRaisesRegex(ValueError, 'VSI correspondence ordinals must be integers'):
            selected_camera_alignment(args.sequence_dir, args.scene, args.frames_receipt, path)

    def test_distorted_mp4_refuses_without_relaxing_correlation(self):
        from arkit_fixtures import make_fixture, write_json
        from prepare_corpus import prepare
        args = make_fixture(self.output / 'compression_stress', fault='compression_stress', codec='mp4v')
        with self.assertRaisesRegex(ValueError, 'correlation or MAE failed') as caught:
            prepare(args)
        self.assertFalse((args.output / 'registry.json').exists())
        write_json(args.output.parent / 'refusal.json', {'fault': 'compression_stress', 'reason': str(caught.exception), 'receipt_published': False})

    def test_source_mutation_during_preparation_refuses_publication(self):
        import prepare_arkit_scene
        from arkit_fixtures import make_fixture, write_json
        args = make_fixture(self.output / 'mid_prepare_drift')
        render = prepare_arkit_scene.render_geometry
        def drift_after_render(*values):
            result = render(*values)
            with (args.sequence_dir / f'{args.scene}_3dod_annotation.json').open('a') as handle:
                handle.write('\n')
            return result
        with patch.object(prepare_arkit_scene, 'render_geometry', side_effect=drift_after_render):
            with self.assertRaisesRegex(ValueError, 'digest/size drift') as caught:
                prepare_arkit_scene.prepare(args)
        self.assertFalse((args.output / 'scene_receipt.json').exists())
        self.assertFalse((args.output / 'registry.json').exists())
        write_json(args.output.parent / 'refusal.json', {'fault': 'mid_prepare_drift', 'reason': str(caught.exception), 'receipt_published': False})

    def test_numeric_timestamp_sort_and_duplicate_refusal(self):
        from arkit_source import timestamped_files
        root = self.output / 'timestamp_names'
        root.mkdir()
        for stamp in ('10.010', '9.990'):
            with (root / f'{self.args.scene}_{stamp}.png').open('xb') as handle:
                handle.write(b'filename-only fixture')
        rows = timestamped_files(root, self.args.scene, '.png')
        self.assertEqual([row['timestamp'] for row in rows], ['9.990', '10.010'])
        with (root / f'{self.args.scene}_9.99.png').open('xb') as handle:
            handle.write(b'duplicate numeric timestamp')
        with self.assertRaisesRegex(ValueError, 'duplicate source timestamp'):
            timestamped_files(root, self.args.scene, '.png')

    def test_sparse_occlusion_limit_and_dense_surface_visibility(self):
        from gt_scene_assets import load_arrays, save_arrays
        from gt_training_r1313 import TrainingGrounding
        from arkit_fixtures import write_json
        mesh = load_arrays(self.receipt['instance_mesh'])
        pose = self.source['camera_poses'][0].astype(np.float64)
        def with_occluder(xs, ys, name):
            camera = np.stack([xs, ys, np.ones_like(xs)], axis=-1).reshape(-1, 3)
            occluder = camera @ pose[:3, :3].T + pose[:3, 3]
            height, width = xs.shape
            yy, xx = np.indices((height - 1, width - 1))
            a = len(mesh['vertices_world']) + yy.reshape(-1) * width + xx.reshape(-1)
            faces = np.concatenate([np.stack([a, a + 1, a + width + 1], axis=1),
                                    np.stack([a, a + width + 1, a + width], axis=1)]).astype(np.int32)
            mesh_pin = save_arrays(self.output / (name + '_occluder_mesh.npz'),
                vertices_world=np.concatenate([mesh['vertices_world'], occluder]).astype(np.float32),
                faces=np.concatenate([mesh['faces'], faces]),
                face_instance_ids=np.concatenate([mesh['face_instance_ids'], np.full(len(faces), -1, dtype=np.int32)]))
            receipt = copy.deepcopy(self.receipt)
            receipt['instance_mesh'] = mesh_pin
            return TrainingGrounding(receipt), mesh_pin
        ys, xs = np.meshgrid(np.linspace(-0.8, 0.8, 33), np.linspace(-1, 1, 41), indexing='ij')
        sparse, sparse_pin = with_occluder(xs, ys, 'sparse')
        yy, xx = np.indices((96, 128), dtype=np.float64)
        dense, dense_pin = with_occluder((xx + 0.5 - 64) / 90, (yy + 0.5 - 48) / 92, 'dense')
        rows = []
        for label in ('chair', 'table'):
            leaked = sparse.visible_instances(self.scene, 1, label)
            leaked_pixels = sum(row['mask_pixel_count'] for row in leaked)
            self.assertGreater(leaked_pixels, 0)
            self.assertEqual(dense.visible_instances(self.scene, 1, label), [])
            self.assertEqual(dense.boxes(self.scene, 1, label), [])
            self.assertEqual(dense.points(self.scene, 1, label), [])
            payload = dense.segment_frame(self.scene, 1, label, self.output / 'tool_runtime/occluded' / label)
            self.assertEqual(payload['instances'], [])
            self.assertEqual(payload['frame_size'], [128, 96])
            rows.append({'label': label, 'sparse_hidden_object_leak_pixels': leaked_pixels,
                         'dense_hidden_object_leak_pixels': 0, 'analytic_expected_visible_pixels': 0})
        diagnostic = {'occluder_camera_depth_m': 1, 'sparse_mesh': sparse_pin, 'dense_mesh': dense_pin,
            'cases': rows, 'inherited_limitation_reproduced': True,
            'reason': 'vertex splats fill only empty depth pixels; sparse foreground triangles do not replace existing farther samples',
            'collection_status': 'blocked_pending_real_scene_visibility_validation; kernels_unchanged'}
        write_json(self.output / 'occlusion_diagnostics.json', diagnostic)
        print('OCCLUSION_LIMITATION', json.dumps(rows, sort_keys=True), flush=True)

    def test_explicit_timestamp_map_and_lossy_video(self):
        from arkit_fixtures import make_fixture
        from arkit_alignment import selected_camera_alignment
        args = make_fixture(self.output / 'timestamp_mp4', mapping_basis='explicit_timestamp_map', codec='mp4v')
        result = selected_camera_alignment(args.sequence_dir, args.scene, args.frames_receipt, args.correspondence)
        self.assertEqual(len(result[4]), 32)
        self.assertEqual(result[-1]['mapping_basis'], 'explicit_timestamp_map')
        self.assertGreaterEqual(min(row['raw_to_vsi_correlation'] for row in result[4]), 0.99)
        self.assertTrue(any(row['raw_to_vsi_mae'] > 0 for row in result[4]))

    def test_selected_png_digest_drift_refuses(self):
        from arkit_fixtures import make_fixture, write_json
        from gt_scene_assets import read_json
        from prepare_corpus import prepare
        args = make_fixture(self.output / 'selected_digest_drift')
        frames = read_json(args.frames_receipt)
        frames['frames'][0]['sha256'] = '0' * 64
        frame_pin = write_json(args.frames_receipt.with_name('bad_frames_receipt.json'), frames)
        mapping = read_json(args.correspondence)
        mapping['source_frames_receipt'] = frame_pin
        mapping_path = args.correspondence.with_name('bad_correspondence.json')
        write_json(mapping_path, mapping)
        args.frames_receipt, args.correspondence = Path(frame_pin['path']), mapping_path
        with self.assertRaisesRegex(ValueError, 'digest/size drift'):
            prepare(args)
        self.assertFalse((args.output / 'registry.json').exists())

    def test_immutable_output_collision_refuses(self):
        from prepare_corpus import prepare
        with self.assertRaisesRegex(FileExistsError, 'immutable'):
            prepare(self.args)

    def test_unknown_scene_label_frame_and_corpus_refuse(self):
        from prepare_corpus import prepare
        from gt_training_r1313 import load_selected_dense
        with self.assertRaisesRegex(ValueError, 'unsupported corpus'):
            prepare(SimpleNamespace(dataset='scannet'))
        with self.assertRaisesRegex(ValueError, 'unknown qualified'):
            load_selected_dense('arkitscenes__99999999')
        with self.assertRaisesRegex(ValueError, 'GT geometry only'):
            load_selected_dense(self.scene, 'mapanything')
        refusal = self.tools.predict_2d_bounding_box.invoke({'scene_id': self.scene, 'frame_index': 1, 'object_label': 'zz_unmapped_fixture_zz'})
        self.assertEqual(refusal['status'], 'refused')
        for frame in (0, 33):
            with self.assertRaisesRegex(ValueError, '1-based'):
                self.tools.predict_2d_bounding_box.invoke({'scene_id': self.scene, 'frame_index': frame, 'object_label': 'chair'})

    def test_mesh_overlap_is_not_assigned_arbitrarily(self):
        from arkit_source import associate_mesh, parse_annotations
        from arkit_fixtures import write_json
        annotation = {'skipped': False, 'data': [
            {'uid': 'a', 'label': 'chair', 'segments': {'obbAligned': {'centroid': [0, 0, 0], 'axesLengths': [4, 4, 4], 'normalizedAxes': np.eye(3).reshape(-1).tolist()}}},
            {'uid': 'b', 'label': 'table', 'segments': {'obbAligned': {'centroid': [0, 0, 0], 'axesLengths': [4, 4, 4], 'normalizedAxes': np.eye(3).reshape(-1).tolist()}}}]}
        path = self.output / 'overlap_annotation.json'
        write_json(path, annotation)
        groups, _ = parse_annotations(path)
        with self.assertRaisesRegex(ValueError, 'OBB fallback forbidden'):
            associate_mesh(np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]]), np.asarray([[0, 1, 2]]), groups)

    def test_package_census_and_unchanged_teacher_bytes(self):
        from audit_package import REQUIRED_FILES, source_census
        from gt_scene_assets import read_json, sha
        package = Path(__file__).resolve().parent
        lane = package.parents[1]
        baseline = read_json(lane / 'out/BASELINE_PINS.json')
        self.assertEqual(set(source_census()), REQUIRED_FILES)
        for name, digest in baseline['package'].items():
            self.assertEqual(sha(lane / 'inputs/pkg_r1313_readonly' / name), digest)
            if name != 'audit_package.py':
                self.assertEqual(sha(package / name), digest)
        for name, digest in baseline['donor'].items():
            self.assertEqual(sha(lane / 'inputs/donor_readonly' / name), digest)
        self.assertEqual(len(baseline['package']), 40)


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--test', action='append')
    args = parser.parse_args()
    allowed = Path(__file__).resolve().parents[2] / 'out'
    output = args.output_root.resolve()
    if not output.is_relative_to(allowed) or os.environ.get('PYTHONDONTWRITEBYTECODE') != '1':
        raise ValueError('fixtures require lane-local out/ and PYTHONDONTWRITEBYTECODE=1')
    output.mkdir(parents=True, exist_ok=True)
    run = output / ('fixtures_' + str(time.time_ns()))
    run.mkdir()
    ARKitAdapterTests.output = run
    with (output / 'tests.log').open('a') as cumulative, (run / 'tests.log').open('x') as local:
        sink = Tee(sys.stdout, cumulative, local)
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink), patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden in fixtures')):
            print('FIXTURE_RUN', run, flush=True)
            suite = unittest.defaultTestLoader.loadTestsFromNames(args.test, module=sys.modules[__name__]) if args.test else unittest.defaultTestLoader.loadTestsFromTestCase(ARKitAdapterTests)
            result = unittest.TextTestRunner(stream=sink, verbosity=2).run(suite)
            status = {'success': result.wasSuccessful(), 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'run_root': str(run)}
            with (run / 'test_result.json').open('x') as handle:
                json.dump(status, handle, indent=2)
                handle.write('\n')
            print(json.dumps(status, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
