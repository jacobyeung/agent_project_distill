from pathlib import Path
import json,os,sys,subprocess,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations';O.mkdir(parents=True,exist_ok=True)
base=B/'base'
if not base.exists():base.symlink_to(L/'work/base',target_is_directory=True)
cases=[
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
for name,source,before,after,test in cases:
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
