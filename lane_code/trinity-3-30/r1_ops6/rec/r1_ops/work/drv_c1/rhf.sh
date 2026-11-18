#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_7f1589c1
KH=/project/community/jjyeung/okh7/x_7f1589c1
printf '%s  %s\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet
[[ $# == 0 ]] || exit 2
python3 -I -B - "$BUN" "$KH" <<'END'
import json,re,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:]);j=b/'rehearsal.job.id'
assert not j.is_symlink();job=j.read_text().strip();assert re.fullmatch('[1-9][0-9]*',job)
p=k/'o'/(job+'.rehearsal.json')
if not p.exists():print('NOT_YET rehearsal receipt');raise SystemExit(4)
assert not p.is_symlink();d=json.loads(p.read_text())
if d.get('status')=='REHEARSAL_RUNNING':print('NOT_YET rehearsal running');raise SystemExit(4)
assert d.get('status') in ('REHEARSAL_OK','REHEARSAL_FAIL') and d.get('job')==job
assert d.get('rehearsal') is True and d.get('admission_executed') is False
print(json.dumps(d,sort_keys=True,indent=2))
print(d['status']+'; never a PASS proof')
raise SystemExit(0 if d['status']=='REHEARSAL_OK' and d['rc']==0 else 4)
END
