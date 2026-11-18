import json,os,sys
from pathlib import Path
from copy import deepcopy
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');K=W/'pkg';sys.path[:0]=[str(K/'work/tree_r1')]
from student_pilot.p3_provenance import file_pin,digest
from student_pilot import r1_training as c
d=W/'tmp/pexp';d.mkdir(parents=True,exist_ok=True)
def w(p,v):p.write_text(json.dumps(v));return file_pin(p)
# artifact in the base (vehicle P) export format: base export writes no r1_progress
art=dict(schema='carrier-c1-artifact-v1',step=200,config_sha256='e'*64,base_identity='x',anchors=list(range(1,33)),placement='append_after_temporal_group_video_tokens_v1',training_mode='final',pose_backing='lm_final_norm',frame_layout='duplicate')
ap=w(d/'artifact.json',art)
cfg=dict(init_artifact={'artifact':ap},r1_training=dict(schema='r1-training-v1',s2=False,continuation_identity='a'*64,store_hashes={'vqa':'b'*64,'routing':'1'*64,'pose':'2'*64,'pointing':'3'*64},row_plan_sha256='c'*64,donor_config_sha256='e'*64))
out={}
try:out['P_format_no_receipt']=c.start(cfg)
except ValueError as e:out['P_format_no_receipt']=str(e)
# operator-written receipt copying N's own identities: P's own stores/row plan never enter the comparison
rec=dict(artifact_sha256=ap['sha256'],**c.boundary(cfg,200));rp=w(d/'receipt.json',rec)
g=deepcopy(cfg);g['r1_training']['continuation_receipt']=rp
out['N_values_receipt']=c.start(g)
# same receipt plus fields recording P's different stores/row plan (as P's run really has)
rec2=dict(rec,p_store_hashes={'routing':'9'*64},p_row_plan_sha256='9'*64);g2=deepcopy(cfg);g2['r1_training']['continuation_receipt']=w(d/'receipt2.json',rec2)
out['receipt_with_P_differing_stores_as_extra_fields']=c.start(g2)
# mismatched step (artifact step 200, receipt says 100)
rec3=dict(rec,step=100);g3=deepcopy(cfg);g3['r1_training']['continuation_receipt']=w(d/'receipt3.json',rec3)
try:out['receipt_step_mismatch']=c.start(g3)
except ValueError as e:out['receipt_step_mismatch']=str(e)
print(json.dumps(out,indent=1));(W/'PEXPORT.json').write_text(json.dumps(out,indent=1))
