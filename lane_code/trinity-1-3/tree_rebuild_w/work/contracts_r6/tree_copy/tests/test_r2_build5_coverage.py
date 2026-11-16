"""Exercise remaining local admission branches with actual files and functions."""
import importlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from tests.test_r2_data_path import directory,fixture,LANE
from student_pilot.p3_provenance import file_pin,load,write


class LocalBranches(unittest.TestCase):
    def test_native_stop_file_and_whole_leg_validation(self):
        import torch
        from student_pilot import carrier_c1_run as R
        from student_pilot.carrier_c1 import RECIPE,parameter_groups
        from student_pilot.carrier_c1_data import C1_A
        from student_pilot.checkpoint_space import plan
        from tests.test_carrier_c1 import fixture as model_fixture
        from tests.test_carrier_c1_run import FixtureRows
        cfg=dict(schema='carrier-c1-run-v1',trace_program_version='3.13',recipe=RECIPE,
                 init='base',parallel='fsdp',all_frames=True,
                 streams=dict(pose={},vqa={},pointing={}),carrier_placement=C1_A,
                 checkpoint_disk_guard=plan(RECIPE,retained_archive_copies=1))
        R.validate(cfg)
        root=directory();flag=root/'stop';flag.write_text('stop')
        model,_,_=model_fixture(4)
        optimizer=torch.optim.AdamW(parameter_groups(model))
        with patch.dict(os.environ,{'K3':str(flag)}):
            result=R.run_steps(model,model,optimizer,FixtureRows(),dict(pose=9,vqa=9,pointing=9),
                               root,{}, {},torch.device('cpu'),smoke_steps=3,distributed=False)
        self.assertEqual(result['last_step'],1)
        self.assertTrue((root/'smoke.json').is_file())

    def test_unsupported_native_readers_refuse_before_inputs(self):
        from student_pilot import carrier_c1_run as R,grounding_eval as G
        calls=((R.inference,(None,None,None)),(R.probe,(None,None,None)),
               (G.load_runtime,(None,None,None,None)),(G.run_worker,(None,)*8),
               (G.merge,(None,None)),(G.to_ground,(None,None,None)))
        for function,args in calls:
            with self.subTest(reader=function.__name__),self.assertRaisesRegex(ValueError,'bank adapter'):
                function(*args)

    def test_trace_callback_and_plain_readers(self):
        from launch_r2 import runtime,staging,entry
        from launch_s1.b import v
        root=directory();write(root/'plain.json',dict(value=True))
        self.assertEqual(staging.read(root/'plain.json'),dict(value=True))
        with patch.dict(sys.modules,{'v':v}):
            native=importlib.import_module('launch_s1.b.a')
            self.assertEqual(native.read(root/'plain.json'),dict(value=True))
        self.assertIsNone(entry.host_receipt(root,{}))
        previous=sys.gettrace()
        try:
            sys.settrace(lambda frame,event,arg: None)
            manager=runtime.statement_hits([dict(source=file_pin(__file__),line=1)])
            with manager as hits:
                callback=sys.gettrace()
                # Monitoring is suppressed while the VM invokes trace hooks.
                # Invoke this real callback normally with real Python frames too.
                sys.settrace(None)
                frame=sys._getframe()
                self.assertIs(callback(frame,'line',None),callback)
                self.assertIs(callback(frame,'call',None),callback)
                self.assertIsNone(callback(manager.gen.gi_frame,'call',None))
            self.assertTrue(any(path==__file__ for path,line in hits))
        finally:sys.settrace(previous)

    def test_native_sampling_binding_and_training_refusal(self):
        from launch_r2.host import native_config
        from student_pilot.r2_config import configure
        from student_pilot import carrier_c1_run as R,r2_policy as P
        root=directory();write(root/'code.json',dict(tree_sha256='a'*64))
        binding=dict(counts=dict(path='fixture',sha256='b'*64))
        result=native_config(dict(code=file_pin(root/'code.json'),r2_build2={}),
                             dict(streams={},r2_membership={},r2_sampling=binding),{},root/'config')
        self.assertEqual(result['r2_sampling'],binding)
        self.assertEqual(result['r2_build2']['counts'],binding['counts'])
        cfg=configure(load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json'),'none')
        cfg['r2_identity']={};cfg.pop('r2_sampling',None)
        with self.assertRaisesRegex(ValueError,'bound r2_sampling'):
            R.run_steps(None,None,None,None,{},root,cfg,{},'cpu',distributed=False)
        with self.assertRaisesRegex(ValueError,'bank adapter'):
            P.legacy_reader_guard(dict(r2_identity={}),{})

    def test_native_response_spans_and_frame_units(self):
        from student_pilot import r2_grammar as G,carrier_c1_routing as R
        row=fixture(directory(),stream='routing')
        row['events'][2]['text']+=' <tool_response>nested</tool_response>'
        row['target'],row['tool_output_spans']=R.render(row['events'],row['answer'])
        with self.assertRaisesRegex(ValueError,'Every response'):
            G.legacy_program(row)
        body='Locate: the chair is seen in frame 1.\nStep: the chair is visible after 2 seconds.'
        with self.assertRaisesRegex(ValueError,'Frames must be named'):
            G.validate_direct('<think>\n'+body+'\n</think>\nA','Is the chair visible after 2 seconds?',32)

    def test_staged_directory_and_empty_inventory(self):
        from launch_r2.checklist import Checklist
        root=directory();(root/'u/d').mkdir(parents=True)
        write(root/'plan.json',dict(entries={'u/d':dict(directory=True,sha256='a'*64)}))
        write(root/'k/0.json',dict(staging=file_pin(root/'plan.json')))
        c=Checklist(root,{}, {})
        with self.assertRaisesRegex(ValueError,'absent or empty'):c.staged()
        (root/'u/d/value').write_bytes(b'fixture')
        self.assertTrue(c.staged()['u/d']['directory'])
        (root/'plan.json').write_text(json.dumps(dict(entries={})))
        (root/'k/0.json').write_text(json.dumps(dict(staging=file_pin(root/'plan.json'))))
        with self.assertRaisesRegex(ValueError,'No staged'):c.staged()
