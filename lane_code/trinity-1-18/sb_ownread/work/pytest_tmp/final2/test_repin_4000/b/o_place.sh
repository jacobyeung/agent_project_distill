#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apf4b34bc0d517d
# D must identify the existing delivery directory, whose basename is opaque.
: "${D:?Set D to the existing opaque delivery directory}"
[[ "$D" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]
printf '%s  %s\n' 868c31372cdc06dcfc95b9fb147bde03f70d9747b91282a06fce58af6f0a5dfe "$D/1.tgz" | sha256sum -c -
test ! -e "$P"
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);m=json.loads((p/'PACKAGE.json').read_text());v=json.loads((p/'0.json').read_text())
for name,digest in m['files'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
assert m['token']==v['token']
with tarfile.open(p/'0.tgz') as t:c=json.load(t.extractfile('9.json'))
assert hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()==v['plan_sha256']
b=c['export_binding'];assert b['run']=='673bc60f' and b['step']==400 and b['member_directory']=='m400'
assert json.loads((p/'a/1.json').read_text())=={'pending':True}
print('Metadata verified; export fill required')
PYCODE
