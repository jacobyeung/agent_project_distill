#!/bin/bash
# cont_ops17 r7: place A4 and B3, then fill A4 then B3 from old A's verified parts; one nohup run, no retries
set -euo pipefail
umask 077
K=/project/community/jjyeung/okh7; S=$K/813f42db/r7
declare -A P=([A]=$K/a15_cot_apd60a20ec01296 [B]=$K/a15_cot_apd50ba921ef1f4)
declare -A D=([A]=$K/a15_cot_ap2227412cc8721d20 [B]=$K/a15_cot_ap3e02451435328134)
declare -A H=([A]=dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459 [B]=55605e7680a27f4f1c30939b1492e6ce2eec520a21bc082d9f1d51d8feaba21e)
for X in A B; do
  printf '%s  %s\n' ${H[$X]} "${D[$X]}/1.tgz" | sha256sum -c -
  test ! -e "${P[$X]}"
done
for X in A B; do
  p=${P[$X]}; mkdir -m 700 "$p"; tar -xzf "${D[$X]}/1.tgz" -C "$p"; chmod 700 "$p/a"
  /usr/bin/python3 -I -s -B - "$p" <<'PYCODE'
import ast,hashlib,io,json,re,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);m=json.loads((p/'PACKAGE.json').read_text());v=json.loads((p/'0.json').read_text())
for name,digest in m['files'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
assert m['token']==v['token'] and p.name=='a15_cot_ap'+v['token'] and re.fullmatch('[a-f][0-9a-f]{10,15}',v['token'])
with tarfile.open(p/'0.tgz') as t:c=json.load(t.extractfile('9.json'))
assert hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()==v['plan_sha256']
assert c['token']==v['token']
b=c['export_binding'];assert b['run']=='673bc60f' and b['step']==200 and b['member_directory']=='m200'
assert json.loads((p/'a/1.json').read_text())=={'pending':True}
# a/5.py check_bundle_guard comparisons
lines=[l for l in (p/'BATCH.sh').read_text().splitlines() if l.startswith('b=bytes.fromhex(')];assert len(lines)==1
raw=bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(raw)) as t:f={x.name:t.extractfile(x).read() for x in t.getmembers()}
assert set(f)=={'0.py','0.json','7.py'} and json.loads(f['0.json'])==v and f['7.py']==(p/'a/6.py').read_bytes()
assert ("'a'+j+%r"%v['token']) in (p/'BATCH.sh').read_text()
print('Metadata and bundle verified',p.name)
PYCODE
done
cat > "$S/fill.sh" <<'SHELLCODE'
#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC
K=/project/community/jjyeung/okh7; S=$K/813f42db/r7
E=$K/a15_cot_apd72cdcff1e22a/a/e
OBJECT=q8/8865619b/673bc60f_m200.tar
for X in A B; do
  if [ $X = A ]; then P=$K/a15_cot_apd60a20ec01296; T=05:00:00; else P=$K/a15_cot_apd50ba921ef1f4; T=02:30:00; fi
  /usr/bin/python3 -I -s -B - "$P" "$E" <<'PYCODE'
import hashlib,json,sys,tarfile,re,os
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
with tarfile.open(p/'0.tgz') as t:b=json.load(t.extractfile('9.json'))['export_binding']
f=(e/'5').read_text().split()
assert len(f)==3 and f[0]==b['object'] and int(f[1])==21583032320 and f[2]=='795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'
for key,name in [('config','7'),('receipt','8'),('data_receipt','9')]:
 assert hashlib.sha256((e/name).read_bytes()).hexdigest()==b['preparation_sha256'][key]
for i in range(4): assert os.stat(e/str(i)).st_size==5395758080
PYCODE
  /usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 200 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
  PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
  if ! /usr/bin/python3 -I -s -B $S/d.py "$P/a/1.json" "$P/a/0.json" "$PREP" > "$S/dry_$X.out" 2>&1; then echo "$(date -u +%TZ) $X DRY FAILED"; tail -5 "$S/dry_$X.out"; exit 1; fi
  echo "$(date -u +%TZ) $X dry pass"
  (cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time $T)
  /usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1])
v=dict(passed=True,inputs_sha256=hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest(),export_sha256=hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest())
(p/'a/10.json').write_text(json.dumps(v,sort_keys=True)+'\n')
PYCODE
  printf '%s\n' 0 > "$P/a/1.txt"
  echo "$(date -u +%TZ) $X filled"
done
SHELLCODE
nohup bash "$S/fill.sh" </dev/null >"$S/fill.log" 2>&1 &
printf '%s\n' "$!" > "$S/fill.pid"; echo fill started pid $(cat $S/fill.pid)
