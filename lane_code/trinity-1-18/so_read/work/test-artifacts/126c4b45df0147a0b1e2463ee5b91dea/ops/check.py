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
print(json.dumps(dict(passed=True,pool_bytes=total)))
