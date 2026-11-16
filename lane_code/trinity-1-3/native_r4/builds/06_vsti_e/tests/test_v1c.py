"""Review regressions exercised through production entry points."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import patch
import io,json,sys,tarfile,unittest,uuid
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine,scorer,policy,report,o,venue,budget,pixels
from boundary import Boundary,drive
SPEC=dict(tree=str(R/'from113/work/tree'),artifact={'path':'fixture','sha256':digest('fixture')},config={'path':'fixture','sha256':digest('fixture')})
engine.initialize(SPEC)

class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=B/'work'/('c_'+uuid.uuid4().hex);cls.root.mkdir()
        cls.bound=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',cls.root/'i',True)
        raw=engine.synthetic_tower(cls.bound,cls.root/'raw')
        cls.geometry=engine.prepare_geometry(cls.bound,SPEC,raw,cls.root/'g',Boundary())
    def test_f1_strict_answer_forms(self):
        for answer,gt,options in [('<answer>1.31</answer>','1.31',[]),('<answer>B</answer>','B',['A. left','B. right']),('1.31 meters','1.31',[]),('The answer is B.','B',['A. left','B. right'])]:
            value=scorer.score(answer,dict(ground_truth=gt,options=options))
            self.assertEqual(value['score'],1.)
        self.assertEqual(scorer.score('<answer>1.31</answer>',dict(ground_truth='1.31',options=[]))['official_fuzzy_score'],0.)
        self.assertEqual(scorer.score('uncertain',dict(ground_truth='1.31',options=[]))['score'],0.)
    def test_f1_historical_answer_forms(self):
        source=R/'from113/work/full_c8r/result.tar.gz'
        with tarfile.open(source) as stream:
            data=[json.loads(line) for line in stream.extractfile('native/paired/results/items.jsonl')]
        counts={};checks=[]
        for typ in ('object_abs_distance','room_size_estimation','camera_displacement','camera_movement_direction','camera_rotation'):
            group=[r for r in data if r['question_type']==typ and r['arm']=='unflagged' and 'decode' in r]
            forms=[scorer.final_text(r['decode']) for r in group]
            counts[typ]=dict(decoded=len(group),nonempty=sum(bool(x) for x in forms),tagged=sum('<answer>' in x for x in forms))
            for row,answer in zip(group,forms,strict=True):
                numeric=typ not in ('camera_movement_direction','camera_rotation')
                kind='numeric' if numeric else 'multiple_choice'
                parsed=scorer.official.parse_answer_v1(answer,kind,None)
                target=parsed['parsed_answer'] if parsed['parse_status']=='ok' else ('1.31' if numeric else 'B')
                # Test positive and wrong targets without assuming the historical scorer was this authority.
                for gt in (target,'2.62' if numeric else 'A'):
                    rec=dict(options=None,answer_type=kind,ground_truth=gt)
                    own=scorer.score(answer,rec)
                    expected=0. if parsed['parse_status']!='ok' else (scorer.official.official_mra(scorer.official.official_to_float(parsed['parsed_answer']),scorer.official.official_to_float(gt),.5,.95,.05) if numeric else scorer.official.official_exact_match(parsed['parsed_answer'],str(gt)))
                    self.assertEqual(own['score'],expected)
                    checks.append(dict(key=row['key'],target=gt,score=own['score'],parsed=parsed))
        self.assertEqual(counts['object_abs_distance']['tagged'],146)
        self.assertEqual(counts['room_size_estimation']['tagged'],34)
        dump(B/'out/HISTORICAL_FORMS.json',dict(source=pin(source),counts=counts,checks=len(checks),mismatches=0,records=checks))
    def test_f1_canary_strict_recomputation(self):
        root=self.root/'strict';engine.run(self.root/'i/BOUND.json',SPEC,self.geometry,root,boundary=Boundary())
        receipt=load(root/'CANARY.json');self.assertTrue(receipt['checks']['strict_scores'])
        records=rows(root/'items.jsonl');records[0]['score']=.12345
        result=engine.canary_check(records,self.bound['canary'],load(root/'REQUEST.json'),load(self.root/'i/SCORES.json'))
        self.assertFalse(result['checks']['strict_scores'])
    def test_f2_shared_packet(self):
        family=load(B/'out/FAMILY.json');receipts=deepcopy(family['added'])
        for r in receipts.values():r.update(sha256=r['sha256'] or 'a'*64,bytes=r['bytes'] or 10,generation='123',verified=True)
        dump(self.root/'receipts.json',receipts);token='123456789abcdef012345678'
        o.packet(B/'out/FAMILY.json',self.root/'receipts.json',self.root/'packet',token,time_limit='03:30:00')
        text=(self.root/'packet/a.sh').read_text()
        self.assertIn('#SBATCH --output=/dev/null',text);self.assertNotIn('/tmp',text)
        self.assertIn(o.PREFIX+'p/'+token+'/o.py',text)
        with self.assertRaisesRegex(ValueError,'shared project'):
            o.packet(B/'out/FAMILY.json',self.root/'receipts.json',self.root/'badpacket',token,resume=dict(path='/tmp/prior.tar'),time_limit='03:30:00')
    def test_f3_s1_staged_namespace(self):
        root=self.root/'namespace'
        args=venue.namespace(root,[],gpu='GPU-allocated-uuid')
        self.assertEqual(args[0],str(root/'bwrap'))
        self.assertEqual(args[args.index('CUDA_VISIBLE_DEVICES')+1],'GPU-allocated-uuid')
        self.assertEqual(venue.namespace(root,[],cpu=True,host_bwrap=True)[0],'/usr/bin/bwrap')
        self.assertIn("gpu=os.environ['CUDA_VISIBLE_DEVICES']",(B/'code/o.py').read_text())
        self.assertIn("os.environ['CUDA_VISIBLE_DEVICES'],False,host_bwrap=False",(B/'code/orchard.py').read_text())
    def test_s2_proof_failure_continues(self):
        for i,failure in enumerate((NS(returncode=3),RuntimeError('call or replay failure'),__import__('subprocess').TimeoutExpired('proof',1))):
            root=self.root/('proof'+str(i));root.mkdir()
            kwargs={'side_effect':failure} if isinstance(failure,Exception) else {'return_value':failure}
            with patch.object(o.subprocess,'run',**kwargs):
                self.assertEqual(o.run_phase(['fixture'],'/x/p.py',root,{},io.StringIO(),1),0)
            self.assertTrue(load(root/'p/PROOF.json')['failed'])
            with patch.object(o.subprocess,'run',return_value=NS(returncode=0)):
                self.assertEqual(o.run_phase(['fixture'],'/x/a.py',root,{},io.StringIO(),1),0)
        with patch.object(o.subprocess,'run',return_value=NS(returncode=1)):
            with self.assertRaises(RuntimeError):o.run_phase(['fixture'],'/x/a.py',self.root,{},io.StringIO(),1)
    def test_s3_parity_refusal_exclusion(self):
        import nomdg as N,perception as P,routed
        from evalpath import parity,items,runtime
        root=self.root/'parity';root.mkdir();boundary=engine.NativeBoundary.__new__(engine.NativeBoundary)
        boundary.model=object();boundary.processor=object();boundary.info={};boundary.cfg={};boundary.spec=dict(device='cpu')
        decoded=dict(heads={},calls=[dict(kind='error',call='<depth_at frame=1 x=500 y=500>',response=policy.RESPONSE,at_token=8)],errors=1)
        p1=dict(checked=1,mismatches=[],sequence=dict(exact=True),cached_positions_complete=True)
        seen=[]
        def p2(model,batch,record,kind,strict):
            seen.append(record['calls']);return {'pass':True,'independent_calls':len(record['calls'])}
        with patch.object(routed,'trainer_row',return_value={}),patch.object(items,'assert_prompt_equal'),patch.object(runtime,'prompt_batch',return_value={}),patch.object(N,'move_batch',side_effect=lambda b,d:b),patch.object(P,'generate',return_value=decoded),patch.object(parity,'LogitTap',return_value=object()),patch.object(parity,'p1',return_value=p1),patch.object(parity,'p2',side_effect=p2),patch.object(parity,'p3',return_value={'pass':True}):
            result=boundary.parity(dict(native='c0',id='q0'),{},'fixture',root)
            self.assertTrue(result['pass']);self.assertEqual(seen,[[]]);self.assertEqual(result['call_errors'],0)
            self.assertEqual(result['excluded_refusals'][0]['position'],8)
        dump(B/'out/PARITY_POLICY_CPU.json',dict(passed=True,synthetic=True,receipt=result))
    def test_s4_geometry_scope(self):
        import geometry_refusals as GR
        root=self.root/'refused';manifest=load(self.geometry);manifest['videos']={}
        for r in manifest['records']:r.update(status='REFUSED',output=None,error=dict(code=GR.NONFATAL_CODE,message=GR.NONFATAL_CODE,exception='GeometryError'))
        dump(root/'G.json',manifest)
        class Calls(Boundary):
            def generate(self,task,row,geo):return drive('<think><move from=1 to=2>\n<ground obj="chair" mode="box">\n</think><answer>'+('A' if task['options'] else '1.0')+'</answer>',geo)
        engine.run(self.root/'i/BOUND.json',SPEC,root/'G.json',root/'j',boundary=Calls())
        data=rows(root/'j/items.jsonl');other=[r for r in data if r['question_type'] not in CAMERA]
        self.assertTrue(other);self.assertTrue(all(not r['no_final_answer'] and not r['geometry_auto_zero'] for r in other))
        self.assertTrue(all(c['refused'] for r in other for c in r['calls']))
        self.assertTrue(all(r['camera_errors']==0 for r in other))
        self.assertTrue(all(r['geometry_auto_zero'] and r['score']==0 for r in data if r['question_type'] in CAMERA))
        engine.merge(self.root/'i/BOUND.json',[root/'j'],root/'M.json')
        bundle=load(root/'M.json');bundle['synthetic']=False
        p=dict(failed=True,status='failed',items=10,synthetic=False,error='fixture proof failure',records=[],read_binding=bundle['request_binding'])
        dump(root/'P.json',p);bundle['proof']=pin(root/'P.json');dump(root/'M.json',bundle)
        result=report.build(root/'M.json',root/'report')
        text=(root/'report/REPORT.md').read_text();headline=next(x for x in text.splitlines() if x.startswith('Primary:'))
        self.assertIn('proof failed',headline)
        for name,m in result['subtasks'].items():
            if m['calls_refused']:self.assertIn(name+' ('+str(sum(m['calls_refused'].values()))+')',headline)
        self.assertTrue(all(m['score'] is not None and m['scene_interval'] is not None for m in result['per_type'].values() if m['items']))
        self.assertIn('PARTIAL',text)
        dump(B/'out/GEOMETRY_SCOPE_CPU.json',dict(passed=True,synthetic=True,auto_zero=sum(r['geometry_auto_zero'] for r in data),decoded_other=len(other),headline=headline))
        index=dict(status='complete',scenes=2,matching=1,differences=[dict(scene='fixture',frames=[dict(slot=2,prepared=1,reference=2)])])
        dump(root/'INDEX.json',index);bound=deepcopy(self.bound);bound['inputs']['INDEX_CHECK.json']=pin(root/'INDEX.json')
        with patch.object(report,'validate_bound',return_value=bound):
            result=report.build(root/'M.json',root/'report_indices')
        self.assertEqual(result['index_check'],index)
        self.assertIn('1/2 scenes match',(root/'report_indices/REPORT.md').read_text())
    def test_s5_complete_and_incomplete_types(self):
        base=dict(calls=[],forced_close=False,no_final_answer=False,geometry_refusal=None,seconds=1,answer='A',score=1.,scene='s',room='r',question_type='camera_displacement')
        partial=report.metrics([base]*49,['camera_displacement']);self.assertEqual(partial['score'],1.);self.assertEqual(partial['status'],'PARTIAL')
        self.assertEqual(report.metrics([base]*50,['camera_displacement'])['score'],1.)
    def test_s7_distinct_deadlines(self):
        b=budget.Budget('2026-11-16T16:15:00Z',clock=lambda:budget.timestamp('2026-11-16T16:02:00Z'))
        self.assertTrue(b.allows('other'));b.observe('other',200)
        self.assertFalse(b.allows('camera_displacement'))
        r=b.record();self.assertEqual(r['subprocess_kill']-r['item_cutoff'],250)
        self.assertEqual(r['return_seconds'],600)
        self.assertEqual(budget.timestamp(b.worker_deadline(20)),b.clock()+620)
        self.assertEqual(budget.timestamp(b.worker_deadline(10000)),b.deadline)
    def test_s8_index_comparison(self):
        selection={'scene0001_00':list(range(32))};dump(self.root/'selected.json',selection)
        self.assertEqual(index_comparison(selection,self.root/'selected.json')['matching'],1)
        changed=deepcopy(selection);changed['scene0001_00'][4]+=1
        result=index_comparison(changed,self.root/'selected.json');self.assertEqual(result['differences'][0]['frames'][0],dict(slot=5,prepared=5,reference=4))
        self.assertEqual(index_comparison(selection)['status'],'pending')
        dump(self.root/'short.json',{'scene0001_00':[1]})
        with self.assertRaises(ValueError):index_comparison(selection,self.root/'short.json')
        import indices
        value=indices.run(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames',self.root/'absent.json',self.root/'indices.json')
        self.assertEqual(value['scenes'],311);self.assertEqual(value['status'],'pending')
    def test_s8_frame_count_rejected(self):
        # Reuse the synthetic MP4 built by the inherited pixel regression when available.
        import av,numpy as np
        from PIL import Image
        root=self.root/'pixel';root.mkdir();video=root/'a.mp4'
        with av.open(str(video),'w') as container:
            stream=container.add_stream('libx264',rate=24);stream.width=32;stream.height=32;stream.pix_fmt='yuv420p'
            for i in range(2):
                for packet in stream.encode(av.VideoFrame.from_ndarray(np.zeros((32,32,3),dtype=np.uint8),format='rgb24')):container.mux(packet)
            for packet in stream.encode():container.mux(packet)
        with av.open(str(video)) as container:
            frame=next(container.decode(video=0));Image.fromarray(frame.to_ndarray(format='rgb24')).save(root/'0.png')
        dump(root/'selection.json',dict(total_num_frames=3,frames=[dict(index=0,png=pin(root/'0.png'))]))
        with self.assertRaisesRegex(ValueError,'frame count'):pixels.compare(video,root/'selection.json',root,sha(video))

if __name__=='__main__':unittest.main(verbosity=2)
