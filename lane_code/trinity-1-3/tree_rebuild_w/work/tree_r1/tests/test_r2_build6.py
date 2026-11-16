"""Next-leg selection, final admission, direct units and score contracts."""
from copy import deepcopy
import json
import unittest
from student_pilot import r2_admission as A, r2_contract as C, r2_policy as P, r2_units as U
from student_pilot.p3_provenance import file_pin, write
from tests.test_r2_data_path import directory, fixture
from tests.r2_init_fixture import INIT, PIN


class Build6(unittest.TestCase):
    def test_selected_archive_layout(self):
        import hashlib,io,tarfile
        from launch_r2.runtime import init_layout
        from launch_r2.host import stage_init
        root=directory()
        for prefix in ('m544','m200'):
            members={prefix+'/artifact.json':b'{}',prefix+'/heads.pt':b'tiny',prefix+'/full_weights/a':b'tiny'}
            archive=root/(prefix+'.tar')
            with tarfile.open(archive,'w') as tar:
                for name,raw in members.items():
                    entry=tarfile.TarInfo(name);entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
            hashes={k:hashlib.sha256(v).hexdigest() for k,v in members.items()}
            result=init_layout(file_pin(archive),root/prefix,hashes,100)
            mirror=__import__('pathlib').Path(result['mirror_root'])/result['artifact']['sha256'][:16]
            self.assertEqual((mirror/'heads.pt').read_bytes(),b'tiny')
            self.assertEqual((mirror/'full_weights/a').read_bytes(),b'tiny')
        with self.assertRaisesRegex(ValueError,'incomplete'):
            stage_init({},root/'bad',{'m1/a':'a','m2/b':'b'},max_member_bytes=100)

    def test_room_call_in_shipped_sessions(self):
        from types import SimpleNamespace
        import numpy as np
        from trace_format.ground_v313 import Session
        from generator.derivgen_v7.derivgen.ground_v313 import Session as GeneratorSession
        from student_pilot.live_trace313 import LiveSession, AuditSession
        from student_pilot.carrier_c1_routing import OwnGeometry
        from student_pilot.ground_lifting import OwnGeometryAdapter
        from trace_format import room_v314 as R
        from trace_format.contracts import contract_epoch
        from tests.test_room_v314 import Sensor
        evidence=[]
        for enabled in (False, True):
            with contract_epoch(enabled):
                for cls in (Session, GeneratorSession):
                    kwargs=dict(multi_instance=True,geometry_mode='sensor')
                    if cls is Session:kwargs['program_version']='3.14'
                    session=cls(None,Sensor(),None,**kwargs)
                    body=session.execute(R.CALL)
                    self.assertGreater(R.parse_response(body)['area_m2'],0)
                    evidence.append(dict(runtime=cls.__module__,enabled=enabled,response=body))
                p=np.zeros((32,9));p[:,6]=1;p[:,7:]=1.2
                geometry=OwnGeometryAdapter(OwnGeometry(p,[0.,-1.,0.],lambda k,uv:np.full(len(uv),2.)))
                live=LiveSession(SimpleNamespace(geometry=geometry),program_version='3.14')
                body=live.execute(R.CALL)
                self.assertIn('area ',body)
                replay=AuditSession(live.queries,program_version='3.14')
                self.assertEqual(replay.execute(R.CALL),body)
                evidence.append(dict(runtime='LiveSession and AuditSession',enabled=enabled,response=body))
                from student_pilot import trace_format313 as routing
                token=routing._current.set(live)
                try:self.assertEqual(routing.respond(R.CALL,live.registry)[0],body)
                finally:routing._current.reset(token)
                from tests.test_trace_format313_decode import FormatTests
                decoder_session=Session(None,Sensor(),None,program_version='3.14')
                records,_=FormatTests().run_rows([[50,1]],sessions=[decoder_session],extra_words={50:R.CALL})
                self.assertGreater(R.parse_response(records[0]['calls'][0]['response'])['area_m2'],0)
                evidence.append(dict(runtime='trace_format313 responder and routed decoder',enabled=enabled,response=records[0]['calls'][0]['response']))
        from tests.test_r2_data_path import PROOFS
        (PROOFS/'ROOM_RUNTIME.json').write_text(json.dumps(dict(boundary='Synthetic dense depth and pose stand in for GPU heads; real room measurement and session readers run.',sessions=evidence)))

    def test_pinned_init_and_unpinned_refusal(self):
        self.assertEqual(C.selected_init(PIN), INIT)
        for pin in (None, {}, dict(path=PIN['path'], sha256='0'*64)):
            with self.assertRaises(ValueError): C.selected_init(pin)
        root=directory();path=root/'i.json'
        for value in ({},dict(schema='r2-init-selection-v1',identity={}),
                      dict(schema='r2-init-selection-v1',identity={**INIT,'step':-1}),
                      dict(schema='r2-init-selection-v1',identity={**INIT,'parent_source_seal':'x'})):
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError): C.selected_init(file_pin(path))
        changed={**INIT,'artifact_sha256':'d'*64,'parent_run':'fixture','step':200}
        path.write_text(json.dumps(dict(schema='r2-init-selection-v1',identity=changed)))
        self.assertEqual(C.selected_init(file_pin(path)),changed)
        spec=dict(contract=C.CONTRACT,init=changed,mode='warm_start',run_id='new',code_sha256='a'*64,mixture_sha256='b'*64)
        self.assertEqual(C.check_init(spec,changed),spec)
        with self.assertRaises(ValueError): C.check_init(spec,INIT)
        from student_pilot.r2_config import configure
        from launch_r2.build import build
        with self.assertRaisesRegex(ValueError,'pinned init'):
            configure({},'none')

    def test_family_gate_refuses_below_ninety_after_exclusions(self):
        reports=[dict(family=names[-1],counts={'x':dict(seen=110,admitted=90,refused=20)},
                      refusals=[dict(reason='excluded:withheld_room') for _ in range(10)]+[dict(reason='missing frame') for _ in range(10)])
                 for names in A.FAMILIES.values()]
        self.assertTrue(all(v==dict(eligible=100,admitted=90) for v in A.family_admission(reports).values()))
        for index in range(len(reports)):
            bad=deepcopy(reports);bad[index]['counts']['x']['admitted']=89
            bad[index]['counts']['x']['refused']=21
            bad[index]['refusals'].append(dict(reason='missing frame'))
            with self.assertRaisesRegex(ValueError,'below 90%'): A.family_admission(bad)
        unknown=deepcopy(reports);unknown[0]['refusals'][0]['reason']='excluded:unknown_overlap'
        with self.assertRaisesRegex(ValueError,'below 90%'):A.family_admission(unknown)
        self.assertEqual(A.family_admission(reports+[dict(family='pose')]),A.family_admission(reports))
        with self.assertRaises(ValueError): A.family_admission([])
        bad=deepcopy(reports);bad[0]['counts']['x']['admitted']=111
        with self.assertRaisesRegex(ValueError,'Invalid'): A.family_admission(bad)
        root=directory();path=root/'m.json'
        with self.assertRaises(ValueError): A.check_family_receipt(None)
        path.write_text('{}')
        with self.assertRaises(ValueError): A.check_family_receipt(file_pin(path))
        path.write_text(json.dumps(dict(schema='r2-materialization-v1',status='ready',intake=reports)))
        self.assertEqual(A.check_family_receipt(file_pin(path)),A.family_admission(reports))
        # Exercise the same pinned-receipt reader called by the launch entry.
        for index in range(len(reports)):
            bad=deepcopy(reports);bad[index]['counts']['x'].update(admitted=89,refused=21)
            bad[index]['refusals'].append(dict(reason='missing frame'))
            path.write_text(json.dumps(dict(schema='r2-materialization-v1',status='ready',intake=bad)))
            with self.assertRaisesRegex(ValueError,'Family admission below 90%'):
                A.check_family_receipt(file_pin(path))

    def test_direct_square_feet_and_inches(self):
        root=directory()
        for unit,asked,kind in [('ft2','square feet',name) for name in U.ROOM]+[('in','inches','object_size_estimation')]:
            row=fixture(root,qid=unit);question='What is the room size in '+asked+'?' if unit=='ft2' else 'How wide is the sofa in inches?'
            row.update(question_type=kind,question=question,answer_unit=unit,answer='12')
            row['student_input']['question']=question
            row['target']='<think>\nLocate: the stove is seen in frame 17.\nLocate: the sofa is seen in frame 2.\nRelate: the stove is to the right of the sofa.\n</think>\n\n12'
            if unit=='ft2':row['target']=row['target'].replace('the stove','the room')
            C.validate(row,'vqa')
            self.assertNotIn('compute',row['target'])
            if unit=='ft2':
                bad=deepcopy(row);bad['target']=bad['target'].replace('Relate:', 'Converting to square feet: Relate:')
                with self.assertRaises(ValueError):C.validate(bad,'vqa')
                bad=deepcopy(row);bad['answer_unit']='ft'
                with self.assertRaisesRegex(ValueError,'unit'):C.validate(bad,'vqa')
            row['student_input']['question']='How wide is the sofa in metres?'
            with self.assertRaisesRegex(ValueError,'unit'):C.validate(row,'vqa')

    def test_read_scores_per_asked_unit_metres_first(self):
        items=[dict(question_type='object_abs_distance',question='How far in feet?',score=2),
               dict(question_type='object_abs_distance',question='How far in metres?',score=4),
               dict(question_type='room_size_estimation',question='What area in square feet?',score=6),
               dict(question_type='room_size_estimation',question='What area in square metres?',score=8),
               dict(question_type='object_counting',question='How many?',score=10)]
        result=U.score_by_unit(items)
        self.assertEqual([row['unit'] for row in result['distance']],['m','ft'])
        self.assertEqual([row['unit'] for row in result['room']],['m2','ft2'])
        self.assertEqual(result['distance'][0],dict(unit='m',count=1,score=4))
        for kind in U.DISTANCE:
            self.assertEqual(U.score_by_unit([dict(question_type=kind,question='How far in metres?',score=4)]),
                             {'distance':[dict(unit='m',count=1,score=4)]})
        receipt=dict(required_scores=['all','without_venue_381879'],metric_units=U.metric_units(items))
        values={k:dict(by_asked_unit=result) for k in receipt['required_scores']}
        self.assertEqual(P.require_scores(receipt,values),values)
        from student_pilot.p3_provenance import load
        path=directory()/'scores.json';write(path,values)
        self.assertEqual(P.require_scores(receipt,load(path)),values)
        bad=deepcopy(values)
        bad['all']['by_asked_unit']['distance']=list(reversed(bad['all']['by_asked_unit']['distance']))
        with self.assertRaisesRegex(ValueError,'metres first'):P.require_scores(receipt,bad)
        bad=deepcopy(values);bad['all']['by_asked_unit']['distance'][0]['score']=float('nan')
        with self.assertRaisesRegex(ValueError,'finite'):P.require_scores(receipt,bad)
        bad['all']['by_asked_unit']['distance'][0].update(count=0,score=None)
        self.assertEqual(P.require_scores(receipt,bad),bad)
        with self.assertRaises(ValueError):P.require_scores(receipt,{k:1 for k in values})
        for question in ('How far in centimetres?','How far in inches?'):
            self.assertIn(U.asked_unit(dict(question_type='object_abs_distance',question=question)),('cm','in'))
        for question in ('How far?','How far in square feet?'):
            with self.assertRaises(ValueError):U.asked_unit(dict(question_type='object_abs_distance',question=question))
        items[0]['score']=float('nan')
        with self.assertRaises(ValueError):U.score_by_unit(items)
