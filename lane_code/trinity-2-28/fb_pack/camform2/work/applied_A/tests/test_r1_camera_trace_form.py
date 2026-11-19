"""Camera prose policy, preservation boundaries, and composition receipt semantics."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from student_pilot.r1_camera_trace_form import CameraTraceForm, POLICY, ROT_OLD, ROT_NEW, rewrite_row, rewrite_text
from student_pilot.carrier_c1_routing import render, ROUTING_SCHEMA
from student_pilot.p3_provenance import file_pin, load
from student_pilot import r1_routing


def fixture(kind='camera_rotation', text=None):
    # Deliberately synthetic; this fixture does not claim native camera admission.
    if text is None:
        text = 'The turn is '+ROT_OLD if kind=='camera_rotation' else (
            'Scoring each option by the matching component: backward = -dz = -0.32 m; forward = dz = 0.32 m.')
    events=[dict(kind='plan',text=text),dict(kind='tool_call',call_id='c',token='<turn from=1 to=2>'),
            dict(kind='tool_response',call_id='c',text='turn = +30 deg')]
    target,spans=render(events,'30')
    return dict(qid='fixture',dataset='d1',scene='fixture_clean',target=target,
                student_input=dict(question='fixture question',options=['A. left','B. right']),
                routing=dict(question_type=kind,events=events,answer='30',gt_answer='30',tool_output_spans=spans))


class CameraForm(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='camform_',dir=os.environ.get('TMPDIR')))

    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));return file_pin(p)

    def policy_pin(self):
        source=Path(__file__).parents[1]/'configs/r1_camera_trace_form_v1.json'
        p=self.root/'policy.json';p.write_bytes(source.read_bytes());return file_pin(p)

    def declaration(self):
        from student_pilot.r1_coverage import ROUTING_FAMILIES
        return self.write('decl.json',dict(schema='r1-routing-slices-v1',bound=[],
            deferred={k:'unit fixture: omitted' for k in ROUTING_FAMILIES}))

    def test_exact_rewrites_preserve_other_fields_and_offsets(self):
        for kind in ('camera_rotation','camera_movement_direction'):
            old=fixture(kind);saved=deepcopy(old);old['tool_output_spans']=deepcopy(old['routing']['tool_output_spans']);saved=deepcopy(old)
            new,ids=rewrite_row(old)
            self.assertTrue(ids);self.assertEqual(old,saved)
            self.assertEqual(new['student_input'],old['student_input'])
            self.assertEqual(new['routing']['events'][1:],old['routing']['events'][1:])
            self.assertEqual(new['tool_output_spans'],new['routing']['tool_output_spans'])
            for a,b in zip(old['routing']['tool_output_spans'],new['routing']['tool_output_spans']):
                self.assertEqual(old['target'][a['start']:a['end']],new['target'][b['start']:b['end']])
            again,ids=rewrite_row(new);self.assertIs(again,new);self.assertEqual(ids,[])

    def test_other_types_and_nonmatching_text_are_identical_objects(self):
        for kind in ('camera_displacement','object_counting','relative_distance','direction'):
            old=fixture(kind,text=ROT_OLD);new,ids=rewrite_row(old)
            self.assertIs(new,old);self.assertFalse(ids)
        old=fixture(text='No matching convention.');self.assertIs(rewrite_row(old)[0],old)

    def test_direction_rule_is_confined_to_scoring_event(self):
        for text in ('backward = -dz = -0.32 m.', 'A note: Scoring each option by the matching component: backward = -dz = -0.32 m.'):
            self.assertEqual(rewrite_text(text),(text,[]))
        text='Scoring each option by the matching component: backward = -dz = -0.32 m; left = -dx = +2.0 m; up = dy = 1.00 m.'
        self.assertEqual(rewrite_text(text)[0], 'Scoring each option by the matching component: backward = -dz; left = -dx; up = dy = 1.00 m.')
        row=fixture();row['routing']['events'][0]['kind']='correction';row['target'],row['routing']['tool_output_spans']=render(row['routing']['events'],'30')
        self.assertIs(rewrite_row(row)[0],row)

    def test_bad_source_target_or_spans_refuse(self):
        for field in ('target','spans','top_spans'):
            row=fixture()
            if field=='target':row['target']+='extra'
            elif field=='spans':row['routing']['tool_output_spans'][0]['start']+=1
            else:row['tool_output_spans']=[]
            with self.assertRaisesRegex(ValueError,'R1_CAMERA_TRACE_'):rewrite_row(row)

    def test_pin_and_policy_are_both_authenticated(self):
        pin=self.policy_pin();CameraTraceForm(pin)
        with self.assertRaises(ValueError):CameraTraceForm({**pin,'sha256':'0'*64})
        for key,value in (('rule_ids',[]),('schema','other'),('input_sha256',{})):
            policy={**POLICY,key:value}
            with self.assertRaisesRegex(ValueError,'R1_CAMERA_TRACE_POLICY_DIFFERS'):
                CameraTraceForm(self.write(key+'.json',policy))
        for invalid in (None,False,{},'v1'):
            with self.assertRaises(ValueError):CameraTraceForm(invalid)

    def compose(self, rows, cfg, batches=(),sources=None,refuse=None):
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for i,row in enumerate(rows):db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
        db.commit();p=self.root/'base.sqlite';p.write_bytes(db.serialize());db.close()
        base=self.write('base.json',dict(schema=ROUTING_SCHEMA,scene_role='train',heldout_overlap=0,database=file_pin(p),division=None))
        with patch.object(r1_routing,'Filters') as filters:
            filters.return_value.reason.side_effect=lambda row,stream:'test_exclusion' if row['qid']=='excluded' else None
            if refuse:
                with patch('student_pilot.carrier_c1_run.Rows.row',side_effect=ValueError('fixture_reader_refusal')):
                    return r1_routing.compose(base,sources or {},batches,cfg,self.root/'composed')
            return r1_routing.compose(base,sources or {},batches,cfg,self.root/'composed')

    def test_receipt_counts_only_admitted_base_rows(self):
        rows=[fixture(),dict(fixture(),qid='excluded')]
        cfg=dict(r1_training=dict(routing_slice_declaration=self.declaration(),camera_trace_form=self.policy_pin()))
        result=self.compose(rows,cfg)
        self.assertEqual(result['count'],1)
        self.assertEqual(result['camera_trace_form']['rewritten_base_rows'],1)
        self.assertEqual(result['camera_trace_form']['rewritten_base_rows_by_type'],dict(camera_rotation=1,camera_movement_direction=0))
        self.assertEqual(result['refused'],{'base:test_exclusion':1})
        self.assertEqual(result['camera_trace_form']['input_sha256']['fbp_cam/work/build.py'],POLICY['input_sha256']['fbp_cam/work/build.py'])

    def test_reader_refused_rows_do_not_enter_counts(self):
        cfg=dict(r1_training=dict(routing_slice_declaration=self.declaration(),camera_trace_form=self.policy_pin()))
        result=self.compose([fixture()],cfg,refuse=True)
        self.assertEqual(result['count'],0);self.assertEqual(result['camera_trace_form']['rewritten_base_rows'],0)

    def test_absent_policy_keeps_old_target_and_no_receipt_entry(self):
        row=fixture();result=self.compose([row],dict(r1_training=dict(routing_slices='deferred_first_boundary')))
        self.assertNotIn('camera_trace_form',result)
        db=sqlite3.connect('file:'+result['database']['path']+'?mode=ro',uri=True)
        try:self.assertEqual(json.loads(db.execute('SELECT row FROM rows').fetchone()[0]),row)
        finally:db.close()

    def test_slice_camera_rows_are_not_rewritten(self):
        from student_pilot.r1_coverage import ROUTING_FAMILIES, EXTRA_PINS
        declaration=dict(schema='r1-routing-slices-v1',bound=['camera_wording'],deferred={k:'fixture omitted' for k in ROUTING_FAMILIES if k!='camera_wording'})
        cfg=dict(r1_training=dict(routing_slice_declaration=self.write('decl.json',declaration),camera_trace_form=self.policy_pin()))
        source=self.write('slice.json',{});row=fixture();intake=self.write('intake.json',{})
        # Slice membership requires the configured source pin; use the declared
        # test source in this isolated unit, without claiming a production slice.
        with patch.dict(EXTRA_PINS,{'camera_wording':source['sha256']}):
            result=self.compose([],cfg,[('camera_wording',source,[dict(row=row)],intake)],{'camera_wording':source})
        self.assertEqual(result['count'],1);self.assertEqual(result['camera_trace_form']['rewritten_base_rows'],0)
        db=sqlite3.connect('file:'+result['database']['path']+'?mode=ro',uri=True)
        try:self.assertEqual(json.loads(db.execute('SELECT row FROM rows').fetchone()[0])['target'],row['target'])
        finally:db.close()
