#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_7f1589c1
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_7f1589c1
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
private "$KH"
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[0-9]+$ ]] || { echo 'REFUSED: invalid job id'; exit 4; }
squeue -u "$USER" -n a15_cot_ap05b8ac69 -o '%i %j %P %T %M %R'
sacct -X -j "$job" -o JobID,JobName%32,Partition,State,ExitCode -P
if [[ -f "$BUN/training.job.id" && ! -L "$BUN/training.job.id" ]]; then
 training=$(cat "$BUN/training.job.id")
 [[ "$training" =~ ^[1-9][0-9]*$ ]] || { echo 'REFUSED: invalid training ID'; exit 4; }
 sacct -X -j "$training" -o JobID,JobName%32,Partition,State,ExitCode -P
fi
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
b=Path('/project/community/jjyeung/okh7/i_7f1589c1')
t=b/'training.job.id'
if t.exists():
 assert not t.is_symlink()
 training=t.read_text().strip();assert re.fullmatch('[1-9][0-9]*',training) and training !=job
 print('CONTINUATION training_job='+training+' proof_job='+job)
 for suffix in ('err','steps','w.steps'):
  p=k/'o'/(training+'.'+suffix);print(p.name)
  if not p.is_file():print('NOT_YET');continue
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-16384));raw=f.read()
  print(redact(raw.decode(errors='replace')))
 record=b/'training.json'
 if record.is_file():print(redact(record.read_text()))
elif (b/'training.started').exists():print('UNCERTAIN training attempt; no training.job.id; inspect training.sbatch.out; do not resubmit')
PYCODE
