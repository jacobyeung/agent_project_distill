from __future__ import annotations
import copy
import importlib.util
import os
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from scipy.spatial.transform import Rotation

from gt_scene_assets import pin, read_json, verify, write_json, validate_scene, load_arrays
from scannet_sens import SensReader, rigid, pose_at_slot
from scannet_adapter import correspondence, correspondence_with_offsets, selected_camera_alignment
from scannet_checks import validate_recovery_receipt, validate_registry_recovery
import test_scannet_adapter as legacy
from verify_scannet_assets import check_job


class PoseRecovery(unittest.TestCase):
    def records(self, count=15):
        result = []
        for i in range(count):
            pose = np.eye(4)
            pose[:3, :3] = Rotation.from_euler('z', i * 10, degrees=True).as_matrix()
            pose[:3, 3] = [i, 2 * i, -i]
            result.append({'camera_to_world': pose.tolist()})
        return result

    def test_two_neighbors_use_linear_translation_and_slerp(self):
        records = self.records()
        for i in (5, 6, 7):
            records[i]['camera_to_world'] = np.full((4, 4), np.nan).tolist()
        pose, evidence = pose_at_slot(records, 5, 2)
        rigid(pose, 'interpolated fixture')
        np.testing.assert_allclose(pose[:3, 3], [5, 10, -5])
        np.testing.assert_allclose(pose[:3, :3], Rotation.from_euler('z', 50, degrees=True).as_matrix(), atol=1e-12)
        self.assertEqual(evidence, {'slot_1based': 2, 'raw_frame_index': 5,
            'neighbor_frame_indices': [4, 8], 'frame_gap': 4})
        self.assertFalse(np.isfinite(records[5]['camera_to_world']).all())

    def test_single_neighbor_on_either_side_is_copied(self):
        for ordinal, bad, neighbor in ((0, range(5), 5), (14, range(10, 15), 9)):
            with self.subTest(ordinal=ordinal):
                records = self.records()
                for i in bad:
                    records[i]['camera_to_world'] = np.full((4, 4), -np.inf).tolist()
                pose, evidence = pose_at_slot(records, ordinal, 1)
                np.testing.assert_array_equal(pose, records[neighbor]['camera_to_world'])
                self.assertEqual(evidence['neighbor_frame_indices'], [neighbor])
                self.assertEqual(evidence['frame_gap'], 5)

    def test_no_finite_neighbor_within_five_frames_refuses(self):
        records = self.records()
        for i in range(2, 13):
            records[i]['camera_to_world'] = np.full((4, 4), np.inf).tolist()
        with self.assertRaisesRegex(ValueError, 'finite proper rigid.*within 5'):
            pose_at_slot(records, 7, 1)

    def test_finite_improper_pose_is_not_repaired(self):
        records = self.records()
        records[7]['camera_to_world'][0][0] = 4
        with self.assertRaisesRegex(ValueError, 'finite proper rigid'):
            pose_at_slot(records, 7, 1)

    def test_finite_improper_neighbor_is_not_skipped(self):
        records = self.records()
        records[7]['camera_to_world'] = np.full((4, 4), np.nan).tolist()
        records[6]['camera_to_world'][0][0] = 4
        with self.assertRaisesRegex(ValueError, 'finite proper rigid'):
            pose_at_slot(records, 7, 1)

    def test_clean_pose_is_identical(self):
        records = self.records()
        pose, evidence = pose_at_slot(records, 7, 1)
        np.testing.assert_array_equal(pose, rigid(records[7]['camera_to_world'], 'v2'))
        self.assertIsNone(evidence)

    def test_slerp_takes_shortest_rotation_path(self):
        records = self.records(3)
        for i, angle in ((0, 170), (2, -170)):
            pose = np.eye(4)
            pose[:3, :3] = Rotation.from_euler('z', angle, degrees=True).as_matrix()
            records[i]['camera_to_world'] = pose.tolist()
        records[1]['camera_to_world'] = np.full((4, 4), np.nan).tolist()
        pose, _ = pose_at_slot(records, 1, 1)
        np.testing.assert_allclose(pose[:3, :3], Rotation.from_euler('z', 180, degrees=True).as_matrix(), atol=1e-12)


class CorrelationRecovery(unittest.TestCase):
    def stream(self, count=9):
        rng = np.random.default_rng(17)
        images = [rng.integers(0, 256, (30, 40, 3), dtype=np.uint8) for _ in range(count)]
        calls = []
        def decode(index):
            self.assertGreaterEqual(index, 0)
            self.assertLess(index, count)
            calls.append(index)
            return images[index], np.full((30, 40), index), {'source_frame_id': index}
        return SimpleNamespace(records=[{} for _ in images], decode=decode), images, calls

    def test_accepts_plus_two_and_records_both_correlations(self):
        sensor, images, calls = self.stream()
        before, _ = correspondence(images[3], images[5], images[5])
        source, depth, record, corr, mae, evidence = correspondence_with_offsets(sensor, 3, images[5], images[5], 4)
        self.assertEqual(record['source_frame_id'], 5)
        np.testing.assert_array_equal(source, images[5])
        self.assertTrue((depth == 5).all())
        self.assertEqual(set(calls), set(range(7)))
        self.assertGreaterEqual(corr, .99)
        self.assertEqual(mae, 0)
        self.assertEqual(evidence, {'slot_1based': 4, 'offset': 2,
            'correlation_before': before, 'correlation_after': corr})

    def test_no_offset_reaches_threshold(self):
        sensor, images, calls = self.stream()
        target = np.random.default_rng(18).integers(0, 256, images[0].shape, dtype=np.uint8)
        _, _, _, corr, _, evidence = correspondence_with_offsets(sensor, 3, target, target, 4)
        self.assertLess(corr, .99)
        self.assertIsNone(evidence)
        self.assertEqual(set(calls), set(range(7)))

    def test_clean_frame_does_not_search(self):
        sensor, images, calls = self.stream()
        _, _, record, corr, _, evidence = correspondence_with_offsets(sensor, 3, images[3], images[3], 4)
        self.assertEqual(calls, [3])
        self.assertEqual(record['source_frame_id'], 3)
        self.assertGreaterEqual(corr, .99)
        self.assertIsNone(evidence)

    def test_boundary_offsets_and_stream_limits(self):
        for ordinal, match in ((0, 3), (8, 5)):
            with self.subTest(ordinal=ordinal):
                sensor, images, calls = self.stream()
                *_, evidence = correspondence_with_offsets(sensor, ordinal, images[match], images[match], 1)
                self.assertEqual(evidence['offset'], match - ordinal)
                self.assertTrue(all(abs(i - ordinal) <= 3 for i in calls))

    def test_offset_four_is_not_used(self):
        sensor, images, calls = self.stream()
        _, _, _, corr, _, evidence = correspondence_with_offsets(sensor, 0, images[4], images[4], 1)
        self.assertLess(corr, .99)
        self.assertIsNone(evidence)
        self.assertNotIn(4, calls)

    def test_nonfinite_correlation_is_recorded_as_null(self):
        sensor, images, _ = self.stream()
        images[3][:] = 0
        with np.errstate(invalid='ignore', divide='ignore'):
            *_, evidence = correspondence_with_offsets(sensor, 3, images[5], images[5], 4)
        self.assertIsNone(evidence['correlation_before'])
        self.assertEqual(evidence['offset'], 2)

    def test_highest_match_wins_over_first_above_threshold(self):
        sensor, images, calls = self.stream()
        noisy = images[5].astype(np.int16) + np.random.default_rng(19).integers(-3, 4, images[5].shape)
        images[0][:] = np.clip(noisy, 0, 255).astype(np.uint8)
        self.assertGreaterEqual(correspondence(images[0], images[5], images[5])[0], .99)
        *_, evidence = correspondence_with_offsets(sensor, 3, images[5], images[5], 4)
        self.assertEqual(evidence['offset'], 2)
        self.assertEqual(set(calls), set(range(7)))

    def test_png_authentication_is_not_relaxed(self):
        sensor, images, _ = self.stream()
        with self.assertRaisesRegex(ValueError, 'PNG'):
            correspondence_with_offsets(sensor, 3, images[5], images[6], 4)


class RecoveryIntegration(unittest.TestCase):
    output = legacy.AdapterFixtures.output
    preparation_fixture = legacy.AdapterFixtures.preparation_fixture

    @classmethod
    def setUpClass(cls):
        legacy.AdapterFixtures.setUpClass.__func__(cls)

    def baseline(self):
        path = Path(os.environ['SCANNET_V2_PACKAGE']) / 'scannet_adapter.py'
        spec = importlib.util.spec_from_file_location('scannet_v2_baseline', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_clean_alignment_matches_v2_with_only_empty_new_fields(self):
        old = self.baseline().selected_camera_alignment(self.reader, self.frames, self.output('clean_v2'))
        new = selected_camera_alignment(self.reader, self.frames, self.output('clean_v3'))
        for old_array, new_array in zip(old[:2], new[:2]):
            np.testing.assert_array_equal(old_array, new_array)
        self.assertEqual(old[2:4], new[2:4])
        for old_rgb, new_rgb in zip(old[4], new[4]):
            np.testing.assert_array_equal(old_rgb, new_rgb)
        proof = read_json(verify(new[5]))
        for field in ('interpolated_pose_slots', 'correlation_offset_slots'):
            self.assertEqual(proof.pop(field), [])
        self.assertEqual(proof, read_json(verify(old[5])))

    def test_full_nonfinite_preparation_and_verifier(self):
        sensor_path = self.root / 'nonfinite.sens'
        sensor_path.write_bytes(self.sens.read_bytes())
        with sensor_path.open('r+b') as stream:
            stream.seek(self.reader.records[17]['record_offset'])
            stream.write(struct.pack('<16f', *([float('-inf')] * 16)))
        with patch.object(self, 'sens', sensor_path):
            root, output = self.preparation_fixture('nonfinite_preparation')
        receipt = read_json(output / 'scene_receipt.json')
        self.assertEqual(receipt['interpolated_pose_slots'], [{'slot_1based': 18,
            'raw_frame_index': 17, 'neighbor_frame_indices': [16, 18], 'frame_gap': 2}])
        self.assertEqual(receipt['correlation_offset_slots'], [])
        self.assertEqual(receipt['frames'], self.frames['frames'])
        validate_scene(receipt, load_dense=True)
        cameras = load_arrays(receipt['calibration'])
        rigid(cameras['camera_poses'][17], 'prepared interpolation')
        alignment = read_json(verify(receipt['alignment']))
        self.assertTrue(all(v is None for row in alignment['frames'][17]['camera_to_world'] for v in row))
        job = root / 'jobs/fixture'
        job.mkdir(parents=True)
        (job / 'assets').symlink_to(output, target_is_directory=True)
        wrapper = write_json(job / 'VALIDATION.json', dict(status='PASS', scene='fixture',
            scene_receipt=pin(output / 'scene_receipt.json'),
            preparer_validation=pin(output / 'VALIDATION_RECEIPT.json'), membership={'question_count': 0}))
        write_json(job / 'TERMINAL.json', dict(status='completed', scene='fixture', validation=wrapper))
        result = check_job(job)
        self.assertEqual(result['status'], 'passed', result['reasons'])
        bad = copy.deepcopy(receipt)
        bad['interpolated_pose_slots'][0]['frame_gap'] = 3
        with self.assertRaisesRegex(ValueError, 'interpolat|gap'):
            validate_recovery_receipt(bad, alignment, cameras)
        bad = copy.deepcopy(cameras)
        bad['camera_poses'][17, 0, 0] = 9
        with self.assertRaisesRegex(ValueError, 'rigid'):
            validate_recovery_receipt(receipt, alignment, bad)

    def test_full_offset_preparation_and_verifier_bounds(self):
        inputs = self.output('offset_inputs')
        sensor_path = inputs / 'source.sens'
        source_bytes = self.sens.read_bytes()
        images = []
        rng = np.random.default_rng(23)
        with sensor_path.open('xb') as stream:
            stream.write(source_bytes[:self.reader.header_pin['size_bytes']])
            for i, record in enumerate(self.reader.records):
                image = rng.integers(0, 256, (60, 80, 3), dtype=np.uint8)
                ok, color = cv2.imencode('.jpg', image)
                self.assertTrue(ok)
                images.append(cv2.imdecode(color, cv2.IMREAD_COLOR))
                depth = source_bytes[record['depth_offset']:record['depth_offset'] + record['depth_size']]
                stream.write(struct.pack('<16f4Q', *np.asarray(record['camera_to_world']).ravel(),
                    record['timestamp_color_us'], record['timestamp_depth_us'], len(color), len(depth)))
                stream.write(color.tobytes())
                stream.write(depth)
            stream.write(struct.pack('<Q', 0))
        video = inputs / 'vsi.avi'
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'FFV1'), 24, (40, 30))
        self.assertTrue(writer.isOpened())
        for i in range(32):
            writer.write(cv2.resize(images[10 if i == 8 else i], (40, 30), interpolation=cv2.INTER_AREA))
        writer.release()
        frames = copy.deepcopy(self.frames)
        frames['video'] = dict(pin(video), decoded_frame_count=32, fps=24)
        capture = cv2.VideoCapture(str(video))
        try:
            for i, row in enumerate(frames['frames']):
                ok, image = capture.read()
                self.assertTrue(ok)
                path = inputs / f'frame_{i:06d}.png'
                self.assertTrue(cv2.imwrite(str(path), image))
                row.update(pin(path))
        finally:
            capture.release()
        with patch.object(self, 'sens', sensor_path), patch.object(self, 'frames', frames):
            root, output = self.preparation_fixture('offset_preparation')
        receipt = read_json(output / 'scene_receipt.json')
        self.assertEqual(receipt['interpolated_pose_slots'], [])
        self.assertEqual(len(receipt['correlation_offset_slots']), 1)
        evidence = receipt['correlation_offset_slots'][0]
        self.assertEqual((evidence['slot_1based'], evidence['offset']), (9, 2))
        self.assertLess(evidence['correlation_before'], .99)
        self.assertGreaterEqual(evidence['correlation_after'], .99)
        self.assertEqual(receipt['frames'], frames['frames'])
        cameras = load_arrays(receipt['calibration'])
        np.testing.assert_array_equal(cameras['camera_poses'][8], np.asarray(self.reader.records[10]['camera_to_world'], np.float32))
        alignment = read_json(verify(receipt['alignment']))
        self.assertEqual(alignment['frames'][8]['source_frame_id'], 10)
        job = root / 'jobs/fixture'
        job.mkdir(parents=True)
        (job / 'assets').symlink_to(output, target_is_directory=True)
        wrapper = write_json(job / 'VALIDATION.json', dict(status='PASS', scene='fixture',
            scene_receipt=pin(output / 'scene_receipt.json'),
            preparer_validation=pin(output / 'VALIDATION_RECEIPT.json'), membership={'question_count': 0}))
        write_json(job / 'TERMINAL.json', dict(status='completed', scene='fixture', validation=wrapper))
        result = check_job(job)
        self.assertEqual(result['status'], 'passed', result['reasons'])
        entry = dict(pin(output / 'scene_receipt.json'), interpolated_pose_slots=[],
                     correlation_offset_slots=copy.deepcopy(receipt['correlation_offset_slots']))
        validate_registry_recovery(entry, receipt)
        for invalid in (3, 2.0, True):
            entry['correlation_offset_slots'][0]['offset'] = invalid
            with self.subTest(registry_offset=invalid), self.assertRaisesRegex(ValueError, 'registry/scene'):
                validate_registry_recovery(entry, receipt)
        for invalid in (-4, 4, 0, True, 2.0):
            bad, bad_alignment = copy.deepcopy(receipt), copy.deepcopy(alignment)
            bad['correlation_offset_slots'][0]['offset'] = invalid
            bad_alignment['correlation_offset_slots'] = copy.deepcopy(bad['correlation_offset_slots'])
            with self.subTest(offset=invalid), self.assertRaisesRegex(ValueError, 'offset'):
                validate_recovery_receipt(bad, bad_alignment, cameras)

    def test_missing_neighbors_refuse_full_scene(self):
        sensor_path = self.root / 'no_neighbors.sens'
        sensor_path.write_bytes(self.sens.read_bytes())
        with sensor_path.open('r+b') as stream:
            for index in range(6):
                stream.seek(self.reader.records[index]['record_offset'])
                stream.write(struct.pack('<16f', *([float('nan')] * 16)))
        with patch.object(self, 'sens', sensor_path), self.assertRaisesRegex(ValueError, 'within 5'):
            self.preparation_fixture('no_neighbors_preparation')
        output = self.root / 'no_neighbors_preparation/prepared'
        refusal = read_json(output / 'REFUSAL_RECEIPT.json')
        self.assertEqual(refusal['status'], 'refused')
        self.assertEqual(refusal['stage'], 'all_32_sensor_ordinals')
        self.assertFalse((output / 'scene_receipt.json').exists())

    def test_failed_offset_search_refuses_real_alignment(self):
        other = SensReader(self.sens)
        other.records = [dict(other.records[31 - i], source_frame_id=i) for i in range(32)]
        with self.assertRaisesRegex(ValueError, 'correlation'):
            selected_camera_alignment(other, self.frames, self.output('offset_refusal'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
