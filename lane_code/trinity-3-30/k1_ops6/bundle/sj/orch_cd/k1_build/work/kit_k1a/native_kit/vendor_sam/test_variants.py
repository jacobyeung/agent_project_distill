"""CPU fixtures exercise inference adapters, contracts, identity, and recovery controls."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import unittest,copy,types,tempfile
import variantlib as V,variant_cache as C,analyze as A,price_masks as P
from test_kit import fixture,fresh
import cache_masks as B
from sam_backend import rle_encode

class Tests(unittest.TestCase):
 def record(self,pres=.8):
  mask=np.zeros((48,64),bool);mask[5:20,5:20]=True
  return dict(presence=pres,instances=[dict(query=4,score=.8,joint_score=.8*pres,box=[5,5,20,20],mask=rle_encode(mask))],prompt='chair',n_above_floor=1,joint_score=.8*pres)
 def test_source_scores_preserved(self):
  a=self.record();b=self.record(.4);b['instances'][0]['mask']=rle_encode(np.ones((48,64),bool));r=C.merge_record(a,b,(48,64),'seat');self.assertEqual(len(r['instances']),2);self.assertEqual(r['instances'][1]['source_presence'],.4);self.assertAlmostEqual(r['instances'][1]['joint_score'],.32)
 def test_mask_dedup(self):self.assertEqual(len(C.merge_record(self.record(),self.record(),(48,64),'seat')['instances']),1)
 def test_tile_projection(self):
  r=self.record();r['instances']=[];e=self.record();e['instances'][0]['mask']=rle_encode(np.ones((12,16),bool));out=C.merge_record(r,e,(48,64),'chair',(4,8,20,20));mask=decode(out['instances'][0]['mask']);self.assertEqual(int(mask.sum()),192);self.assertTrue(mask[8:20,4:20].all())
 def test_tile_bounds(self):
  for h,w in [(480,640),(640,480),(48,64)]:
   cover=np.zeros((h,w),bool)
   for x,y,x2,y2 in V.tile_boxes((h,w)):cover[y:y2,x:x2]=True
   self.assertTrue(cover.all())
 def test_dense_parity(self):C.baseline_parity(self.record(),self.record())
 def test_dense_parity_refuses(self):
  b=self.record();b['instances'][0]['query']=5
  with self.assertRaises(ValueError):C.baseline_parity(self.record(),b)
 def test_prompt_rules(self):self.assertEqual(V.aliases('office chair'),['chair','desk chair']);self.assertEqual(V.aliases('unknown'),[])
 def test_cause_precedence(self):
  r=dict(visible_frames=0,largest_pixels=0,usable_frames=0,prompt_relation='exact',presence_max_visible=0)
  self.assertEqual(A.cause(r),'no_visible_pixels');r.update(visible_frames=1,largest_pixels=100);self.assertEqual(A.cause(r),'below_program_size');r.update(largest_pixels=200,usable_frames=1);self.assertEqual(A.cause(r),'few_views');r.update(usable_frames=3,prompt_relation='query_finer');self.assertEqual(A.cause(r),'lexical_mismatch');r.update(prompt_relation='exact');self.assertEqual(A.cause(r),'presence_gate');r['presence_max_visible']=.3;self.assertEqual(A.cause(r),'unresolved')
 def test_relation(self):
  for a,b,r in [('office chair','chair','query_finer'),('chair','office chair','query_coarser'),('sofa','couch','synonym'),('chair','chair','exact')]:self.assertEqual(A.relation(a,b),r)
 def test_gate_only_absent(self):
  raw={'frames':{str(k):{'phrases':{'chair':self.record()}} for k in range(32)}}
  raw['frames']['4']['phrases']['chair']['instances']=[];raw['frames']['8']['phrases']['chair']['instances']=[]
  pres={('s','chair',k):.9 if k==4 else .1 for k in range(32)}
  self.assertEqual(V.selected_slots(raw,'chair',V.SPECS['student_tiles'],pres,'s'),[4]);self.assertEqual(V.selected_slots(raw,'chair',V.SPECS['tiles']),[4,8])
 def test_numpy_diagnostics_serialization(self):
  p=fresh();gt=P.base_geometry(np.ones((32,24,32)),np.tile(np.eye(4),(32,1,1)),np.tile(np.eye(3),(32,1,1)));gt.ids=[1];gt.labels=['chair'];gt.inst[:]=1
  raw={'frames':{str(k):{'phrases':{'chair':{'instances':[]}}} for k in range(32)}}
  *_,ev=P.diagnostic_objects({'scene':'scannet/f','names':{'chair':'chair'}},raw,{'chair':[]},gt);write_rows(p/'diagnostics.jsonl',[ev]);self.assertEqual(rows(p/'diagnostics.jsonl')[0]['chair']['gt_visible_frame_instances'],32)
 def fixture(self):
  p=fresh();m,c,q=fixture(p);a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(p/'base'),stub=True,review_halt=False,max_bytes=10000000,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None);self.assertEqual(B.run(a),0);return p,m,c,q
 def args(self,p,mp,name):return types.SimpleNamespace(manifest=str(mp),baseline_cache=str(p/'base'),out=str(p/name/'candidates'),stub=True,review_halt=False,max_bytes=10000000,max_seconds=120,stall_seconds=60,checkpoint=None,source=None,receipt=None,frames=str(p/'frames'),presence=None,reuse_dense=None)
 def manifest(self,p,m,c,name):
  vm=V.make_manifest(m,name,sha(p/'manifest.json'),{c['scene']:sha(p/'base'/('scannet__fixture_00.npz'))},**({'dense':V.dense_source(p/'dense'/'candidates') if name in V.COMBOS else None} if hasattr(V,'COMBOS') else {}));vm['test_stub']=True;dest=p/name;dest.mkdir(exist_ok=True);mp=dest/'MANIFEST.json';dump(mp,vm);return mp,vm
 def test_dense_and_link_resume_and_price(self):
  p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'dense');a=self.args(p,mp,'dense');self.assertEqual(C.run(a),0);path=Path(a.out)/'scannet__fixture_00.npz';old=sha(path);self.assertEqual(C.run(a),0);self.assertEqual(sha(path),old)
  mp2,_=self.manifest(p,m,c,'dense_link05');aa=self.args(p,mp2,'dense_link05');aa.reuse_dense=a.out;self.assertEqual(C.run(aa),0)
  pa=types.SimpleNamespace(manifest=str(mp2),items=str(p/'items.jsonl'),cache=aa.out,exports=str(p/'exports'),out=str(p/'priced'),gt_captures=None,scene=None,allow_stub=True);P.run(pa);before=sha(p/'priced/PER_ITEM.jsonl');P.run(pa);self.assertEqual(before,sha(p/'priced/PER_ITEM.jsonl'))
 def test_alias_and_tiles(self):
  p,m,c,q=self.fixture()
  for name in ('aliases','tiles'):
   mp,vm=self.manifest(p,m,c,name);a=self.args(p,mp,name);self.assertEqual(C.run(a),0);v=load_cache(Path(a.out)/'scannet__fixture_00.npz');validate_cache(v,vm['captures'][0],sha(mp),True)
 def test_student_tiles_bound_presence(self):
  p,m,c,q=self.fixture();rawpath=p/'base/scannet__fixture_00.npz';raw=load_cache(rawpath)
  raw['frames']['0']['phrases']['chair']['instances']=[]
  np.savez_compressed(rawpath,payload=np.frombuffer(json.dumps(raw).encode(),np.uint8))
  with (p/'base/scannet__fixture_00.journal.jsonl').open('a') as f:f.write(json.dumps(dict(event='complete',sha256=sha(rawpath)))+'\n')
  pp=p/'fixture_presence.jsonl';prs=[dict(scene=c['scene'],phrase='chair',slot=k,frame_index=f['index'],frame_sha256=f['sha256'],p_yes=.9 if k==0 else .1,checkpoint_id='synthetic-test-only',binding='synthetic-test-only',stub=False,oracle=False) for k,f in enumerate(c['frames'])];write_rows(pp,prs)
  mp,vm=self.manifest(p,m,c,'student_tiles');vm['experiment']['presence_sha256']=sha(pp);dump(mp,vm);a=self.args(p,mp,'student_tiles');a.presence=str(pp);self.assertEqual(C.run(a),0);vv=load_cache(Path(a.out)/'scannet__fixture_00.npz');self.assertTrue(vv['frames']['0']['phrases']['chair']['instances']);self.assertTrue(all('source_tile' in x for x in vv['frames']['0']['phrases']['chair']['instances']));self.assertTrue(vv['stub'])
  write_rows(pp,prs[:-1]);vm['experiment']['presence_sha256']=sha(pp)
  with self.assertRaises(ValueError):C.load_presence(pp,vm)
 def test_stale_presence_frame_refused(self):
  p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'student_tiles');pp=p/'bad_presence.jsonl';write_rows(pp,[dict(scene=c['scene'],phrase='chair',slot=0,frame_index=-1,frame_sha256='bad',p_yes=.9,checkpoint_id='fixture',binding='fixture')]);vm['experiment']['presence_sha256']=sha(pp)
  with self.assertRaises(ValueError):C.load_presence(pp,vm)
 def test_stop_time_disk_halt(self):
  p,m,c,q=self.fixture();mp,_=self.manifest(p,m,c,'aliases');a=self.args(p,mp,'aliases');o=Path(a.out);o.mkdir();(o/'STOP').write_text('STOP');self.assertEqual(C.run(a),4);(o/'STOP').write_text('RESUME');a.max_seconds=0;self.assertEqual(C.run(a),4);a.max_seconds=120;a.max_bytes=1;self.assertEqual(C.run(a),4);dump(o/'HALTED.json',{'why':'test'})
  with self.assertRaises(ValueError):C.run(a)
 def test_contract_tamper(self):
  p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'dense');vm['density']['joint_floor']=0
  with self.assertRaises(ValueError):validate_manifest(vm)
 def test_presence_real_backend_request_schema(self):
  from presence_run import request
  from verifykit.model import HFBackend
  from PIL import Image
  backend=HFBackend.__new__(HFBackend);backend.device='cpu';backend.parity_checked={'V1'};backend.pointing=types.SimpleNamespace(image_prompt=lambda processor,task:task['point_prompt']);backend.processor=lambda **kw:types.SimpleNamespace(to=lambda device:kw)
  result=backend.batch([request('office chair')],[Image.new('RGB',(10,10))]);self.assertIn('office chair',result['text'][0])
 def test_presence_reader_stub_and_resume(self):
  import presence_run as S
  p,m,c,q=self.fixture();a=types.SimpleNamespace(manifest=str(p/'manifest.json'),frames=str(p/'frames'),out=str(p/'presence'),checkpoint=None,batch_size=4,max_seconds=120,stall_seconds=60,stub=True,review_halt=False);self.assertEqual(S.run(a),0);h=sha(p/'presence/PRESENCE.jsonl');self.assertEqual(S.run(a),0);self.assertEqual(h,sha(p/'presence/PRESENCE.jsonl'))
  mp,vm=self.manifest(p,m,c,'student_tiles');vm['experiment']['presence_sha256']=h
  with self.assertRaises(ValueError):C.load_presence(p/'presence/PRESENCE.jsonl',vm)

if __name__=='__main__':
 import torch
 torch.set_num_threads(1);unittest.main(verbosity=2)
