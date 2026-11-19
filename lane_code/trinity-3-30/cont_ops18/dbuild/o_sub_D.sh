#!/bin/bash
# Run on Orchard login after placement/fill. T must match the sealed build walltime.
set -euo pipefail
umask 077
: "${P:?Set P to /project/community/jjyeung/okh7/a15_cot_ap<token>}"
: "${T:?Set T to the package sealed walltime HH:MM:SS}"
[[ "$P" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]
[[ "$T" =~ ^[0-9]{2}:[0-5][0-9]:[0-5][0-9]$ ]]
test "$(cat "$P/a/1.txt")" = 0
cd "$P"
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
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
assert c['full_reader_passed'] is True
import runpy
runpy.run_path(str(p/'a/5.py'))['validate_full_reader']([{'full_reader':c['full_reader']}])
# a/6.py picks the first manifest item belonging to each set, in this order.
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('R0-dev-reworded','r0_0064a29747f8cc8de793_ho'),('R0-dev-twin','r0_0064a29747f8cc8de793')]
assert all(r['record']['type']=='object_abs_distance' for r in rows)
assert m==runpy.run_path(str(p/'a/6.py'))['memory_bound']()
assert c['full_reader']==json.loads((p/'a/c/FULL_READER.json').read_text())
print('All CPU receipt checks passed')
PYCODE
test ! -e "$P/a/8.txt"
squeue -u jjyeung -p general -h > "$P/a/9.txt"
test ! -s "$P/a/9.txt"
/usr/bin/python3 -I -s -B - <<'PYCODE'
import os
root='/project/community/jjyeung/okh7/ae71c903';total=0
if not os.path.isdir(root) or os.path.islink(root):raise ValueError('Return pool is absent or a symlink')
def fail(error):raise error
for base,dirs,files in os.walk(root,followlinks=False,onerror=fail):
 for name in dirs:
  if os.path.islink(os.path.join(base,name)):raise ValueError('Unexpected pool symlink')
 for name in files:
  p=os.path.join(base,name)
  if os.path.islink(p):raise ValueError('Unexpected pool symlink')
  total+=os.stat(p).st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
print(total)
PYCODE
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time "$T"
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time "$T")
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s
' "$JOB" > "$P/a/8.txt"
cat "$P/a/8.txt"; TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M %N"
