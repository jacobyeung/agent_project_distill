#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_69d2930d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_69d2930d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
fresh "$KH"
test "$(cat "$BUN/e0/rc")" = 0
fresh "$BUN/d0"
mkdir -m 700 "$BUN/d0"
cat > "$BUN/d0/r.py" <<'PYCODE'
import json,subprocess,sys
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_69d2930d');h=b.parent/'x_3fdda0fb';k=b.parent/'x_69d2930d'
assert not k.exists() and not k.is_symlink(), 'KH must be absent'
# Evidence validation runs before allocation-time admission.
# Refuse any deriver that is not byte-identical to the frozen final archive.
import hashlib
if (b/'d.py').is_symlink():raise SystemExit('REFUSED: linked deriver')
if hashlib.sha256((b/'d.py').read_bytes()).hexdigest()!='7fefa38dc7d6ae05fac7d25fea2c71483cf312c1a42f99f9823636c57ce4d2ae':
 raise SystemExit('REFUSED: d.py SHA differs from final archive')

for name in ('n.json','records/n.json'):
 if hashlib.sha256((b/name).read_bytes()).hexdigest()!='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411':
  raise SystemExit('REFUSED: REMOVE list SHA differs from packet A')
cfg=json.loads((b/'config.json').read_text())
assert cfg['remove_files'][-1]==dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json',sha256='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
assert (b/'e0/rc').read_text().strip()=='0'
with (b/'compare.json').open('x') as f:
 subprocess.run([sys.executable,'-B',str(b/'d.py'),'--source',str(h),'--source-manifest-sha256','661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3','--packet',str(b),'--bundle',str(b),'--out',str(k),'--selection-evidence',str(b/'q/q.json'),'--evidence',str(b/'e')],stdout=f,check=True)
d=json.loads((b/'compare.json').read_text());assert d['status']=='READY' and d['missing_source_members']==[]
cur=json.loads((k/'k/0.json').read_text())
rows=[x for x in cur['extra'] if x.get('dest')=='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json']
assert rows==[dict(dest='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json',parts=[str(b/'n.json')],sha256='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')]
(k/'o').mkdir(mode=0o700,exist_ok=True)
print('PASS REMOVE n.json SHA 02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411; staged for packet A');print(json.dumps(d,sort_keys=True));print('READY; CPU proof only; production GO remains false')

PYCODE
cat > "$BUN/d0/r.sh" <<'SHCODE'
#!/bin/bash
set +x
set -uo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_69d2930d
python3 -B "$BUN/d0/r.py"
rc=$?
printf '%s\n' "$rc" > "$BUN/d0/rc"
exit "$rc"
SHCODE
nohup nice -n 19 ionice -c 3 bash "$BUN/d0/r.sh" > "$BUN/d0/o.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$BUN/d0/pid"
echo "STARTED d0; pid $!; poll once per minute"
