"""Native Rows CLI passes and end-to-end schedule tamper refusals, all NONPRODUCTION."""
import copy,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];FB=W.parent;OLD=FB/'prior2b'
ROOT=W/'work/integration_tests';ROOT.mkdir(parents=True,exist_ok=True)
inputs={}
def pin(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 v=dict(path=str(p),sha256=h.hexdigest());inputs[str(p)]=v;return v
def load(p):pin(p);return json.loads(Path(p).read_text())
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(dict(v,inputs=list(inputs.values())),sort_keys=True,indent=2)+'\n');return pin(p)
pin(__file__);checker=pin(W/'out/prove_on_prepared.py')
fixture=load(OLD/'work/mix_fixture/FIXTURE.json')
weights=pin(FB/'prior2/out/TOWARD_HARD_WEIGHTS.json')
expected=load(OLD/'work/final_gate/RESULT.json')
common=['nice','-n','10',sys.executable,checker['path'],'--base-tree',str(OLD/'work/sealed_base'),
        '--patched-tree',str(OLD/'work/sealed_new'),'--weights',weights['path']]
env=dict(os.environ,OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',PYTHONDONTWRITEBYTECODE='1',
         CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
records=[]
def run(name,f,error=None,extra_checks=None,real=False):
 d=ROOT/name;d.mkdir(exist_ok=True)
 if real:
  v=load(f);args=['--config',v['native_config']['path'],'--prepared-receipt',v['prepared_receipt']['path']]
  for flag,key in [('--receipt','stream_receipts'),('--offset-table','offset_tables')]:
   for s,p in v[key].items():args += [flag,s+'='+p['path']]
 else:args=['--fixture',str(f)]
 cmd=common+args+['--output-dir',str(d/'result')]
 with (d/'stdout.log').open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
 result=load(d/'result/RESULT.json')
 checks=dict(expected_exit=r.returncode==(1 if error else 0),no_production_pass=result['production_gate']!='PASS')
 if error:checks['named_error']=error in result.get('error','')
 else:
  checks.update(status_pass=result['status']=='PASS',scope=result['scope']=='FIXTURE_ONLY_NOT_PRODUCTION',
                plans_unchanged=result['plan_sha256']==expected['plan_sha256'],
                cells_unchanged=result['cells']==expected['cells'],audits_unchanged=result['loader_audits']==expected['loader_audits'])
 if extra_checks:checks.update(extra_checks(result))
 record=dict(name=name,status='PASS' if all(checks.values()) else 'FAIL',checks=checks,actual_error=result.get('error'),
             command=shlex.join(cmd),returncode=r.returncode,result=pin(d/'result/RESULT.json'))
 records.append(record);print(name,record['status'],result.get('error',''),checks,flush=True)
 return result

unchanged=run('labelled_fixture_unchanged',OLD/'work/mix_fixture/FIXTURE.json')
offsets=load(unchanged['recomputed_offsets']['path'])
def enabled(name,change=None,unlabel=False):
 d=ROOT/name;d.mkdir(exist_ok=True)
 f=copy.deepcopy(fixture);cfg=load(f['native_config']['path']);receipt=load(f['prepared_receipt']['path'])
 value=copy.deepcopy(offsets)
 if change:change(value,cfg)
 dp=put(d/'production_offsets.json',value)
 cfg['r1_training']['direction_prior']=weights
 cfg['r2_sampling']['direction_prior']=dp
 cfg['r1_training']['row_plan_sha256']=hashlib.sha256(json.dumps(cfg['r2_sampling'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 receipt['r2_sampling']=copy.deepcopy(cfg['r2_sampling']);receipt['r1_training']=copy.deepcopy(cfg['r1_training'])
 if unlabel:cfg.pop('scope',None);receipt.pop('scope',None)
 f['prepared_receipt']=put(d/'receipt.json',receipt);cfg['preparation']=f['prepared_receipt'];f['native_config']=put(d/'config.json',cfg)
 path=d/'FIXTURE.json';put(path,f);return path,dp

path,production_pin=enabled('enabled')
run('labelled_enabled',path,extra_checks=lambda r:dict(supplied_binding_used=r['binding']['direction_prior']==production_pin,
                                                      production_plan_source=r['enabled_plan_source']=='production_binding'))
def swap(v,cfg):
 c=v['cells']['facing_pairs'];n=len(c['back']);c.update(back=c['front'][:n],front=c['back']+c['front'][n:])
def non_target(v,cfg):
 ids=load(cfg['r2_sampling']['indices']['path'])['cells']['direction']
 targets=set(v['cells']['direction']['back']+v['cells']['direction']['front'])
 v['cells']['direction']['back'][0]=next(i for i in ids if i not in targets)
for name,fn in [('facing_sides_swapped',swap),('non_target_in_toward_hard',non_target)]:
 path,_=enabled(name,fn);run(name,path,'PRODUCTION_PRIOR_OFFSETS_MISMATCH:cells')
 # Removing scope and supplying both prior fields still cannot grant a real PASS.
 path,_=enabled(name+'_unlabelled',fn,unlabel=True)
 run(name+'_as_real',path,'REAL_LAUNCH_STORE_HASHES_MISMATCH:vqa',real=True)

put(W/'out/INTEGRATION_TESTS.json',dict(status='PASS' if all(r['status']=='PASS' for r in records) else 'FAIL',
    records=records,command=shlex.join(sys.argv),scope='FIXTURE_ONLY_NOT_PRODUCTION',production_gate='MISSING',
    plan_sha256=unchanged['plan_sha256'],cells=len(unchanged['cells']),
    draws=sum(c['draws'] for c in unchanged['cells'].values())))
(W/'STATUS.md').write_text('The checker authenticates N’s launch lineage and the production offsets. Native fixture and tamper integration results are recorded in out/INTEGRATION_TESTS.json; these synthetic fixtures cannot establish a production PASS. Final packaging and the host input inventory remain in progress.\n')
raise SystemExit(0 if all(r['status']=='PASS' for r in records) else 1)
