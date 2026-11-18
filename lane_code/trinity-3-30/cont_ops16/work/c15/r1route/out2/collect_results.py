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
summary['supplementary']['fill_fixture_cases']=dict(passed=sum(x['passed'] for x in json.loads((R/'FILL_TESTS.json').read_text())),scope='Real config and S1 receipt; synthetic data receipt and artifact. Includes 2 unchanged-production-payload rejection cases.')
summary['supplementary']['integrated_fill_metadata_fixture_cases']=dict(passed=len(json.loads((R/'INTEGRATED_FILL.json').read_text())),scope='Disposable fixture payload resealed only for synthetic data receipt; actual fill and metadata-check helper code unchanged.')
summary['supplementary']['return_cli_cases']=dict(passed=sum(json.loads((R/k/'RETURN_CLI.json').read_text())['tests'] for k in ('A','B')))
summary['supplementary']['python36_guard_dispatch']=dict(passed=sum(json.loads((R/k/'PY36_GUARD.json').read_text())['entry_sequence_passed'] for k in ('A','B')))
final=json.loads((R/'FINAL_VERIFICATION.json').read_text())
for name in ('operator_syntax','python36_compile','operator_guards'):summary['supplementary'][name]=dict(passed=len(final[name]))
assert summary['totals']['release_A']['passed']==43 and summary['totals']['release_B']['passed']==49
assert summary['totals']['base_A']['passed']==47 and summary['totals']['base_A']['blocked']==10
assert summary['totals']['base_B']['passed']==53 and summary['totals']['base_B']['blocked']==1
assert all(v.get('failed',0)==0 and v.get('error',0)==0 for v in summary['suites'].values())
(R/'GATE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
# Hash audit of all surviving original files; no paths outside W are searched.
wanted=json.loads((R/'A/src/9.json').read_text())['export_binding']['preparation_sha256'];matches={k:[] for k in wanted}
for root,dirs,files in os.walk(W):
 dirs[:]=[d for d in dirs if d!='out2' and not (Path(root)/d).is_symlink()]
 for name in files:
  p=Path(root)/name
  if p.is_symlink() or p.stat().st_size>2000000:continue
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  for key,digest in wanted.items():
   if h==digest:matches[key].append(str(p.relative_to(W)))
(R/'INPUT_AVAILABILITY.json').write_text(json.dumps(dict(expected_sha256=wanted,matching_surviving_files=matches,search_scope='All original W files <= 2,000,000 bytes, excluding symlinks and out2; exact receipt filenames in extracted T1/T2 contain the old 469ddece preparation.',missing_done_receipt=True,full_tar_sha256_known_locally=False),indent=2)+'\n')
size=0;allocated=0;count=0
for root,dirs,files in os.walk(W):
 dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
 for name in files:
  p=Path(root)/name
  if p.is_symlink():continue
  st=p.stat();size+=st.st_size;allocated+=st.st_blocks*512;count+=1
assert size<2000000000 and allocated<2000000000
(R/'WORKSPACE_SIZE.json').write_text(json.dumps(dict(logical_bytes=size,allocated_file_bytes=allocated,regular_files=count,limit_bytes=2000000000,symlink_targets_counted_once=True),indent=2)+'\n')
print(json.dumps(summary['totals']));print('workspace',size,allocated)
