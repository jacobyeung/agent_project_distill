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
fresh "$KH"
test "$(cat "$BUN/e0/rc")" = 0
fresh "$BUN/d0"
mkdir -m 700 "$BUN/d0"
cat > "$BUN/d0/r.py" <<'PYCODE'
import json,subprocess,sys
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_c5f3847d');h=b.parent/'x_3fdda0fb';k=b.parent/'x_c5f3847d'
assert not k.exists() and not k.is_symlink(), 'KH must be absent'
# FIX6 separates read-only evidence validation from allocation-time g.check.
# Refuse any deriver that is not byte-identical to the frozen final archive.
import hashlib
if (b/'d.py').is_symlink():raise SystemExit('REFUSED: linked deriver')
if hashlib.sha256((b/'d.py').read_bytes()).hexdigest()!='40c7908b891246e09bdd1878b1a54f039a00dfaa340362849a722ce5a8269f06':
 raise SystemExit('REFUSED: d.py SHA differs from final archive')

assert (b/'e0/rc').read_text().strip()=='0'
with (b/'compare.json').open('x') as f:
 subprocess.run([sys.executable,'-B',str(b/'d.py'),'--source',str(h),'--source-manifest-sha256','661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3','--packet',str(b),'--bundle',str(b),'--out',str(k),'--selection-evidence',str(b/'q/q.json'),'--evidence',str(b/'e')],stdout=f,check=True)
d=json.loads((b/'compare.json').read_text());assert d['status']=='READY' and d['missing_source_members']==[]
(k/'o').mkdir(mode=0o700,exist_ok=True)
print(json.dumps(d,sort_keys=True));print('READY; CPU proof only; production GO remains false')

PYCODE
cat > "$BUN/d0/r.sh" <<'SHCODE'
#!/bin/bash
set +x
set -uo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_c5f3847d
python3 -B "$BUN/d0/r.py"
rc=$?
printf '%s\n' "$rc" > "$BUN/d0/rc"
exit "$rc"
SHCODE
nohup nice -n 19 ionice -c 3 bash "$BUN/d0/r.sh" > "$BUN/d0/o.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$BUN/d0/pid"
echo "STARTED d0; pid $!; poll once per minute"
