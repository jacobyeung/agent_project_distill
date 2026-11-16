"""Adversarial metadata branches; no producer or reader function is replaced."""
from copy import deepcopy
import gzip
import io
import json
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
from tests.test_r2_data_path import directory, fixture, manifest, SOURCES, RECORDS
from student_pilot import r2_contract as C, r2_frames as F, trace_grammar as G
from student_pilot import carrier_c1_routing as routing
from student_pilot.p3_provenance import file_pin, load, digest, write
from student_pilot.r2_intake import intake, read_rows
from student_pilot.r2_dense import build_training
from student_pilot.r2_materialize import materialize
from student_pilot.r2_exclusions import Exclusions, upstream
from student_pilot.r2_adapters import normalize
from student_pilot.r2_real_proof import prove


class Refusals(unittest.TestCase):
    def setUp(self):
        self.root = directory()
        self.row = fixture(self.root)
        self.pins = {role: file_pin(RECORDS/name) for role, name in SOURCES.items()}
        self.enterContext(patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2': str(self.root/'frames')}), STUDENT_R2_LOCAL_NODE='1'))

    def test_mapping_paths_and_race(self):
        for path in ('relative.png', '/scratch/../home/file'):
            with self.assertRaises(ValueError):
                F.resolve_frame(path)
        for mapping in ('[]', '{"relative":"relative"}'):
            with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=mapping), self.assertRaises(ValueError):
                F.resolve_frame('/logical/r2/0.png')
        with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP='{}'), self.assertRaises(F.NeedsFrameHost):
            F.resolve_frame('/data2/not-opened.png')
        outside = self.root/'outside.png'
        outside.write_bytes(b'fixture')
        (self.root/'frames/escape.png').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            F.resolve_frame('/logical/r2/escape.png')
        with self.assertRaises(ValueError):
            F.FrameMemo(0)
        # Fault injection changes the real file between its two fstat calls.
        # It does not stand in for RGB reads or the hasher.
        original, calls = os.fstat, []
        def racing_stat(fd):
            calls.append(fd)
            if len(calls) == 2:
                path = self.root/'frames/0.png'
                os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns+1_000_000))
            return original(fd)
        with patch.object(F.os, 'fstat', side_effect=racing_stat), self.assertRaisesRegex(ValueError, 'changed while hashing'):
            F.FrameMemo().verify(self.row['student_input']['frames'][0])

    def test_frame_and_row_schema(self):
        for changes in (dict(frames=[]), dict(fps=0), dict(total_num_frames=1), dict(timestamps=[]),
                        dict(frames=[dict(path='x', sha256='bad')]*32)):
            row = deepcopy(self.row); row['student_input'].update(changes)
            with self.assertRaises(ValueError):
                C.validate(row, 'vqa')
        for changes in (dict(qid=''), dict(answer='B'), dict(answer_unit='yards'), dict(question_type=None),
                        dict(question_type='object_size_estimation')):
            with self.assertRaises(ValueError):
                C.validate({**self.row, **changes}, 'vqa')
        with self.assertRaises(ValueError):
            C.validate(self.row, 'vqa', expected='0'*64)
        with self.assertRaises(ValueError):
            C.validate(self.row, 'unknown')
        C.validate(self.row, 'vqa', expected=digest(self.row), require_frames=True)
        for i, value in enumerate((dict(contract='bad'), dict(contract=C.CONTRACT, rows={}))):
            path = self.root/f'membership{i}.json'; write(path, value)
            with self.assertRaises(ValueError):
                C.Admission(file_pin(path)).check(self.row, 'vqa')
        pose = fixture(self.root, stream='pose')
        target = pose['target_record']; target['camera'][0][0] = float('nan')
        with self.assertRaises(ValueError):
            C.perception(pose, 'pose', target)
        pointing = fixture(self.root, stream='pointing')
        pointing['target'] = '<think>\n\n</think>\n{"point_2d": [9999, 0]}'
        with self.assertRaises(ValueError):
            C.perception(pointing, 'pointing', {})

    def test_dense_missing_and_conflicts(self):
        for i in range(4):
            row = deepcopy(self.row)
            source = row['student_input']['dense_source']['frames']
            if i == 0:
                row['student_input'].pop('dense_source')
            elif i == 1:
                source.append({**source[0], 'sha256': '0'*64})
            elif i == 2:
                source[0]['sha256'] = '0'*64
            else:
                row['student_input']['dense_source']['frames'] = source[::2]
            with self.assertRaises((ValueError, F.NeedsFrameHost)):
                build_training(row)

    def test_scene_and_upstream_refusals(self):
        with self.assertRaises(ValueError):
            Exclusions({})
        changed = deepcopy(self.pins); changed['benchmark']['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            Exclusions(changed)
        exclusions = Exclusions(self.pins)
        for coverage in (None, dict(status='unknown', names=['d1/fixture_clean']),
                         dict(status='known', names=['unknown/scene']),
                         dict(status='known', names=['d1/wrong']),
                         dict(status='known', names=['d1/fixture_clean'])):
            row = {**self.row, 'canonical': 'scannet/different'}
            with self.assertRaises(ValueError):
                exclusions.check(row, coverage)
        excluded = {**self.row, 'scene': 'scene0000_00', 'canonical': 'scannet/scene0000_00'}
        excluded['provenance'] = {**excluded['provenance'], 'canonical': excluded['canonical']}
        admitted, report = intake(manifest(self.root/'excluded', [excluded]))
        self.assertFalse(admitted)
        self.assertIn('excluded:', report['refusals'][0]['reason'])
        for i, value in enumerate((dict(exclusions={}), dict(exclusions=self.pins, counts=dict(x={})))):
            path = self.root/f'previous{i}.json'; write(path, value)
            with self.assertRaises(ValueError):
                upstream([file_pin(path)], self.pins)

    def test_manifest_errors_and_bounded_stream(self):
        original = manifest(self.root/'m', [self.row])
        for i, changes in enumerate((dict(schema='old'), dict(scene_coverage=None), dict(prefiltered=True),
                                     dict(row_bindings={}))):
            value = {**load(original), **changes}
            path = self.root/f'm{i}.json'; write(path, value)
            if 'row_bindings' in changes:
                self.assertFalse(intake(path)[0])
            else:
                with self.assertRaises(ValueError):
                    intake(path)
        with self.assertRaises(ValueError):
            intake(original, limit=None)
        path = self.root/'badcoverage.json'; value = load(load(original)['scene_coverage']['path'])
        value['rows_sha256'] = '0'*64; write(path, value)
        bad = load(original); bad['scene_coverage'] = file_pin(path)
        write(self.root/'m_badcoverage.json', bad)
        with self.assertRaises(ValueError):
            intake(self.root/'m_badcoverage.json')
        duplicate = manifest(self.root/'duplicate', [self.row, self.row])
        self.assertEqual(len(intake(duplicate)[0]), 1)
        with gzip.open(self.root/'slice.gz', 'wt') as handle:
            handle.write(json.dumps(self.row)+'\n'+json.dumps(self.row)+'\n')
        self.assertEqual(len(list(read_rows(file_pin(self.root/'slice.gz'), 1))), 1)

    def test_adapters_native_program_and_pending_join(self):
        row = fixture(self.root, stream='routing')
        row['answer'] = '0.35'; row['target'], row['tool_output_spans'] = routing.render(row['events'], row['answer'])
        inputs = row.pop('student_input')
        row.pop('dataset'); row.pop('scene')
        rgb = dict(inputs, frames=[dict(p, source_index=i) for i, p in zip(inputs['frame_indices'], inputs['frames'], strict=True)])
        adapted = normalize(row, {row['qid']: rgb})
        self.assertTrue(adapted['target'].endswith('</answer>'))
        G.validate_program(adapted)
        with self.assertRaises(ValueError):
            normalize(row)
        changed = deepcopy(rgb); changed['frames'][0]['source_index'] = 1
        with self.assertRaises(ValueError):
            normalize(row, {row['qid']: changed})
        pending = deepcopy(self.row)
        pending['frames_pending'] = dict(d='d1', s='wrong', i=inputs['frame_indices'])
        with self.assertRaises(ValueError):
            normalize(pending)

    def test_grammar_arithmetic_program_and_measurements(self):
        for expression, allowed in (('2 +', {2}), ('2 / 0', {2, 0}), ('1e308 * 1e308', {1e308})):
            with self.assertRaises(ValueError):
                G.arithmetic(expression, allowed)
        for text, question in (('Relate: the chair is right of the stove.', 'Which side?'),
                               ('Locate: stove is seen in frame 1.\nRelate: stove is 3 meters right of sofa.', 'Threshold 3 meters.'),
                               ('Locate: stove is seen in frame 1.\nRelate: it is A.', 'Which side?')):
            with self.assertRaises(ValueError):
                G.validate_direct('<think>\n'+text+'\n</think>\nA', question, 32)
        for mutation in ('ending', 'call_id', 'number'):
            row = fixture(self.root, stream='routing')
            if mutation == 'ending':
                row['answer'] = '0.35'
            elif mutation == 'call_id':
                row['events'][2]['call_id'] = 'unmatched'
            else:
                row['events'][-1]['text'] = '\nStep: distance is 999 m.'
            row['target'], row['tool_output_spans'] = routing.render(row['events'], row['answer'])
            with self.assertRaises(ValueError):
                G.validate_program(row)

    def test_cli_native_entries_and_failed_build(self):
        original = manifest(self.root/'m', [self.row])
        for module, args in (
            ('student_pilot.r2_intake', ['--manifest', str(original), '--output', str(self.root/'cli_intake.json')]),
            ('student_pilot.r2_materialize', ['--manifest', str(original), '--output', str(self.root/'cli_stores'), '--no-dense'])):
            with patch.object(sys, 'argv', [module, *args]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                try:
                    runpy.run_module(module, run_name='__main__')
                except SystemExit as error:
                    self.assertEqual(error.code, 0)
        with patch.dict(os.environ, STUDENT_R2_LOCAL_NODE='0'), self.assertRaises(ValueError):
            materialize([original], self.root/'full', full=True)
        bad = manifest(self.root/'bad', [{**self.row, 'target': 'A'}])
        with self.assertRaisesRegex(ValueError, 'invalid rows'):
            materialize([bad], self.root/'invalid')
        extra = manifest(self.root/'extra', [{**self.row, 'qid': 'second'}])
        with patch('student_pilot.r2_materialize.MAX_ROWS_PER_FAMILY', 1), self.assertRaisesRegex(ValueError, 'Combined manifests'):
            materialize([original, extra], self.root/'combined')

    def test_real_proof_declared_fixture_inventory(self):
        with self.assertRaisesRegex(ValueError, 'inputs absent'):
            prove(self.root/'absent', self.root, self.root/'out')
        index = self.root/'REAL_ROW_INPUTS.json'
        index.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            prove(self.root, self.root, self.root/'out')
        paths = [manifest(self.root/stream, [fixture(self.root, qid=stream, stream=stream)], stream=stream)
                 for stream in ('vqa', 'routing', 'pose', 'pointing')]
        spec = dict(schema='r2-real-proof-inputs-v1', expected_families=['vqa', 'routing', 'pose', 'pointing'], manifests=[file_pin(p) for p in paths])
        index.write_text(json.dumps(spec))
        result = prove(self.root, self.root, self.root/'proof_fixture')
        self.assertFalse(result['rgb_read'])
        with patch.object(sys, 'argv', ['proof', str(self.root), str(self.root), '--output', str(self.root/'proof_cli')]):
            runpy.run_module('student_pilot.r2_real_proof', run_name='__main__')
        for i, changes in enumerate((dict(expected_families=['missing']), dict(manifests=[file_pin(paths[0])], expected_families=['vqa']))):
            index.write_text(json.dumps({**spec, **changes}))
            with self.assertRaises(ValueError):
                prove(self.root, self.root, self.root/f'fail{i}')
        # The declared roots cannot name a manifest from an unrelated publication.
        child = self.root/'child'; child.mkdir()
        (child/'REAL_ROW_INPUTS.json').write_text(json.dumps(spec))
        with self.assertRaisesRegex(ValueError, 'outside'):
            prove(child, child, child/'out')
        for i, rows in enumerate(([], [self.row, {**self.row, 'qid': 'bad', 'target': 'A'}])):
            path = manifest(self.root/f'proof_bad{i}', rows, family='vqa')
            revised = {**spec, 'manifests': [file_pin(path), *spec['manifests'][1:]]}
            index.write_text(json.dumps(revised))
            with self.assertRaisesRegex(ValueError, 'boundary|invalid rows'):
                prove(self.root, self.root, self.root/f'proof_badout{i}')
