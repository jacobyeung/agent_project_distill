"""v3.12.1 import keeps generated text and admission provenance explicit."""
import unittest

from student_pilot import carrier_c1_routing as routing, p3_printed_calculator
from student_pilot.e2e_routing_rows import adapt_generated


def source():
    calls=[dict(call='<ground obj="chair">',response='<tool_response>\nchair: not seen\n</tool_response>')]
    body='I will inspect the chair.\n'+calls[0]['call']+'\n'+calls[0]['response']+'\nI use the supplied direct derivation.'
    return dict(spec_version='3.12.1',qid='diagnostic-ground-row',type='object_abs_distance',
        suffix='<think>\n'+body+'\n</think>\n<answer>A</answer>',answer='A',events=calls,
        diagnostic_only=True,training_admitted=False,geometry_source='gt',mask_source='gt',
        scene_gt_sha256='a'*64,gt_authority='independent fixture',simulated_misses=['chair'])


class RoutingRows(unittest.TestCase):
    def test_native_events_match_the_source_except_the_chat_closing_delimiter(self):
        row=source();inputs=dict(question='Question?',options=['A. one'],frames=[])
        packed=adapt_generated(row,inputs,dataset='fixture',scene='fixture-scene')
        self.assertEqual(packed['target'],row['suffix'].replace('\n</think>\n<answer>','\n</think>\n\n<answer>'))
        target,spans,_=routing.render_full(packed['routing']['events'],packed['routing']['answer'])
        self.assertEqual(target,packed['target'])
        self.assertEqual(len(spans),1)
        self.assertEqual(target[spans[0]['start']:spans[0]['end']],row['events'][0]['response'])
        self.assertEqual(packed['student_input'],inputs)
        self.assertIsNot(packed['student_input'],inputs)
        self.assertTrue(packed['ground_build']['diagnostic_only'])
        self.assertFalse(packed['ground_build']['training_admitted'])
        with self.assertRaisesRegex(ValueError,'Infrastructure-only'):
            routing.check_row(packed['routing'])
        self.assertIs(routing.calculator_for(packed['routing']),p3_printed_calculator)

    def test_ground_and_gap_render_without_adding_to_the_five_base_tokens(self):
        self.assertEqual(len(routing.OPENERS),5)
        events=[dict(kind='tool_call',token='<ground obj="chair">'),
                dict(kind='canonical_text',text='\n'),
                dict(kind='tool_call',token='<gap a="chair" b="desk" b="lamp">')]
        text,_,segments=routing.render_full(events,'<answer>B</answer>')
        self.assertIn('<gap a="chair" b="desk" b="lamp">',text)
        openers=[text[a:b] for a,b,name in segments if name=='opener']
        self.assertEqual(openers,['<ground','<gap'])
        for revision in ('3.11','3.12','3.12.1','3.12.2'):
            self.assertIs(routing.calculator_for(dict(trace_revision=revision)),p3_printed_calculator)

    def test_v3122_preserves_new_format_and_refuses_the_retired_probability(self):
        row=source();row['spec_version']='3.12.2'
        packed=adapt_generated(row,{},dataset='fixture',scene='s')
        self.assertEqual(packed['routing']['trace_revision'],'3.12.2')
        row['suffix']=row['suffix'].replace('chair: not seen','chair: frames 1,2 (best 2, p 1.00)')
        row['events'][0]['response']=row['events'][0]['response'].replace('chair: not seen','chair: frames 1,2 (best 2, p 1.00)')
        with self.assertRaisesRegex(ValueError,'retired probability'):
            adapt_generated(row,{},dataset='fixture',scene='s')

    def test_corrupt_events_and_answer_envelope_refuse(self):
        row=source();row['events'][0]['call']='<ground obj="different">'
        with self.assertRaisesRegex(ValueError,'differs from its suffix'):
            adapt_generated(row,{},dataset='fixture',scene='s')
        row=source();row['answer']='B'
        with self.assertRaisesRegex(ValueError,'supplied answer envelope'):
            adapt_generated(row,{},dataset='fixture',scene='s')
