from pathlib import Path
import sys,os,subprocess,json,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build20';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations'
O.mkdir(parents=True,exist_ok=True)
shutil.copytree(T,M,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.git','artifacts'))
cases=[
 ('pose_schema','r1_handover.py',"if receipt.get('schema') == 'c1-pose-mix-v1':","if False:",'test_real_pose_target'),
 ('pose_pin','r1_handover.py',"or not re.fullmatch('[0-9a-f]{64}', str(pin['sha256']))","or False",'test_real_pose_target'),
 ('pose_stream','r1_handover.py',"if name != 'pose' or set(receipt)","if False or set(receipt)",'test_real_pose_target'),
 ('mix_source','r1_handover.py',"if any(part.get(k) != source[k] for k in keys):","if False:",'test_prepared_mix'),
 ('mix_database','r1_handover.py',"if child.get('database') != part.get('database'):","if False:",'test_prepared_mix'),
 ('mix_order','r1_handover.py',"not 0 <= v[1] < limits[v[0]]","False",'test_prepared_mix'),
 ('mix_subset','r1_handover.py',"or not {tuple(v) for v in selected} <= {tuple(v) for v in order}","or False",'test_prepared_mix'),
 ('identity','r2_contract.py',"if identity['artifact_sha256'] != value['artifact'].get('sha256'):","if False:",'test_selection_binds_returned_identity'),
 ('slots','r1_components.py',"if set(status) != set((*LINEAGE, *EXTERNAL, *NEW)):","if False:",'test_guard_status_tampering'),
 ('records','r1_components.py',"if any(v.get('status') != 'VERIFIED' or not v.get('record') for v in status.values()):","if False:",'test_guard_status_tampering'),
 ('guard','r1_components.py',"if set(banks) & set(SCOPE):","if False:",'test_guard_status_tampering'),
 ('preparation_hash','r1_components.py',"or artifact.get('component_evidence_sha256') != digest(recorded)","or False",'test_guard_preparation_and_records'),
 ('preparation_map','r1_components.py',"or recorded != status","or False",'test_guard_preparation_and_records'),
 ('binding','r1_components.py',"if not pin or normalize(load(pinned(pin)).get('component_evidence', {})) != status:","if False:",'test_export_binding'),
]
results=[]
for name,module,before,after,test in cases:
    clean=(T/'student_pilot'/module).read_text();assert before in clean,(name,before)
    selected='tests.test_r1_build20.Review20.'+test
    entry=dict(name=name,module=module,test=selected)
    for mode in ('control','mutant'):
        (M/'student_pilot'/module).write_text(clean if mode=='control' else clean.replace(before,after,1))
        with (O/(name+'_'+mode+'.log')).open('w') as f:
            r=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test20.py'),selected],env={**os.environ,'R2_TREE':str(M),'B20_PROOF':'mutations/run'},stdout=f,stderr=subprocess.STDOUT)
        entry[mode]=r.returncode
    (M/'student_pilot'/module).write_text(clean)
    entry['caught']=entry['control']==0 and entry['mutant']!=0;results.append(entry)
    (O/'RESULT.json').write_text(json.dumps(results,indent=2));print(name,entry['caught'],flush=True)
