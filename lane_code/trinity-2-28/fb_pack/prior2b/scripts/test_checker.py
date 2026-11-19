"""Fail-closed CLI checks; every modified receipt is explicitly a synthetic fixture."""
import json,hashlib,subprocess,sys,copy
from pathlib import Path
W=Path(__file__).resolve().parents[1];root=W/'work/checker_negative';root.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def load(p):return json.loads(Path(p).read_text())
base=load(W/'work/mix_fixture/FIXTURE.json');inputs=[pin(__file__),pin(W/'out/prove_on_prepared.py'),pin(W/'work/mix_fixture/FIXTURE.json')]
def put(path,v):
 v=dict(v,inputs=inputs);path.write_text(json.dumps(v,sort_keys=True)+'\n');return pin(path)
def rebind(name,modify):
 d=root/name;d.mkdir(exist_ok=True);f=copy.deepcopy(base);cfg=load(f['native_config']['path']);receipt=load(f['prepared_receipt']['path'])
 modify(d,f,cfg,receipt)
 f['prepared_receipt']=put(d/'receipt.json',receipt);cfg['preparation']=f['prepared_receipt'];f['native_config']=put(d/'config.json',cfg)
 put(d/'FIXTURE.json',f);return d

def duplicate(d,f,cfg,r):
 old=f['offset_tables']['pointing'];table=load(old['path']);table[1]=table[0];p=d/'duplicate_indices.json';p.write_text(json.dumps(table)+'\n');q=pin(p)
 f['offset_tables']['pointing']=q;r['streams']['pointing']['indices']=q

def missing(d,f,cfg,r):f['offset_tables']['routing']['path']=str(d/'MISSING_routing_indices.json')

def bad_hash(d,f,cfg,r):
 p=d/'changed_indices.json';p.write_bytes(Path(f['offset_tables']['pointing']['path']).read_bytes()+b' ');f['offset_tables']['pointing']['path']=str(p)

def incomplete(d,f,cfg,r):
 pop=load(cfg['r2_sampling']['population']['path']);pop['complete']=False;new=put(d/'incomplete_population.json',pop)
 cfg['r2_sampling']['population']=new;r['r2_sampling']=copy.deepcopy(cfg['r2_sampling'])
 # Bind the fixture's config consistently, so only the population completeness gate rejects it.
 digest=hashlib.sha256(json.dumps(cfg['r2_sampling'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 cfg['r1_training']['row_plan_sha256']=digest;r['r1_training']=copy.deepcopy(cfg['r1_training'])

records=[]
for name,fn,reason in [('duplicate',duplicate,'DUPLICATE_SOURCE_OFFSET'),('missing',missing,'MISSING_routing_indices.json'),('hash',bad_hash,'HASH_MISMATCH'),('incomplete',incomplete,'R1_COMPLETE_FILTERED_POPULATION_REQUIRED')]:
 d=rebind(name,fn)
 cmd=[sys.executable,str(W/'out/prove_on_prepared.py'),'--base-tree',str(W/'work/sealed_base'),'--patched-tree',str(W/'work/sealed_new'),'--weights',str(W/'out/TOWARD_HARD_WEIGHTS.json'),'--fixture',str(d/'FIXTURE.json'),'--output-dir',str(d/'result')]
 r=subprocess.run(cmd,text=True,capture_output=True);(d/'stdout.log').write_text(r.stdout+r.stderr)
 result=load(d/'result/RESULT.json') if (d/'result/RESULT.json').is_file() else {}
 record=dict(name=name,status='PASS' if r.returncode==1 and reason in result.get('error','') else 'FAIL',expected_error=reason,actual_error=result.get('error'),returncode=r.returncode,command=cmd,result=pin(d/'result/RESULT.json') if result else 'MISSING')
 records.append(record);print(record,flush=True)
# A labeled fixture cannot claim a real prepared PASS.
f=base;cfg=load(f['native_config']['path']);cmd=[sys.executable,str(W/'out/prove_on_prepared.py'),'--base-tree',str(W/'work/sealed_base'),'--patched-tree',str(W/'work/sealed_new'),'--weights',str(W/'out/TOWARD_HARD_WEIGHTS.json'),'--config',f['native_config']['path'],'--prepared-receipt',f['prepared_receipt']['path'],'--output-dir',str(root/'fixture_as_real')]
r=subprocess.run(cmd,text=True,capture_output=True);result=load(root/'fixture_as_real/RESULT.json')
records.append(dict(name='fixture_as_real',status='PASS' if r.returncode==1 and 'FIXTURE_CANNOT_BE_USED_AS_REAL' in result.get('error','') else 'FAIL',actual_error=result.get('error'),returncode=r.returncode,command=cmd,result=pin(root/'fixture_as_real/RESULT.json')))
put(W/'out/CHECKER_NEGATIVE_TESTS.json',dict(status='PASS' if all(v['status']=='PASS' for v in records) else 'FAIL',records=records))
