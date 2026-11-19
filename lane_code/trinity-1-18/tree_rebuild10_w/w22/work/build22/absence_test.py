from pathlib import Path
from copy import deepcopy
import sys,json,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import torch
torch.set_num_threads(8);torch.set_num_interop_threads(1)
from student_pilot import r1_absence as A,r1_components as C
from student_pilot.p3_provenance import load,file_pin

class Absence22(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cfg=load(D/'inputs/config.json');cls.cfg['r1_training']['not_present_slots']=list(A.PREFIXES)
  cls.model=A.build(cls.cfg)
  p=D/'proofs/absence';p.mkdir(parents=True,exist_ok=True)
  cls.pin=file_pin(p/'heads.pt') if (p/'heads.pt').exists() else None
  if cls.pin is None:torch.save({'pose.example':torch.zeros(1)},p/'heads.pt');cls.pin=file_pin(p/'heads.pt')
  cls.state=torch.load(cls.pin['path'],map_location='meta',weights_only=True)
 def test_three_proofs_and_all_refusals(self):
  evidence=A.evidence(self.cfg,{'heads':self.pin})
  for slot in A.PREFIXES:
   self.assertEqual(evidence[slot]['status'],'NOT_PRESENT');A.verify(evidence[slot],self.cfg,slot)
   bad=deepcopy(self.cfg)
   if slot=='heads_gf1_connector':bad['geometry_connector']='gf1'
   else:bad['frame_embeddings']=True
   with self.assertRaisesRegex(ValueError,'CONFIG_NAMES'):A.prove(bad,self.model,self.state,slot,self.pin)
   name='gf1' if slot=='heads_gf1_connector' else 'frame_embeddings'
   self.model.auxiliary_heads.add_module(name,torch.nn.Identity())
   with self.assertRaisesRegex(ValueError,'BUILT_MODULE'):A.prove(self.cfg,self.model,self.state,slot,self.pin)
   self.model.auxiliary_heads._modules.pop(name)
   state={**self.state,A.PREFIXES[slot][0]+'weight':torch.zeros(1)}
   with self.assertRaisesRegex(ValueError,'STATE_TENSOR'):A.prove(self.cfg,self.model,state,slot,self.pin)
   for field in ('modules','tensors'):
    bad=deepcopy(evidence[slot]);bad['record'][field].append('forged')
    with self.assertRaisesRegex(ValueError,'PROOF_DIFFERS'):A.verify(bad,self.cfg,slot)
  (D/'NOT_PRESENT.json').write_text(json.dumps(evidence,indent=2)+'\n')
 def test_lineage_data_forbidden_and_deferred_still_blocks(self):
  for slot in ('init_m544','data_rows_r2','heads_pose'):
   with self.assertRaisesRegex(ValueError,'SLOT_FORBIDDEN'):A.prove(self.cfg,self.model,self.state,slot,self.pin)
  evidence=A.evidence(self.cfg,{'heads':self.pin});evidence['init_m544']={'status':'DEFERRED'}
  for boundary in ('official-read','official-init','handover'):
   with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_DEFERRED'):
    C.guard({'component_evidence':evidence},['VSI-Bench'],boundary)
 def test_real_constructor_component_branch(self):
  from student_pilot.carrier_c1_data import C1_B
  cfg=deepcopy(self.cfg);cfg['carrier_placement']=C1_B
  model=A.build(cfg)
  self.assertTrue(hasattr(model.auxiliary_heads,'frame_embeddings'))
  with self.assertRaisesRegex(ValueError,'CONFIG_NAMES'):
   A.prove(cfg,model,model.state_dict(),'heads_frame_embeddings',self.pin)
 def test_official_boundary_failing_before_and_current_tensor_refusal(self):
  import importlib.util
  from student_pilot import r2_policy as P
  from student_pilot.p3_provenance import digest
  root=D/'proofs/absence/official';root.mkdir(exist_ok=True)
  source=root/'source.json';source.write_text('{}')
  registry=P.slots()
  for name,slot in registry.items():
   record=dict(schema=slot['expected_schema'],component=name,component_class=slot['component_class'],phase=slot['phase'],
     inputs=[file_pin(source)],verdict='PROVEN_CLEAN',exclusions_complete=True)
   if name in P.LINEAGE:record.update(checked_banks=list(P.SCOPE),overlaps=[])
   if name in P.EXTERNAL:record.update(verdict='EXEMPT_FROZEN',frozen=True)
   p=root/(name+'.json');p.write_text(json.dumps(record));slot['record']=file_pin(p)
  p=root/'registry.json';p.write_text(json.dumps(registry));rp=file_pin(p)
  evidence=C.normalize(P.components(rp,'training'));evidence.update(A.evidence(self.cfg,{'heads':self.pin}))
  prep=deepcopy(self.cfg);prep.update(schema='c1-preparation-v1',component_evidence=evidence)
  prep['r1_training']['registry']=rp;p=root/'prep.json';p.write_text(json.dumps(prep))
  artifact=dict(component_evidence=evidence,component_preparation=file_pin(p),component_evidence_sha256=digest(evidence),heads=self.pin)
  spec=importlib.util.spec_from_file_location('student_pilot.old_components22',D/'before/r1_components.py')
  old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_RECORD_REQUIRED'):old.guard(artifact,['VSI-Bench'],'official-read')
  C.guard(artifact,['VSI-Bench'],'official-read')
  p=root/'one_tensor.pt';torch.save({'frame_embeddings.weight':torch.zeros(1)},p)
  with self.assertRaisesRegex(ValueError,'STATE_TENSOR'):C.guard(dict(artifact,heads=file_pin(p)),['VSI-Bench'],'official-read')

if __name__=='__main__':unittest.main(verbosity=2)
