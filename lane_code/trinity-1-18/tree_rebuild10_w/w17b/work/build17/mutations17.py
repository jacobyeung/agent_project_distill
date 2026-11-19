from pathlib import Path
import json,os,sys,subprocess,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations';O.mkdir(parents=True,exist_ok=True)
base=B/'base'
if not base.exists():base.symlink_to(L/'work/base',target_is_directory=True)
cases=[
 ('export_q','student_pilot/r1_persisted.py',"if mode != 'q' or not _proof.get():",'if False:','tests.test_r1_export17.Export17.test_training_config_refuses'),
 ('export_scope','student_pilot/r1_persisted.py',"if mode != 'q' or not _proof.get():","if mode != 'q':",'tests.test_r1_export17.Export17.test_export_only_admits_only_in_proof_scope'),
 ('export_stop_producer','launch_r1/p_export_receipt.py',"if step >= stop_step(cfg):",'if False:','tests.test_r1_export17.Export17.test_stop_producer_and_reader_refuse'),
 ('export_stop_reader','student_pilot/r1_persisted.py',"if receipt['step'] >= stop_step(cfg):",'if False:','tests.test_r1_export17.Export17.test_stop_producer_and_reader_refuse'),
 ('export_training','launch_r1/entry.py',"if receipt.get('schema') == 'p-export-only-v1':",'if False:','tests.test_r1_export17.Export17.test_export_only_admits_only_in_proof_scope'),
 ('export_shard','student_pilot/r1_persisted.py',"if sha256(path) != pin['sha256']:",'if False:','export_mutation17.HashTwin.test_same_size_shard_refuses'),
 ('export_status','student_pilot/r1_persisted.py',"if receipt.get('checkpoint_status') != NO_CHECKPOINT or receipt.get('stop_step') != stop_step(cfg):",'if False:','tests.test_r1_export17.Export17.test_reader_status_and_closure_refuse'),
 ('export_milestone','launch_r1/p_export_receipt.py',"if type(step) is not int or step not in recipe_for(cfg)['milestones']:",'if False:','export_edges17.ProducerEdges.test_step_and_stop_refusals'),
 ('export_invalid_stop','launch_r1/p_export_receipt.py',"if type(limit) is not int or limit <= 0:",'if False:','export_edges17.ProducerEdges.test_step_and_stop_refusals'),
 ('export_escape','launch_r1/p_export_receipt.py',"if Path(name).is_absolute() or '..' in Path(name).parts or not path.is_relative_to(directory.resolve()):",'if False:','export_edges17.ProducerEdges.test_manifest_refusals'),
 ('export_file_hash','launch_r1/p_export_receipt.py',"if pin['sha256'] != item['sha256'] or ('bytes' in item and path.stat().st_size != item['bytes']):",'if False:','export_edges17.ProducerEdges.test_manifest_refusals'),
 ('export_duplicate','launch_r1/p_export_receipt.py',"if 'export/'+name in closure:",'if False:','export_edges17.ProducerEdges.test_manifest_refusals'),
 ('export_missing_weights','launch_r1/p_export_receipt.py',"if not weights['files'] or set(prep['streams']) != set(cfg['streams']):",'if False:','export_edges17.ProducerEdges.test_manifest_refusals'),
 ('export_stream','launch_r1/p_export_receipt.py',"if stream['receipt'] != pin:",'if False:','export_edges17.ProducerEdges.test_stream_refusal_and_index_closure'),
 ('export_binding','launch_r1/p_export_receipt.py',"bound.get('config_sha256') != identity",'False','tests.test_r1_export17.Export17.test_producer_binding_and_job_refuse'),
 ('export_trainer','launch_r1/p_export_receipt.py',"if commit != trainer_commit:",'if False:','tests.test_r1_export17.Export17.test_producer_binding_and_job_refuse'),
 ('export_job','launch_r1/p_export_receipt.py',"if not job_id or not trainer_commit:",'if False:','tests.test_r1_export17.Export17.test_producer_binding_and_job_refuse'),
 ('authority','student_pilot/r1_rooms.py',"if set(pins) != set(AUTHORITY) or any(pins[k]['sha256'] != v for k,v in AUTHORITY.items()):","if False:",'tests.test_r1_build17.Rooms.test_pinned_rule_and_alias_precedence'),
 ('slice_room','student_pilot/r1_routing.py','rooms.admit(row)','pass','tests.test_r1_build17.Composition.test_new_heldout_row_refuses'),
 ('audit_slice','student_pilot/r1_rooms.py',"or report['unremoved_hits']!=0",'or False','tests.test_r1_build17.Rooms.test_complete_audit_and_new_slice_pin'),
 ('milestone','launch_r1/production_proof.py',"request.get('milestone',step)!=step",'False','tests.test_r1_build17.Boundary.test_proof_wrong_receipt_and_milestone'),
 ('metadata_scope','student_pilot/r1_persisted.py','{**_paths.get(), **paths}','paths','tests.test_r1_build17.Boundary.test_nested_metadata_scope'),
 ('metadata_required','student_pilot/r1_handover.py',"raise ValueError('P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED') from error","return {}",'tests.test_r1_build17.Boundary.test_missing_manifest'),
 ('persisted_receipt','student_pilot/r1_persisted.py',"if sha256(path) != pin['sha256']:",'if False:','tests.test_r1_build16.Build16.test_persisted_forgery_and_mismatch'),
 ('counting_list','student_pilot/r1_population.py',"if card.get('counting_admission') == 'procedure_only_v1':",'if False:','tests.test_r1_build16.Build16.test_producer_refuses_without_z'),
]
for p in T.rglob('*'):
    if p.is_file() and not set(p.relative_to(T).parts)&{'.git','__pycache__','artifacts'}:
        q=M/p.relative_to(T);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
results=[]
prior_result=O/'RESULT.json'
if prior_result.exists():
    results=json.loads(prior_result.read_text())['results']
    results=[r for r in results if r['source_sha256']==hashlib.sha256((T/r['source']).read_bytes()).hexdigest()]
for name,source,before,after,test in cases:
    if any(r['name']==name and r['source_sha256']==hashlib.sha256((T/source).read_bytes()).hexdigest() and r['test']==test for r in results):
        continue
    env={**os.environ,'R2_TREE':str(M),'B17_PROOF':'mutations/run'}
    cmd=[sys.executable,'-I','-s','-B',str(B/'test17.py'),test]
    p=M/source;raw=(T/source).read_text();assert raw.count(before)==1,(name,before)
    phases={}
    for phase in ('clean','mutant'):
        p.write_text(raw if phase=='clean' else raw.replace(before,after))
        with (O/(name+'_'+phase+'.log')).open('w') as log:
            result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode<0:raise SystemExit('Process killed; stop without rerun')
        phases[phase]=result.returncode
        if phase=='clean':assert result.returncode==0,(name,'clean failed')
        else:assert result.returncode!=0,(name,'mutation escaped')
    p.write_text(raw)
    results.append(dict(name=name,source=source,test=test,status='CAUGHT',returncodes=phases,source_sha256=hashlib.sha256(raw.encode()).hexdigest()))
    (O/'RESULT.json').write_text(json.dumps(dict(results=results),indent=2))
    print(name,'CAUGHT',flush=True)
