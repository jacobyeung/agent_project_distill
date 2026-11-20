from common import *
import ast,subprocess,shutil
F=D/'hidden';pins={v['sha256']:v for v in J.load(D/'PINS.json')['pins']};sh=J.sha(F/'selection.json')
cat=next(iter(pins));mounts=[]
for v in J.load(D/'EXTERNAL_LINKS.json'):mounts+=['--ro-bind',v['path'],'/tmp/f/'+str((L/v['target']).relative_to(F))]
for part in ('inputs','payload'):mounts+=['--ro-bind',str(L.parent/'w24/work/build24m3/hidden'/part),'/tmp/f/'+part]
source=ast.parse((D/'closure.py').read_text())
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(D/'closure.py'),'exec'))
sys.path.insert(0,str(kit('q')/'b'));from px import inventory
from z import selected400
spec=J.load(kit('q')/'k/p.json');authority=set(inventory(kit('q')))|{v['sha256'] for v in spec['uploads']}
for row in J.load(L.parent/'ext/m400real/MANIFEST.json')['files']:
 try:selected400(row['path'])
 except ValueError:continue
 authority.add(row['sha256'])
resolved=J.load(F/'resolved.json');extra=set(resolved['small_files'])-authority
resolved['small_files']={h:v for h,v in resolved['small_files'].items() if h in authority}
assert all(v['sha256'] in authority for v in resolved['external_metadata'])
replace(F/'resolved.json',json.dumps(resolved,sort_keys=True,indent=2)+'\n')
records=[]
expected='Missing or changed pinned input: /tmp/f/payload/a67a3f6f489031d4163b75dbae45d665a05fecf4dcbe6f2f33b0dee6567de7b5'
for ix,name in enumerate(('q','n','n_go','qd')):
 for j,mode in enumerate(('r','q')):
  number=500+ix*2+j;rp=F/(name+'_'+mode+'_'+str(number))/'result.json'
  r=J.load(rp) if rp.is_file() else run(name,mode,number)
  r.update(kit=name,round=number);assert r['refusal']==expected,r['refusal']
  assert 'refreshed=refresh(refresh_request' in r['traceback']
  assert any(c['sha256']==cat and c['size']==74599 and not c['boundary'] for c in r['calls'])
  r['final_kit_seal']=J.seal(kit(name));records.append(r)
# Catalog and both catalog maps contain only inventory-authenticated pins.
nested=[]
def walk(v,field):
 if isinstance(v,dict):
  if set(v)=={'path','sha256'}:nested.append(dict(field=field,sha256=v['sha256']));assert v['sha256'] in authority
  for key,w in v.items():walk(w,field+'.'+key)
 elif isinstance(v,list):
  for i,w in enumerate(v):walk(w,field+'.'+str(i))
walk(J.load(D/'inputs/pool_selection_eac5f9f0.json'),'catalog')
old=J.load(D/'HIDDEN_PATH_TESTS.json');old.update(records=records,strict_inventory_only=True,fixture_extra_metadata_excluded=sorted(extra),catalog_nested_pins=nested,next_boundary=dict(sha256=expected.rsplit('/',1)[1],inventory=inventory(kit('q'))[expected.rsplit('/',1)[1]],stage='pl.plan_payload -> i.refresh -> s1_pool_relocate.relocate -> p3_provenance.pinned',production_refusal_predicted=False))
replace(D/'HIDDEN_PATH_TESTS.json',json.dumps(old,sort_keys=True,indent=2)+'\n')
# Native missing-inventory, bad-size, and bad-hash checks. Mutations stay local.
negative=[]
for ix,case in enumerate(('missing_r','missing_q','size','hash')):
 k=fixture('q',600+ix);p=J.load(k/'k/p.json')
 if case.startswith('missing'):
  p['uploads']=[r for r in p['uploads'] if r['sha256']!=cat];p['pin_paths'].pop(cat)
 elif case=='size':
  next(r for r in p['uploads'] if r['sha256']==cat)['bytes']+=1
 cap(k,'k/p.json',p);reseal(k)
 node=F/('negative_'+case);(node/'p').mkdir(parents=True);extra_mounts=[]
 if case=='hash':
  bad=F/'bad_catalog';raw=(D/'inputs/pool_selection_eac5f9f0.json').read_bytes();bad.write_bytes(b'!'+raw[1:]);extra_mounts=['--ro-bind',str(bad),'/tmp/f/target/u/'+cat]
 args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--dev','/dev','--proc','/proc','--tmpfs','/tmp','--ro-bind','/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu','/opt/py','--ro-bind',str(T),'/tmp/t','--ro-bind',str(k),'/tmp/k','--ro-bind',str(F),'/tmp/f',*mounts,*extra_mounts,'--bind',str(node),'/tmp/node','--setenv','Q_ROOT','/tmp/node','/opt/py/bin/python3','-B','-s','/tmp/f/run.py','q' if case=='missing_q' else 'r']
 subprocess.run(args,check=True);v=J.load(node/'result.json');refusal=v['refusal']
 if case.startswith('missing'):
  field='P.materialization.inputs.catalog.' if case=='missing_r' else 'config.s1_routing.catalog.'
  assert refusal=='R1_STAGED_PIN_MISSING:'+cat+':'+field+cat,refusal
 else:assert refusal=='E10:/tmp/f/target/u/'+cat,refusal
 negative.append(dict(case=case,refusal=refusal));print(case,refusal,flush=True)
J.write(D/'CATALOG_AUTH_TESTS.json',dict(status='PASS',records=negative,real_catalog_sha256=cat,bytes=74599,inventory_sha256=J.sha(D/'inputs/P_SHA256SUMS.txt')))
