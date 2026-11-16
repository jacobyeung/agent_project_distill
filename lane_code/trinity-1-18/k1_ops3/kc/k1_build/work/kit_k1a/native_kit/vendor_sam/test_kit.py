import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import unittest,copy,tempfile,types,time
import route_table as R,price_masks as P,cache_masks as C
import torch
import torch.nn.functional as TF
import sam3_tower as ST
from sam_backend import make_postprocess,rle_encode
TESTROOT=HERE/'tests_runs';TESTROOT.mkdir(exist_ok=True)
def fresh():return Path(tempfile.mkdtemp(dir=TESTROOT))
def fixture(path,hw=(48,64)):
 from PIL import Image
 frames=[]
 for k in range(32):
  im=Image.new('RGB',hw[::-1],(k,80,120));buf=__import__('io').BytesIO();im.save(buf,format='PNG');data=buf.getvalue();h=hashlib.sha256(data).hexdigest();p=path/'frames'/h[:2]/(h+'.png');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);frames.append(dict(index=k*3,sha256=h,path=h[:2]+'/'+h+'.png'))
 c=dict(scene='scannet/fixture_00',native='d1/fixture_00',group='g3s32',hw=list(hw),anchor_indices=[k*3 for k in range(32)],frames=frames,names={'chair':'chair'},phrases=['chair'])
 m=json.loads((HERE.parent/'out/MANIFEST.json').read_text());m['captures']=[c];m['detect_calls']=1;dump(path/'manifest.json',m)
 ex=path/'exports';grid=np.ones((32,12,12),np.float32)*2
 for name in ['heads_g3s32','heads_g3s32_vcd']:
  dst=ex/name;dst.mkdir(parents=True);np.savez_compressed(dst/'scannet__fixture_00.npz',depth_grid=grid,grid_uv=np.linspace(0,1000,12),r_grav=np.tile(np.eye(3),(32,1,1)),t_grav=np.zeros((32,3)),fov_hw=np.ones((32,2)),anchor_frame_indices=c['anchor_indices'],layout='per_frame',gravity_source='predicted')
 q=dict(qid='q',question_type='object_counting',question='How many chair(s) are in this room?',program=dict(question_type='object_counting',question='How many chair(s) are in this room?',options=[]),operands=['chair'],options=[],unit=None,binding_error=None,released_answer_in_options='1',scene=c['scene'],dataset='scannet',native=c['native'],room='d1/fixture',fixed=True,stratum='primary')
 write_rows(path/'items.jsonl',[q]);m['items_sha256']=sha(path/'items.jsonl');dump(path/'manifest.json',m);return m,c,q
class RouteTests(unittest.TestCase):
 def test_route(self):self.assertEqual(R.interval([(str(i),0.,1.) for i in range(4)])['verdict'],'route')
 def test_direct(self):self.assertEqual(R.interval([(str(i),1.,0.) for i in range(4)])['verdict'],'direct')
 def test_undecided(self):self.assertEqual(R.interval([(str(i),float(i%2),float(1-i%2)) for i in range(10)])['verdict'],'undecided')
 def test_zero_boundary(self):self.assertEqual(R.interval([('a',1.,1.),('b',1.,1.)])['verdict'],'undecided')
 def test_one_room_degenerate(self):self.assertEqual(R.interval([('a',0.,1.)])['verdict'],'route')
 def test_cluster_weight(self):
  x=[('a',0.,1.)]*9+[('b',1.,0.)];r=R.interval(x);self.assertAlmostEqual(r['difference_pp'],80);self.assertEqual(r['rooms'],2);self.assertEqual(r['low_pp'],-100)
 def test_seed(self):self.assertEqual(R.interval([('a',0.,1.),('b',1.,0.)]),R.interval([('a',0.,1.),('b',1.,0.)]))
 def test_duplicate(self):
  with self.assertRaises(ValueError):R.index([dict(q=1),dict(q=1)],lambda r:r['q'])
 def test_invalid_scores(self):
  for x in [None,float('nan'),True,1.01,-.1]:
   with self.assertRaises(ValueError):R.checked_score(x)
 def records(self):
  qs=[];ds=[];ps=[]
  for i in range(3):
   q=dict(qid=str(i),question_type='t',room='r'+str(i),scene='s'+str(i),dataset='d',stratum='primary',released_answer_in_options='1');qs.append(q);ds.append(dict(key='devrows:'+str(i),question_type='t',room=q['room'],stratum='primary',scores={'released_answer':0.}));ps.append(dict(qid=str(i),type='t',room=q['room'],scene=q['scene'],dataset='d',stratum='primary',source='g3t',policy='frozen',arm='predicted',score=1.,no_answer=False,released_answer='1'))
  return qs,dict(rows=ds,model='cp1',arm='ON16k',request_binding='x'),ps
 def test_missing_pair_refused(self):
  q,d,p=self.records()
  with self.assertRaises(ValueError):R.build(q,d,p[:-1])
 def test_metadata_refused(self):
  q,d,p=self.records();p[0]['room']='wrong'
  with self.assertRaises(ValueError):R.build(q,d,p)
 def test_stub_refused(self):
  q,d,p=self.records();p[0]['stub']=True
  with self.assertRaises(ValueError):R.build(q,d,p)
 def test_standin_no_decision(self):
  q,d,p=self.records()
  for r in p:r['arm']='gt'
  out=R.build(q,d,p,True);self.assertTrue(all(r['decision']=='not_a_decision_upper_bound' for r in out['table']))
 def test_decomposition_telescopes(self):
  q,d,p=self.records();p=[]
  for qq in q:
   for arm,s in [('predicted',.1),('oracle_accept',.3),('gt_proposed',.4),('gt_ever_proposed',.7),('gt',.9)]:p.append(dict(qid=qq['qid'],type='t',room=qq['room'],scene=qq['scene'],dataset='d',stratum='primary',source='g3t',policy='frozen',arm=arm,score=s,no_answer=False,released_answer='1'))
  out=R.build(q,d,p);self.assertAlmostEqual(sum(x['difference_pp'] for x in out['decomposition'] if x['dataset']=='All'),80)
class KitTests(unittest.TestCase):
 def test_manifest_all(self):
  m=json.loads((HERE.parent/'out/MANIFEST.json').read_text());validate_manifest(m);self.assertEqual(len(m['captures']),152)
 def test_frame_order_refused(self):
  m=json.loads((HERE.parent/'out/MANIFEST.json').read_text());m['captures'][0]['frames'].reverse()
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_prompt_refused(self):
  m=json.loads((HERE.parent/'out/MANIFEST.json').read_text());m['captures'][0]['names']['chair']='table'
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_density_refused(self):
  m=json.loads((HERE.parent/'out/MANIFEST.json').read_text());m['density']['cap']=30
  with self.assertRaises(ValueError):validate_manifest(m)
 def test_rle(self):
  rng=np.random.default_rng(1)
  for hw in [(1,1),(20,30),(30,20)]:
   a=rng.random(hw)>.5;self.assertTrue(np.array_equal(a,decode(rle_encode(a))))
 def test_rle_bad(self):
  with self.assertRaises(ValueError):decode(dict(size=[2,2],counts=[1,1]))
 def test_retention_native_parity(self):
  post=make_postprocess(TF,torch,ST.FrameDetections,.2,10)
  for seed in range(20):
   g=torch.Generator().manual_seed(seed);v=dict(pred_logits=torch.randn(1,200,1,generator=g),presence_logit_dec=torch.tensor([[.3]]),pred_boxes=torch.rand(1,200,4,generator=g),pred_masks=torch.randn(1,200,6,8,generator=g));a=ST.postprocess(v,(24,32));b,_=post(v,(24,32));self.assertEqual(a.query_ids.tolist(),b.query_ids.tolist());self.assertTrue(torch.equal(a.masks,b.masks))
 def test_models_saved_parity(self):
  for m in P.MODELS.values():self.assertLess(m['max_probability_error'],1e-12);self.assertGreater(m['parity_rows'],5000)
 def test_count_fallback(self):
  cs=[dict(candidate_id='a',features={'peak':.2}),dict(candidate_id='b',features={'peak':.8})];self.assertEqual(P.S.accept(cs,{'a':.01,'b':.02},.15)[0]['candidate_id'],'b')
 def test_merge_block(self):self.assertEqual(len(P.S.merge_learned(['a','b'],lambda i,j:.9,.2,lambda i,j:True)),2)
 def test_merge_average(self):self.assertEqual(len(P.S.merge_learned(['a','b'],lambda i,j:.3,.2)),1)
 def test_stall(self):
  with self.assertRaises(TimeoutError):C.timed(.01,time.sleep,.05)
 def test_hard_watchdog(self):
  from launch_guard import supervise
  p=fresh();rc=supervise([sys.executable,'-I','-s','-c','import time; time.sleep(10)'],p,.05,.01);self.assertEqual(rc,3);self.assertTrue((p/'HALTED.json').exists())
 def test_stub_end_to_end(self):
  p=fresh();m,c,q=fixture(p);a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(p/'cache'),stub=True,review_halt=False,max_bytes=10_000_000,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None)
  self.assertEqual(C.run(a),0);cache=p/'cache/scannet__fixture_00.npz';before=sha(cache);self.assertEqual(C.run(a),0);self.assertEqual(sha(cache),before)
  raw=load_cache(cache)
  with self.assertRaises(ValueError):validate_cache(raw,c,sha(p/'manifest.json'))
  validate_cache(raw,c,sha(p/'manifest.json'),True)
  aa=types.SimpleNamespace(manifest=str(p/'manifest.json'),items=str(p/'items.jsonl'),cache=str(p/'cache'),exports=str(p/'exports'),out=str(p/'priced'),gt_captures=None,scene=None,allow_stub=True)
  P.run(aa);rr=rows(p/'priced/PER_ITEM.jsonl');self.assertEqual(len(rr),1);self.assertEqual(rr[0]['arm'],'predicted');self.assertIsNotNone(rr[0]['score']);self.assertIsNone(rr[0]['error']);sm=load_cache(p/'priced/scannet__fixture_00.selected.npz');self.assertEqual(sm['schema'],'devs1-selected-masks-v1');self.assertIn('chair',sm['counting'])
  raw['frames']['0']['phrases']={}
  with self.assertRaises(ValueError):validate_cache(raw,c,sha(p/'manifest.json'),True)
 def test_preflight_png(self):
  from preflight import audit
  p=fresh();fixture(p,hw=(64,48));r=audit(p/'manifest.json',p/'frames');self.assertEqual(r['frames'],32)
 def test_preflight_corrupt_png(self):
  from preflight import audit
  p=fresh();m,c,q=fixture(p);(p/'frames'/c['frames'][0]['path']).write_bytes(b'bad')
  with self.assertRaises(ValueError):audit(p/'manifest.json',p/'frames')
 def test_stop_and_resume(self):
  p=fresh();m,c,q=fixture(p);o=p/'cache';o.mkdir();(o/'STOP').write_text('')
  a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(o),stub=True,review_halt=False,max_bytes=10_000_000,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None)
  self.assertEqual(C.run(a),4);self.assertFalse((o/'COMPLETE.json').exists());(o/'STOP').write_text('RESUME');self.assertEqual(C.run(a),0)
 def test_time_cap(self):
  p=fresh();fixture(p);a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(p/'cache'),stub=True,review_halt=False,max_bytes=10_000_000,max_seconds=0,stall_seconds=60,checkpoint=None,source=None,receipt=None)
  self.assertEqual(C.run(a),4)
 def test_disk_cap(self):
  p=fresh();fixture(p);a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(p/'cache'),stub=True,review_halt=False,max_bytes=1,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None)
  self.assertEqual(C.run(a),4);self.assertFalse(list((p/'cache').glob('*.npz')))
 def test_halt_refusal(self):
  p=fresh();fixture(p);o=p/'cache';o.mkdir();dump(o/'HALTED.json',{'reason':'failure'})
  a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(o),stub=True,review_halt=False)
  with self.assertRaises(ValueError):C.run(a)
 def test_unsafe_output(self):
  with self.assertRaises(ValueError):scratch('/tmp/output')
 def test_corrupt_resume(self):
  p=fresh();m,c,q=fixture(p);o=p/'cache';o.mkdir();(o/'scannet__fixture_00.npz').write_bytes(b'broken')
  a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(o),stub=True,review_halt=False,max_bytes=10_000_000,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None)
  with self.assertRaises(ValueError):C.run(a)
 def test_pair_features(self):
  p=fresh();m,c,q=fixture(p);P.SG.H,P.SG.W=24,32;geom=P.SG.GeomTower(p/'exports/heads_g3s32_vcd/scannet__fixture_00.npz');mask=np.ones((24,32),bool);mi={1:mask};cc={'features':{'peak':.8}};g=P.PF.geom_of(geom,mi);f=P.PF.pair_features(cc,cc,mi,mi,g,g,geom);self.assertAlmostEqual(f['iou2d_max'],1);self.assertTrue(0<=P.probability('pairs',f)<=1)
 def test_portrait_feature_path(self):
  p=fresh();m,c,q=fixture(p,hw=(64,48));raw=dict(phrases=['chair'],frames={str(k):{'phrases':{'chair':{'presence':.9,'instances':[{'score':.9,'mask':rle_encode(np.ones((64,48),bool))}]}}} for k in range(32)});rr=P.candidates(c,raw,p/'exports/heads_g3s32_vcd/scannet__fixture_00.npz');self.assertTrue(rr['chair']);self.assertTrue(all(np.isfinite(list(x['features'].values())).all() for x in rr['chair']))
 def test_loss_decomposition_masks(self):
  c={'scene':'scannet/test','names':{'chair':'chair'}};left=np.zeros((24,32),bool);left[:,2:11]=True;right=np.zeros_like(left);right[:,21:30]=True;wrong=np.zeros_like(left);wrong[:,13:18]=True
  gt=P.base_geometry(np.ones((32,24,32)),np.tile(np.eye(4),(32,1,1)),np.tile(np.eye(3),(32,1,1)));gt.ids=[1,2];gt.labels=['chair','chair'];gt.inst[:,left]=1;gt.inst[:,right]=2
  raw={'frames':{str(k):{'phrases':{'chair':{'instances':[{'mask':rle_encode(np.repeat(np.repeat(left,2,0),2,1))}] if k==0 else []}}} for k in range(32)}}
  cs={'chair':[{'candidate_id':'wrong','masks':{1:wrong},'p':.9,'features':{'peak':.9}},{'candidate_id':'right','masks':{1:left},'p':.1,'features':{'peak':.8}}]}
  full,prop,ever,ev=P.diagnostic_objects(c,raw,cs,gt);self.assertEqual((len(full['chair']),len(prop['chair']),len(ever['chair'])),(2,1,1));self.assertEqual(len(prop['chair'][0]),1);self.assertEqual(len(ever['chair'][0]),32);self.assertEqual([r['y'] for r in cs['chair']],[0,1]);self.assertEqual(P.selected(cs['chair'],None)[1],['wrong']);self.assertEqual(P.selected(cs['chair'],None,oracle=True)[1],['right'])
 def test_frozen_overlapping_instances(self):
  d=np.ones((32,40,50),np.float32)*2;poses=np.tile(np.eye(4),(32,1,1));ks=np.tile(np.array([[50,0,25],[0,50,20],[0,0,1.]]),(32,1,1));b=P.base_geometry(d,poses,ks);mask=np.ones((40,50),bool)
  ctx=P.context(b,d,poses,ks,{'chair':[{1:mask},{1:mask}]});self.assertEqual(len(ctx.ids('chair')),2);self.assertTrue(all(ctx.fused.seen(i) for i in ctx.ids('chair')))
if __name__=='__main__':
 torch.set_num_threads(1);unittest.main(verbosity=2)
