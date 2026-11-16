import copy,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parents[1];D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0');sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
out=H/'evidence/derivation';out.mkdir(exist_ok=False)
results={}
# Missing payloads must not be silently waived in a complete derivation.
try:dk.derive(D/'kitfull',out/'empty_full',{})
except ValueError as e:assert 'source kit files absent' in str(e);results['empty_complete_blocker']=str(e)
r=dk.derive(D/'kitfull',out/'empty',{'fixture':True})
changed=[]
for line in (D/'kitfull/SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ')
 if (D/'kitfull'/n).exists() and dk.sha(out/'empty'/n)!=h:changed.append(n)
assert changed==['k/launch.json'],changed
actual=json.loads((out/'empty/k/launch.json').read_text());want=json.loads((D/'kitfull/k/launch.json').read_text())
assert actual==dict(want,status='FIXTURE',production_authorized=False)
results['empty_fixture']={'changed':changed,'only_fixture_safety_fields':True,'missing':r['absent_source_files']}
o=json.loads((D/'a2/v5b/over_fx.json').read_text().replace('/scratch/jjyeung/orch_n30/cont_ops/work/d0',str(D)))
for k,p in o['content'].items():
 if not Path(p).is_absolute():o['content'][k]=str(D/'a2'/p)
r=dk.derive(D/'kitfull',out/'d0',o)
sys.path.insert(0,str(out/'d0/b'));from d import contract
la=json.loads((out/'d0/k/launch.json').read_text());cfg=json.loads((out/'d0'/la['config']['file']).read_text())
assert r['config_identity']=='80f4af947f0ca9edfac04041cf65e079edb92752618b2de6dc4078491a88f1ba'
assert dk.digest(contract(la,cfg))=='aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19'
results['d0']={'identity':r['config_identity'],'contract':dk.digest(contract(la,cfg))}
new=json.loads((H/'build/fx/k/launch.json').read_text());newcfg=json.loads((H/'build/fx'/new['config']['file']).read_text())
expected=copy.deepcopy(cfg);tok=json.loads((H/'TOKENS_H1.json').read_text())
for n in ['output','preparation_output']:expected[n]=expected[n].rsplit('/',1)[0]+'/'+tok['run']
expected.update(h1=dk.H1,milestones=[100,200],code=newcfg['code'],admission=newcfg['admission'])
expected['recipe']['milestones']=[100,200];expected['recipe']['scheduled_sampling'].update(dk.SAMPLING);expected['scheduled_sampling'].update(dk.SAMPLING)
assert newcfg==expected, sorted(k for k in newcfg if newcfg[k]!=expected.get(k))
results['h1_exact_fields']=True
base=json.loads((H/'build/over_fx.json').read_text())
negative=[{'unknown':1},{'config':{'optimizer':{}}},{'config':{'recipe':{'steps':2}}},{'deployment':{'trainer':{}}},{'add_k':{'i.py':{}}}]
for sub in [dict(h1={**dk.H1,'stop_after_step':201}),dict(scheduled_sampling={'seed':4}),dict(recipe={'wall_seconds':5})]:
 v=copy.deepcopy(base);v['config'].update(sub);negative.append(v)
v=copy.deepcopy(base);v['code_tree']['runtime_patch']={};negative.append(v)
for i,v in enumerate(negative):
 try:dk.derive(D/'kitfull',out/f'refused_{i}',v)
 except (ValueError,KeyError) as e:results[f'refused_{i}']=str(e)
 else:raise AssertionError('unknown or forbidden override admitted')
# Validate the new archive's files using the unchanged native runtime inventory checker.
from v import tree
pin={'path':str(H/'build/fx/k/s1_record.json'),'sha256':dk.sha(H/'build/fx/k/s1_record.json')}
assert tree(pin,H/'build/tree',new['source_revision'])
results['native_tree_check']='PASS'
dk.write(H/'evidence/derivation.json',results)
print(json.dumps(results,indent=1))
