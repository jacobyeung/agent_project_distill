"""Exercise only s.sh's Python evidence gate; never execute sbatch."""
import copy, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
H=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='submit_',dir=H/'evidence/fix8_admission'))
k=out/'kit';b=out/'bundle'
for p in (k,b,k/'b',k/'k',k/'o'):p.mkdir()
(k/'b/a.py').write_text('def main(root): pass # TEST_ONLY certification stub\n')
ids=json.loads((H/'ids.json').read_text());(b/'ids.json').write_text(json.dumps(ids))
(b/'jb.sh').write_bytes((H/'payload/jb.sh').read_bytes())
(k/'SHA256SUMS.txt').write_text('TEST_ONLY manifest\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
 wrapper_sha256=sha(b/'jb.sh'),manifest_sha256=sha(k/'SHA256SUMS.txt'))
(b/'go.json').write_text(json.dumps(go))
launch=json.loads((H/'build/fx/k/launch.json').read_text())
(k/'k/launch.json').write_text(json.dumps(launch))
proof=dict(status='PASS',rc=0,job='123',config_identity=ids['identity'],contract_sha256=ids['contract'],
 config=launch['config'],manifest_sha256=go['manifest_sha256'],wrapper_sha256=go['wrapper_sha256'],
 cuda_visible_devices='',effective_config_verified=True,first_batch_executed=False,training_executed=False,
 admission_result=dict(status='PREPARED'),prepared_seals=dict(TEST_ONLY=True),real_job_reuse=False)
s=(H/'payload/s.sh').read_text();start=s.index("<<'P'\n")+len("<<'P'\n")
code=s[start:s.index('\nP\n',start)]
cases=[]
for name,field,value in [('pass',None,None),('failed','status','FAIL'),('rc','rc',1),
 ('foreign','config_identity','0'*64),('manifest','manifest_sha256','0'*64),
 ('review_pin','config',{}),('wrapper','wrapper_sha256','0'*64),('gpu','cuda_visible_devices','0'),
 ('seal','effective_config_verified',False),('not_prepared','admission_result',{}),
 ('training','training_executed',True),('reuse','real_job_reuse',True),('missing',None,None)]:
    v=copy.deepcopy(proof)
    if field:v[field]=value
    (k/'o/123.proof.json').write_text(json.dumps(v))
    env=dict(os.environ,PROOF_JOB='' if name=='missing' else '123')
    r=subprocess.run([sys.executable,'-B','-',str(k),str(b)],input=code,text=True,capture_output=True,env=env)
    (out/(name+'.log')).write_text(r.stdout+r.stderr)
    assert (r.returncode==0)==(name=='pass'),(name,r.stderr)
    cases.append(name)
(H/'evidence/fix8_admission/submit_tests.json').write_text(json.dumps(dict(status='PASS',cases=cases,path=str(out),
 scope='TEST_ONLY receipt binding cases; certification stubbed; no shell/sbatch executed'),indent=2)+'\n')
print('PASS',len(cases),'submission evidence cases')
