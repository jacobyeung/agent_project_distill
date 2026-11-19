"""Regressions for deferred refusal, byte identity, and changed-line accounting."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from student_pilot import r1_coverage, r1_training, carrier_c1_run
from student_pilot.r1_camera_trace_form import CameraTraceForm, POLICY, ROT_OLD, rewrite_row
from student_pilot.p3_provenance import file_pin
from tests.test_r1_camera_trace_form import fixture
from student_pilot.carrier_c1_routing import render

class CameraFormReview(unittest.TestCase):
    def policy(self):
        import student_pilot.r1_camera_trace_form as module
        return file_pin(Path(module.__file__).parents[1]/'configs/r1_camera_trace_form_v1.json')

    def test_deferred_field_presence_refuses_before_pin_reads(self):
        for field in (self.policy(), 'not-a-pin', None, False, {}):
            cfg={'r1_training':{'routing_slices':'deferred_first_boundary','camera_trace_form':field}}
            with self.subTest(field=field), patch('student_pilot.r1_coverage.pinned',side_effect=AssertionError('pin read')):
                with self.assertRaisesRegex(ValueError,'^R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION$'):
                    r1_coverage.deferred(cfg,read_pins=True)

    def test_config_validation_refuses_before_other_validation(self):
        cfg={'r1_training':{'routing_slices':'deferred_first_boundary','camera_trace_form':'not-a-pin'}}
        for validator in (r1_training.validate, carrier_c1_run.validate):
            with self.subTest(validator=validator.__module__), patch('student_pilot.r1_persisted.init_policy',side_effect=AssertionError('other validation')):
                with self.assertRaisesRegex(ValueError,'^R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION$'):
                    validator(cfg)

    def test_absent_field_and_composing_mode_still_supported(self):
        self.assertTrue(r1_coverage.deferred({'r1_training':{'routing_slices':'deferred_first_boundary'}}))
        self.assertFalse(r1_coverage.deferred({'r1_training':{'camera_trace_form':self.policy()}}))
        CameraTraceForm(self.policy())

    def test_reformatted_and_reordered_policy_refuse(self):
        root=Path(tempfile.mkdtemp(prefix='camform2_policy_'))
        for i,text in enumerate((json.dumps(POLICY,indent=4)+'\n',json.dumps(POLICY,sort_keys=True)+'\n')):
            p=root/f'policy{i}.json';p.write_text(text)
            self.assertEqual(json.loads(text),POLICY)
            with self.assertRaisesRegex(ValueError,'R1_CAMERA_TRACE_POLICY_DIFFERS'):CameraTraceForm(file_pin(p))

    def test_two_matching_events_count_two_lines_one_row(self):
        row=fixture();row['routing']['events'].insert(1,dict(kind='canonical_text',text='Again '+ROT_OLD))
        row['target'],row['routing']['tool_output_spans']=render(row['routing']['events'],'30')
        form=CameraTraceForm(self.policy());_,ids=rewrite_row(row);form.record(row,ids)
        receipt=form.receipt({'database':self.policy()})
        self.assertEqual(receipt['rewritten_base_rows'],1)
        self.assertEqual(receipt['rewritten_base_rows_by_rule']['CAM-ROT-WORDS-v1'],1)
        self.assertEqual(receipt['changed_base_lines'],2)
        self.assertEqual(receipt['changed_base_lines_by_type']['camera_rotation'],2)
        self.assertEqual(receipt['changed_base_lines_by_rule']['CAM-ROT-WORDS-v1'],2)

    def test_multiline_event_counts_lines_not_occurrences(self):
        row=fixture(text=ROT_OLD+' '+ROT_OLD+'\n'+ROT_OLD)
        form=CameraTraceForm(self.policy());_,ids=rewrite_row(row);form.record(row,ids)
        receipt=form.receipt({'database':self.policy()})
        self.assertEqual(receipt['changed_base_lines'],2)
        self.assertEqual(receipt['changed_base_lines_by_rule']['CAM-ROT-WORDS-v1'],2)

if __name__=='__main__':unittest.main()
