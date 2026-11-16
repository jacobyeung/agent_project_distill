"""evalx fork: stub tests for the dense_aliases combination (dense cache reused, alias prompts at the dense floor and cap, merged with IoU>0.95 dedup)."""
import unittest,types
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_variants import *
import test_variants as TV


class Combo(TV.Tests):
 def test_dense_aliases_reuse_resume_price(self):
  self._combo()
 def _combo(self):
  _t(self)

def _t(self):
 p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'dense');a=self.args(p,mp,'dense');self.assertEqual(C.run(a),0)
 mp2,vm2=self.manifest(p,m,c,'dense_aliases');aa=self.args(p,mp2,'dense_aliases');aa.reuse_dense=a.out;self.assertEqual(C.run(aa),0)
 d=load_cache(Path(a.out)/'scannet__fixture_00.npz');v=load_cache(Path(aa.out)/'scannet__fixture_00.npz');validate_cache(v,vm2['captures'][0],sha(mp2),True)
 self.assertEqual(vm2['density']['joint_floor'],.05);self.assertEqual(vm2['density']['cap'],100)
 for k in range(32):
  dn=d['frames'][str(k)]['phrases']['chair']['instances'];vn=v['frames'][str(k)]['phrases']['chair']['instances'];self.assertGreaterEqual(len(vn),len(dn))
 old=sha(Path(aa.out)/'scannet__fixture_00.npz');self.assertEqual(C.run(aa),0);self.assertEqual(sha(Path(aa.out)/'scannet__fixture_00.npz'),old)
 pa=types.SimpleNamespace(manifest=str(mp2),items=str(p/'items.jsonl'),cache=aa.out,exports=str(p/'exports'),out=str(p/'priced_da'),gt_captures=None,scene=None,allow_stub=True);P.run(pa);self.assertTrue((p/'priced_da/COMPLETE.json').exists())
 self.assertTrue(V.check_manifest(vm2))

def _tt(self):
 p,m,c,q=self.fixture();mp,vm=self.manifest(p,m,c,'dense');a=self.args(p,mp,'dense');self.assertEqual(C.run(a),0)
 mp2,vm2=self.manifest(p,m,c,'dense_tiles');aa=self.args(p,mp2,'dense_tiles');aa.reuse_dense=a.out;self.assertEqual(C.run(aa),0)
 v=load_cache(Path(aa.out)/'scannet__fixture_00.npz');validate_cache(v,vm2['captures'][0],sha(mp2),True);self.assertEqual(vm2['density']['cap'],100);self.assertTrue(V.check_manifest(vm2))
 d=load_cache(Path(a.out)/'scannet__fixture_00.npz')
 for k in range(32):self.assertGreaterEqual(len(v['frames'][str(k)]['phrases']['chair']['instances']),len(d['frames'][str(k)]['phrases']['chair']['instances']))
 pa=types.SimpleNamespace(manifest=str(mp2),items=str(p/'items.jsonl'),cache=aa.out,exports=str(p/'exports'),out=str(p/'priced_dt'),gt_captures=None,scene=None,allow_stub=True);P.run(pa);self.assertTrue((p/'priced_dt/COMPLETE.json').exists())
Combo.test_dense_tiles_reuse_price=_tt

if __name__=='__main__':unittest.main(defaultTest='Combo')
