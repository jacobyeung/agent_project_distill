"""Control-flow unit test only: native preparation/population/audit are replaced.

This is deliberately not the required native production-mode fixture.
"""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from tests.test_r1_build16 import Build16
from tests.test_r2_build_n1 import write
from student_pilot import r1_persisted as P
from student_pilot.p3_provenance import load,pinned

class Mode(unittest.TestCase):
    setUp=Build16.setUp
    tearDown=Build16.tearDown
    root=Build16.root
    fixture=Build16.fixture

    def test_relocation_scope_and_final_mapping(self):
        from launch_r1 import production_proof as Q
        for step in (200,400,600):
            root,cfg,_,_=self.fixture(step)
            cfg['preparation']=cfg['r1_training']['p_run']['preparation']
            cfg['code']=write(root/'source.json',dict(schema='fixture'))
            cfg['s1_routing']={'fixture':True}
            cfg['r1_training']['routing_inputs']={'fixture':True}
            cfg['r1_training']['row_sources']=write(root/'sources.json',{})
            cfg['remove_files']=[write(root/'remove.json',[])]
            card=load(pinned(cfg['r1_training']['mix']))
            card['counting_admission']='procedure_only_v1'
            cfg['r1_training']['mix']=write(root/'proof_card.json',card)
            pin=write(root/'mode_cfg.json',cfg)
            room=write(root/'rooms.json',dict(complete=True,unknown_overlap=0,k1_rooms=50,
                r0_rooms=372,row_sources=cfg['r1_training']['row_sources'],
                remove_files=cfg['remove_files'],authorities=[cfg['code']]))
            request=dict(config=pin,room_audit=room,staged_pins=[pin,room],frame_roots=[])
            with patch('os.uname',return_value=SimpleNamespace(nodename='trinity-1-18')):
                refused=Q.run(request,root/'host_refusal')
            self.assertIn('R1_PROOF_FRAME_HOST_REQUIRED',refused['refusal'])
            seen=[]
            def boundary(label):
                self.assertTrue(P.active())
                artifact=cfg['init_artifact']['artifact']
                self.assertEqual(str(pinned(artifact)),cfg['r1_training']['persisted_files'][artifact['sha256']])
                seen.append(label)
            def admit(*args,**kwargs):boundary('prepare');return dict(config=pin)
            def bind(value,output):boundary('population');return pin
            def audit(value,output):boundary('audit');return dict(control_flow_only=True)
            with (patch('os.uname',return_value=SimpleNamespace(nodename='fixture-host')),
                 patch('student_pilot.s1_admission.admit',side_effect=admit),
                 patch('student_pilot.r1_population.bind_prepared',side_effect=bind),
                 patch('student_pilot.r1_loader.production_audit',side_effect=audit)):
                result=Q.run(request,root/'mode')
            if step==200:
                self.assertEqual(result['status'],'REFUSE')
                self.assertIn('R1_PROOF_EXPORT_STEP_REQUIRED',result['refusal'])
            else:
                self.assertEqual(result['status'],'ADMIT',result)
            self.assertEqual(result['absolute_resume_step'],step)
            self.assertEqual(seen,['prepare','population','audit'])
            self.assertFalse(result['GO'])
            write(root/'mode/UNIT_SCOPE.json',dict(qualification='control flow only',
                replaced=['s1_admission.admit','r1_population.bind_prepared','r1_loader.production_audit'],
                required_native_mode_fixture=False))

    def test_nonfinite_forward_refuses(self):
        from launch_r1 import production_proof as Q
        with patch('student_pilot.carrier_c1_run.first_batch_check',
                   return_value=[dict(finite=False)]):
            with self.assertRaisesRegex(ValueError,'R1_PROOF_FORWARD_NONFINITE'):
                Q.forward(dict(world_size=4),self.root('nonfinite'),400)
