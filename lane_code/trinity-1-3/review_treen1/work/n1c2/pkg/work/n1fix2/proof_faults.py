"""Native refusal checks with malformed inputs and one explicit filesystem race injection."""
from pathlib import Path
import json,sys,os,hashlib,base64
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/faults'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from launch_r1 import entry,build
from launch_r2.build import capsule_json
from student_pilot import r1_training as training,row_text_audit as audit
from student_pilot.p3_provenance import file_pin
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.checkpoint_space import plan
from tests.test_r2_build_n1 import configuration,write
records=[]
for name in ('token','no_token','raced'):
    p=O/name
    if p.exists():p.rename(O/(name+'_retained'))
def refuse(name,fn,reason):
    try:fn()
    except ValueError as e:assert reason in str(e),(name,str(e));records.append(dict(case=name,reason=str(e)))
    else:raise AssertionError(name)
bad_pin=write(O/'bad_receipt.json',dict(database={'sha256':'bad'}))
refuse('invalid_store',lambda:training.target_identity(dict(r1_training={},streams={'vqa':bad_pin})),'TARGET_STORE_INVALID')
refuse('external_namespace',lambda:entry.create_job_tmp('/outside'),'JOB_TMP_REQUIRED')
with patch.object(entry,'TMP_NAMESPACE',O):
    job=O/'token';token=entry.create_job_tmp(job)
    refuse('foreign_token',lambda:entry.fresh_tmp(job/'work',{'job_tmp':str(job)},object()),'TOKEN_INVALID')
    entry.fresh_tmp(job/'work',{'job_tmp':str(job)},token)
    refuse('reused_token',lambda:entry.fresh_tmp(job/'work',{'job_tmp':str(job)},token),'TOKEN_INVALID')
    cfg=configuration();cfg={k:cfg[k] for k in ('training_mode','mix','world_size','reference_world_size','steps','milestones','scheduled_sampling','recipe')}
    cfg['checkpoint_disk_guard']=plan(recipe_for(cfg),retained_archive_copies=1)
    fresh=O/'no_token'
    result=entry.frame_host(cfg,fresh/'work',dict(job_tmp=str(fresh),binaries=['bash']))
    assert result['missing']==['R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING']
    raced=O/'raced';token=entry.create_job_tmp(raced)
    native=entry.fresh_tmp
    def race(root,request,token):
        result=native(root,request,token)
        root.mkdir(mode=0o700);(root/'late.json').write_text('{}')
        return result
    with patch.object(entry,'fresh_tmp',race):
        refuse('late_root_write',lambda:entry.frame_host(cfg,raced/'work',dict(job_tmp=str(raced),binaries=['bash']),job_tmp_token=token),'ROOT_NOT_EMPTY')
text='<tool_response>not seen</tool_response>'
assert not audit.recorded_responses({'routing':{}},text)
assert not audit.recorded_responses(dict(tool_output_spans=[dict(start=1,end=len(text))]),text)
assert not audit.recorded_responses(dict(tool_output_spans=[dict(start=0,end=len(text),event_index=0,call_id='a')],events=[dict(kind='wrong',text=text,call_id='a')]),text)
refuse('reader_scale_provenance',lambda:audit.check(dict(ground_record={'geometry_mode':'tower'}),'vqa'),'tower_scale_provenance_not_from_head')
kit=O/'kit';(kit/'k').mkdir(parents=True,exist_ok=True)
(kit/'b').mkdir(exist_ok=True)
(kit/'b/wh.json').write_bytes((T/'launch_s1/b/wh.json').read_bytes())
(kit/'job.sh').write_text('#!/bin/bash\nexit 1\n')
def capsule(name,value):(kit/name).write_bytes(capsule_json(value))
raw=b'{}';h=hashlib.sha256(raw).hexdigest()
capsule('k/c.json',dict(r1_training={'mix':{'path':'u/a','sha256':h}}))
capsule('k/s.json',dict(entries={'u/a':{'payload':base64.b64encode(raw).decode()}}))
capsule('k/8.json',dict(report_sha256='0'*64))
def manifest():
    values={str(p.relative_to(kit)):hashlib.sha256(p.read_bytes()).hexdigest() for p in kit.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
    (kit/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(values.items())))
manifest();refuse('kit_mix_pin',lambda:build.verify(kit),'MIX_EVIDENCE_DIFFERS')
capsule('k/8.json',dict(report_sha256=h))
refuse('kit_file_bytes',lambda:build.verify(kit),'CONTENT_DIFFERS')
manifest();build.verify(kit)
refuse('kit_not_empty',lambda:build.build(B/'inputs/config.json',B/'inputs',kit),'ROOT_NOT_EMPTY')
(O/'RESULT.json').write_text(json.dumps(dict(cases=records,scope='Native input refusal functions. The only internal fault injection creates a file after native fresh_tmp returns, reproducing a race before frame_host checks its root; this is separate from the end-to-end producer proof.'),indent=2))
monitor.save(O);print('Native fault checks passed.')
