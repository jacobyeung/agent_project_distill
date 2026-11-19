"""Review sb_f64rev findings 4-6: the export-layout helper needs explicit matching frame_input
declarations, the reader nests only increasing anchors, f64_read installs as src/b/f64_read.py, and
the GPU pilot calls only trainer functions that exist."""
import ast
import importlib.machinery
import json
import os
import sys
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT / 'read'), str(KIT / 'scripts')]

import f64_read as R  # noqa: E402
from student_pilot import frame_input as F  # noqa: E402
from student_pilot.carrier_c1_data import nested_indices  # noqa: E402

T, FPS = 368, 24.0
ANCHORS = [i * (T - 1) // 31 for i in range(32)]
DUPLICATE = {'frame_layout': 'duplicate'}


def pin(k):
    return {'path': f'/scratch/frames/{k:05d}.png', 'sha256': f'{k:064x}'}


class ExportLayout(unittest.TestCase):
    def test_reviewer_absent_export_declaration_refuses(self):
        with self.assertRaisesRegex(ValueError, 'export_frame_input_absent'):
            R.training_layout(DUPLICATE, {'frame_count': 32, 'frame_input': F.NESTED})

    def test_null_export_declaration_refuses(self):
        with self.assertRaisesRegex(ValueError, 'export_frame_input_differs_from_config'):
            R.training_layout(dict(DUPLICATE, frame_input=None), {'frame_count': 32, 'frame_input': F.NESTED})

    def test_config_absent_null_or_different_refuses(self):
        artifact = dict(DUPLICATE, frame_input=F.NESTED)
        for config in ({'frame_count': 32}, {'frame_count': 32, 'frame_input': None},
                       {'frame_count': 32, 'frame_input': dict(F.NESTED, viewpoints=48)},
                       {'frame_count': 32, 'frame_input': dict(F.NESTED, rule='uniform')}):
            with self.assertRaisesRegex(ValueError, 'export_frame_input_differs_from_config'):
                R.training_layout(artifact, config)

    def test_matching_but_invalid_spec_refuses(self):
        bad = {'viewpoints': 64}
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_UNSUPPORTED'):
            R.training_layout(dict(DUPLICATE, frame_input=bad), {'frame_count': 32, 'frame_input': bad})

    def test_matching_declarations_read_nested_and_neither_reads_32(self):
        nested = R.training_layout(dict(DUPLICATE, frame_input=F.NESTED), {'frame_count': 32, 'frame_input': F.NESTED})
        self.assertTrue(R.check_layout(R.READ_FRAMES, nested)['matches_training'])
        for artifact, config in ((DUPLICATE, {'frame_count': 32}),
                                 (dict(DUPLICATE, frame_input=None), {'frame_count': 32, 'frame_input': None})):
            layout = R.training_layout(artifact, config)
            self.assertEqual(layout, dict(layout='duplicate', count=32))
            with self.assertRaisesRegex(ValueError, 'read_frame_layout_differs_from_training'):
                R.check_layout(R.READ_FRAMES, layout)


class ReaderAnchors(unittest.TestCase):
    def capture(self, anchors):
        return {'native': 'd1/s1', 'anchor_indices': list(anchors), 'timestamps': [k / FPS for k in anchors],
                'fps': FPS, 'total_num_frames': T}

    def row(self, anchors):
        return {'qid': 'q1', 'student_input': {'frames': [pin(k) for k in anchors], 'frame_indices': list(anchors),
                                               'timestamps': [k / FPS for k in anchors], 'fps': FPS,
                                               'total_num_frames': T, 'question': 'q', 'options': []}}

    def entry(self, anchors):
        plan = R.plan_manifest({'captures': [self.capture(sorted(anchors))]})['captures']['d1/s1']
        return dict(plan, pins={str(k): pin(k) for k in plan['decode']})

    def test_increasing_anchors_nest(self):
        row = R.student_row(self.row(ANCHORS), self.capture(ANCHORS), self.entry(ANCHORS))
        self.assertEqual(F.anchors(row['student_input']), ANCHORS)

    def test_reversed_or_mismatched_anchors_refuse(self):
        reversed_anchors = ANCHORS[::-1]
        with self.assertRaisesRegex(ValueError, 'strictly increasing'):
            R.student_row(self.row(reversed_anchors), self.capture(reversed_anchors), self.entry(ANCHORS))
        with self.assertRaisesRegex(ValueError, 'strictly increasing'):
            R.student_row(self.row(ANCHORS[:-1] + [ANCHORS[-1] - 1]), self.capture(ANCHORS), self.entry(ANCHORS))


class Install(unittest.TestCase):
    def test_reader_imports_f64_read_as_a_top_level_module_of_src_b(self):
        patch = (KIT / 'read' / 'reader_f64.patch').read_text()
        imports = [line[1:].strip() for line in patch.splitlines() if line.startswith('+') and 'f64_read' in line]
        self.assertEqual(imports, ['from f64_read import student_row',
                                   'from f64_read import check_layout as check_frames, training_layout'])
        module = json.loads((KIT / 'read' / 'READ_CONFIG_F64.json').read_text())['code']['module']
        self.assertEqual(module['install_as'], 'src/b/f64_read.py')
        self.assertNotIn('install_beside', module)

    @unittest.skipUnless(os.environ.get('F64_READER_ROOT'), 'F64_READER_ROOT names an installed src/b')
    def test_installed_reader_root_resolves_this_module(self):
        root = Path(os.environ['F64_READER_ROOT'])
        self.assertTrue((root / 'e2e_reader' / 'parity.py').is_file())
        spec = importlib.machinery.PathFinder.find_spec('f64_read', [str(root)])
        self.assertEqual(Path(spec.origin).resolve(), (KIT / 'read' / 'f64_read.py').resolve())
        self.assertIsNone(importlib.machinery.PathFinder.find_spec('f64_read', [str(root / 'e2e_reader')]))


class GpuPilot(unittest.TestCase):
    def test_pilot_uses_existing_trainer_functions(self):
        source = (KIT / 'scripts' / 'mem_pilot.py').read_text()
        tree = ast.parse(source)
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name) and node.value.id == 'run'}
        from student_pilot import carrier_c1_run, carrier_c1_routing, full_ft, r1_handover, r1_training, trace_version
        from student_pilot import carrier_c1
        from launch_r1 import entry
        self.assertEqual(sorted(n for n in used if not hasattr(carrier_c1_run, n)), [])
        self.assertTrue(used >= {'prepared', 'load_model', 'wrap_model', 'optimize_step', 'checkpoint', 'Rows'})
        for module, name in ((carrier_c1_routing, 'Gates'), (full_ft, 'base_parameters'), (r1_handover, 'verify_trainable_groups'),
                             (r1_training, 'start'), (trace_version, 'bind'), (trace_version, 'metadata'),
                             (carrier_c1, 'RECIPE'), (carrier_c1, 'parameter_groups'), (entry, 'admit')):
            self.assertTrue(hasattr(module, name), name)

    def test_longest_plan_cycles_and_refuses_gaps(self):
        import mem_pilot
        layout = [('pose', [0, 1, 2, 3])] * 3 + [('vqa', [4, 5, 6, 7])]
        longest = {'pose': [dict(index=i, tokens=100 - i) for i in range(6)], 'vqa': [dict(index=9, tokens=50)]}
        plan, tokens = mem_pilot.longest_plan(layout, longest, 4)
        self.assertEqual(plan, [('pose', [0, 1, 2, 3]), ('pose', [4, 5, 0, 1]), ('pose', [2, 3, 4, 5]), ('vqa', [9] * 4)])
        self.assertEqual(tokens[0], [100, 99, 98, 97])
        with self.assertRaisesRegex(ValueError, 'no passing rows for stream routing'):
            mem_pilot.longest_plan([('routing', [0, 1, 2, 3])], longest, 4)
        with self.assertRaisesRegex(ValueError, 'world size'):
            mem_pilot.longest_plan([('pose', [0, 1])], longest, 4)


if __name__ == '__main__':
    unittest.main()
