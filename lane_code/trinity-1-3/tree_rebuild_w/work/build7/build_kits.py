"""Restage A2 then A0 with unresolved inputs explicit and GO closed."""
import hashlib,json,os,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7';T=L/'work/tree_r1'
sys.path.insert(0,str(T));os.environ['R2_FIXTURES']=str(L/'fixtures')
from launch_r2.build import build,scan,verify
from student_pilot.p3_provenance import write
from student_pilot.response_spec import sha256
from tests.test_r2_build import inputs
out=B/'kits';out.mkdir(parents=True,exist_ok=True)
policy=json.loads((B/'TRAINABLE_POLICY.json').read_text())
# The bound parent includes depth_init: load_depth_stage1 freezes the private copy.
policy['private_vit']=dict(trainable=False,learning_rate=0.,source='load_depth_stage1')
resolution_files=[str(p.relative_to(L)) for p in (L/'fixtures').rglob('*processor*') if p.is_file()]
values=dict(schema='kit-inputs-v7',training_objective='sft',init=None,row_stores=None,dense_manifest=None,
 max_pixels=None,min_pixels=None,frame_count=32,frame_layout='duplicate',frame_markers=True,
 weight_scale=1.0,weight_scale_basis='GUESS: equal to final-mode gravity weight',minority_count=2000,
 trainable_modules=policy,response_spec=dict(version='tool-response-text-v1',sha256=sha256()),
 r0_sha256='f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479',
 claim_reader='harness_served',read_order=['ReVSI official999','VSI-Bench'],room_claim=False,
 processor_authority='base_identity c202236235762e1c871ad0ccb60c8ee5ba337b9a',
 dense_authority='DENSE_FRAMES_PLAN_20261115.md option (a): real Orchard GF-1 dense manifest',
 gf1_cache_option=dict(enabled=False,dtype='float32'),h1=dict(faithful_own_camera_rows=False))
values['qualification_blockers']=[
 'ROWS_RULE_TEXT_PRESENT:rows_lanes',
 'ROWS_MINORITY_FORMS_UNBOUND:rows_lanes',
 'R0_FULL_INPUT_INVENTORY_UNAVAILABLE:rows_and_frames_lanes',
 'BOTH_PATH_AND_CACHE_INDEPENDENT_REVIEW_PENDING:review_lane',
 'PREPARED_MULTI_STORE_RECEIPT_BINDING_UNIMPLEMENTED:tree_lane',
 'READER_FORWARD_HOOK_REQUIRED:b04_e2ehook',
 'FRAME64_ALL_READERS_UNQUALIFIED:tree_lane']
results=[]
for arm,connector in (('a2','gf1'),('a0','none')):
 value=dict(values)
 if arm=='a2':value['trainable_stages']=dict(stage1={'gf1':dict(trainable=True,learning_rate=1e-4),
      'other_modules':dict(trainable=False,learning_rate=0.)},stage2=policy)
 kit=out/arm
 result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),launch_inputs=value)
 result.update(scan=scan(kit),verified_sha256=verify(kit),kit_path=str(kit.relative_to(L)))
 results.append(result);print(json.dumps(dict(arm=arm,sha256=result['kit_sha256'],blockers=result['blockers'])),flush=True)
write(out/'RESULTS.json',results)
(B/'PROCESSOR_SEARCH.json').write_text(json.dumps(dict(scope='fixtures only; no external paths read',files=resolution_files,
    resolution='Required pinned parameter; the D0-bound processor config is absent locally'),indent=2)+'\n')
with (B/'STATUS.md').open('a') as f:f.write('\nBoth kits are staged from empty, A2 first. Hashes and input blockers: `work/build7/kits/RESULTS.json`. No init or dense fixture was substituted.\n')
