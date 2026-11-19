#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_ee227714
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_ee227714
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b' "$BUN/p.tar" | sha256sum -c --quiet; }
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
b=Path('/project/community/jjyeung/okh7/i_ee227714');h=b.parent/'x_3fdda0fb';k=b.parent/'x_ee227714'
assert not k.exists() and not k.is_symlink(), 'KH must be absent'
# Evidence validation runs before allocation-time admission.
# Refuse any deriver that is not byte-identical to the frozen final archive.
import hashlib
if (b/'d.py').is_symlink():raise SystemExit('REFUSED: linked deriver')
if hashlib.sha256((b/'d.py').read_bytes()).hexdigest()!='83e185a45f02a814ae19d76333666aa2707da229421566dadba0a2e9656b818c':
 raise SystemExit('REFUSED: d.py SHA differs from final archive')

for name in ('n.json','records/n.json'):
 if hashlib.sha256((b/name).read_bytes()).hexdigest()!='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411':
  raise SystemExit('REFUSED: REMOVE list SHA differs from packet C')
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
print('PASS REMOVE n.json SHA 02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411; staged for packet C');print(json.dumps(d,sort_keys=True));print('READY; CPU proof only; production GO remains false')

PYCODE
cat > "$BUN/d0/r.sh" <<'SHCODE'
#!/bin/bash
set +x
set -uo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_ee227714
python3 -B "$BUN/d0/r.py"
rc=$?
printf '%s\n' "$rc" > "$BUN/d0/rc"
exit "$rc"
SHCODE
nohup nice -n 19 ionice -c 3 bash "$BUN/d0/r.sh" > "$BUN/d0/o.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$BUN/d0/pid"
echo "STARTED d0; pid $!; poll once per minute"
