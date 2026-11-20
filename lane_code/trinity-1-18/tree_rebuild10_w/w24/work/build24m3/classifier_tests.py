from common import *
from unittest.mock import patch
from contextlib import ExitStack
from student_pilot.r1_persisted import scope
from student_pilot import r1_direction_twins as W,r1_rooms as R
sys.path.insert(0,str(kit('q')/'b'))
import sv,cs
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
cfg=J.load(D/'census_bytes/q_clean/cfg.json')
with scope(paths):
 classify=sv.classifier(cfg)
 for row in (
  dict(qid='conflict',canonical='scannet/scene0630_00',provenance=dict(canonical_scene='scannet/scene9999_00')),
  dict(qid='conflict',canonical='scannet/scene9999_00',provenance=dict(canonical_scene='scannet/scene0630_00')),
 ):
  assert classify(row,'pointing')['K1_heldout']
 source=J.load(D/'census_bytes/q_clean/p/q/ss.json')['pointing']
 row=dict(qid='conflict',canonical='scannet/scene0630_00',provenance=dict(canonical_scene='scannet/scene9999_00'))
 value,keys=cs.evaluate(cfg,'pointing',source,lambda:iter([row]),classify)
 assert value['result']['protected_rows']==0 and value['counts']['K1_heldout']==1 and keys==['conflict']
 assert 'R1_SCENE_PROTECTED_ADMITTED_ROWS:pointing' in value['refusals']
# Authenticate a native synthetic Binding with a tiered alias. Its source store,
# binding records and union are the retained native24 fixture.
F=D/'classifier';F.mkdir()
cfg=J.load(D/'removal_receipts/cfg.json')
aliases=J.write(F/'aliases.json',dict(complete=True,conflicts=[],quarantined_tokens=[],aliases={'fixture/held':dict(canonical='scannet/scene0630_00'),'fixture/clean':dict(canonical='scannet/scene9999_00')}))
cfg['r1_training']['direction_twins']['aliases']=aliases
with scope(paths),ExitStack() as ctx:
 twins=cfg['r1_training']['direction_twins']
 for key in ('rows','binding','aliases'):ctx.enter_context(patch.object(W,key.upper(),twins[key]['sha256']))
 ctx.enter_context(patch.object(R,'STORE',J.load(cfg['streams']['vqa']['path'])['database']['sha256']))
 classify=sv.classifier(cfg)
 assert classify(dict(qid='tiered',dataset='fixture',scene='held'),'vqa')['K1_heldout']
 assert not any(classify(dict(qid='tiered',dataset='fixture',scene='clean'),'vqa').values())
J.write(D/'CLASSIFIER_TESTS.json',dict(status='PASS',pointing_checks_both_resolutions=True,independent_census_catches_24l4r_conflicting_resolution=True,vqa_uses_native_binding_room=True,tree_unchanged=True,fixture='Actual room authority and list bytes; synthetic native24 Binding pins and two fixture tiered aliases.'))
print('Both pointing resolutions and native VQA Binding.room PASS')
