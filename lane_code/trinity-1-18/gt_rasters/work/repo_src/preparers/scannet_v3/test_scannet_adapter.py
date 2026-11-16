"""Real CPU fixtures for sensor parsing, geometry, correspondence and binding."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace
import unittest
import zlib
import cv2
import numpy as np
from gt_scene_assets import DATA_ROOT, pin, write_json, save_arrays, verify, read_json
from scannet_sens import SensReader, calibrated_header
from scannet_adapter import membership_boxes, correspondence, selected_camera_alignment, visibility_proof
from scannet_contract import census, verify_contract, authenticated_frames, SCHEMA, EXTRA_FILES
from audit_package import REQUIRED_FILES

ROOT = Path(os.environ.get('SCANNET_TEST_ROOT', DATA_ROOT / 'runtime_control/gt_teacher_r1313/materialization_v2/scannet_v3_validation')).resolve()


def make_sens(path, count=32, *, codec=2, extrinsic=None, version=4):
    k = np.eye(4, dtype=np.float32); k[0, 0] = 70; k[1, 1] = 71; k[:2, 2] = [39.5, 29.5]
    ex = np.eye(4, dtype=np.float32) if extrinsic is None else extrinsic
    images = []
    pack = lambda fmt, *values: struct.pack('<' + fmt, *values)
    yy, xx = np.indices((60, 80))
    with path.open('xb') as f:
        f.write(pack('IQ', version, 7) + b'fixture')
        for value in (k, ex, k, ex):
            f.write(pack('16f', *value.ravel()))
        f.write(pack('2i4IfQ', codec, 1, 80, 60, 80, 60, 1000, count))
        for i in range(count):
            rgb = np.stack([(xx * 2 + i) % 255, (yy * 3 + i * 2) % 255, (xx + yy + i * 3) % 255], axis=-1).astype(np.uint8)
            ok, payload = cv2.imencode('.jpg', rgb, [cv2.IMWRITE_JPEG_QUALITY, 98]); assert ok
            images.append(cv2.imdecode(payload, cv2.IMREAD_COLOR))
            depth = zlib.compress(np.full((60, 80), 2000 + i, '<u2').tobytes())
            pose = np.eye(4, dtype=np.float32); pose[0, 3] = i / 100
            f.write(pack('16f', *pose.ravel()) + pack('4Q', 1000 + i, 2000 + i, len(payload), len(depth)))
            f.write(payload.tobytes()); f.write(depth)
        f.write(pack('Q', 0))
    return k, images


class AdapterFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / ('fixtures_' + str(time.time_ns()))
        cls.root.mkdir(parents=True, exist_ok=False)
        cls.sens = cls.root / 'source.sens'
        cls.k, cls.images = make_sens(cls.sens)
        cls.reader = SensReader(cls.sens)
        cls.video = cls.root / 'vsi.avi'
        writer = cv2.VideoWriter(str(cls.video), cv2.VideoWriter_fourcc(*'FFV1'), 24, (40, 30))
        assert writer.isOpened()
        for image in cls.images:
            writer.write(cv2.resize(image, (40, 30), interpolation=cv2.INTER_AREA))
        writer.release()
        cap = cv2.VideoCapture(str(cls.video)); rows = []
        for i in range(32):
            ok, image = cap.read(); assert ok
            path = cls.root / f'frame_{i:06d}.png'
            assert cv2.imwrite(str(path), image)
            rows.append(dict(pin(path), ordinal=i, stem=path.stem, timestamp_sec=i / 24))
        cap.release()
        indices = write_json(cls.root / 'indices.json', {'schema': 'r1308-selected-indices-v1', 'indices': list(range(32))})
        cls.frames = {'dataset': 'scannet', 'scene_name': 'fixture', 'image_count': 32,
            'frames': rows, 'selected_frames': [r['stem'] for r in rows], 'indices': indices,
            'video': dict(pin(cls.video), decoded_frame_count=32, fps=24)}

    def output(self, name):
        p = self.root / name; p.mkdir(exist_ok=False); return p

    def test_sens_layout_depth_and_payload_binding(self):
        sensor = self.reader
        header_only = SensReader(self.sens, header_only=True)
        self.assertEqual(header_only.header_pin, sensor.header_pin)
        self.assertTrue(all(sensor.header[k] == v for k, v in header_only.header.items()))
        self.assertEqual(header_only.records, [])
        self.assertEqual(sensor.header['num_frames'], 32)
        self.assertEqual(sensor.header['depth_shift'], 1000)
        image, depth, row = sensor.decode(17)
        np.testing.assert_array_equal(image, self.images[17])
        self.assertTrue((depth == 2017).all())
        self.assertEqual(row['source_frame_id'], 17)
        self.assertEqual(row['timestamp_color_us'], 1017)
        self.assertEqual(row['timestamp_depth_us'], 2017)
        self.assertAlmostEqual(row['camera_to_world'][0][3], .17, places=6)
        self.assertEqual(len(row['color_payload_sha256']), 64)
        self.assertEqual(len(row['depth_payload_sha256']), 64)

    def test_truncation_version_codec_and_ordinal_refusal(self):
        for name, size in [('header', 20), ('payload', 1000)]:
            path = self.root / (name + '.sens'); path.write_bytes(self.sens.read_bytes()[:size])
            with self.assertRaises(ValueError): SensReader(path)
        for name, kwargs in [('codec', {'codec': 0}), ('version', {'version': 3})]:
            path = self.root / (name + '.sens'); make_sens(path, count=1, **kwargs)
            with self.assertRaises(ValueError): SensReader(path)
        for ordinal in (-1, 32, True):
            with self.assertRaises(ValueError): self.reader.decode(ordinal)

    def test_calibration_preservation_and_extrinsic_refusal(self):
        np.testing.assert_array_equal(calibrated_header(self.reader.header), self.k[:3, :3])
        header = copy.deepcopy(self.reader.header); header['extrinsic_depth'][0][3] = .02
        with self.assertRaisesRegex(ValueError, 'nonidentity'): calibrated_header(header)
        header = copy.deepcopy(self.reader.header); header['intrinsic_color'][0][1] = .1
        with self.assertRaisesRegex(ValueError, 'intrinsic'): calibrated_header(header)

    def test_all_32_ordinals_and_scaled_calibration(self):
        poses, ks, hw, rows, rgb, proof = selected_camera_alignment(self.reader, self.frames, self.output('alignment'))
        self.assertEqual(hw, (30, 40))
        self.assertEqual([r['source_frame_id'] for r in rows], list(range(32)))
        self.assertEqual(read_json(verify(proof))['validated_slots'], 32)
        for i, row in enumerate(rows):
            np.testing.assert_array_equal(poses[i], np.asarray(self.reader.records[i]['camera_to_world'], np.float32))
            np.testing.assert_array_equal(ks[i], np.diag([.5, .5, 1]) @ self.k[:3, :3])
            self.assertGreaterEqual(row['raw_to_vsi_correlation'], .99)
            self.assertEqual(row['selected_rgb_sha256'], self.frames['frames'][i]['sha256'])

    def test_receipt_ordinal_count_stem_and_png_drift_refusals(self):
        for kind in ('duplicate', 'count', 'stem', 'png'):
            frames = copy.deepcopy(self.frames)
            if kind == 'duplicate': frames['frames'][1]['ordinal'] = 0
            if kind == 'count': frames['video']['decoded_frame_count'] = 33
            if kind == 'stem': frames['frames'][0]['stem'] = 'frame_000007'
            if kind == 'png': frames['frames'][0]['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                selected_camera_alignment(self.reader, frames, self.output('bad_' + kind))

    def test_wrong_source_ordinal_fails_unchanged_correlation(self):
        image = cv2.resize(self.images[0], (40, 30), interpolation=cv2.INTER_AREA)
        wrong = np.random.default_rng(17).integers(0, 256, image.shape, dtype=np.uint8)
        corr, _ = correspondence(wrong, image, image)
        self.assertLess(corr, .99)
        with self.assertRaisesRegex(ValueError, 'PNG'):
            correspondence(image, image, wrong)
        other = SensReader(self.sens)
        # Change the real source file's frame association through the index, not a mock decoder.
        other.records = [dict(other.records[31 - i], source_frame_id=i) for i in range(32)]
        with self.assertRaisesRegex(ValueError, 'correlation'):
            selected_camera_alignment(other, self.frames, self.output('wrong_source'))

    def test_vertex_association_and_all_member_box_convention(self):
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 1], [9, 8, 7], [2, 2, 2]], np.float32)
        faces = np.array([[0, 1, 2], [0, 1, 4]], np.int32)
        segments = {'sceneId': 'fixture', 'segIndices': [3, 3, 3, 4, 9]}
        agg = {'sceneId': 'scannet.fixture', 'segmentsFile': 'scannet.fixture_vh_clean_2.0.010000.segs.json', 'segGroups': [{'id': 6, 'objectId': 17, 'label': 'chair', 'segments': [3, 4]}]}
        groups, face_ids, vertex_ids, diagnostics = membership_boxes(vertices, faces, segments, agg, 'fixture')
        self.assertEqual(face_ids.tolist(), [17, -1])
        self.assertEqual(vertex_ids.tolist(), [17, 17, 17, 17, -1])
        self.assertEqual(groups[0]['obb']['centroid'], [4.5, 4, 3.5])
        self.assertEqual(groups[0]['obb']['axesLengths'], [4.5, 4, 3.5])
        self.assertEqual(diagnostics[0]['source_group_id'], 6)
        overlap = copy.deepcopy(agg); overlap['segGroups'].append({'id': 9, 'objectId': 19, 'label': 'other', 'segments': [3]})
        with self.assertRaisesRegex(ValueError, 'multiple'): membership_boxes(vertices, faces, segments, overlap, 'fixture')
        absent = copy.deepcopy(agg); absent['segGroups'][0]['segments'].append(77)
        with self.assertRaisesRegex(ValueError, 'absent'): membership_boxes(vertices, faces, segments, absent, 'fixture')
        flat = vertices.copy(); flat[:, 2] = 0
        with self.assertRaisesRegex(ValueError, 'degenerate'): membership_boxes(flat, faces, segments, agg, 'fixture')

    def test_all_frame_unchanged_geometry_and_grounding(self):
        from prepare_gt_scene import render_geometry
        out = self.output('geometry')
        yy, xx = np.indices((15, 19)); points = np.column_stack([(xx.ravel() - 9) / 10, (yy.ravel() - 7) / 10, np.full(xx.size, 2.)])
        vertices = np.concatenate([points, points + [0, 0, .2]]).astype(np.float32)
        faces = []
        for y in range(14):
            for x in range(18):
                a = y * 19 + x; faces.extend([[a, a + 1, a + 19], [a + 1, a + 20, a + 19]])
        faces = np.asarray(faces, np.int32)
        aggregation = {'sceneId': 'scannet.fixture', 'segmentsFile': 'scannet.fixture_vh_clean_2.0.010000.segs.json', 'segGroups': [{'id': 0, 'objectId': 0, 'label': 'chair', 'segments': [1]}]}
        groups, face_ids, _, _ = membership_boxes(vertices, faces, {'sceneId': 'fixture', 'segIndices': [1] * len(vertices)}, aggregation, 'fixture')
        poses = np.repeat(np.eye(4, dtype=np.float32)[None], 32, axis=0)
        k = np.array([[30, 0, 20], [0, 30, 15], [0, 0, 1]], np.float32)
        ks = np.repeat(k[None], 32, axis=0)
        data, audits = render_geometry(vertices, poses, ks, (30, 40), list(range(32)))
        self.assertEqual(len(audits), 32)
        self.assertLess(max(r['max_reprojection_px'] for r in audits), .05)
        receipt = {'runtime_scene_id': 'scannet__fixture',
            'calibration': save_arrays(out / 'calibration.npz', camera_poses=poses, intrinsics=ks, raster_hw=np.array([30, 40]), indices=np.arange(32)),
            'instances': write_json(out / 'instances.json', {'segGroups': groups}),
            'instance_mesh': save_arrays(out / 'mesh.npz', vertices_world=vertices, faces=faces, face_instance_ids=face_ids),
            'annotations': write_json(out / 'annotations.json', {'instances': [{'instance_id': 0, 'label': 'chair'}]})}
        proofs, vis = visibility_proof(out, receipt, [np.zeros((30, 40, 3), np.uint8)] * 32, data)
        self.assertEqual([r['slot_1based'] for r in proofs], [1, 17])
        rows = read_json(verify(vis))['frames']; self.assertEqual(len(rows), 32)
        self.assertTrue(all(r['visible_mask_pixels'] >= 32 for r in rows))

    def test_contract_and_raw_receipt_binding(self):
        root = self.output('closure')
        for name in set(REQUIRED_FILES) | EXTRA_FILES:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('# fixture\n')
        frames = write_json(self.root / 'frames_receipt.json', self.frames)
        plan = write_json(self.root / 'plan.json', {'scenes': [{'scene': 'fixture', 'dataset': 'scannet', 'frames_receipt': frames}]})
        spec = write_json(self.root / 'contract.json', {'schema': SCHEMA, 'collector_admission': False,
            'source_files': census(root), 'plan': plan})
        verify_contract(spec['path'], spec['sha256'], root)
        (root / 'scannet_sens.py').write_text('# drift\n')
        with self.assertRaisesRegex(ValueError, 'closure'): verify_contract(spec['path'], spec['sha256'], root)
        with self.assertRaisesRegex(ValueError, 'digest'): verify_contract(spec['path'], '0' * 64, root)
        raw = self.root / 'raw_binding.bin'; raw.write_bytes(b'original'); binding = pin(raw); raw.write_bytes(b'changed!')
        with self.assertRaisesRegex(ValueError, 'drift'): verify(binding, prepared=False)

    def test_real_pinned_plan_authentication_and_receipt_drift(self):
        frames = write_json(self.root / 'auth_frames.json', self.frames)
        plan = write_json(self.root / 'auth_plan.json', {'scenes': [{'scene': 'fixture', 'dataset': 'scannet', 'frames_receipt': frames}]})
        spec = write_json(self.root / 'auth_contract.json', {'schema': SCHEMA, 'collector_admission': False,
            'source_files': census(), 'plan': plan})
        args = SimpleNamespace(contract=Path(spec['path']), contract_sha256=spec['sha256'],
            scene='fixture', frames_receipt=Path(frames['path']), frames_receipt_sha256=frames['sha256'])
        authenticated, _ = authenticated_frames(args)
        self.assertEqual(authenticated, self.frames)
        bad = copy.copy(args); bad.frames_receipt_sha256 = '0' * 64
        with self.assertRaisesRegex(ValueError, 'PLAN'): authenticated_frames(bad)
        bad = copy.copy(args); bad.scene = 'not_in_plan'
        with self.assertRaisesRegex(ValueError, 'pinned plan'): authenticated_frames(bad)
        mutated = copy.deepcopy(self.frames); mutated['dataset'] = 'scannetppv2'
        Path(frames['path']).write_text(json.dumps(mutated))
        with self.assertRaisesRegex(ValueError, 'drift'): authenticated_frames(args)

    def test_review_mismatched_identity_probe(self):
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 1]], np.float32)
        faces = np.array([[0, 1, 2]], np.int32)
        seg = {'sceneId': 'fixture', 'segIndices': [1, 1, 1]}
        agg = {'sceneId': 'scannet.fixture',
               'segmentsFile': 'scannet.fixture_vh_clean_2.0.010000.segs.json',
               'segGroups': [{'id': 0, 'objectId': 0, 'label': 'chair', 'segments': [1]}]}
        membership_boxes(vertices, faces, seg, agg, 'fixture')
        for kind in ('segmentation', 'aggregation', 'segmentsFile', 'both', 'missing'):
            with self.subTest(kind=kind):
                a, b = copy.deepcopy(seg), copy.deepcopy(agg)
                if kind in ('segmentation', 'both'): a['sceneId'] = 'other'
                if kind == 'aggregation': b['sceneId'] = 'scannet.other'
                if kind in ('segmentsFile', 'both'): b['segmentsFile'] = 'scannet.other_vh_clean_2.0.010000.segs.json'
                if kind == 'missing': a.pop('sceneId')
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    membership_boxes(vertices, faces, a, b, 'fixture')
        for groups in ([], None):
            b = copy.deepcopy(agg); b['segGroups'] = groups
            with self.assertRaisesRegex(ValueError, 'empty'):
                membership_boxes(vertices, faces, seg, b, 'fixture')

    def preparation_fixture(self, name, bad_pose=False):
        import scannet_adapter
        from unittest.mock import patch
        root = self.output(name)
        raw = root / 'fixture'; raw.mkdir()
        # A real binary PLY, released annotation layout and calibrated sensor stream.
        yy, xx = np.indices((15, 19))
        points = np.column_stack([(xx.ravel() - 9) / 10, (yy.ravel() - 7) / 10, np.full(xx.size, 2.)])
        vertices = np.concatenate([points, points + [0, 0, .2]]).astype('<f4')
        faces = []
        for y in range(14):
            for x in range(18):
                a = y * 19 + x; faces.extend([[a, a + 1, a + 19], [a + 1, a + 20, a + 19]])
        mesh = raw / 'fixture_vh_clean_2.ply'
        with mesh.open('xb') as f:
            f.write(('ply\nformat binary_little_endian 1.0\nelement vertex ' + str(len(vertices)) +
                     '\nproperty float x\nproperty float y\nproperty float z\nelement face ' + str(len(faces)) +
                     '\nproperty list uchar int vertex_indices\nend_header\n').encode())
            f.write(vertices.tobytes())
            for face in faces: f.write(struct.pack('<B3i', 3, *face))
        (raw / 'fixture.sens').write_bytes(self.sens.read_bytes())
        if bad_pose:
            with (raw / 'fixture.sens').open('r+b') as f:
                f.seek(self.reader.records[17]['record_offset'])
                f.write(struct.pack('<16f', *([0.0] * 16)))
        write_json(raw / 'fixture.aggregation.json', {'sceneId': 'scannet.fixture',
            'segmentsFile': 'scannet.fixture_vh_clean_2.0.010000.segs.json',
            'segGroups': [{'id': 0, 'objectId': 0, 'label': 'chair', 'segments': [1]}]})
        write_json(raw / 'fixture_vh_clean_2.0.010000.segs.json',
                   {'sceneId': 'fixture', 'segIndices': [1] * len(vertices)})
        (raw / 'fixture.txt').write_text('axisAlignment = ' + ' '.join(map(str, np.eye(4).ravel())) + '\n')
        frames = write_json(root / 'frames.json', self.frames)
        plan = write_json(root / 'plan.json', {'scenes': [{'scene': 'fixture', 'dataset': 'scannet', 'frames_receipt': frames}]})
        contract = write_json(root / 'contract.json', {'schema': SCHEMA, 'collector_admission': False,
            'source_files': census(), 'plan': plan})
        args = SimpleNamespace(contract=Path(contract['path']), contract_sha256=contract['sha256'],
            frames_receipt=Path(frames['path']), frames_receipt_sha256=frames['sha256'],
            scene='fixture', output=root / 'prepared')
        # Redirect only the raw storage root; all preparation and validators execute.
        with patch.object(scannet_adapter, 'RAW_ROOT', root):
            if bad_pose:
                with self.assertRaisesRegex(ValueError, 'finite proper rigid'):
                    scannet_adapter.prepare(args)
            else:
                scannet_adapter.prepare(args)
        return root, args.output

    def test_late_pose_refusal_keeps_box_declaration(self):
        from scannet_checks import require_box_declaration
        _, output = self.preparation_fixture('late_pose', bad_pose=True)
        self.assertEqual(len((output / 'ORDINAL_PROGRESS.jsonl').read_text().splitlines()), 17)
        self.assertFalse((output / 'scene_receipt.json').exists())
        self.assertFalse((output / 'source_provenance.json').exists())
        for name in ('instances.json', 'INPUT_RECEIPT.json', 'REFUSAL_RECEIPT.json'):
            require_box_declaration(read_json(output / name), name)
        failure = read_json(output / 'REFUSAL_RECEIPT.json')
        self.assertEqual(failure['source_identity']['scene'], 'fixture')
        self.assertIn('sens_header', failure['source_identity'])

    def test_success_and_admission_box_convention_refusals(self):
        from gt_scene_assets import validate_scene
        from scannet_checks import BOX_DECLARATION, require_box_declaration, validate_identity_receipt
        root, output = self.preparation_fixture('success')
        receipt = read_json(output / 'scene_receipt.json')
        validate_scene(receipt, load_dense=True)
        # The untouched collector must accept the existing receipt schema.
        import importlib.util
        original = Path(os.environ['SCANNET_V2_PACKAGE']) / 'gt_scene_assets.py'
        spec = importlib.util.spec_from_file_location('original_assets', original)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        original_receipt = dict(receipt)
        for field in ('interpolated_pose_slots', 'correlation_offset_slots'):
            self.assertEqual(original_receipt.pop(field), [])
        module.validate_scene(original_receipt, load_dense=True)
        for name in ('INPUT_RECEIPT.json', 'VALIDATION_RECEIPT.json'):
            require_box_declaration(read_json(output / name), name)
        for asset in ('instances', 'source_provenance', 'receipt_pin'):
            for field, expected in BOX_DECLARATION.items():
                for mode in ('missing', 'wrong'):
                    with self.subTest(asset=asset, field=field, mode=mode):
                        bad = copy.deepcopy(receipt)
                        value = bad['instances'] if asset == 'receipt_pin' else read_json(bad[asset]['path'])
                        if mode == 'missing': value.pop(field)
                        else: value[field] = not expected if type(expected) is bool else 'incorrect'
                        if asset != 'receipt_pin':
                            target = root / f'{asset}_{field}_{mode}.json'
                            new_pin = write_json(target, value)
                            bad[asset].update(new_pin)
                        with self.assertRaisesRegex(ValueError, 'box declaration'):
                            validate_scene(bad)
        source = read_json(receipt['source_provenance']['path'])
        binding = source['source_identity']
        self.assertEqual(set(binding['raw_sources']), {'mesh', 'aggregation', 'segmentation', 'sensor', 'metadata'})
        raw = root / 'fixture'
        # Header-only drift keeps file size and annotations unchanged.
        with (raw / 'fixture.sens').open('r+b') as f:
            f.seek(12); f.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'identity receipt'):
            validate_identity_receipt(receipt)

    def test_source_identity_refusals_and_header_binding(self):
        from scannet_checks import source_identity, annotation_identity
        from types import SimpleNamespace
        # The direct validator must refuse a mismatched selected segmentation basename.
        with self.assertRaisesRegex(ValueError, 'filename'):
            annotation_identity({'sceneId': 'fixture'}, {'sceneId': 'scannet.fixture',
                'segmentsFile': 'scannet.fixture_vh_clean_2.0.010000.segs.json'}, 'fixture', 'wrong.json')
        with self.assertRaisesRegex(ValueError, 'official scene'):
            source_identity('other', self.frames, {}, {}, self.reader)
        root, output = self.preparation_fixture('identity_source')
        source = read_json(output / 'source_provenance.json')
        frames_pin = source['source_frames_receipt']
        frames = read_json(frames_pin['path']); raw = source['raw_sources']
        sensor = SensReader(raw['sensor']['path'])
        for kind in ('sensor', 'mesh', 'aggregation', 'segmentation', 'metadata'):
            bad = copy.deepcopy(raw); bad[kind]['path'] = str(root / ('other' + Path(bad[kind]['path']).suffix))
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'filename/scene'):
                source_identity('fixture', frames, frames_pin, bad, sensor)
        for kind in ('mesh', 'aggregation', 'segmentation', 'metadata'):
            bad = copy.deepcopy(raw); bad[kind]['sha256'] = '0' * 64
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'drift'):
                source_identity('fixture', frames, frames_pin, bad, sensor)

    def test_reverification_accepts_v2_and_refuses_missing_carrier_declaration(self):
        from verify_scannet_assets import check_job
        root, output = self.preparation_fixture('reverification')
        job = root / 'jobs' / 'fixture'; job.mkdir(parents=True)
        # Preserve all original pins by linking the directory, never replacing its files.
        (job / 'assets').symlink_to(output, target_is_directory=True)
        receipt = pin(output / 'scene_receipt.json')
        wrapper = write_json(job / 'VALIDATION.json', dict(status='PASS', scene='fixture',
            scene_receipt=receipt, preparer_validation=pin(output / 'VALIDATION_RECEIPT.json'),
            membership={'question_count': 0}))
        write_json(job / 'TERMINAL.json', dict(status='completed', scene='fixture', validation=wrapper))
        result = check_job(job)
        self.assertEqual(result['status'], 'passed', result['reasons'])
        carrier = read_json(output / 'instances.json'); carrier.pop('box_convention')
        bad_carrier = write_json(root / 'missing_convention.json', carrier)
        bad_receipt = read_json(output / 'scene_receipt.json'); bad_receipt['instances'].update(bad_carrier)
        bad_receipt_pin = write_json(root / 'bad_scene_receipt.json', bad_receipt)
        # Build a separate completed-job fixture with authentic hashes of the bad carrier.
        bad_job = root / 'bad_jobs' / 'fixture'; bad_job.mkdir(parents=True)
        (bad_job / 'assets').symlink_to(output, target_is_directory=True)
        bad_wrapper = write_json(bad_job / 'VALIDATION.json', dict(status='PASS', scene='fixture',
            scene_receipt=bad_receipt_pin, preparer_validation=pin(output / 'VALIDATION_RECEIPT.json'),
            membership={'question_count': 0}))
        write_json(bad_job / 'TERMINAL.json', dict(status='completed', scene='fixture', validation=bad_wrapper))
        result = check_job(bad_job)
        self.assertEqual(result['status'], 'would-be-refused')
        self.assertEqual(result['checks']['R2_carrier'], 'refused')

    def test_validation_process_failure_and_timeout(self):
        from validate_scannet import run_child
        code, error = run_child([sys.executable, '-B', '-c', 'raise SystemExit(7)'],
            self.root / 'failed_child.log', dict(os.environ))
        self.assertEqual(code, 7); self.assertIsNone(error)
        code, error = run_child([sys.executable, '-B', '-c', 'import time; time.sleep(5)'],
            self.root / 'timed_out_child.log', dict(os.environ), timeout=.05)
        self.assertEqual(code, 124); self.assertIn('terminated and reaped', error)


if __name__ == '__main__':
    unittest.main(verbosity=2)
