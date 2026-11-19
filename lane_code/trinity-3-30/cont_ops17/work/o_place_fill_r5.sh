#!/bin/bash
# cont_ops17: place A2 and B2 from their delivery dirs, then fill both (A2 first) from old A's verified parts; one nohup run, no retries
set -euo pipefail
umask 077
K=/project/community/jjyeung/okh7; S=$K/813f42db
declare -A P=([A]=$K/a15_cot_ap075d0b3e2f1ae [B]=$K/a15_cot_ape669778af6a6b)
declare -A D=([A]=$K/a15_cot_ap50d47ea09a3f72c0 [B]=$K/a15_cot_apd6150b4b31562008)
declare -A H=([A]=91a92a05b23f0dc5a7124df625dc432c70e67417234834731e05c1ebc2e99719 [B]=2128544d16bfdde2d891f07a219d55d5d8c790ba7a7de2a59b1f56ee4da1e5ae)
for X in A B; do
  printf '%s  %s\n' ${H[$X]} "${D[$X]}/1.tgz" | sha256sum -c -
  test ! -e "${P[$X]}"
done
for X in A B; do
  p=${P[$X]}; mkdir -m 700 "$p"; tar -xzf "${D[$X]}/1.tgz" -C "$p"; chmod 700 "$p/a"
  /usr/bin/python3 -I -s -B - "$p" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);m=json.loads((p/'PACKAGE.json').read_text());v=json.loads((p/'0.json').read_text())
for name,digest in m['files'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
assert m['token']==v['token'] and p.name=='a15_cot_ap'+v['token']
with tarfile.open(p/'0.tgz') as t:c=json.load(t.extractfile('9.json'))
assert hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()==v['plan_sha256']
assert c['token']==v['token']
b=c['export_binding'];assert b['run']=='673bc60f' and b['step']==200 and b['member_directory']=='m200'
assert json.loads((p/'a/1.json').read_text())=={'pending':True}
print('Metadata verified',p.name)
PYCODE
done
cat > "$S/fill.sh" <<'SHELLCODE'
#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC
K=/project/community/jjyeung/okh7; S=$K/813f42db
E=$K/a15_cot_apd72cdcff1e22a/a/e
OBJECT=q8/8865619b/673bc60f_m200.tar
for X in A B; do
  if [ $X = A ]; then P=$K/a15_cot_ap075d0b3e2f1ae; T=05:00:00; else P=$K/a15_cot_ape669778af6a6b; T=02:30:00; fi
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
  /usr/bin/python3 -I -s -B $S/d.py "$P/a/1.json" "$P/a/0.json" "$PREP" > "$S/dry_$X.out" 2>&1
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
