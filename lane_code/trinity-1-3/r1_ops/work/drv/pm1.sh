#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_c5f3847d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_c5f3847d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
private "$O"
private "$BUN"
private "$KH"
job=$(cat "$BUN/job2.id" 2>/dev/null || cat "$BUN/job.id")
[[ "$job" =~ ^[0-9]+$ ]] || { echo 'REFUSED: invalid job id'; exit 4; }
squeue -u "$USER" -o '%i %j %P %T %M %R'
python3 -B - "$KH" "$job" <<'PYCODE'
import json,re,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2]
def redact(s):
 s=re.sub(r'https?://[^\s<>\"\x27]+','[URL WITHHELD]',s)
 s=re.sub(r'(?i)Bearer +[^ ,]+','Bearer [WITHHELD]',s)
 s=re.sub(r'ya29[.][A-Za-z0-9._-]+','[TOKEN WITHHELD]',s)
 return re.sub(r'(?i)(authorization|access_token|refresh_token|upload_id|password|secret|token)[\"\x27 	]*[:=][\"\x27 	]*[^\s,}]+',r'\1=[WITHHELD]',s)
for suffix in ('err','steps','w.steps'):
 p=k/'o'/(job+'.'+suffix);print(p.name)
 if not p.is_file():print('NOT_YET');continue
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-16384));raw=f.read()
 print(redact('\n'.join(raw.decode(errors='replace').splitlines()[-20:])))
p=k/'o'/(job+'.proof.json')
if not p.is_file():print(p.name,'NOT_YET')
else:
 d=json.loads(p.read_text());print(p.name);print(redact(json.dumps(d,sort_keys=True,indent=2)))
PYCODE
