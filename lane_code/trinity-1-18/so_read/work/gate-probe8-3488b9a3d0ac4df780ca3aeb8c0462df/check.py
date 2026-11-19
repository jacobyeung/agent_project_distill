import hashlib,json,os,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);pool=Path(sys.argv[2]);h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pub=json.loads((p/'0.json').read_text());proof=json.loads((p/'a/c/CPU.json').read_text())
with tarfile.open(p/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
if h(p/'0.tgz')!=pub['payload_sha256']:raise ValueError('Payload differs')
for key in ('passed','entry_sequence_passed','bundle_guard_passed'):
 if proof.get(key) is not True:raise ValueError('CPU receipt failed: '+key)
if (proof['plan']!=pub['plan_sha256'] or proof['payload']!=pub['payload_sha256'] or proof['inputs']!=h(p/'a/1.json') or proof['operator_sha256']!=h(p/'a/6.py')):raise ValueError('CPU receipt binding differs')
memory=proof['memory']
if memory.get('fits') is not True or memory.get('basis')!='fixed_g3t_shapes' or memory.get('read_cache_bytes')!=cfg['read_cache_bytes']:raise ValueError('CPU memory proof differs')
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
assert type(w['bytes']) is int and w['bytes']==4*1024**2
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
print('All CPU receipt checks passed')
for name in ('dry.json','dry2.json'):
 if json.loads((p/'a'/name).read_text()).get('passed') is not True:raise ValueError('Dry check failed')
if not pool.is_dir() or pool.is_symlink():raise ValueError('Return pool missing or linked')
total=0
def fail(error):raise error
for base,dirs,files in os.walk(str(pool),followlinks=False,onerror=fail):
 for name in dirs+files:
  f=Path(base)/name
  if f.is_symlink():raise ValueError('Unexpected pool symlink')
 for name in files:
  total+=(Path(base)/name).stat().st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
def decode(v):
 if isinstance(v,str):return bytes.fromhex(v[1:]).decode() if v.startswith('u') else (_ for _ in ()).throw(ValueError('Invalid gate token'))
 if isinstance(v,dict):return {decode(k):decode(x) for k,x in v.items()}
 if isinstance(v,list):return [decode(x) for x in v]
 return v
gate=decode(json.loads((p/'a/g.json').read_text())['u0'])
keys=('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth','read_processor_only','read_processor_cache','read_vision_cache','read_sam_cache','read_cache_bytes')
expected={k:cfg[k] for k in keys}
if (gate.get('passed') is not True or gate.get('adoption_plan_sha256')!=pub['plan_sha256'] or gate.get('required_device_type')!='H100_80GB' or json.dumps(gate.get('adoption_profile'),sort_keys=True)!=json.dumps(expected,sort_keys=True)):raise ValueError('GPU gate differs from adopted plan/profile/device')
assets=dict(restore=proof['ready']['restore'],binding=proof['ready']['binding'],export_pin=h(p/'a/export.json'))
if gate.get('adoption_assets')!=assets:raise ValueError('GPU gate assets differ from CPU proof')
if gate.get('adoption_kit')!=cfg['gate_kit_sha256']:raise ValueError('GPU gate kit/comparator/sample differ from MANIFEST pins')
environment=json.loads((p/'a/c/ENVIRONMENT.json').read_text())
environment_sha=h(p/'a/c/ENVIRONMENT.json')
if environment_sha!=proof['ready']['environment']:raise ValueError('CPU environment receipt differs')
expected_environment=dict(sha256=environment_sha,torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])
if gate.get('adoption_environment')!=expected_environment:raise ValueError('GPU gate environment versions/hash differ')
print(json.dumps(dict(passed=True,pool_bytes=total)))
