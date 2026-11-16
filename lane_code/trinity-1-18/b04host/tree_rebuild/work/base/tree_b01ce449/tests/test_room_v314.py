"""CPU room-call contracts, live head reads, decoder bytes and row admission."""
import copy
import unittest
from types import SimpleNamespace as NS
import numpy as np
from trace_format import room_v314 as R
from trace_format.ground_v313 import Session
from trace_format.ground_v312 import wrap
from derivgen.ground_v313 import Session as GeneratorSession
from derivgen.programs_v314 import render
from derivgen.room_rows_v314 import QUESTION, agrees, validate_computation
from derivgen.ground_v313_tokens import tokenizer_for_rows, gate_positions
from render_room_v314 import prepare, check_row
from student_pilot import trace_format313 as routing
from student_pilot.live_trace313 import LiveSession, AuditSession, parse_response

class Sensor:
    kind='gt'
    def __init__(self):
        self.depth=np.full((32,48,64),2.,dtype=np.float32)
        self.K=np.array([[40.,0.,32.],[0.,40.,24.],[0.,0.,1.]])
        self.valid=np.ones(32,dtype=bool)
    def cam(self,k):return np.diag([1.,-1.,-1.]),np.zeros(3)
    def has(self,k):return bool(self.valid[k-1])
    def frame_of(self,k):return k

class RoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=tokenizer_for_rows('/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json')
    def session(self,geo=None,mode='sensor',version='3.14'):
        return Session(None,geo or Sensor(),None,program_version=version,geometry_mode=mode)
    def item(self,geo=None):
        return dict(qid='room_test',type='room_size_estimation',roles={},question=QUESTION,options=[],
                    gt_answer=R.measure(geo or Sensor())['area_m2'],gt_authority={'rule':'current_floor_area'})
    def prepared(self):
        geo=Sensor();frames=list(range(32));pin={'path':'/scratch/fixture.npz','sha256':'a'*64}
        canonical='scannet/scene9999_00';it=self.item(geo)
        it.update(frame_indices=frames,gt_authority=dict(gt=pin,frame_indices=frames,canonical=canonical))
        clip=NS(geo=geo,masks=None)
        row,packed=prepare(it,clip,None,self.tok,canonical=canonical,pin=pin,frames=frames,dev={'scannet/scene0000_00'})
        return row,packed,it,clip
    def test_sensor_vote1_predicted_vote2(self):
        sensor=R.measure(Sensor());pred=R.measure(Sensor(),'predicted')
        self.assertEqual(sensor['area_m2'],pred['area_m2'])
        self.assertEqual((sensor['min_frames'],pred['min_frames']),(1,2))
        self.assertEqual(sensor['frames'],list(range(1,33)))
        self.assertEqual(sensor['floor_height_m'],-2.1)
    def test_voting_counts_frames_not_pixels(self):
        p=np.tile([0.,0.,1.],(100,1));q=np.tile([10.,10.,1.],(100,1))
        with self.assertRaisesRegex(R.RoomRefusal,'no_floor_seen'):
            R.from_points([p,q],[1,2],'predicted',gravity_source='own')
        self.assertGreater(R.from_points([p,q],[1,2],'sensor',gravity_source='scene')['area_m2'],0)
    def test_empty_floor(self):
        g=Sensor();g.depth[:]=0
        with self.assertRaisesRegex(R.RoomRefusal,'no_floor_seen'):R.measure(g)
    def test_too_few_frames(self):
        g=Sensor();g.valid[1:]=False
        with self.assertRaisesRegex(R.RoomRefusal,'too_few_frames'):R.measure(g)
    def test_nan_depth_and_pose(self):
        for source in ('depth','pose'):
            g=Sensor()
            if source=='depth':g.depth[0,0,0]=np.nan
            else:g.cam=lambda k:(np.full((3,3),np.nan),np.zeros(3))
            with self.assertRaisesRegex(R.RoomRefusal,'nonfinite'):R.measure(g)
    def test_invalid_geometry_and_unavailable(self):
        with self.assertRaisesRegex(R.RoomRefusal,'geometry_unavailable'):R.measure(None)
        with self.assertRaisesRegex(R.RoomRefusal,'invalid_geometry'):R.measure(NS())
        g=Sensor();g.K[0,0]=0
        with self.assertRaisesRegex(R.RoomRefusal,'invalid_geometry'):R.measure(g)
    def test_extent_limit_before_allocation(self):
        p=np.tile([0.,0.,1.],(100,1));p[-1,0]=1e15
        with self.assertRaisesRegex(R.RoomRefusal,'extent_limit'):
            R.from_points([p,p],[1,2],'predicted',gravity_source='own')
    def test_duplicate_and_out_of_range_frames_refuse(self):
        p=np.zeros((100,3))
        for frames in ([1,1],[1,33],[2,1]):
            with self.assertRaisesRegex(R.RoomRefusal,'invalid_geometry'):
                R.from_points([p,p],frames,'predicted',gravity_source='own')
    def test_explicit_valid_mask_cannot_be_overridden_by_has(self):
        g=Sensor();g.valid[1:]=False;g.has=lambda k:True
        with self.assertRaisesRegex(R.RoomRefusal,'too_few_frames'):R.measure(g)
    def test_export_profile_matches_raw_heads(self):
        from student_pilot.ground_profiles import load_geometry
        from student_pilot.scene_state import FrameMap
        path='/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64/scannet__scene0011_00.npz'
        with np.load(path) as z:frames=tuple(z['anchor_frame_indices'].tolist())
        geo=load_geometry(path,FrameMap(frames),'tower_scaled')
        result=R.measure(geo,'predicted')
        self.assertEqual(result,R.measure(geo.geometry,'predicted'))
        live=LiveSession(NS(geometry=geo),program_version='3.14')
        self.assertEqual(live.execute(R.CALL),R.format_result(result))
    def test_bad_mode_refuses(self):
        with self.assertRaisesRegex(ValueError,'geometry_mode'):self.session(mode='auto')
    def test_v313_and_disabled_refuse(self):
        for s in (self.session(version='3.13'),Session(None,Sensor(),None,program_version='3.14',enabled=False)):
            with self.assertRaisesRegex(ValueError,'form_requires_v3.14'):s.execute(R.CALL)
        with self.assertRaisesRegex(ValueError,'form_requires_v3.14'):
            GeneratorSession(None,Sensor(),None).execute(R.CALL)
    def test_malformed_call_refuses(self):
        for c in ('<ground mode="room" obj="floor">','<ground mode="floor">','<ground mode="room" >'):
            with self.assertRaises(ValueError):self.session().execute(c)
    def test_sensor_preserves_native_label_basis(self):
        g=Sensor();wrapped=NS(room_geometry=g)
        self.assertEqual(R.measure(wrapped),R.measure(g))
    def test_parser_checks_frames_area_and_units(self):
        body=self.session().execute(R.CALL);parsed=parse_response(R.CALL,body,'3.14')
        self.assertGreater(parsed['area_m2'],0)
        for bad in (body.replace('m^2','m'),body.replace('frames 1,2,','frames 1,1,'),body.replace('area ','area 9')):
            with self.assertRaises(ValueError):parse_response(R.CALL,bad,'3.14')
        with self.assertRaisesRegex(ValueError,'form_requires_v3.14'):parse_response(R.CALL,body,'3.13')
    def test_fallback_for_every_refusal_code(self):
        for code in ('no_floor_seen','too_few_frames','nonfinite','geometry_unavailable','invalid_geometry','extent_limit'):
            s=self.session()
            def fail(code=code):raise R.RoomRefusal(code)
            s._room=fail;token=routing._current.set(s)
            try:
                body,info=routing.respond(R.CALL,s.registry)
                self.assertEqual(body,'error: room_'+code+'; answer directly from the video')
                self.assertTrue(info['direct_answer_fallback']);self.assertEqual(info['code'],'room_'+code)
                self.assertNotIn('area ',body)
            finally:routing._current.reset(token)
    def test_generator_decoder_exact_bytes_and_gate(self):
        row=render(self.item(),GeneratorSession(None,Sensor(),None,multi_instance=True),lambda s:len(self.tok.encode(s).ids))
        body=self.session().execute(R.CALL)
        self.assertEqual(row['events'][0]['response'].encode(),wrap(body).encode())
        self.assertTrue(gate_positions(self.tok,row['suffix']))
        self.assertEqual(self.tok.encode('<ground',add_special_tokens=False).ids,[self.tok.token_to_id('<ground')])
        validate_computation(row)
    def test_pack_and_all_scene_checks(self):
        row,packed,_,_=self.prepared()
        self.assertEqual(packed['target'].encode(),row['suffix'].encode())
        self.assertEqual(len(row['room_checks']),8)
        spans=packed['tool_output_spans']
        self.assertEqual([packed['target'][s['start']:s['end']] for s in spans],[e['response'] for e in row['events']])
    def test_template_label_tokens_and_dev_mutations(self):
        row,packed,item,clip=self.prepared()
        for field,value,reason in (('question','How big?','template'),('answer','9999.00','label'),
                                   ('suffix_tokens',0,'tokens'),('mdg_gate_token_positions',[],'tokens')):
            bad=copy.deepcopy(row);bad[field]=value
            with self.assertRaisesRegex(ValueError,reason):check_row(bad,item,clip,None,self.tok,set())
        with self.assertRaisesRegex(ValueError,'dev_scan_or_room'):
            check_row(row,item,clip,None,self.tok,{'scannet/scene9999_01'})
    def test_prose_and_pack_mutations_refuse(self):
        from orchard_ground_adapter import validate
        row,packed,_,_=self.prepared()
        bad=copy.deepcopy(packed);bad['target']=bad['target'].replace('covered floor','benchmark label')
        with self.assertRaises(ValueError):validate(bad)
        row['suffix']=row['suffix'].replace('covered floor','benchmark label')
        with self.assertRaisesRegex(ValueError,'prose'):validate_computation(row)
    def test_generator_rejects_disagreement_and_predicted_targets(self):
        it=self.item();it['gt_answer']=999
        with self.assertRaisesRegex(ValueError,'independent_room_disagreement'):
            render(it,GeneratorSession(None,Sensor(),None,multi_instance=True),len)
        with self.assertRaisesRegex(ValueError,'training_requires_sensor'):
            render(self.item(),GeneratorSession(None,Sensor(),None,multi_instance=True,geometry_mode='predicted'),len)
        self.assertTrue(agrees('1.23',1.234));self.assertFalse(agrees('1.23',1.236));self.assertFalse(agrees('nan',1))
    def test_live_head_depth_pose_replay(self):
        from student_pilot.carrier_c1_routing import OwnGeometry
        from student_pilot.ground_lifting import OwnGeometryAdapter
        p=np.zeros((32,9));p[:,6]=1;p[:,7:]=1.2;reads=[]
        def depth(k,uv):reads.append((k,len(uv)));return np.full(len(uv),2.)
        adapter=OwnGeometryAdapter(OwnGeometry(p,[0.,-1.,0.],depth))
        live=LiveSession(NS(geometry=adapter),program_version='3.14')
        body=live.execute(R.CALL)
        self.assertEqual(live.geometry_mode,'predicted')
        self.assertEqual(reads,[(k,2601) for k in range(1,33)])
        replay=AuditSession(live.queries,program_version='3.14')
        self.assertEqual(body.encode(),replay.execute(R.CALL).encode());self.assertFalse(replay.pending)
        live.execute(R.CALL);self.assertEqual(len(reads),32)
    def test_real_decoder_injects_generator_bytes(self):
        from tests.test_trace_format313_decode import FormatTests
        row=render(self.item(),GeneratorSession(None,Sensor(),None,multi_instance=True),len)
        record,_=FormatTests().run_rows([[50,1]],sessions=[self.session()],extra_words={50:R.CALL})
        self.assertEqual(wrap(record[0]['calls'][0]['response']).encode(),row['events'][0]['response'].encode())
        self.assertEqual(record[0]['calls'][0]['kind'],'ground')

if __name__=='__main__':unittest.main()
