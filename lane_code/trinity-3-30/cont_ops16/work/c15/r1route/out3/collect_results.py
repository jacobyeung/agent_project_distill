from pathlib import Path
import ast,collections,hashlib,json,os
R=Path(__file__).resolve().parent;W=R.parent;G=R/'gates'
# A class-wide missing fixture blocks every case declared in that class.
p=G/'results/base_b1_constraints.json';v=json.loads(p.read_text());holder=v['records'][0]
if holder['test'].startswith('setUpClass'):
 tree=ast.parse((G/'base/b1/tests/test_constraints.py').read_text());names=[n.name for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
 v['class_setup_failure']=holder;v['records']=[dict(test='suite.ProductionConstraints.'+n,status='blocked',detail=holder['detail'],executed=False) for n in names];v['counts']['blocked']=len(names);p.write_text(json.dumps(v,indent=2)+'\n')
summary={'suites':{},'totals':{},'supplementary':{},'blocked':[]}
for mode in ('base','release'):
 for k,label in [('b1','A'),('b2','B')]:
  totals=collections.Counter()
  for p in sorted((G/'results').glob(mode+'_'+k+'_*.json')):
   v=json.loads(p.read_text());summary['suites'][p.stem]=v['counts'];totals.update(v['counts'])
   for item in v['records']:
    if item['status']!='passed':summary['blocked'].append(dict(suite=p.stem,**item))
  summary['totals'][mode+'_'+label]=dict(totals)
v=json.loads((G/'results/scoring_recovered.json').read_text());summary['supplementary']['scoring']=v['counts'];summary['blocked'] += [dict(suite='scoring',**x) for x in v['records'] if x['status']!='passed']
summary['supplementary']['fill_fixture_cases']=dict(passed=sum(x['passed'] for x in json.loads((R/'FILL_TESTS.json').read_text())),scope='Synthetic artifact and data receipt; test-copy helpers pin the small archive. Includes 2 production-preparation-pin rejection cases.')
summary['supplementary']['integrated_fill_metadata_fixture_cases']=dict(passed=len(json.loads((R/'INTEGRATED_FILL.json').read_text())),scope='Disposable helper pins a small archive; disposable payload pins synthetic data receipt. Production payloads untouched.')
summary['supplementary']['return_cli_cases']=dict(passed=sum(json.loads((R/k/'RETURN_CLI.json').read_text())['tests'] for k in ('A','B')))
summary['supplementary']['python36_guard_dispatch']=dict(passed=sum(json.loads((R/k/'PY36_GUARD.json').read_text())['entry_sequence_passed'] for k in ('A','B')))
final=json.loads((R/'FINAL_VERIFICATION.json').read_text())
for name in ('operator_syntax','python36_compile','operator_guards'):summary['supplementary'][name]=dict(passed=len(final[name]))
assert summary['totals']['release_A']['passed']==43 and summary['totals']['release_B']['passed']==49
assert summary['totals']['base_A']['passed']==47 and summary['totals']['base_A']['blocked']==10
assert summary['totals']['base_B']['passed']==53 and summary['totals']['base_B']['blocked']==1
assert all(v.get('failed',0)==0 and v.get('error',0)==0 for v in summary['suites'].values())
for name,filename in [('R3_regressions','R3_TESTS.json'),('baseline_and_independent_reference','BASELINE_TESTS.json')]:
 summary['supplementary'][name]=json.loads((R/filename).read_text())['counts']
summary['supplementary']['real_preparation_integrated']=dict(passed=len(json.loads((R/'REAL_INTEGRATED_FILL.json').read_text())),scope='All exact preparation files and unchanged production payloads; small synthetic artifact with test-only archive constant substitution.')
(R/'GATE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary['totals']));print(json.dumps(summary['supplementary']))
