from pathlib import Path
import json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build20';O=B/'proofs/job_mutations';O.mkdir(parents=True,exist_ok=True)
p=B/'mutant/joblib.py';clean=(B/'joblib.py').read_text()
cases=[
 ('kit_seal',"if actual!=expected:raise ValueError('E13')","if False:raise ValueError('E13')"),
 ('done',"if done.get('step')!=400 or done.get('ok')!=1 or done.get('checkpoint_overlap')!='no':","if False:"),
 ('receipt_schema',"receipt.get('schema')!='p-export-only-v1'","False"),
 ('part_size',"if n!=entry['bytes'] or entry.get('sha256',h.hexdigest())!=h.hexdigest():","if entry.get('sha256',h.hexdigest())!=h.hexdigest():"),
 ('part_hash',"if n!=entry['bytes'] or entry.get('sha256',h.hexdigest())!=h.hexdigest():","if n!=entry['bytes']:"),
 ('artifact_identity',"artifact.get('config_sha256')!=spec['p_identity']","False"),
 ('resolved_seal',"if resolved['kit_sha256']!=seal(kit):raise ValueError('E32')","if False:raise ValueError('E32')"),
]
rows=[]
for name,a,b in cases:
    assert a in clean
    row=dict(name=name)
    for mode in ('control','mutant'):
        p.write_text(clean if mode=='control' else clean.replace(a,b,1))
        with (O/(name+'_'+mode+'.log')).open('w') as f:
            result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test20.py'),'jobtest.Job20.test_resolver_and_payload'],
                env={**os.environ,'B20_JOB_MODULE':str(p),'B20_PROOF':'job_mutations/run'},stdout=f,stderr=subprocess.STDOUT)
        row[mode]=result.returncode
    row['caught']=row['control']==0 and row['mutant']!=0;rows.append(row)
    (O/'RESULT.json').write_text(json.dumps(rows,indent=2));print(name,row['caught'],flush=True)
p.write_text(clean)
