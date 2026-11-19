"""Language-family rendering and masked ground/fallback event integration."""
from copy import deepcopy
import json
import os
from unittest.mock import patch
import unittest
from tests.test_r2_data_path import PROOFS, directory, fixture, manifest, TinyProcessor, LANE
from student_pilot import carrier_c1_routing as R, r2_contract as C, r2_grammar as G
from student_pilot.ground_rows import render_ground
from student_pilot.r2_materialize import materialize
from student_pilot.carrier_c1_run import Rows
from student_pilot.p3_provenance import load


def ground(root, family):
    row = fixture(root, qid=family)
    failed = family == 'recovery'
    question = 'What is the distance between the ceiling lamp and heater in centimeters?'
    answer = '2.55' if failed else '255'
    question = question.replace('centimeters', 'meters') if failed else question
    call = '<ground obj="ceiling lamp" mode="box">' if failed else '<gap a="ceiling lamp" b="heater" rule="box_grid_5cm">'
    response = 'ceiling lamp: not seen' if failed else 'distance 2.55 m'
    step = '\nLocate: the ceiling lamp is seen in frame 16.\nLocate: the heater is seen in frame 13.' if failed else '\nStep: compute 2.55 * 100 = 255.'
    events = [dict(kind='ground_trace_start', trace_revision='3.14'),
              dict(kind='canonical_text', text='<think>\nCall: measure the box gap.\n'),
              dict(kind='ground_call', token=call+'\n', call_id='g'),
              dict(kind='ground_response', text='<tool_response>'+response+'</tool_response>', call_id='g'),
              dict(kind='canonical_text', text=step+'\n</think>\n<answer>'+answer+'</answer>')]
    if not failed:
        grounds = []
        for i, name in enumerate(('ceiling lamp', 'heater')):
            grounds.extend([dict(kind='ground_call', token=f'<ground obj="{name}" mode="box">\n', call_id=f'box{i}'),
                            dict(kind='ground_response', text=f'<tool_response>{name}: best frame 13; B{i}: centre (1.44, 1.10, 0.80) m; size 0.43 x 0.43 x 0.04 m; yaw 64 deg</tool_response>', call_id=f'box{i}')])
        events[2:2] = grounds
    target, spans, _ = render_ground(events, answer)
    row.update(schema='derivgen-row-v2', form='spec-v3.14-ground-v1', infrastructure_only=False,
               response_source='ground_truth', question_type='object_abs_distance', events=events,
               answer=answer, gt_answer=answer, target=target, tool_output_spans=spans, question=question)
    row['student_input']['question'] = question
    row['provenance']['alias'] = 'd1/fixture_clean'
    calls = [e for e in events if e['kind']=='ground_call']
    responses = [e for e in events if e['kind']=='ground_response']
    row.update(trace_revision='3.14', candidate_id=family, gt_accepted=True)
    row['ground_record'] = dict(qid=family, answer=answer, gt_answer=answer, question=question,
        options=row['options'], candidate_id=family, type='object_abs_distance', spec_version='3.14',
        mask_source='gt', geometry_source='gt', gt_authority={}, not_seen=failed, gt_agrees=True,
        training_admitted=False, simulated_misses=['ceiling lamp'] if failed else [],
        unit='meters' if failed else 'centimeters',
        events=[dict(call=c['token'].strip(),response=r['text'],
                     audit=dict(simulated=failed,status='not seen' if failed else 'seen'))
                for c,r in zip(calls,responses)])
    return row


class Families(unittest.TestCase):
    def test_each_rendered_family_uses_native_encoder(self):
        root = directory()
        rows = []
        for family, kind in [('facing', 'object_rel_direction_hard'), ('totals', 'object_counting'),
                             ('relative_distance', 'object_rel_distance'), ('object_size', 'object_size_estimation'),
                             ('appearance_order', 'object_appearance_order'), ('route_planning', 'route_planning'),
                             ('box_3d', 'object_3d_box'), ('room_size', 'room_size_estimation')]:
            row = fixture(root, qid=family)
            row['question_type'] = kind
            if family == 'totals':
                row['target'] = '<think>\nLocate: chair a is seen in frame 1.\nLocate: chair b is seen in frame 2.\nStep: list [chair a; chair b]; count = 2.\n</think>\n2'
                row['answer'] = '2'
                row['question'] = row['student_input']['question'] = 'How many chairs are visible?'
            if family in ('room_size', 'object_size'):
                row['answer'] = '12.18' if family == 'room_size' else '101'
                row['question'] = row['student_input']['question'] = ('What is the combined room size in square meters?' if family == 'room_size' else 'What is the longest dimension of the stove in centimeters?')
                logic = 'Step: the question asks for the combined visible floor area.' if family == 'room_size' else 'Locate: the stove is seen in frame 17.\nStep: the question asks for the longest dimension.'
                row['target'] = '<think>\n'+logic+'\n</think>\n'+row['answer']
            if family == 'box_3d':
                row['answer'] = '{"center": [0, 0, 0], "size": [1, 1, 1], "rotation": [0, 0, 0]}'
                row['target'] = '<think>\nLocate: the stove is seen in frame 17.\n</think>\n'+row['answer']
            rows.append((family, 'vqa', row))
        for family in ('units', 'recovery'):
            rows.append((family, 'routing', ground(root, family)))
        for family in ('camera_movement_direction', 'camera_rotation'):
            row = fixture(root, qid=family, stream='routing')
            row['question_type'] = family
            if family == 'camera_rotation':
                row['events'][1]['token'] = '<turn from=1 to=25>'
            row['answer'] = '<answer>A</answer>'
            row['target'], row['tool_output_spans'] = R.render(row['events'], row['answer'])
            rows.append((family, 'routing', row))
        paths = [manifest(root/family, [row], stream=stream, family=family) for family, stream, row in rows]
        with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2': str(root/'frames')})):
            report = materialize(paths, root/'stores')
            self.assertEqual(report['status'], 'ready')
            receipt = load(report['receipt']['path'])
            self.assertEqual(sum(v['count'] for v in receipt['streams'].values()),len(rows))
            reader = Rows(receipt, TinyProcessor())
            proofs = []
            try:
                for stream, value in receipt['streams'].items():
                    for i in range(value['count']):
                        batch, _, audit = reader.get(stream, i)
                        row, _ = reader.row(stream, i)
                        self.assertGreater(int((batch['labels'] != -100).sum()), 0)
                        if stream == 'routing':
                            self.assertGreater(audit['tool_spans'], 0)
                        proofs.append(dict(family=row['qid'], stream=stream, encoded=True))
            finally:
                reader.close()
        (PROOFS/'FAMILY_ENCODER_PROOF.json').write_text(json.dumps(dict(rows=proofs, fixture_only=True), indent=2))

    def test_ground_event_fail_closed(self):
        root = directory()
        row = ground(root, 'units')
        G.validate_program(row)
        for changes in (dict(response_source='unknown'), dict(target='changed')):
            with self.assertRaises(ValueError):
                C.event_row({**row, **changes})
        invalid = deepcopy(row)
        invalid['events'][-1]['text'] = invalid['events'][-1]['text'].replace('= 255.', '= 256.')
        invalid['target'], invalid['tool_output_spans'], _ = render_ground(invalid['events'], invalid['answer'])
        with self.assertRaises(ValueError):
            G.validate_program(invalid)
        smuggled = deepcopy(row)
        smuggled['events'][1]['text'] += '<tool_response>unmasked response</tool_response>'
        smuggled['target'], smuggled['tool_output_spans'], _ = render_ground(smuggled['events'], smuggled['answer'])
        with self.assertRaisesRegex(ValueError, 'masked span|unrecorded_response'):
            G.validate_program(smuggled)
        fallback = ground(root, 'recovery')
        G.validate_program(fallback)
        missing = deepcopy(fallback)
        missing['events'][-1]['text'] = '\n</think>\n<answer>2.55</answer>'
        missing['target'], missing['tool_output_spans'], _ = render_ground(missing['events'], missing['answer'])
        with self.assertRaises(ValueError):
            C.event_row(missing)
        repeated = deepcopy(fallback)
        repeated['events'].insert(-1, dict(kind='ground_call', token='<ground obj="ceiling lamp" mode="box">', call_id='retry'))
        repeated['target'], repeated['tool_output_spans'], _ = render_ground(repeated['events'], repeated['answer'])
        with self.assertRaises(ValueError):
            C.event_row(repeated)
