"""CP2 levers: the tool-mode prompt flag on routed rows and the CP2 routing policy."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from student_pilot import carrier_c1_routing as routing
from student_pilot import carrier_c1_run as run

FLAG = 'Tool mode: on.'


def routing_row(qid, category, question='How far is the chair from the door?'):
    return {'qid': qid, 'dataset': 'd1', 'scene': 'v0', 'student_input': {'question': question, 'frames': []},
            'routing': {'category': category, 'question_type': 'object_abs_distance'}}


class ToolModeFlag(unittest.TestCase):
    def test_flag_prefixes_only_routed_rows(self):
        routed, direct = routing_row('r', 'route'), routing_row('d', 'direct')
        flagged = routing.tool_mode(routed, FLAG)
        self.assertEqual(flagged['student_input']['question'], FLAG + '\nHow far is the chair from the door?')
        self.assertEqual(routed['student_input']['question'], 'How far is the chair from the door?')
        self.assertIs(routing.tool_mode(direct, FLAG), direct)
        self.assertIs(routing.tool_mode(routed, None), routed)
        self.assertEqual(routing.tool_mode({'qid': 'v', 'student_input': {'question': 'q'}}, FLAG)['student_input']['question'], 'q')

    def test_flag_must_be_one_stripped_line(self):
        routing.validate_tool_mode_flag(FLAG)
        for bad in ('', ' x', 'x ', 'a\nb', 'x' * 201, None, 3):
            with self.assertRaisesRegex(ValueError, 'tool_mode_flag'):
                routing.validate_tool_mode_flag(bad)

    def test_rows_apply_the_receipt_flag_to_routing_rows_only(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as root:
            paths = {}
            for stream, rows in (('routing', [routing_row('r', 'route'), routing_row('d', 'direct')]),
                                 ('vqa', [{'qid': 'v', 'student_input': {'question': 'q'}}])):
                path = Path(root) / f'{stream}.sqlite'
                conn = sqlite3.connect(str(path))
                conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
                for i, row in enumerate(rows):
                    conn.execute('INSERT INTO rows VALUES (?,?,?)', (i, json.dumps(row), '{}'))
                conn.commit()
                conn.close()
                paths[stream] = {'database': {'path': str(path), 'sha256': run.sha256(path)}, 'count': len(rows)}
            rows = run.Rows({'streams': paths, 'tool_mode_flag': FLAG, 'training_mode': 'final'}, processor=None)
            self.assertTrue(rows.row('routing', 0)[0]['student_input']['question'].startswith(FLAG + '\n'))
            self.assertEqual(rows.row('routing', 1)[0]['student_input']['question'], 'How far is the chair from the door?')
            self.assertEqual(rows.row('vqa', 0)[0]['student_input']['question'], 'q')
            plain = run.Rows({'streams': paths, 'training_mode': 'final'}, processor=None)
            self.assertFalse(plain.row('routing', 0)[0]['student_input']['question'].startswith(FLAG))


class CalculatorV3(unittest.TestCase):
    def test_closest_prints_only_the_min_line_and_keeps_every_pair(self):
        from student_pilot import p3_printed_calculator as calculator
        self.assertEqual(calculator.API_VERSION, 'printed-point-calculator-v3')
        registry = calculator.PrintedPointRegistry()
        for x in (0, 10, 1, 9):
            registry.register(camera=[x, 0, 0], f1=[x, 0, 0], spread=0, requested_frame=1)
        out = registry.execute('<closest A=P1,P2 B=P3,P4>')
        self.assertEqual(out['text'], 'min P1-P3 1.00 m')
        result = out['result']
        self.assertEqual(len(result['pairs']), 4)
        self.assertEqual(len(result['minima']), 2)
        self.assertIs(result['tied'], True)


class TraceRevisionCalculator(unittest.TestCase):
    def test_revision_3_11_rows_rerender_closest_as_one_min_line(self):
        import copy
        from tests.test_carrier_c1_routing import DerivgenRows
        DerivgenRows.setUpClass()
        rows = [r for r in DerivgenRows.rows if any(e['kind'] == 'calculator_call' and e['command'].startswith('<closest')
                                                     for e in r['events'])]
        self.assertTrue(rows)
        row = rows[0]
        legacy, _, _ = routing.rerender(row, routing.RecordedGeometry(row))
        self.assertEqual(legacy, row['target'])
        fresh = copy.deepcopy(row)
        fresh['trace_revision'] = '3.11'
        self.assertIs(routing.calculator_for(fresh), routing.calculator)
        self.assertIs(routing.calculator_for(row), routing.calculator_v2)
        v3, _, _ = routing.rerender(fresh, routing.RecordedGeometry(fresh))
        self.assertNotEqual(v3, legacy)
        self.assertLess(len(v3), len(legacy))


class NestedVqaCarriers(unittest.TestCase):
    class Tok:
        _c1_frame_markers = True

        def encode(self, text, **kwargs):
            if not text.startswith('Frame '):
                return [5]
            return [40, 100 + int(text.split()[1].rstrip(':'))]

        def convert_tokens_to_ids(self, token):
            return {'<|fim_middle|>': 5, '<|vision_start|>': 62}.get(token, 61)

    def batch(self, groups):
        import torch
        ids = torch.tensor([[2] + [v for _ in range(groups) for v in (62, 61, 63)] + [10, 11, 12]])
        batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                     mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[groups, 2, 2]]))
        batch['labels'][0, -2:] = ids[0, -2:]
        return batch

    def test_anchor_carriers_follow_only_anchor_groups_of_64(self):
        from student_pilot.carrier_c1_data import insert_frame_carriers
        anchors = list(range(0, 64, 2))
        out = insert_frame_carriers(self.batch(64), self.Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                    frame_layout='duplicate', anchors=anchors)
        seq = out['input_ids'][0].tolist()
        expected = [2] + [v for k in range(1, 65) for v in ((40, 100 + k, 62, 61, 5, 63) if (k - 1) % 2 == 0
                                                              else (40, 100 + k, 62, 61, 63))] + [10, 11, 12]
        self.assertEqual(seq, expected)
        positions = out['aux_camera_positions'][0].tolist()
        self.assertEqual(len(positions), 32)
        self.assertTrue(all(seq[p] == 5 and seq[p - 1] == 61 for p in positions))
        refs = out['aux_camera_rope_sources'][0].tolist()
        self.assertTrue(all(seq[r] == 61 and seq[r + 1] == 5 for r in refs))
        last_visual = max(i for i, v in enumerate(seq) if v == 61)
        self.assertEqual(int(out['aux_video_prefix_end'][0]), max(max(positions), last_visual))
        self.assertEqual(out['labels'][0, -2:].tolist(), [11, 12])
        self.assertEqual(out['mm_token_type_ids'][0].tolist().count(2), 64)

    def test_without_anchors_more_than_32_groups_refuse_and_32_keep_cp1_bytes(self):
        from student_pilot.carrier_c1_data import insert_frame_carriers
        with self.assertRaisesRegex(ValueError, 'at most 32 frames'):
            insert_frame_carriers(self.batch(33), self.Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                  frame_layout='duplicate')
        plain = insert_frame_carriers(self.batch(32), self.Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                      frame_layout='duplicate')
        same = insert_frame_carriers(self.batch(32), self.Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                     frame_layout='duplicate', anchors=list(range(32)))
        for key in ('input_ids', 'aux_camera_positions', 'aux_camera_rope_sources', 'aux_video_prefix_end'):
            self.assertTrue(bool((plain[key] == same[key]).all()), key)

    def test_nested_indices_bisect_the_largest_gap_with_earliest_ties(self):
        from student_pilot.carrier_c1_data import nested_indices
        anchors = [int(k * 823 / 32) for k in range(32)]
        indices, slots = nested_indices(anchors)
        self.assertEqual(len(indices), 64)
        self.assertEqual(indices, sorted(set(indices)))
        self.assertEqual([indices[k] for k in slots], anchors)
        self.assertEqual(nested_indices([0, 4, 8], count=5), ([0, 2, 4, 6, 8], [0, 2, 4]))
        self.assertEqual(nested_indices([0, 3, 9], count=4), ([0, 3, 6, 9], [0, 1, 3]))
        with self.assertRaisesRegex(ValueError, 'cannot reach'):
            nested_indices([0, 1, 2], count=4)

    def test_anchor_slots_validation(self):
        from student_pilot.carrier_c1_data import anchor_slots
        inputs = {'frames': [{}] * 64, 'anchor_slots': list(range(0, 64, 2))}
        self.assertEqual(anchor_slots(inputs), list(range(0, 64, 2)))
        self.assertIsNone(anchor_slots({'frames': [{}] * 32}))
        for bad in ([3, 2], [0, 0], [64], list(range(33))):
            with self.assertRaisesRegex(ValueError, 'anchor_slots'):
                anchor_slots({'frames': [{}] * 64, 'anchor_slots': bad})
        with self.assertRaisesRegex(ValueError, 'anchor_slots'):
            anchor_slots(inputs, 'spread')


class Cp2Policy(unittest.TestCase):
    def test_cp2_policy_routes_the_ten_trace_types(self):
        policy = routing.POLICIES['cp2-tool-mode-20261109']
        for qtype in ('absolute_distance_object', 'camera_obj_abs_dist', 'object_rel_distance', 'relative_distance_object',
                      'object_rel_direction_medium', 'object_rel_direction_hard', 'object_abs_distance',
                      'camera_displacement', 'camera_movement_direction', 'camera_rotation'):
            self.assertIn(qtype, policy['route'])
            self.assertNotIn(qtype, policy['direct'])
        self.assertFalse(set(policy['route']) & set(policy['direct']))
        self.assertEqual(set(policy['route']) | set(policy['direct']), set(routing.ALL_TYPES))

    def test_flagless_policy_routes_exactly_the_ten_trace_types(self):
        policy, flagged = routing.POLICIES['cp2-routed-20261110'], routing.POLICIES['cp2-tool-mode-20261109']
        self.assertEqual(len(policy['route']), 10)
        self.assertLess(set(policy['route']), set(flagged['route']))
        for qtype in ('room_size_estimation', 'relative_direction_object', 'absolute_direction_object'):
            self.assertIn(qtype, policy['direct'])
        self.assertFalse(set(policy['route']) & set(policy['direct']))
        self.assertEqual(set(policy['route']) | set(policy['direct']), set(routing.ALL_TYPES))


if __name__ == '__main__':
    unittest.main()
