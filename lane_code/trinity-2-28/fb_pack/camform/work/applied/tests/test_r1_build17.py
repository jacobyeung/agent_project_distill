"""Room and continuation boundaries; these units do not certify a native host job."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import os,json,unittest
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot import r1_rooms as R
from tests.test_r2_build_n1 import write
from tests import test_r1_build16 as b16
from tests import test_r1_build13 as b13

L=Path(os.environ['R2_LANE_ROOT'])


class Rooms(unittest.TestCase):
    def setUp(self):
        self.cfg=load(L/'work/build17/inputs/config.json')
        self.pins=self.cfg['r1_training']['room_authority']
        self.rooms=R.Rooms(self.pins)
        self.root=Path(os.environ['R2_PROOFS'])/'rooms17';self.root.mkdir(parents=True,exist_ok=True)

    def test_pinned_rule_and_alias_precedence(self):
        r=self.rooms
        self.assertEqual((len(r.k1),len(r.reserve)),(50,372))
        self.assertEqual(r.room('scannet/scene0630_04'),'scannet/scene0630')
        self.assertEqual(r.room('scannetppv2/abcdef0123'),'scannetpp/abcdef0123')
        self.assertEqual(r.room('arkitscenes/41069175'),'arkitscenes/venue381810')
        self.assertEqual(r.room('arkitscenes/999999999'),'arkitscenes/capture999999999')
        alias=next(k for k,v in r.aliases.items() if r.room(v) in r.k1)
        d,s=alias.split('/')
        self.assertEqual(r.status(dict(dataset=d,scene=s))[0],'k1_heldout')
        self.assertEqual(r.canonical(dict(dataset=d,scene=s,canonical='scannet/scene9997_00')),
                         ('scannet/scene9997_00','row_field'))
        for can,expected in [('scannet/scene0630_04','k1_heldout'),
                             ('scannet/scene9997_00','ok'),('bad/capture','unresolved')]:
            self.assertEqual(r.status(dict(canonical=can))[0],expected)
        with self.assertRaisesRegex(ValueError,'R1_ROOM_ROW_REFUSED:unresolved'):r.admit(dict(dataset='d1',scene='unknown'))
        with self.assertRaisesRegex(ValueError,'R1_ROOM_ROW_REFUSED:k1_heldout'):r.admit(dict(canonical='arkitscenes/41069175'))
        with self.assertRaisesRegex(ValueError,'R1_ROOM_CANONICAL_UNRESOLVED'):r.room('bad/x')
        bad=deepcopy(self.pins);bad['split']['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'AUTHORITY_PIN_MISMATCH'):R.Rooms(bad)

    def test_complete_audit_and_new_slice_pin(self):
        self.cfg=load(L/'work/build18/inputs/config.json')
        pin=self.cfg['r1_training']['room_audit'];audit=R.verify_audit(self.cfg,pin)
        self.assertEqual(audit['unknown_overlap'],0)
        self.assertGreater(audit['store']['unresolved'],0)
        self.assertIn('not declared overlap-free',audit['certifies'])
        cfg=deepcopy(self.cfg);cfg['remove_files']=cfg['remove_files'][:-1]
        with self.assertRaisesRegex(ValueError,'ROOM_AUTHORITY_INCOMPLETE'):R.verify_audit(cfg,pin)
        bad=deepcopy(audit);bad['slices']['units']['unremoved_hits']=1
        with self.assertRaisesRegex(ValueError,'ROOM_SLICE_UNCERTIFIED'):
            R.verify_audit(self.cfg,write(self.root/'bad.json',bad))
        source=load(pinned(self.cfg['r1_training']['row_sources']))
        source['units']['source']=write(self.root/'added.json',dict(canonical='arkitscenes/41069175'))
        cfg=deepcopy(self.cfg);cfg['r1_training']['row_sources']=write(self.root/'sources.json',source)
        with self.assertRaisesRegex(ValueError,'ROOM_AUTHORITY_INCOMPLETE'):R.verify_audit(cfg,pin)
        bad=deepcopy(audit);bad['store']['scope']='all_rows_clean'
        with self.assertRaisesRegex(ValueError,'ROOM_STORE_UNCERTIFIED'):
            R.verify_audit(self.cfg,write(self.root/'bad.json',bad))

    def test_regenerated_list_and_card(self):
        self.assertEqual((L/'work/build17/inputs/s.json').read_bytes(),(L/'work/build16/inputs/s.json').read_bytes())
        old=load(L/'work/build16/inputs/config.json')
        self.assertEqual([p['sha256'] for p in old['remove_files']],[p['sha256'] for p in self.cfg['remove_files']])
        a=load(pinned(self.cfg['r1_training']['mix']));b=load(L/'work/build16/inputs/mix.json')
        self.assertEqual(a['cells'],b['cells']);self.assertEqual(a['weight_scale'],.04)
        self.assertEqual(self.cfg['init_artifact']['artifact']['sha256'],old['init_artifact']['artifact']['sha256'])


class Composition(unittest.TestCase):
    setUp=b13.PopulationTests.setUp
    tearDown=b13.PopulationTests.tearDown
    write=b13.PopulationTests.write
    composition=b13.PopulationTests.composition
    def test_new_heldout_row_refuses(self):
        from student_pilot.r1_routing import compose
        row=dict(qid='new',dataset='d1',scene='fixture_clean',canonical='arkitscenes/41069175',
                 question_type='camera_displacement',target='<think>The camera moves right.</think>A')
        base,cfg,sources=self.composition([])
        cfg['r1_training']['room_authority']=load(L/'work/build17/inputs/config.json')['r1_training']['room_authority']
        with self.assertRaisesRegex(ValueError,'R1_ROOM_ROW_REFUSED:k1_heldout'):
            compose(base,sources,[('recovery',self.source,[dict(row=row)],self.source)],cfg,self.root/'bad')


class Boundary(unittest.TestCase):
    setUp=b16.Build16.setUp
    tearDown=b16.Build16.tearDown
    root=b16.Build16.root
    fixture=b16.Build16.fixture

    def test_handover_rebind(self):
        from student_pilot.r1_handover import bind_target
        from student_pilot.r1_training import start
        from student_pilot.r1_persisted import scope
        for step in (400,600):
            root,cfg,_,_=self.fixture(step)
            cfg['preparation_output']=str(root/'prepared_new')
            with scope(cfg['r1_training']['persisted_files']):
                result=bind_target(cfg,root/'bound_target.json')
                self.assertEqual(start(result),step)
                bad=deepcopy(cfg);bad['lm_lr_scale']=.123
                with self.assertRaisesRegex(ValueError,'LR_SCHEDULE_MISMATCH'):
                    bind_target(bad,root/'bad_target.json')

    def test_nested_metadata_scope(self):
        from student_pilot.r1_persisted import scope,active
        root=self.root('metadata');pin=write(root/'local.json',dict(metadata=True))
        remote=dict(pin,path=str(root/'absent.json'))
        with scope({pin['sha256']:pin['path']}):
            with scope({'a'*64:str(root/'unused')}):self.assertEqual(pinned(remote),Path(pin['path']))
            self.assertEqual(pinned(remote),Path(pin['path']))
        self.assertFalse(active())
        with self.assertRaises(ValueError):pinned(remote)

    def test_proof_wrong_receipt_and_milestone(self):
        from launch_r1.production_proof import run
        root,cfg,_,_=self.fixture(400)
        cfg['s1_routing']={'fixture':True};cfg['r1_training']['routing_inputs']={'fixture':True}
        cfg['r1_training']['mix']=write(root/'card17.json',dict(counting_admission='procedure_only_v1'))
        cfgpin=write(root/'q17.json',cfg)
        request=dict(config=cfgpin,staged_pins=[cfgpin],room_audit={},milestone=600)
        room=dict(certifies='unit-control-flow-only',store={})
        with patch.object(R,'verify_audit',return_value=room),patch('os.uname',return_value=SimpleNamespace(nodename='fixture-host')):
            result=run(request,root/'wrong_step')
            self.assertIn('R1_PROOF_EXPORT_STEP_REQUIRED',result['refusal'])
            request['milestone']=400
            cfg['r1_training']['handover_receipt']['sha256']='f'*64
            request['config']=write(root/'q17.json',cfg);request['staged_pins']=[request['config']]
            result=run(request,root/'wrong_pin')
            self.assertIn('P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED',result['refusal'])

    def test_missing_manifest(self):
        from student_pilot.r1_handover import donor_meta_model
        root,cfg,_,_=self.fixture()
        p=load(pinned(cfg['r1_training']['p_run']['config']))
        prep=load(pinned(p['preparation']));prep['model']['path']=str(root/'missing.json')
        p['preparation']=write(root/'missing_manifest_preparation.json',prep)
        with self.assertRaisesRegex(ValueError,'P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED'):donor_meta_model(p)

    def test_job_resources(self):
        root=L/'work/build17/proofs/operator'
        cpu=(root/'j.sh').read_text();gpu=(root/'j1.sh').read_text()
        self.assertNotIn('--job-name',cpu+gpu)
        self.assertIn('--mem=256G',cpu);self.assertIn('--mem=192G',gpu)
        self.assertIn('--gres=gpu:1',gpu)
        self.assertNotIn('20971520',cpu+gpu)
