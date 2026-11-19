from pathlib import Path
import collections,hashlib,json,re
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):return json.loads((O/n).read_text())
base,new=read('SUITE_BASE_FINAL.json'),read('SUITE_NEW_FINAL.json')
def canonical(text):
 text=re.sub(re.escape(str(W))+r'/work/(?:base|new)/', '<tree>/', text)
 return re.sub(re.escape(str(W))+r'/work/suite_final_(?:base|new)/[^/\s\"\']+/', '<suite_fixture>/', text)
def events(report):
 out=[]
 for kind in ('errors','failures'):
  for name,trace in report[kind]:
   if name=='failed' or 'raise RuntimeError(message)' in trace:
    paths=re.findall(r'/work/(?:base|new)/(tests/[^"\n]+\.py)',trace)
    name='collection:'+paths[0].replace('/','.') if paths else 'collection:'+trace.splitlines()[-1]
   lines=trace.strip().splitlines()
   markers=[i for i,line in enumerate(lines) if re.match(r'^(?:[\w.]+(?:Error|Exception)|SystemExit):',line)]
   cause=' '.join(lines[markers[-1]:]) if markers else lines[-1]
   out.append(dict(test=canonical(name),raw_test=name,kind=kind[:-1],cause=cause,traceback=trace))
 return out
b,n=events(base),events(new);bids={x['test'] for x in b};nids={x['test'] for x in n}
added=[x for x in n if x['test'] not in bids]
changed=[]
for x in n:
 causes=[v['cause'] for v in b if v['test']==x['test']]
 if causes and canonical(x['cause']) not in [canonical(c) for c in causes]:changed.append(x)
signatures=lambda rows:collections.Counter((x['test'],x['kind'],canonical(x['cause'])) for x in rows)
new_signatures=signatures(n)-signatures(b)
inputs={str(O/p):sha(O/p) for p in ('SUITE_BASE_FINAL.json','SUITE_NEW_FINAL.json','K1_INVARIANCE.json','ABSENT_BASE.json','ABSENT_NEW.json','ADVERSARIAL.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','ENVIRONMENT.json','BASE_NEGATIVE.json','FILES_TOUCHED.json','INPUTS.json')}
inputs[str(Path(__file__).resolve())]=sha(__file__)
source_checks={}
for label, report in [('base',base),('new',new)]:
 prefix=str(W/'work'/label)+'/'
 expected={p:h for p,h in report.get('input_sha256',report.get('inputs_sha256',{})).items() if p.startswith(prefix)}
 mismatches=[p for p,h in expected.items() if sha(p)!=h]
 assert len(expected)==(939 if label=='base' else 942), len(expected)
 assert not mismatches, mismatches
 source_checks[label]=dict(files=len(expected),all_tree_hashes_match_before_after=True)
executed=O/'RUN_SUITE_EXECUTED.py'
inputs[str(executed)]=sha(executed)
for report in (base,new):assert report['input_sha256'][str(W/'code/run_suite_final.py')]==sha(executed)

unit=(O/'unit_final.log').read_text();unit_count=int(re.search(r'Ran (\d+) tests',unit)[1]);assert unit.strip().endswith('OK')
inputs[str(O/'unit_final.log')]=sha(O/'unit_final.log')
inputs[str(W/'code/run_unit.py')]=sha(W/'code/run_unit.py')
parity=read('ABSENT_BASE.json')['outputs']==read('ABSENT_NEW.json')['outputs'];assert parity
invariance=read('K1_INVARIANCE.json');assert invariance['status']=='PASS'
for f in ('EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','ADVERSARIAL.json'):assert read(f)['status']=='PASS'
summary=lambda r:dict(tests_run=r['tests_run'],errors=len(r['errors']),failures=len(r['failures']),skipped=len(r['skipped']),seconds=r['seconds'],command=r['command'])
result=dict(input_sha256=inputs,source_verification=source_checks,execution_runner_replica={sha(executed):str(executed)},source_verification_method='Rehash each recorded tree input after testing; compare tree inputs only, excluding the runner pin included by the raw auxiliary flag.',status='PASS' if not new_signatures else 'FAIL',comparison_normalization='Only base/new tree roots and the first disposable directory under suite_final_base/new are normalized; subtest arguments, exception types and causes remain compared as a multiset.',new_failure_signatures=[dict(test=k[0],kind=k[1],cause=k[2],count=v) for k,v in new_signatures.items()],base=summary(base),new=summary(new),new_failures=added,preexisting_failure_count=len(b),preexisting_failures=b,changed_existing_failure_messages=changed,resolved_test_ids=sorted(bids-nids),donor_unit_tests=dict(count=unit_count,status='PASS',command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/run_unit.py'),K1=dict(status='PASS',variants=['V1','V2'],captures=[c['canonical'] for c in read('K1_SELECTION.json')['captures']],steps_per_variant=2,weights=invariance['weights']),absent_field=dict(status='PASS',state_tensors=len(read('ABSENT_BASE.json')['outputs']['state']),byte_identical_outputs=True),export_tampering=dict(status='PASS',cases=len(read('ADVERSARIAL.json')['checks'])),real_weight_check=dict(status='MISSING',command='bash out/REAL_WEIGHT_COMMAND.sh',requirements=read('INPUTS.json')['missing']),transport='No Gloo/loopback execution: inherited GO result reports zero steps. Native optimize_step runs locally in the donor fixture; export transport alone is mocked.',suite_guard=base['guard'])
(O/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# Base CPU failures and causes','',f"The guarded full CPU run observed {len(b)} errors/failures on base. Each entry below is retained in TESTS.json with its traceback.",'']
for e in b:
 lines.extend([f"- `{e['test']}` ({e['kind']}): {e['cause'].replace(chr(10),' ')[:800]}"])
(O/'PREEXISTING_FAILURES.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:result[k] for k in ('status','base','new','new_failures')},indent=2))
