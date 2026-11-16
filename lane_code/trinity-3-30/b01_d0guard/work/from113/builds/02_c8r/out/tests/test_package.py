import json,sys,unittest,uuid
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work'
R=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(R/'orchard_native'),str(R/'native/out2'),str(R),str(W/'tree')]
import native_launcher as L
import native_local_check as LC
import native_common as C
import native_metrics as M
import gravity_guard as GG

class Package(unittest.TestCase):
 def setUp(self):
  self.root=B/'work/package_tests'/uuid.uuid4().hex;self.root.mkdir(parents=True)
  self.family=C.load(B/'out/c8r/FAMILY_C8R.json')
 def test_seal_matches_shipped_pins(self):
  assets=deepcopy(self.family['assets'])
  next(x for x in assets['small_objects'] if x['role']=='code')['generation']='0'
  path=self.root/'FAMILY.json'
  L.seal(assets,self.family['worker_contract'],path)
  got=C.load(path)
  for field in ('code_pins','bootstrap_pins','worker_contract','limits','direct_launcher_digest'):
   self.assertEqual(got[field],self.family[field])
 def test_packet_and_pilot_time(self):
  family=B/'out/c8r/FAMILY_C8R.json';review=self.root/'REVIEW.json';order=self.root/'ORDER.md'
  artifact=W/'obj/m544_artifact.json';transport=self.root/'TRANSPORT.json';token='a'+uuid.uuid4().hex
  C.dump(review,dict(verdict='ACCEPT',reviewer='fixture; no production authority',synthetic=False,family_sha256=C.sha(family)))
  order.write_text('LAUNCH EVALX NATIVE pilot 544 general '+token+' '+C.sha(family)+' '+C.sha(artifact)+'\n')
  C.dump(transport,C.load(W/'p9/metadata/CONFIG.json')['transport'])
  dest=self.root/'packet'
  cfg=L.prepare(family,review,order,artifact,transport,'pilot','general',token,dest)
  L.validate_batch((dest/'BATCH.sh').read_text(),cfg,dict(self.family,bytes=family.read_bytes()),review.read_bytes(),order.read_bytes())
  self.assertIn('--time=02:00:00',L.submit_argv(cfg))
  self.assertEqual(C.load(dest/'PACKET.json')['gravity_guard'],GG.identity())
 def test_local_scope_preserves_other_assets(self):
  prior=C.load(B.parent/'01_c8/out/c8/FAMILY_C8.json');base=C.load(W/'p9/metadata/FAMILY.json')
  with patch.object(LC.C,'checked',side_effect=lambda x:x['path']),patch.object(LC.C,'load',side_effect=[base,prior]):
   result=LC.scope(self.family)
  self.assertTrue(result['reviewed_code_checked_against_current_family'])
 def test_guard_changed_verdict_refused(self):
  recorder=GG.Recorder()
  with GG.capture('fixture','capture'):
   recorder.record(False,False)
   with self.assertRaisesRegex(RuntimeError,'verdict_changed'):recorder.record(True,False)
 def test_guard_capture_set_refused(self):
  with self.assertRaisesRegex(ValueError,'capture sets differ'):M.validate_gravity_guard({}, {'dev-S1':[]})
 def test_request_guard_identity_refused(self):
  import nomdg as N
  import routed
  with patch.object(N,'TREE',W/'tree'),patch.object(routed,'TREE',W/'tree'):
   sources=routed.source_pins()
   request=dict(schema=N.SCHEMA,arm='paired',scope='r1',mask_source='by_type',prompt_flag=None,
    max_new_tokens=16384,thinking=True,decoding='greedy',layout='duplicate',
    decode_budget=N.Q.DECODE_BUDGET,candidate_universe_policy=N.Q.UNIVERSE,
    geometry_refusal_policy=N.GR.POLICY,fusion_policy=N.FUSION,
    grounding=dict(allow_own_fallback=False,depth_source='tower_scaled'),artifact=dict(sha256='1'*64),
    adapter_sources=N.adapter_sources(),tree_sources=sources,runtime_tree=N.tree_identity(W/'tree',sources),
    gravity_guard={'invalid':'fixture'})
   request['binding']=N.digest(request)
   with self.assertRaisesRegex(ValueError,'Gravity guard request identity differs'):N.validate_request(request)

if __name__=='__main__':unittest.main()
