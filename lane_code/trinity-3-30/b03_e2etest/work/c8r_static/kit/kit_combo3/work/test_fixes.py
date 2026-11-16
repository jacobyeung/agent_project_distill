"""Review fixes for kit_combo2 (verdict FREEZE AFTER FIXES): each test fails on kit_combo2 and passes on kit_combo3."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_variants import *
import test_variants as TV

def _dense(self):
 p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'dense');a=self.args(p,mp,'dense');self.assertEqual(C.run(a),0);return p,m,c,q,a

def _recommit(directory,sid,value):
 path=Path(directory)/(sid+'.npz');b=__import__('io').BytesIO();np.savez_compressed(b,payload=np.frombuffer(json.dumps(value).encode(),np.uint8));path.write_bytes(b.getbuffer())
 with (Path(directory)/(sid+'.journal.jsonl')).open('a') as f:f.write(json.dumps(dict(event='complete',sha256=sha(path)))+'\n')

class Fixes(TV.Tests):
 def test_f1_combo_refuses_without_dense_reuse(self):
  for name in ('dense_aliases','dense_tiles'):
   p,m,c,q,a=_dense(self);mp,vm=self.manifest(p,m,c,name);aa=self.args(p,mp,name);aa.reuse_dense=None
   with self.assertRaises(ValueError):C.run(aa)
   self.assertFalse(list(Path(aa.out).glob('*.npz')) if Path(aa.out).exists() else [])
 def test_f2_manifest_pins_dense_source(self):
  p,m,c,q,a=_dense(self);mp,vm=self.manifest(p,m,c,'dense_aliases');d=vm['experiment'].get('dense_source') or {}
  self.assertEqual(d.get('npz_sha256'),{c['scene']:sha(Path(a.out)/'scannet__fixture_00.npz')});self.assertEqual(d.get('manifest_sha256'),sha(p/'dense/MANIFEST.json'))
  self.assertEqual(set(vm['experiment'].get('inference_code_sha256') or {}),set(getattr(V,'CODE',['missing'])))
 def test_f2_refuses_changed_dense_npz(self):
  p,m,c,q,a=_dense(self);mp,vm=self.manifest(p,m,c,'dense_aliases')
  v=load_cache(Path(a.out)/'scannet__fixture_00.npz');v['frames']['0']['phrases']['chair']['instances']=[];_recommit(a.out,'scannet__fixture_00',v)
  aa=self.args(p,mp,'dense_aliases');aa.reuse_dense=a.out
  with self.assertRaises(ValueError):C.run(aa)
 def test_f2_refuses_other_receipt_or_baseline_pins(self):
  for field in ('receipt_sha256','baseline'):
   p,m,c,q,a=_dense(self);dm=json.loads((p/'dense/MANIFEST.json').read_text())
   if field=='baseline':dm['experiment']['baseline_cache_sha256']={c['scene']:'0'*64}
   else:dm[field]='0'*64
   dump(p/'dense/MANIFEST.json',dm);v=load_cache(Path(a.out)/'scannet__fixture_00.npz');v['manifest_sha256']=sha(p/'dense/MANIFEST.json');_recommit(a.out,'scannet__fixture_00',v);dump(Path(a.out)/'COMPLETE.json',dict(json.loads((Path(a.out)/'COMPLETE.json').read_text()),manifest_sha256=sha(p/'dense/MANIFEST.json')))
   dump(Path(a.out)/'BINDING.json',dict(json.loads((Path(a.out)/'BINDING.json').read_text()),manifest_sha256=sha(p/'dense/MANIFEST.json')))
   with self.assertRaises(ValueError):
    mp,vm=self.manifest(p,m,c,'dense_aliases');aa=self.args(p,mp,'dense_aliases');aa.reuse_dense=a.out;C.run(aa)
 def test_f2_refuses_other_cached_receipt(self):
  p,m,c,q,a=_dense(self);v=load_cache(Path(a.out)/'scannet__fixture_00.npz');v['receipt']={'checkpoint_sha256':'0'*64};_recommit(a.out,'scannet__fixture_00',v)
  with self.assertRaises(ValueError):
   mp,vm=self.manifest(p,m,c,'dense_aliases');aa=self.args(p,mp,'dense_aliases');aa.reuse_dense=a.out;C.run(aa)
 def test_f2_refuses_changed_inference_code_pin(self):
  p,m,c,q,a=_dense(self);mp,vm=self.manifest(p,m,c,'dense_aliases');codes=vm['experiment'].get('inference_code_sha256')
  self.assertIsInstance(codes,dict);codes['variant_cache.py']='0'*64;vm['experiment']['dense_source']['code_sha256']=codes;dump(mp,vm)
  aa=self.args(p,mp,'dense_aliases');aa.reuse_dense=a.out
  with self.assertRaises(ValueError):C.run(aa)
 def test_f5_resume_appends_nothing_and_binds_code(self):
  p,m,c,q,a=_dense(self);mp,vm=self.manifest(p,m,c,'dense_aliases');aa=self.args(p,mp,'dense_aliases');aa.reuse_dense=a.out;self.assertEqual(C.run(aa),0)
  j=Path(aa.out)/'scannet__fixture_00.journal.jsonl';before=sha(j);self.assertEqual(C.run(aa),0);self.assertEqual(sha(j),before)
  b=json.loads((Path(aa.out)/'BINDING.json').read_text());self.assertEqual(b.get('code_sha256'),V.code_pins() if hasattr(V,'code_pins') else 'missing');self.assertEqual(b.get('dense_source_manifest_sha256'),sha(p/'dense/MANIFEST.json'))
 def test_f5_one_complete_event_after_resumes(self):
  p,m,c,q,a=_dense(self);self.assertEqual(C.run(a),0);self.assertEqual(C.run(a),0)
  rs=rows(Path(a.out)/'scannet__fixture_00.journal.jsonl');self.assertEqual(rs[-1]['event'],'complete');self.assertEqual(sum(r['event']=='complete' for r in rs),1)
 def test_f8_prompt_provenance(self):
  p,m,c,q=self.fixture();check=getattr(__import__('kitlib'),'check_prompt_provenance',None);self.assertIsNotNone(check)
  check(m,[q]);bad=copy.deepcopy(m);bad['captures'][0]['names']={'sofa':'sofa'}
  with self.assertRaises(ValueError):check(bad,[q])
 def test_f8_benchmark_manifest_needs_explicit_inputs(self):
  saved=sys.argv;sys.argv=['experiment.py','--variant','dense','--stage','plan','--out','/scratch/x','--manifest','/scratch/x/MANIFEST.json','--baseline-cache','/scratch/x','--exports','/scratch/x','--baseline-program','/scratch/x','--gt-captures','/scratch/x']
  import runpy,contextlib,io
  try:
   with self.assertRaises(SystemExit) as e,contextlib.redirect_stderr(io.StringIO()):runpy.run_path(str(HERE/'experiment.py'),run_name='__main__')
  finally:sys.argv=saved
  self.assertEqual(e.exception.code,2)
 def test_f8_vsi_dataset_name(self):
  import devs1_pricing as DP
  root=fresh();z=root/'heads_g3s64';z.mkdir()
  np.savez(z/'scannetpp__abc.npz',depth_grid=np.ones((32,5,5),np.float32),r_grav=np.tile(np.eye(3),(32,1,1)),t_grav=np.zeros((32,3)),fov_hw=np.ones((32,2)),anchor_frame_indices=np.arange(32),layout='per_frame')
  D,c2w,K=DP.tower_raw(root,'scannetpp','abc','g3s64','g3t',list(range(32)),(8,8));self.assertEqual(D.shape,(32,8,8))

if __name__=='__main__':unittest.main(defaultTest='Fixes')
